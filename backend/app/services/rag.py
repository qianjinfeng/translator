"""RAG translation memory service.

Provides storage and retrieval of translation pairs for use as
few-shot examples during AI translation.  Supports exact hash-based
lookup and SQL LIKE substring fallback for similar-text retrieval.
"""

from __future__ import annotations

import hashlib

from sqlalchemy.orm import Session as DBSession

from app.models.translation import TranslationMemory


class TranslationMemoryService:
    """Service for storing and retrieving translation memory pairs."""

    def __init__(self, db: DBSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store_translation_pair(
        self,
        source_text: str,
        translated_text: str,
        source_lang: str,
        target_lang: str,
        glossary_id: str | None = None,
    ) -> TranslationMemory:
        """Hash *source_text* and persist the translation pair.

        Args:
            source_text: Original text segment.
            translated_text: Translated text segment.
            source_lang: Source language code (e.g. ``"en"``).
            target_lang: Target language code (e.g. ``"zh"``).
            glossary_id: Optional glossary UUID used for this translation.

        Returns:
            The newly created TranslationMemory row.
        """
        source_hash = self._hash_text(source_text)

        entry = TranslationMemory(
            source_hash=source_hash,
            source_text=source_text,
            translated_text=translated_text,
            source_lang=source_lang,
            target_lang=target_lang,
            glossary_id=glossary_id,
        )
        self.db.add(entry)
        self.db.commit()
        return entry

    def find_similar(
        self,
        source_text: str,
        source_lang: str,
        target_lang: str,
        limit: int = 5,
    ) -> list[dict[str, str]]:
        """Find similar translation pairs for *source_text*.

        First attempts an exact hash match (fast path).  If fewer than
        *limit* results are found, falls back to a SQL ``LIKE`` substring
        match over the same language pair.

        Returns:
            A list of dicts with ``"source_text"`` and ``"translated_text"``
            keys, ordered by recency (newest first), up to *limit* items.
        """
        results: list[dict[str, str]] = []
        seen_texts: set[str] = set()

        # --- 1. Exact hash match ------------------------------------------------
        source_hash = self._hash_text(source_text)
        exact_matches = (
            self.db.query(TranslationMemory)
            .filter(
                TranslationMemory.source_hash == source_hash,
                TranslationMemory.source_lang == source_lang,
                TranslationMemory.target_lang == target_lang,
            )
            .order_by(TranslationMemory.created_at.desc())
            .limit(limit)
            .all()
        )

        for m in exact_matches:
            if m.source_text not in seen_texts:
                results.append({
                    "source_text": m.source_text,
                    "translated_text": m.translated_text,
                })
                seen_texts.add(m.source_text)

        if len(results) >= limit:
            return results[:limit]

        # --- 2. LIKE substring fallback -----------------------------------------
        remaining = limit - len(results)
        like_pattern = f"%{source_text}%"
        like_matches = (
            self.db.query(TranslationMemory)
            .filter(
                TranslationMemory.source_text.ilike(like_pattern),
                TranslationMemory.source_lang == source_lang,
                TranslationMemory.target_lang == target_lang,
            )
            .order_by(TranslationMemory.created_at.desc())
            .limit(remaining + 10)  # fetch extra to account for dedup
            .all()
        )

        for m in like_matches:
            if m.source_text not in seen_texts:
                results.append({
                    "source_text": m.source_text,
                    "translated_text": m.translated_text,
                })
                seen_texts.add(m.source_text)
                if len(results) >= limit:
                    break

        return results[:limit]

    def get_context_for_segments(
        self,
        segments: list[str],
        source_lang: str,
        target_lang: str,
        limit: int = 5,
    ) -> list[dict[str, str]]:
        """Aggregate similar pairs across multiple segments.

        For each segment in *segments*, calls :meth:`find_similar` and
        deduplicates the aggregated results, returning up to *limit*
        pairs total.

        Args:
            segments: A list of source-text strings.
            source_lang: Source language code.
            target_lang: Target language code.
            limit: Maximum number of pairs to return.

        Returns:
            A deduplicated list of ``{"source_text", "translated_text"}``
            dicts.
        """
        aggregated: list[dict[str, str]] = []
        seen_texts: set[str] = set()

        for seg_text in segments:
            pairs = self.find_similar(seg_text, source_lang, target_lang, limit)
            for pair in pairs:
                if pair["source_text"] not in seen_texts:
                    aggregated.append(pair)
                    seen_texts.add(pair["source_text"])
                    if len(aggregated) >= limit:
                        return aggregated

        return aggregated

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_text(text: str) -> str:
        """Return the SHA-256 hex digest of *text*."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
