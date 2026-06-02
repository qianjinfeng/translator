"""Tests for MockProvider and provider factory."""

from __future__ import annotations

import asyncio

import pytest

from app.services.ai import MockProvider, get_provider
from app.services.segment import DocumentSegment


@pytest.fixture
def mock_provider() -> MockProvider:
    return MockProvider()


@pytest.fixture
def sample_segments() -> list[DocumentSegment]:
    return [
        DocumentSegment(index=0, source_text="The patient has a fever.", segment_type="paragraph"),
        DocumentSegment(index=1, source_text="Blood pressure is normal.", segment_type="paragraph"),
        DocumentSegment(index=2, source_text="The clinical test result is abnormal.", segment_type="paragraph"),
    ]


@pytest.mark.asyncio
async def test_mock_provider_returns_translated_segments_with_prefix(
    mock_provider: MockProvider,
    sample_segments: list[DocumentSegment],
) -> None:
    """EN -> ZH should prepend [ZH] and produce pinyin-like output."""
    result = await mock_provider.translate(sample_segments, "EN", "ZH")
    assert len(result) == 3
    for seg in result:
        assert seg.source_text.startswith("[ZH] ")


@pytest.mark.asyncio
async def test_mock_provider_zh_to_en(
    mock_provider: MockProvider,
) -> None:
    """ZH -> EN should prepend [EN]."""
    segments = [
        DocumentSegment(index=0, source_text="病人有发烧症状。", segment_type="paragraph"),
    ]
    result = await mock_provider.translate(segments, "ZH", "EN")
    assert len(result) == 1
    assert result[0].source_text.startswith("[EN] ")


@pytest.mark.asyncio
async def test_mock_provider_glossary_injection(
    mock_provider: MockProvider,
) -> None:
    """Glossary terms should appear in the mock-translated output."""
    segments = [
        DocumentSegment(index=0, source_text="The patient has a fever.", segment_type="paragraph"),
    ]
    glossary = {"fever": "发热"}
    result = await mock_provider.translate(segments, "EN", "ZH", glossary=glossary)
    translated = result[0].source_text
    assert "发热" in translated, f"Glossary term '发热' not found in: {translated}"


@pytest.mark.asyncio
async def test_mock_provider_introduces_delay(
    mock_provider: MockProvider,
) -> None:
    """Should delay ~50ms per segment (allow some tolerance)."""
    segments = [
        DocumentSegment(index=i, source_text=f"Segment {i}.", segment_type="paragraph")
        for i in range(5)
    ]

    start = asyncio.get_event_loop().time()
    await mock_provider.translate(segments, "EN", "ZH")
    elapsed = asyncio.get_event_loop().time() - start

    # 5 segments * 50ms = 250ms minimum; allow small tolerance
    assert (
        elapsed >= 0.20
    ), f"Expected at least 200ms delay, got {elapsed:.3f}s"


@pytest.mark.asyncio
async def test_mock_provider_preserves_metadata(
    mock_provider: MockProvider,
) -> None:
    """Segment metadata should be preserved (deep-copied) in output."""
    segments = [
        DocumentSegment(
            index=0,
            source_text="Hello world.",
            segment_type="header",
            metadata={"font": "bold", "style": "heading1"},
        ),
    ]
    result = await mock_provider.translate(segments, "EN", "ZH")
    assert result[0].index == 0
    assert result[0].segment_type == "header"
    assert result[0].metadata == {"font": "bold", "style": "heading1"}


@pytest.mark.asyncio
async def test_mock_provider_handles_mixed_language_input(
    mock_provider: MockProvider,
) -> None:
    """Should handle segments with mixed EN+DE content (no crash)."""
    segments = [
        DocumentSegment(index=0, source_text="Patient has fever and Husten.", segment_type="paragraph"),
        DocumentSegment(index=1, source_text="Blutdruck is normal.", segment_type="paragraph"),
    ]
    result = await mock_provider.translate(segments, "EN+DE", "EN+ZH")
    assert len(result) == 2
    # Each segment should have some translation marker
    for seg in result:
        assert seg.source_text != ""


# ------------------------------------------------------------------
# Provider factory tests
# ------------------------------------------------------------------


def test_get_provider_mock() -> None:
    provider = get_provider("mock")
    assert isinstance(provider, MockProvider)


def test_get_provider_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown translation provider"):
        get_provider("nonexistent")
