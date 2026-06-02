"""Unified intermediate format for parsed document segments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentSegment:
    """A single segment of a parsed document with its metadata.

    Attributes:
        index: Zero-based position of this segment in the document.
        source_text: The original text content.
        segment_type: One of "paragraph", "table_cell", "header", "list_item", "image_text".
        metadata: Formatting and structural information.
    """

    index: int
    source_text: str
    segment_type: str = "paragraph"
    metadata: dict[str, Any] = field(default_factory=dict)
