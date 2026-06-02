"""Rebuild a DOCX from original document + translated segments.

Supports two modes:
- BILINGUAL: insert the translated text after each original segment (styled
  differently, e.g. italic / blue).
- STANDALONE: replace original text with translation while preserving the
  original document structure and as much formatting as possible.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from docx import Document as DocxDocument
from docx.shared import Pt, RGBColor
from docx.text.paragraph import Paragraph
from docx.text.run import Run

from app.services.segment import DocumentSegment

# Colour used for translated text in bilingual mode
TRANSLATION_COLOR = RGBColor(0x1A, 0x56, 0xDB)
BILINGUAL_STYLE_NAME = "TranslatedText"


def _apply_formatting_to_run(run: Run, metadata: dict[str, Any]) -> None:
    """Apply formatting *metadata* (from a DocumentSegment) onto *run*."""
    if "font_name" in metadata:
        run.font.name = metadata["font_name"]
    if "font_size" in metadata:
        run.font.size = Pt(float(metadata["font_size"]))  # type: ignore[arg-type]
    if metadata.get("bold"):
        run.bold = True
    if metadata.get("italic"):
        run.italic = True
    if metadata.get("underline"):
        run.underline = True
    if "color" in metadata:
        try:
            run.font.color.rgb = RGBColor.from_string(metadata["color"])
        except (ValueError, AttributeError):
            pass


def _build_translated_para(
    orig_para: Paragraph,
    translated_text: str,
    metadata: dict[str, Any],
) -> Paragraph:
    """Build a new paragraph with the translated text, using formatting from
    *metadata* fallback to the original paragraph's first-run formatting."""
    new_para = deepcopy(orig_para._element)
    new_para = Paragraph(new_para, orig_para._parent)  # type: ignore[arg-type]

    # Clear existing runs and set text
    for run in new_para.runs:
        run._element.getparent().remove(run._element)

    run = new_para.add_run(translated_text)
    _apply_formatting_to_run(run, metadata)

    return new_para


def _get_paragraph_formatting(para: Paragraph) -> dict[str, Any]:
    """Return a best-effort formatting dict from the first run of *para*."""
    meta: dict[str, Any] = {}
    for run in para.runs:
        if run.text.strip():
            f = run.font
            if f.name:
                meta["font_name"] = f.name
            if f.size:
                meta["font_size"] = f.size.pt  # type: ignore[union-attr]
            if f.bold:
                meta["bold"] = True
            if f.italic:
                meta["italic"] = True
            if f.underline:
                meta["underline"] = True
            if f.color and f.color.rgb:
                meta["color"] = str(f.color.rgb)
            break
    return meta


def rebuild_docx(
    original_path: str,
    segments: list[DocumentSegment],
    output_path: str,
    mode: str = "STANDALONE",
) -> str:
    """Rebuild a DOCX file from the original document and translated segments.

    Args:
        original_path: Path to the original DOCX file.
        segments: Translated DocumentSegment list (order must match the parsed
            segments returned by ``parse_docx``).
        output_path: Where to write the output DOCX.
        mode: ``"STANDALONE"`` (replace original text) or ``"BILINGUAL"``
            (insert translated text after each original segment).

    Returns:
        The ``output_path`` that was written to.
    """
    doc = DocxDocument(original_path)
    mode_upper = mode.upper()

    if mode_upper == "BILINGUAL":
        _rebuild_bilingual(doc, segments)
    else:
        _rebuild_standalone(doc, segments)

    doc.save(output_path)
    return output_path


def _rebuild_standalone(
    doc: DocxDocument, segments: list[DocumentSegment]
) -> None:
    """STANDALONE mode: replace original text in-place, keeping structure."""
    body = doc.element.body
    seg_iter = iter(segments)

    for seg in seg_iter:
        _replace_segment_in_body(body, seg)

    # If there are extra segments beyond what we could replace, ignore them.


def _rebuild_bilingual(
    doc: DocxDocument, segments: list[DocumentSegment]
) -> None:
    """BILINGUAL mode: insert translated paragraph below each original one.

    Segments are processed in *descending* index order so that insertions
    do not shift the positions of pending segments.
    """
    body = doc.element.body
    for seg in sorted(segments, key=lambda s: s.index, reverse=True):
        _insert_translation_after_segment(body, seg, doc)


def _find_element_for_index(body, index: int):
    """Find the body child element that corresponds to the DocumentSegment at
    the given index by walking paragraphs and tables in order."""
    # We need to walk the body children and map back to segment indices.
    # Since we're rebuilding, the easiest approach is to match by index
    # stored temporarily in the segment metadata.
    child_idx = 0
    for child in body:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "p":
            if child_idx == index:
                return child
            child_idx += 1
        elif tag == "tbl":
            # Table provides multiple cells, skip over them in index space
            # but we don't replace the table, just the cells inside
            child_idx += _count_table_cells(child)
    return None


def _count_table_cells(tbl_element) -> int:
    """Count non-empty table cells in a table element."""
    from docx.oxml.ns import qn
    count = 0
    for row in tbl_element.findall(qn("w:tr")):
        for cell in row.findall(qn("w:tc")):
            text = "".join(
                p.text or ""
                for p in cell.findall(qn("w:p"))
                if p.text
            )
            if text.strip():
                count += 1
    return count or 1  # at least 1 if table has content


def _replace_segment_in_body(body, seg: DocumentSegment) -> None:
    """Replace the text of the body element corresponding to *seg.index*."""
    # Walk children until we find the matching element by index
    idx = 0
    for child in body:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "p":
            if idx == seg.index:
                # Replace paragraph text
                para = Paragraph(child, body)
                _clear_and_set_text(para, seg.source_text, seg.metadata)
                return
            idx += 1
        elif tag == "tbl":
            cell_count = _count_table_cells(child)
            # Check if segment index falls within this table
            if idx <= seg.index < idx + cell_count:
                _replace_table_cell_text(child, seg)
                return
            idx += cell_count


def _replace_table_cell_text(tbl_element, seg: DocumentSegment) -> None:
    """Replace text in a specific table cell identified by row/col in metadata."""
    from docx.oxml.ns import qn
    row = seg.metadata.get("row", 0)
    col = seg.metadata.get("col", 0)
    rows = tbl_element.findall(qn("w:tr"))
    if row < len(rows):
        cells = rows[row].findall(qn("w:tc"))
        if col < len(cells):
            cell = cells[col]
            # Clear existing paragraph text and set new
            for p_elem in cell.findall(qn("w:p")):
                for r_elem in p_elem.findall(qn("w:r")):
                    r_elem.getparent().remove(r_elem)
                # Add new run
                from docx.oxml import OxmlElement
                new_run = OxmlElement("w:r")
                new_text = OxmlElement("w:t")
                new_text.text = seg.source_text
                new_run.append(new_text)
                p_elem.append(new_run)


def _clear_and_set_text(
    para: Paragraph, text: str, metadata: dict[str, Any]
) -> None:
    """Remove all runs from *para* and add a single run with *text*."""
    for run in para.runs:
        run._element.getparent().remove(run._element)
    if text.strip():
        run = para.add_run(text)
        if metadata:
            _apply_formatting_to_run(run, metadata)


def _insert_translation_after_segment(
    body, seg: DocumentSegment, doc: DocxDocument
) -> None:
    """Insert a new paragraph containing the translation after the element for
    *seg.index*."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    idx = 0
    for child in body:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "p":
            if idx == seg.index:
                # Create a new paragraph element
                new_p = OxmlElement("w:p")
                new_run = OxmlElement("w:r")
                # Style the run differently for translations
                rPr = OxmlElement("w:rPr")
                # Italic
                italic_elem = OxmlElement("w:i")
                rPr.append(italic_elem)
                # Color
                color_elem = OxmlElement("w:color")
                color_elem.set(qn("w:val"), "1A56DB")
                rPr.append(color_elem)
                new_run.append(rPr)

                new_text = OxmlElement("w:t")
                new_text.set(qn("xml:space"), "preserve")
                new_text.text = seg.source_text
                new_run.append(new_text)
                new_p.append(new_run)

                # Insert after the current element
                child.addnext(new_p)
                return
            idx += 1
        elif tag == "tbl":
            cell_count = _count_table_cells(child)
            if idx <= seg.index < idx + cell_count:
                # For table cells in bilingual mode, we also append translation
                # after the cell paragraph
                _insert_translation_in_cell(child, seg)
                return
            idx += cell_count


def _insert_translation_in_cell(tbl_element, seg: DocumentSegment) -> None:
    """Append a translated paragraph inside the matching table cell."""
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    row = seg.metadata.get("row", 0)
    col = seg.metadata.get("col", 0)
    rows = tbl_element.findall(qn("w:tr"))
    if row < len(rows):
        cells = rows[row].findall(qn("w:tc"))
        if col < len(cells):
            cell = cells[col]
            # Add a new paragraph with the translation
            new_p = OxmlElement("w:p")
            new_run = OxmlElement("w:r")
            rPr = OxmlElement("w:rPr")
            italic_elem = OxmlElement("w:i")
            rPr.append(italic_elem)
            color_elem = OxmlElement("w:color")
            color_elem.set(qn("w:val"), "1A56DB")
            rPr.append(color_elem)
            new_run.append(rPr)
            new_text = OxmlElement("w:t")
            new_text.set(qn("xml:space"), "preserve")
            new_text.text = seg.source_text
            new_run.append(new_text)
            new_p.append(new_run)
            cell.append(new_p)
