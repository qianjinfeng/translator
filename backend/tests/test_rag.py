"""Tests for the RAG translation memory service."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as DBSession

from app.database import Base
from app.services.rag import TranslationMemoryService


# ---------------------------------------------------------------------------
# In-memory SQLite engine for test isolation
# ---------------------------------------------------------------------------

_engine = create_engine("sqlite:///:memory:", echo=False)
_SessionLocal = sessionmaker(bind=_engine)


@pytest.fixture
def db() -> DBSession:
    """Yield a fresh DB session per test, rolling back after use."""
    Base.metadata.create_all(bind=_engine)
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def rag_service(db: DBSession) -> TranslationMemoryService:
    return TranslationMemoryService(db)


# ---------------------------------------------------------------------------
# Store tests
# ---------------------------------------------------------------------------


class TestTranslationMemoryStore:
    def test_store_basic_pair(self, rag_service: TranslationMemoryService) -> None:
        entry = rag_service.store_translation_pair(
            source_text="Hello world",
            translated_text="你好世界",
            source_lang="en",
            target_lang="zh",
        )
        assert entry.id is not None
        assert entry.source_text == "Hello world"
        assert entry.translated_text == "你好世界"
        assert entry.source_lang == "en"
        assert entry.target_lang == "zh"
        assert entry.glossary_id is None

    def test_store_with_glossary(self, rag_service: TranslationMemoryService) -> None:
        entry = rag_service.store_translation_pair(
            source_text="fever",
            translated_text="发热",
            source_lang="en",
            target_lang="zh",
            glossary_id="glossary-123",
        )
        assert entry.glossary_id == "glossary-123"

    def test_store_generates_hash(self, rag_service: TranslationMemoryService) -> None:
        entry = rag_service.store_translation_pair(
            source_text="The patient has a fever.",
            translated_text="病人发烧了。",
            source_lang="en",
            target_lang="zh",
        )
        # SHA256 is always 64 hex chars
        assert len(entry.source_hash) == 64
        assert isinstance(entry.source_hash, str)

    def test_same_text_produces_same_hash(
        self, rag_service: TranslationMemoryService
    ) -> None:
        e1 = rag_service.store_translation_pair(
            source_text="Same text",
            translated_text="相同文本",
            source_lang="en",
            target_lang="zh",
        )
        e2 = rag_service.store_translation_pair(
            source_text="Same text",
            translated_text="相同文本",
            source_lang="en",
            target_lang="zh",
        )
        assert e1.source_hash == e2.source_hash


# ---------------------------------------------------------------------------
# Find similar tests
# ---------------------------------------------------------------------------


class TestFindSimilar:
    def test_exact_hash_match(self, rag_service: TranslationMemoryService) -> None:
        rag_service.store_translation_pair(
            "The patient has a fever.", "病人发烧了。", "en", "zh"
        )
        results = rag_service.find_similar(
            "The patient has a fever.", "en", "zh"
        )
        assert len(results) == 1
        assert results[0]["source_text"] == "The patient has a fever."
        assert results[0]["translated_text"] == "病人发烧了。"

    def test_exact_hash_match_different_lang(
        self, rag_service: TranslationMemoryService
    ) -> None:
        """Stored en->zh pair should NOT match en->de lookup."""
        rag_service.store_translation_pair(
            "Hello", "你好", "en", "zh"
        )
        results = rag_service.find_similar("Hello", "en", "de")
        assert len(results) == 0

    def test_exact_hash_no_match_returns_empty(
        self, rag_service: TranslationMemoryService
    ) -> None:
        results = rag_service.find_similar("Nothing stored", "en", "zh")
        assert results == []

    def test_like_fallback(self, rag_service: TranslationMemoryService) -> None:
        """Exact hash misses but LIKE finds a similar text."""
        rag_service.store_translation_pair(
            "The patient has a high fever and needs treatment.",
            "病人高烧需要治疗。",
            "en",
            "zh",
        )
        # Different wording but contains "fever"
        results = rag_service.find_similar("fever", "en", "zh")
        assert len(results) >= 1
        assert "fever" in results[0]["source_text"]

    def test_limit_respected(self, rag_service: TranslationMemoryService) -> None:
        for i in range(10):
            rag_service.store_translation_pair(
                f"Segment number {i}.", f"段落{i}。", "en", "zh"
            )
        results = rag_service.find_similar("Segment", "en", "zh", limit=3)
        assert len(results) == 3

    def test_multiple_stored_pairs(
        self, rag_service: TranslationMemoryService
    ) -> None:
        rag_service.store_translation_pair("Hello", "你好", "en", "zh")
        rag_service.store_translation_pair("World", "世界", "en", "zh")
        results = rag_service.find_similar("Hello", "en", "zh")
        assert len(results) == 1
        assert results[0]["source_text"] == "Hello"


# ---------------------------------------------------------------------------
# Get context for segments tests
# ---------------------------------------------------------------------------


class TestGetContextForSegments:
    def test_aggregates_across_segments(
        self, rag_service: TranslationMemoryService
    ) -> None:
        rag_service.store_translation_pair(
            "Heart rate is normal.", "心率正常。", "en", "zh"
        )
        rag_service.store_translation_pair(
            "Blood pressure is high.", "血压高。", "en", "zh"
        )

        results = rag_service.get_context_for_segments(
            ["Heart rate", "Blood pressure"], "en", "zh", limit=5
        )
        assert len(results) == 2

    def test_deduplicates(self, rag_service: TranslationMemoryService) -> None:
        rag_service.store_translation_pair(
            "The patient is stable.", "病人稳定。", "en", "zh"
        )
        results = rag_service.get_context_for_segments(
            ["The patient is stable.", "patient is stable"], "en", "zh", limit=5
        )
        # Should not duplicate the same source_text
        sources = [r["source_text"] for r in results]
        assert len(sources) == len(set(sources))

    def test_empty_segments_list(
        self, rag_service: TranslationMemoryService
    ) -> None:
        results = rag_service.get_context_for_segments([], "en", "zh")
        assert results == []

    def test_no_matches(self, rag_service: TranslationMemoryService) -> None:
        results = rag_service.get_context_for_segments(
            ["Nothing here"], "en", "zh"
        )
        assert results == []
