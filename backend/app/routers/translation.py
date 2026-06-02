"""Translation API router -- upload, translate, download workflow."""

from __future__ import annotations

import json
import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session as DBSession

from app.config import settings
from app.database import get_db
from app.models.translation import TranslationTask, TranslationSegment, TaskStatus
from app.services.parser import DocumentParser
from app.services.translator import TranslationService

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /api/translation/upload
# ---------------------------------------------------------------------------


@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    config: str = Form(...),
    db: DBSession = Depends(get_db),
):
    """Upload a document and translate it.

    Accepts a DOCX or PDF file together with a JSON config string
    submitted as a form field.  Parses the document, persists a
    TranslationTask with its segments, runs the translation pipeline
    synchronously (MVP), and returns the task ID with its final status.
    """
    # --- Validate file -------------------------------------------------------
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = (
        file.filename.rsplit(".", 1)[-1].lower()
        if "." in file.filename
        else ""
    )
    if ext not in ("docx", "pdf"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported: docx, pdf",
        )

    # --- Parse config --------------------------------------------------------
    try:
        config_data = json.loads(config)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid config JSON")

    if not isinstance(config_data, dict):
        raise HTTPException(status_code=400, detail="Config must be a JSON object")

    # --- Save uploaded file --------------------------------------------------
    unique_name = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(settings.upload_dir, unique_name)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    with open(file_path, "wb") as f:
        f.write(content)

    # --- Parse document ------------------------------------------------------
    parser = DocumentParser()
    try:
        parsed_segments = parser.parse(file_path, ext)
    except Exception as exc:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=400, detail=f"Failed to parse document: {exc}"
        )

    # --- Create translation task ---------------------------------------------
    task = TranslationTask(
        original_filename=file.filename,
        original_format=ext,
        source_languages=config_data.get("source_languages", "en"),
        target_languages=config_data.get("target_languages", "zh"),
        output_mode=config_data.get("output_mode", "bilingual"),
        ai_provider=config_data.get("ai_provider", "mock"),
        rag_enabled=config_data.get("rag_enabled", False),
        image_translation_enabled=config_data.get("image_translation_enabled", False),
        glossary_id=config_data.get("glossary_id"),
        status=TaskStatus.PARSED.value,
        uploaded_file_path=file_path,
        total_segments=len(parsed_segments),
        translated_segments=0,
        progress_pct=0.0,
    )
    db.add(task)
    db.flush()  # populate task.id

    # --- Create translation segments -----------------------------------------
    for seg in parsed_segments:
        db_segment = TranslationSegment(
            task_id=task.id,
            segment_index=seg.index,
            source_text=seg.source_text,
            segment_type=seg.segment_type,
            metadata_json=json.dumps(seg.metadata) if seg.metadata else None,
        )
        db.add(db_segment)

    db.commit()

    # --- Run translation (sync for MVP) --------------------------------------
    service = TranslationService(db)
    await service.translate_task(task.id)

    db.refresh(task)

    return {
        "task_id": task.id,
        "status": task.status,
        "progress_pct": task.progress_pct,
    }


# ---------------------------------------------------------------------------
# GET /api/translation/tasks
# ---------------------------------------------------------------------------


@router.get("/tasks")
async def list_tasks(db: DBSession = Depends(get_db)):
    """List all translation tasks, newest first."""
    tasks = (
        db.query(TranslationTask)
        .order_by(TranslationTask.created_at.desc())
        .all()
    )
    return {
        "tasks": [
            {
                "id": t.id,
                "original_filename": t.original_filename,
                "original_format": t.original_format,
                "source_languages": t.source_languages,
                "target_languages": t.target_languages,
                "output_mode": t.output_mode,
                "status": t.status,
                "total_segments": t.total_segments,
                "translated_segments": t.translated_segments,
                "progress_pct": t.progress_pct,
                "error_message": t.error_message,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in tasks
        ]
    }


# ---------------------------------------------------------------------------
# GET /api/translation/tasks/{task_id}
# ---------------------------------------------------------------------------


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, db: DBSession = Depends(get_db)):
    """Get a single translation task with its segments."""
    task = (
        db.query(TranslationTask)
        .filter(TranslationTask.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    segments = (
        db.query(TranslationSegment)
        .filter(TranslationSegment.task_id == task_id)
        .order_by(TranslationSegment.segment_index)
        .all()
    )

    return {
        "task": {
            "id": task.id,
            "original_filename": task.original_filename,
            "original_format": task.original_format,
            "source_languages": task.source_languages,
            "target_languages": task.target_languages,
            "output_mode": task.output_mode,
            "ai_provider": task.ai_provider,
            "rag_enabled": task.rag_enabled,
            "image_translation_enabled": task.image_translation_enabled,
            "glossary_id": task.glossary_id,
            "status": task.status,
            "total_segments": task.total_segments,
            "translated_segments": task.translated_segments,
            "progress_pct": task.progress_pct,
            "error_message": task.error_message,
            "uploaded_file_path": task.uploaded_file_path,
            "output_file_path": task.output_file_path,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        },
        "segments": [
            {
                "id": seg.id,
                "segment_index": seg.segment_index,
                "source_text": seg.source_text,
                "translated_text": seg.translated_text,
                "segment_type": seg.segment_type,
            }
            for seg in segments
        ],
    }


# ---------------------------------------------------------------------------
# POST /api/translation/tasks/{task_id}/translate
# ---------------------------------------------------------------------------


@router.post("/tasks/{task_id}/translate")
async def translate_task_manual(
    task_id: str,
    db: DBSession = Depends(get_db),
):
    """Manually trigger or re-trigger translation for a task.

    Resets any previously translated segments and runs the pipeline
    again from scratch.
    """
    task = (
        db.query(TranslationTask)
        .filter(TranslationTask.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status == TaskStatus.TRANSLATING.value:
        raise HTTPException(
            status_code=409,
            detail="Translation is already in progress for this task",
        )

    # Reset translated segments
    segments = (
        db.query(TranslationSegment)
        .filter(TranslationSegment.task_id == task_id)
        .all()
    )
    for seg in segments:
        seg.translated_text = None
    db.commit()

    service = TranslationService(db)
    await service.translate_task(task.id)

    db.refresh(task)
    return {
        "task_id": task.id,
        "status": task.status,
        "progress_pct": task.progress_pct,
    }


# ---------------------------------------------------------------------------
# GET /api/translation/tasks/{task_id}/download
# ---------------------------------------------------------------------------


@router.get("/tasks/{task_id}/download")
async def download_document(
    task_id: str,
    db: DBSession = Depends(get_db),
):
    """Download the rebuilt (translated) document."""
    task = (
        db.query(TranslationTask)
        .filter(TranslationTask.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not task.output_file_path or not os.path.exists(task.output_file_path):
        raise HTTPException(
            status_code=404,
            detail="Translated document not available yet",
        )

    return FileResponse(
        path=task.output_file_path,
        filename=f"translated_{task.original_filename}",
        media_type=(
            "application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document"
        ),
    )
