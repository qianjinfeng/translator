"""Abstract base class for AI translation providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.segment import DocumentSegment


class TranslationProvider(ABC):
    """Abstract translation provider that all backends must implement."""

    @abstractmethod
    async def translate(
        self,
        segments: list[DocumentSegment],
        source_lang: str,
        target_lang: str,
        glossary: dict[str, str] | None = None,
        rag_examples: list[tuple[str, str]] | None = None,
    ) -> list[DocumentSegment]:
        """Translate a list of document segments from source_lang to target_lang.

        Args:
            segments: Document segments to translate.
            source_lang: Source language code (e.g. "EN", "DE").
            target_lang: Target language code (e.g. "ZH", "EN").
            glossary: Optional term mappings to enforce in translations.
            rag_examples: Optional few-shot examples from translation memory.
                Each element is a ``(source_text, translated_text)`` tuple.

        Returns:
            Translated document segments.
        """
        ...
