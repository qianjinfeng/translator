"""Translation orchestration service.

Coordinates document parsing, AI translation, and document rebuilding.
Updates progress incrementally in the database for frontend polling.

Supports optional RAG translation memory (few-shot examples from
previously translated pairs) and image translation (placeholder).
"""

from __future__ import annotations

import logging
import os

from sqlalchemy.orm import Session as DBSession

from app.config import settings
from app.models.translation import TranslationTask, TranslationSegment, TaskStatus
from app.services.ai import get_provider
from app.services.parser import DocumentParser
from app.services.segment import DocumentSegment
from app.services.rag import TranslationMemoryService
from app.services.image_extractor import extract_images_from_docx

logger = logging.getLogger(__name__)


class TranslationService:
    """Orchestrates the full translation pipeline for a task."""

    def __init__(self, db: DBSession) -> None:
        self.db = db
        self.parser = DocumentParser()

    async def translate_task(self, task_id: str) -> None:
        """Run the translation pipeline for a given task.

        Loads the task and its segments from the database, translates
        segments one at a time through the configured AI provider,
        commits incremental progress, and rebuilds the output document
        on completion.  On failure the task is marked as failed with
        an error message.

        Args:
            task_id: The UUID of the TranslationTask to process.

        Raises:
            ValueError: If *task_id* does not exist.
        """
        task = (
            self.db.query(TranslationTask)
            .filter(TranslationTask.id == task_id)
            .first()
        )
        if not task:
            raise ValueError(f"Task {task_id} not found")

        segments = (
            self.db.query(TranslationSegment)
            .filter(TranslationSegment.task_id == task_id)
            .order_by(TranslationSegment.segment_index)
            .all()
        )

        if not segments:
            task.status = TaskStatus.FAILED.value
            task.error_message = "No segments to translate"
            self.db.commit()
            return

        # ------------------------------------------------------------------
        # Build optional glossary dict
        # ------------------------------------------------------------------
        glossary: dict[str, str] | None = None
        if task.glossary_id:
            from app.models.glossary import GlossaryEntry

            entries = (
                self.db.query(GlossaryEntry)
                .filter(GlossaryEntry.glossary_id == task.glossary_id)
                .all()
            )
            if entries:
                glossary = {e.source_term: e.target_term for e in entries}

        # ------------------------------------------------------------------
        # Image translation: extract images and create additional segments
        # ------------------------------------------------------------------
        if task.image_translation_enabled:
            image_segments = self._create_image_segments(task)
            if image_segments:
                for img_seg in image_segments:
                    self.db.add(img_seg)
                self.db.commit()

        # Re-fetch segments to include any newly added image segments
        segments = (
            self.db.query(TranslationSegment)
            .filter(TranslationSegment.task_id == task_id)
            .order_by(TranslationSegment.segment_index)
            .all()
        )

        # ------------------------------------------------------------------
        # Initialise optional RAG service
        # ------------------------------------------------------------------
        rag_service: TranslationMemoryService | None = None
        if task.rag_enabled:
            rag_service = TranslationMemoryService(self.db)

        # ------------------------------------------------------------------
        # Mark as translating
        # ------------------------------------------------------------------
        task.status = TaskStatus.TRANSLATING.value
        task.total_segments = len(segments)
        task.translated_segments = 0
        task.progress_pct = 0.0
        self.db.commit()

        try:
            provider = get_provider(task.ai_provider)

            for segment in segments:
                # --- RAG: retrieve similar pairs as few-shot examples ----------
                rag_examples: list[tuple[str, str]] | None = None
                if rag_service is not None:
                    similar = rag_service.find_similar(
                        segment.source_text,
                        task.source_languages,
                        task.target_languages,
                        limit=settings.rag_max_examples,
                    )
                    if similar:
                        rag_examples = [
                            (p["source_text"], p["translated_text"])
                            for p in similar
                        ]

                # Wrap the single segment for the provider interface
                doc_segments = [
                    DocumentSegment(
                        index=segment.segment_index,
                        source_text=segment.source_text,
                        segment_type=segment.segment_type,
                    )
                ]
                result = await provider.translate(
                    doc_segments,
                    task.source_languages,
                    task.target_languages,
                    glossary,
                    rag_examples,
                )
                if result:
                    segment.translated_text = result[0].source_text

                # --- RAG: store successful translation in memory --------------
                if rag_service is not None and segment.translated_text:
                    rag_service.store_translation_pair(
                        source_text=segment.source_text,
                        translated_text=segment.translated_text,
                        source_lang=task.source_languages,
                        target_lang=task.target_languages,
                        glossary_id=task.glossary_id,
                    )

                task.translated_segments += 1
                task.progress_pct = round(
                    (task.translated_segments / task.total_segments) * 100, 1
                )
                self.db.commit()

            # --------------------------------------------------------------
            # Rebuild the output document
            # --------------------------------------------------------------
            output_filename = (
                f"translated_{os.path.basename(task.uploaded_file_path)}"
            )
            output_path = os.path.join(settings.output_dir, output_filename)

            # Re-read segments to get fresh translated_text values
            all_segments = (
                self.db.query(TranslationSegment)
                .filter(TranslationSegment.task_id == task_id)
                .order_by(TranslationSegment.segment_index)
                .all()
            )

            rebuild_segments = [
                DocumentSegment(
                    index=s.segment_index,
                    source_text=s.translated_text or s.source_text,
                    segment_type=s.segment_type,
                )
                for s in all_segments
            ]

            # Map output_mode to the uppercase expected by the rebuilder
            rebuild_mode = (
                "BILINGUAL"
                if task.output_mode.lower() == "bilingual"
                else "STANDALONE"
            )

            self.parser.rebuild(
                task.uploaded_file_path,
                rebuild_segments,
                output_path,
                rebuild_mode,
            )

            task.output_file_path = output_path
            task.status = TaskStatus.COMPLETED.value
            task.progress_pct = 100.0
            self.db.commit()

        except Exception as exc:
            task.status = TaskStatus.FAILED.value
            task.error_message = str(exc)
            self.db.commit()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_image_segments(
        self, task: TranslationTask
    ) -> list[TranslationSegment]:
        """Extract images from the uploaded document and create segments.

        When *image_translation_enabled* is ``True`` on the task, this
        method reads the original uploaded file, extracts embedded images,
        and creates placeholder ``TranslationSegment`` rows with
        ``segment_type="image_text"`` and ``source_text="[IMAGE]"``.

        Returns:
            A list of new (unsaved) TranslationSegment objects, or an
            empty list if no images were found.
        """
        segments: list[TranslationSegment] = []
        fmt = task.original_format.lower()

        try:
            if fmt == "docx":
                images = extract_images_from_docx(task.uploaded_file_path)
            else:
                # PDF image extraction not yet implemented
                images = []

            if not images:
                return []

            # Determine the starting index for image segments
            # (append after existing text segments)
            existing = (
                self.db.query(TranslationSegment)
                .filter(TranslationSegment.task_id == task.id)
                .order_by(TranslationSegment.segment_index.desc())
                .first()
            )
            next_index = (existing.segment_index + 1) if existing else 0

            for img in images:
                seg = TranslationSegment(
                    task_id=task.id,
                    segment_index=next_index,
                    source_text="[IMAGE]",
                    segment_type="image_text",
                )
                segments.append(seg)
                next_index += 1

        except Exception:
            # Fail gracefully for image extraction — the text translation
            # should still proceed.
            logger.warning(
                "Image extraction failed for task %s (%s), continuing with text-only translation",
                task.id, fmt, exc_info=True,
            )

        return segments
