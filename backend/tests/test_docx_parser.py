"""Tests for the DOCX parser."""

import os
import tempfile

from docx import Document
from docx.shared import Pt, RGBColor

from app.services.docx_parser import parse_docx
from app.services.segment import DocumentSegment


def _create_simple_docx(path: str) -> None:
    """Create a minimal DOCX at *path* with paragraphs and a table."""
    doc = Document()
    doc.add_paragraph("Hello world", style="Normal")
    doc.add_paragraph("This is a second paragraph.")
    doc.save(path)


def _create_docx_with_table(path: str) -> None:
    """Create a DOCX containing a table."""
    doc = Document()
    doc.add_paragraph("Before table")
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "A1"
    table.cell(0, 1).text = "B1"
    table.cell(1, 0).text = "A2"
    table.cell(1, 1).text = "B2"
    doc.add_paragraph("After table")
    doc.save(path)


def _create_docx_with_headers_and_lists(path: str) -> None:
    """Create a DOCX with headings and list items."""
    doc = Document()
    doc.add_heading("Introduction", level=1)
    doc.add_paragraph("Some intro text.")
    doc.add_heading("Details", level=2)
    doc.add_paragraph("First item", style="List Bullet")
    doc.add_paragraph("Second item", style="List Bullet")
    doc.save(path)


def _create_docx_with_formatting(path: str) -> None:
    """Create a DOCX with varied text formatting."""
    doc = Document()
    para = doc.add_paragraph()
    run = para.add_run("Bold and italic text")
    run.bold = True
    run.italic = True
    run.font.name = "Arial"
    run.font.size = Pt(14)
    run.font.color.rgb = RGBColor(0xFF, 0x00, 0x00)
    doc.save(path)


class TestDocxParser:
    def test_parse_simple_paragraphs(self):
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            path = f.name
        try:
            _create_simple_docx(path)
            segments = parse_docx(path)
            assert len(segments) == 2
            assert segments[0].source_text == "Hello world"
            assert segments[1].source_text == "This is a second paragraph."
            for s in segments:
                assert s.segment_type == "paragraph"
                assert isinstance(s.index, int)
        finally:
            os.unlink(path)

    def test_parse_paragraph_types(self):
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            path = f.name
        try:
            _create_docx_with_formatting(path)
            segments = parse_docx(path)
            assert len(segments) == 1
            assert segments[0].source_text == "Bold and italic text"
            assert segments[0].segment_type == "paragraph"
        finally:
            os.unlink(path)

    def test_table_cells_extracted(self):
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            path = f.name
        try:
            _create_docx_with_table(path)
            segments = parse_docx(path)
            # Before table (1) + 4 cells + After table (1) = 6
            assert len(segments) == 6

            table_segments = [s for s in segments if s.segment_type == "table_cell"]
            assert len(table_segments) == 4
            assert table_segments[0].source_text == "A1"
            assert table_segments[0].metadata.get("row") == 0
            assert table_segments[0].metadata.get("col") == 0
            assert table_segments[1].source_text == "B1"
            assert table_segments[1].metadata.get("row") == 0
            assert table_segments[1].metadata.get("col") == 1
        finally:
            os.unlink(path)

    def test_headers_and_lists(self):
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            path = f.name
        try:
            _create_docx_with_headers_and_lists(path)
            segments = parse_docx(path)

            headers = [s for s in segments if s.segment_type == "header"]
            assert len(headers) == 2
            assert headers[0].source_text == "Introduction"
            assert headers[1].source_text == "Details"

            list_items = [s for s in segments if s.segment_type == "list_item"]
            assert len(list_items) == 2
            assert list_items[0].source_text == "First item"
            assert list_items[1].source_text == "Second item"
        finally:
            os.unlink(path)

    def test_formatting_metadata_preserved(self):
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            path = f.name
        try:
            _create_docx_with_formatting(path)
            segments = parse_docx(path)
            assert len(segments) == 1
            seg = segments[0]
            assert seg.metadata.get("bold") is True
            assert seg.metadata.get("italic") is True
            assert seg.metadata.get("font_name") == "Arial"
            assert seg.metadata.get("font_size") == 14.0
            # Color stored as hex string e.g. "FF0000"
            assert seg.metadata.get("color") == "FF0000"
        finally:
            os.unlink(path)

    def test_ordering_preserved(self):
        """Paragraphs, table, and more paragraphs keep correct order."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            path = f.name
        try:
            _create_docx_with_table(path)
            segments = parse_docx(path)
            texts = [s.source_text for s in segments]
            assert texts == ["Before table", "A1", "B1", "A2", "B2", "After table"]
        finally:
            os.unlink(path)

    def test_returns_list_of_document_segment(self):
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            path = f.name
        try:
            _create_simple_docx(path)
            segments = parse_docx(path)
            assert all(isinstance(s, DocumentSegment) for s in segments)
        finally:
            os.unlink(path)
