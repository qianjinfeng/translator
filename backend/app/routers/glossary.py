"""Glossary API router.

Full CRUD for glossaries and entries, plus CSV/Excel import.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.glossary import Glossary, GlossaryEntry

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class GlossaryCreate(BaseModel):
    name: str
    department: str | None = None
    description: str | None = None


class GlossaryUpdate(BaseModel):
    name: str | None = None
    department: str | None = None
    description: str | None = None


class EntryCreate(BaseModel):
    source_term: str
    target_term: str
    context_note: str | None = None


class EntryUpdate(BaseModel):
    source_term: str | None = None
    target_term: str | None = None
    context_note: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _glossary_to_dict(glossary: Glossary, entry_count: int | None = None) -> dict[str, Any]:
    return {
        "id": glossary.id,
        "name": glossary.name,
        "department": glossary.department,
        "description": glossary.description,
        "entry_count": entry_count if entry_count is not None else len(glossary.entries),
        "created_at": glossary.created_at.isoformat(),
        "updated_at": glossary.updated_at.isoformat(),
    }


def _entry_to_dict(entry: GlossaryEntry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "glossary_id": entry.glossary_id,
        "source_term": entry.source_term,
        "target_term": entry.target_term,
        "context_note": entry.context_note,
        "created_at": entry.created_at.isoformat(),
    }


def _get_glossary_or_404(db: Session, glossary_id: str) -> Glossary:
    glossary = db.query(Glossary).filter(Glossary.id == glossary_id).first()
    if glossary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Glossary not found")
    return glossary


def _get_entry_or_404(db: Session, glossary_id: str, entry_id: int) -> GlossaryEntry:
    entry = (
        db.query(GlossaryEntry)
        .filter(GlossaryEntry.id == entry_id, GlossaryEntry.glossary_id == glossary_id)
        .first()
    )
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return entry


def _parse_csv(content: bytes) -> list[dict[str, str]]:
    """Parse CSV bytes into a list of {source_term, target_term, context_note} dicts."""
    text = content.decode("utf-8-sig")  # handles BOM
    reader = csv.DictReader(io.StringIO(text))
    rows: list[dict[str, str]] = []
    for row in reader:
        source = (row.get("source_term") or "").strip()
        target = (row.get("target_term") or "").strip()
        context = (row.get("context_note") or "").strip()
        if not source or not target:
            continue
        rows.append({
            "source_term": source,
            "target_term": target,
            "context_note": context or None,
        })
    return rows


def _parse_excel(content: bytes) -> list[dict[str, str]]:
    """Parse .xlsx bytes into a list of entry dicts."""
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
    ws = wb.active
    if ws is None:
        return []

    rows: list[dict[str, str]] = []
    header = None
    for row_cells in ws.iter_rows(values_only=True):
        if not any(c is not None for c in row_cells):
            continue
        if header is None:
            header = [str(c).strip().lower() if c else "" for c in row_cells]
            continue
        row_dict = dict(zip(header, [str(c) if c is not None else "" for c in row_cells]))
        source = (row_dict.get("source_term") or "").strip()
        target = (row_dict.get("target_term") or "").strip()
        context = (row_dict.get("context_note") or "").strip()
        if not source or not target:
            continue
        rows.append({
            "source_term": source,
            "target_term": target,
            "context_note": context or None,
        })
    return rows


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/")
def list_glossaries(db: Session = Depends(get_db)):
    """List all glossaries with entry counts."""
    glossaries = db.query(Glossary).order_by(Glossary.created_at.desc()).all()

    # Subquery count for efficiency
    count_subq = (
        db.query(
            GlossaryEntry.glossary_id,
            func.count(GlossaryEntry.id).label("cnt"),
        )
        .group_by(GlossaryEntry.glossary_id)
        .subquery()
    )

    result: list[dict[str, Any]] = []
    for g in glossaries:
        entry_count = 0
        for row in db.query(count_subq).filter(count_subq.c.glossary_id == g.id):
            entry_count = row.cnt
        result.append(_glossary_to_dict(g, entry_count))

    return {"glossaries": result}


@router.get("/{glossary_id}")
def get_glossary(glossary_id: str, db: Session = Depends(get_db)):
    """Get a single glossary with all entries."""
    glossary = _get_glossary_or_404(db, glossary_id)
    entries = (
        db.query(GlossaryEntry)
        .filter(GlossaryEntry.glossary_id == glossary_id)
        .order_by(GlossaryEntry.created_at.desc())
        .all()
    )
    return {
        "glossary": _glossary_to_dict(glossary, len(entries)),
        "entries": [_entry_to_dict(e) for e in entries],
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_glossary(body: GlossaryCreate, db: Session = Depends(get_db)):
    """Create an empty glossary."""
    glossary = Glossary(
        name=body.name,
        department=body.department,
        description=body.description,
    )
    db.add(glossary)
    db.commit()
    db.refresh(glossary)
    return _glossary_to_dict(glossary, 0)


@router.put("/{glossary_id}")
def update_glossary(glossary_id: str, body: GlossaryUpdate, db: Session = Depends(get_db)):
    """Update glossary metadata."""
    glossary = _get_glossary_or_404(db, glossary_id)
    if body.name is not None:
        glossary.name = body.name
    if body.department is not None:
        glossary.department = body.department
    if body.description is not None:
        glossary.description = body.description
    db.commit()
    db.refresh(glossary)
    return _glossary_to_dict(glossary)


@router.delete("/{glossary_id}")
def delete_glossary(glossary_id: str, db: Session = Depends(get_db)):
    """Delete a glossary and all its entries."""
    glossary = _get_glossary_or_404(db, glossary_id)
    db.delete(glossary)
    db.commit()
    return {"detail": "Glossary deleted"}


@router.post("/{glossary_id}/import")
def import_glossary_entries(
    glossary_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Import entries from CSV or Excel file."""
    glossary = _get_glossary_or_404(db, glossary_id)

    # Validate file extension
    filename = (file.filename or "").lower()
    if filename.endswith(".csv"):
        content = file.file.read()
        rows = _parse_csv(content)
    elif filename.endswith(".xlsx"):
        content = file.file.read()
        rows = _parse_excel(content)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a .csv or .xlsx file.",
        )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid entries found in the file. Ensure source_term and target_term columns are present.",
        )

    # Batch create entries
    entries = [GlossaryEntry(glossary_id=glossary.id, **row) for row in rows]
    db.add_all(entries)
    db.commit()

    return {
        "detail": f"Imported {len(entries)} entries",
        "imported_count": len(entries),
    }


@router.post("/{glossary_id}/entries", status_code=status.HTTP_201_CREATED)
def add_entry(glossary_id: str, body: EntryCreate, db: Session = Depends(get_db)):
    """Add a single entry to a glossary."""
    glossary = _get_glossary_or_404(db, glossary_id)
    entry = GlossaryEntry(
        glossary_id=glossary.id,
        source_term=body.source_term,
        target_term=body.target_term,
        context_note=body.context_note,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _entry_to_dict(entry)


@router.put("/{glossary_id}/entries/{entry_id}")
def update_entry(
    glossary_id: str,
    entry_id: int,
    body: EntryUpdate,
    db: Session = Depends(get_db),
):
    """Update an entry."""
    entry = _get_entry_or_404(db, glossary_id, entry_id)
    if body.source_term is not None:
        entry.source_term = body.source_term
    if body.target_term is not None:
        entry.target_term = body.target_term
    if body.context_note is not None:
        entry.context_note = body.context_note
    db.commit()
    db.refresh(entry)
    return _entry_to_dict(entry)


@router.delete("/{glossary_id}/entries/{entry_id}")
def delete_entry(glossary_id: str, entry_id: int, db: Session = Depends(get_db)):
    """Delete an entry."""
    entry = _get_entry_or_404(db, glossary_id, entry_id)
    db.delete(entry)
    db.commit()
    return {"detail": "Entry deleted"}
