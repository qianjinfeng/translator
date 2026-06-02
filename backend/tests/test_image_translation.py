"""Tests for image extraction and image translator service."""

from __future__ import annotations

import os
import tempfile

import pytest

from docx import Document
from docx.shared import Inches

from app.services.image_extractor import (
    extract_images_from_docx,
    extract_images_from_pdf,
    ImageData,
)
from app.services.image_translator import ImageTranslatorService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_docx_with_image(path: str) -> str:
    """Create a minimal DOCX with a single embedded 1x1 PNG image."""
    doc = Document()

    # Write a valid minimal PNG file to a temp location
    # 1x1 pixel red PNG, generated with known valid bytes
    png_bytes = _make_minimal_png()
    png_fd, png_path = tempfile.mkstemp(suffix=".png")
    os.write(png_fd, png_bytes)
    os.close(png_fd)

    try:
        doc.add_paragraph("Text before image.")
        doc.add_picture(png_path, width=Inches(1.0))
        doc.add_paragraph("Text after image.")
        doc.save(path)
    finally:
        os.unlink(png_path)

    return path


def _make_minimal_png() -> bytes:
    """Return a valid 1x1 minimal PNG (single red pixel) using zlib.

    Builds a minimal PNG with IHDR, IDAT (raw red pixel compressed),
    and IEND chunks.
    """
    import struct
    import zlib

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        """Build a PNG chunk: length + type + data + CRC."""
        body = chunk_type + data
        return struct.pack(">I", len(data)) + body + struct.pack(
            ">I", zlib.crc32(body) & 0xFFFFFFFF
        )

    signature = b"\x89PNG\r\n\x1a\n"
    # IHDR: 1x1, 8-bit RGBA
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    # IDAT: single red pixel (R=255, G=0, B=0, A=255)
    raw_pixel = b"\xff\x00\x00\xff"
    compressed = zlib.compress(raw_pixel)
    return (
        signature
        + _chunk(b"IHDR", ihdr_data)
        + _chunk(b"IDAT", compressed)
        + _chunk(b"IEND", b"")
    )


def _create_docx_without_images(path: str) -> str:
    """Create a DOCX with no images."""
    doc = Document()
    doc.add_paragraph("Only text.")
    doc.save(path)
    return path


# ---------------------------------------------------------------------------
# Image Extractor Tests
# ---------------------------------------------------------------------------


class TestExtractImagesFromDocx:
    def test_no_images_returns_empty_list(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            path = f.name
        try:
            _create_docx_without_images(path)
            images = extract_images_from_docx(path)
            assert images == []
        finally:
            os.unlink(path)

    def test_non_existent_file_returns_empty(self) -> None:
        images = extract_images_from_docx("/nonexistent/file.docx")
        assert images == []

    def test_invalid_file_returns_empty(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            f.write(b"not a valid zip")
            path = f.name
        try:
            images = extract_images_from_docx(path)
            assert images == []
        finally:
            os.unlink(path)

    def test_extracted_images_have_expected_structure(self) -> None:
        """If an image is embedded, ImageData fields should be populated."""
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            path = f.name
        try:
            _create_docx_with_image(path)
            images = extract_images_from_docx(path)
            # A docx with add_picture should have at least 1 image
            assert len(images) >= 1
            img = images[0]
            assert isinstance(img, ImageData)
            assert isinstance(img.index, int)
            assert isinstance(img.image_bytes, bytes)
            assert len(img.image_bytes) > 0
            assert img.mime_type in ("image/png", "image/jpeg")
        finally:
            os.unlink(path)


class TestExtractImagesFromPdf:
    def test_returns_empty_list(self) -> None:
        images = extract_images_from_pdf("/fake/file.pdf")
        assert images == []


# ---------------------------------------------------------------------------
# Image Translator Service Tests
# ---------------------------------------------------------------------------


class TestImageTranslatorService:
    @pytest.mark.asyncio
    async def test_process_image_returns_placeholder(self) -> None:
        service = ImageTranslatorService()
        image = ImageData(
            index=0,
            image_bytes=b"fake-image-data",
            mime_type="image/png",
            alt_text="test",
        )
        result = await service.process_image(image)
        assert result == "[Image text: requires vision model]"

    @pytest.mark.asyncio
    async def test_process_images_multiple(self) -> None:
        service = ImageTranslatorService()
        images = [
            ImageData(index=0, image_bytes=b"img1", mime_type="image/png"),
            ImageData(index=1, image_bytes=b"img2", mime_type="image/jpeg"),
        ]
        results = await service.process_images(images)
        assert len(results) == 2
        for text in results:
            assert text == "[Image text: requires vision model]"

    @pytest.mark.asyncio
    async def test_process_images_empty(self) -> None:
        service = ImageTranslatorService()
        results = await service.process_images([])
        assert results == []
