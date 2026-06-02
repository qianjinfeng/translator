"""Image extraction from documents.

Provides utilities to extract embedded images from DOCX and PDF
documents, returning image bytes and metadata for downstream
processing (e.g. OCR / vision-model translation).
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from typing import Any

from lxml import etree


@dataclass
class ImageData:
    """Represents a single image extracted from a document.

    Attributes:
        index: Zero-based image position in the document.
        image_bytes: Raw image file bytes.
        mime_type: MIME type (e.g. ``"image/png"``, ``"image/jpeg"``).
        alt_text: Optional alternative text / description.
    """

    index: int
    image_bytes: bytes
    mime_type: str = "image/png"
    alt_text: str = ""


# XML namespaces used in DOCX
_NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
_NS_PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
_NS_WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
_NS_REL = "http://schemas.openxmlformats.org/package/2006/relationships"

_MIME_MAP: dict[str, str] = {
    "image/png": "image/png",
    "image/jpeg": "image/jpeg",
    "image/gif": "image/gif",
    "image/bmp": "image/bmp",
    "image/tiff": "image/tiff",
    "image/svg+xml": "image/svg+xml",
    "image/x-emf": "image/x-emf",
    "image/x-wmf": "image/x-wmf",
}


def extract_images_from_docx(file_path: str) -> list[ImageData]:
    """Extract all embedded images from a DOCX file.

    Scans the document body XML for inline ``<w:drawing>`` elements,
    resolves the relationship IDs to media parts inside the ZIP archive,
    and returns their raw bytes and MIME types.

    Args:
        file_path: Absolute path to the ``.docx`` file.

    Returns:
        A list of :class:`ImageData` objects in document order, one per
        embedded image found.  Returns an empty list if no images or if
        the file cannot be read.
    """
    images: list[ImageData] = []
    seen_r_ids: set[str] = set()

    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            # Read the main document XML
            if "word/document.xml" not in zf.namelist():
                return []
            doc_xml = zf.read("word/document.xml")

            # Read relationships
            rels_xml = zf.read("word/_rels/document.xml.rels")
            rels_map = _parse_rels(rels_xml)

            # Parse document XML and find all drawings
            root = etree.fromstring(doc_xml)
            # Register namespaces for XPath
            ns_map = {
                "w": _NS_W,
                "wp": _NS_WP,
                "a": _NS_A,
                "pic": _NS_PIC,
                "r": _NS_R,
            }

            # Find all blip elements (image references) in the document body
            # Use .// for relative path since lxml doesn't allow // at root
            blip_elements = root.findall(".//w:drawing//a:blip", ns_map)

            index = 0
            for blip in blip_elements:
                embed_attr = blip.get(f"{{{_NS_R}}}embed")
                if not embed_attr or embed_attr in seen_r_ids:
                    continue
                seen_r_ids.add(embed_attr)

                # Resolve relationship to get media path
                media_path = rels_map.get(embed_attr)
                if not media_path:
                    continue

                # Ensure path starts with "word/" for proper zip lookup
                if not media_path.startswith("word/"):
                    media_path = f"word/{media_path}"

                # Read image bytes
                if media_path not in zf.namelist():
                    # Try without the "word/" prefix
                    alt_path = media_path.replace("word/", "", 1)
                    if alt_path in zf.namelist():
                        media_path = alt_path
                    else:
                        continue

                image_bytes = zf.read(media_path)

                # Determine MIME type from extension
                mime_type = _guess_mime(media_path)

                # Try to get alt text from the description element nearby
                alt_text = _extract_alt_text(blip, ns_map)

                images.append(
                    ImageData(
                        index=index,
                        image_bytes=image_bytes,
                        mime_type=mime_type,
                        alt_text=alt_text,
                    )
                )
                index += 1

    except (zipfile.BadZipFile, KeyError, OSError):
        # Not a valid zip / docx — return what we have (likely empty)
        pass

    return images


def extract_images_from_pdf(file_path: str) -> list[ImageData]:
    """Extract images from a PDF file.

    **MVP placeholder**: docling already skips picture items during
    parsing (see :mod:`app.services.pdf_parser`).  This function is a
    stub for future implementation using docling's :class:`PictureItem`
    or a dedicated PDF image extractor.

    Args:
        file_path: Absolute path to the ``.pdf`` file.

    Returns:
        An empty list (future implementation).
    """
    # TODO: Implement PDF image extraction using docling picture items
    # or PyMuPDF/fitz.
    return []


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


def _parse_rels(rels_xml: bytes) -> dict[str, str]:
    """Parse a ``.rels`` XML file and return ``{rId: Target}`` mapping.

    Args:
        rels_xml: Raw XML bytes of the relationships file.

    Returns:
        A dict mapping relationship IDs to target paths.
    """
    rels: dict[str, str] = {}
    root = etree.fromstring(rels_xml)
    for child in root:
        r_id = child.get("Id")
        target = child.get("Target")
        if r_id and target:
            rels[r_id] = target
    return rels


def _guess_mime(path: str) -> str:
    """Guess the MIME type from a file path extension."""
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "tiff": "image/tiff",
        "tif": "image/tiff",
        "svg": "image/svg+xml",
        "emf": "image/x-emf",
        "wmf": "image/x-wmf",
    }
    return mime_map.get(ext, "image/png")


def _extract_alt_text(blip_element: Any, ns_map: dict[str, str]) -> str:
    """Extract alternative/description text from a blip's parent chain.

    Looks for ``<wp:docPr>`` or ``<pic:cNvPr>`` elements that carry
    a ``name`` or ``descr`` attribute.

    Args:
        blip_element: The ``<a:blip>`` lxml element.
        ns_map: XML namespace prefix map for XPath.

    Returns:
        The alt text string, or an empty string if none found.
    """
    # Walk up to find the docPr / cNvPr element
    parent = blip_element.getparent()
    while parent is not None:
        # Check child elements for docPr
        for child in parent:
            local = etree.QName(child).localname
            if local == "docPr":
                return child.get("descr") or child.get("name") or ""
            if local == "cNvPr":
                return child.get("descr") or child.get("name") or ""
        parent = parent.getparent()
    return ""
