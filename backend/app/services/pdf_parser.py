"""Parse PDF files into DocumentSegment list using docling.

docling converts PDFs into a structured document format (DoclingDocument)
which we then flatten into our unified DocumentSegment representation.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling_core.types.doc import DoclingDocument

from app.services.segment import DocumentSegment


def _get_label_str(item: object) -> str | None:
    """Extract the label string from a docling document item.

    ``DocItem`` and its subclasses (``TableItem``, ``PictureItem``) have a
    ``.label`` attribute that is a ``DocItemLabel`` enum; ``GroupItem`` uses
    ``GroupLabel``.  This helper normalises them to a lowercase string, or
    returns ``None`` when the item has no label.
    """
    label = getattr(item, "label", None)
    if label is None:
        return None
    # Enum values: try .value first, then str()
    if hasattr(label, "value"):
        return label.value
    return str(label)


def _get_item_text(item: object) -> str:
    """Extract text from a docling document item, if present."""
    text = getattr(item, "text", None)
    if text and isinstance(text, str):
        return text.strip()
    return ""


def _docling_to_segments(doc: DoclingDocument) -> list[DocumentSegment]:
    """Convert a DoclingDocument into a flat list of DocumentSegments.

    Walks the ``body`` items in reading order and maps:
      - text / paragraph    → "paragraph"
      - section-header      → "header"
      - list-item           → "list_item"
      - table               → "table_cell" (one per cell)
      - title, page-header  → "header"
      - caption, formula    → "paragraph"
    """
    segments: list[DocumentSegment] = []
    index = 0

    # iterate_items yields (NodeItem, level) tuples
    for item, _level in doc.iterate_items():
        label = _get_label_str(item)
        if label is None:
            continue

        # --- Table ---
        if label == "table" and hasattr(item, "data") and item.data is not None:
            data = item.data  # pandas DataFrame
            for row_idx, row_data in data.iterrows():
                for col_idx, cell_value in enumerate(row_data):
                    text = str(cell_value) if cell_value is not None else ""
                    text = text.strip()
                    if not text:
                        continue
                    segments.append(
                        DocumentSegment(
                            index=index,
                            source_text=text,
                            segment_type="table_cell",
                            metadata={
                                "source_label": label,
                                "row": int(row_idx),
                                "col": int(col_idx),
                            },
                        )
                    )
                    index += 1
            continue

        # --- Pictures / charts (skip, no textual content) ---
        if label in ("picture", "chart"):
            continue

        # --- Text-based items ---
        text = _get_item_text(item)
        if not text:
            continue

        # Map docling labels to our segment types
        if label in ("section_header", "title", "page_header"):
            seg_type = "header"
        elif label == "list_item":
            seg_type = "list_item"
        else:
            # text, paragraph, caption, formula, code, footnote, reference, etc.
            seg_type = "paragraph"

        segments.append(
            DocumentSegment(
                index=index,
                source_text=text,
                segment_type=seg_type,
                metadata={"source_label": label},
            )
        )
        index += 1

    return segments


def parse_pdf(file_path: str) -> list[DocumentSegment]:
    """Parse a PDF file into a list of DocumentSegments using docling.

    Args:
        file_path: Absolute path to the .pdf file.

    Returns:
        A list of DocumentSegment objects in reading order.
    """
    converter = DocumentConverter()
    result = converter.convert(file_path)
    doc = result.document
    return _docling_to_segments(doc)


def parse_pdf_from_bytes(
    content: bytes, filename: str = "document.pdf"
) -> list[DocumentSegment]:
    """Parse a PDF from raw bytes by writing to a temporary file.

    Useful for API endpoints that receive file uploads.
    """
    suffix = Path(filename).suffix if filename else ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        return parse_pdf(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
