"""Unified document parser interface.

Provides a single entry point for parsing and rebuilding documents
regardless of the source format (DOCX, PDF, etc.).
"""

from __future__ import annotations

from app.services.segment import DocumentSegment
from app.services.docx_parser import parse_docx
from app.services.docx_rebuilder import rebuild_docx
from app.services.pdf_parser import parse_pdf


class DocumentParser:
    """Unified interface for parsing and rebuilding documents."""

    SUPPORTED_FORMATS = {"docx", "pdf"}

    def parse(self, file_path: str, format: str) -> list[DocumentSegment]:
        """Parse a document into a list of DocumentSegments.

        Args:
            file_path: Absolute path to the document file.
            format: File format (``"docx"`` or ``"pdf"``).

        Returns:
            A list of DocumentSegment objects in reading order.
        """
        fmt = format.lower()
        if fmt == "docx":
            return parse_docx(file_path)
        elif fmt == "pdf":
            return parse_pdf(file_path)
        else:
            raise ValueError(
                f"Unsupported format '{format}'. "
                f"Supported formats: {', '.join(sorted(self.SUPPORTED_FORMATS))}"
            )

    def rebuild(
        self,
        original_path: str,
        segments: list[DocumentSegment],
        output_path: str,
        mode: str = "STANDALONE",
    ) -> str:
        """Rebuild a document from its original file and translated segments.

        Args:
            original_path: Path to the original document.
            segments: Translated segments (order must match parsed output).
            output_path: Where to write the rebuilt document.
            mode: ``"STANDALONE"`` or ``"BILINGUAL"``.

        Returns:
            The ``output_path`` that was written to.

        Raises:
            ValueError: If the original file format is not supported for rebuilding.
        """
        fmt = original_path.rsplit(".", 1)[-1].lower() if "." in original_path else ""

        if fmt == "docx":
            return rebuild_docx(original_path, segments, output_path, mode)
        elif fmt == "pdf":
            raise NotImplementedError(
                "Rebuilding PDFs is not yet supported. "
                "Use DOCX as the output format for translated PDF documents."
            )
        else:
            raise ValueError(
                f"Unsupported format '{fmt}' for rebuilding. "
                "Supported: docx"
            )
