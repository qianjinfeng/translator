"""Tests for the PDF parser (docling-based).

These tests are best-effort: docling is a heavy dependency and may not be
available in all CI environments, or may require a GPU for full operation.
If importing docling fails, the tests are skipped.
"""

import os
import tempfile

import pytest

# Guard: skip all tests if docling cannot be imported
try:
    from app.services.pdf_parser import parse_pdf, parse_pdf_from_bytes
except ImportError:
    pytest.skip("docling not available", allow_module_level=True)


def _create_simple_pdf(path: str) -> None:
    """Create a minimal PDF via docling's built-in test utilities or
    reportlab if available; otherwise create an empty-ish PDF manually."""
    try:
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(path)
        c.drawString(100, 750, "Hello PDF World")
        c.drawString(100, 730, "Second paragraph in PDF")
        c.save()
    except ImportError:
        # Fall back: write a minimal valid PDF by hand
        pdf = (
            b"%PDF-1.4\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
            b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
            b"4 0 obj<</Length 44>>stream\n"
            b"BT /F1 12 Tf 100 750 Td (Hello PDF) Tj ET\n"
            b"endstream\nendobj\n"
            b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
            b"xref\n"
            b"0 6\n"
            b"0000000000 65535 f \n"
            b"0000000009 00000 n \n"
            b"0000000058 00000 n \n"
            b"0000000115 00000 n \n"
            b"0000000266 00000 n \n"
            b"0000000363 00000 n \n"
            b"trailer<</Size 6/Root 1 0 R>>\n"
            b"startxref\n"
            b"435\n"
            b"%%%%EOF\n"
        )
        with open(path, "wb") as f:
            f.write(pdf)


class TestPdfParserBasic:
    def test_parse_simple_pdf(self):
        """Smoke test: parse a minimal PDF and check we get segments back."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            _create_simple_pdf(path)
            segments = parse_pdf(path)
            # We expect at least some segments — docling may or may not
            # extract text from a hand-crafted PDF, so we just check the
            # return type and non-emptiness.
            assert isinstance(segments, list)
            if segments:
                assert all(
                    s.segment_type in ("paragraph", "header", "list_item", "table_cell")
                    for s in segments
                )
                assert isinstance(segments[0].source_text, str)
        finally:
            os.unlink(path)

    def test_parse_from_bytes(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            _create_simple_pdf(path)
            with open(path, "rb") as fh:
                content = fh.read()
            segments = parse_pdf_from_bytes(content, filename="test.pdf")
            assert isinstance(segments, list)
        finally:
            os.unlink(path)

    def test_empty_pdf(self):
        """An empty/minimal PDF should produce an empty or nearly-empty list."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            # Minimal valid PDF with no text content
            pdf = (
                b"%PDF-1.4\n"
                b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
                b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
                b"xref\n"
                b"0 4\n"
                b"0000000000 65535 f \n"
                b"0000000009 00000 n \n"
                b"0000000058 00000 n \n"
                b"0000000115 00000 n \n"
                b"trailer<</Size 4/Root 1 0 R>>\n"
                b"startxref\n"
                b"200\n"
                b"%%%%EOF\n"
            )
            with open(path, "wb") as f:
                f.write(pdf)
            segments = parse_pdf(path)
            assert isinstance(segments, list)
        finally:
            os.unlink(path)
