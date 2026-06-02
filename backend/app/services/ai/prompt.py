"""Prompt builder for AI translation providers."""

from __future__ import annotations


def build_translation_prompt(
    source_lang: str,
    target_lang: str,
    glossary: dict[str, str] | None = None,
    document_context: str | None = None,
    rag_examples: list[tuple[str, str]] | None = None,
) -> str:
    """Build a system-level translation prompt for medical documents.

    Args:
        source_lang: Source language code (e.g. "EN", "DE").
        target_lang: Target language code (e.g. "ZH", "EN").
        glossary: Optional term mappings (source term -> target term).
        document_context: Optional document-level context description.
        rag_examples: Optional few-shot examples from translation memory.
            Each element is a ``(source_text, translated_text)`` tuple.

    Returns:
        A system prompt string.
    """
    parts: list[str] = [
        f"You are a medical document translator. Translate {source_lang} text to {target_lang}.",
        "Preserve all formatting, including punctuation, line breaks, and special characters.",
        "Maintain medical terminology accuracy.",
    ]

    if glossary:
        terms = ", ".join(f"{src}→{tgt}" for src, tgt in glossary.items())
        parts.append(f"Use these term mappings: {terms}")

    if document_context:
        parts.append(f"Document context: {document_context}")

    if rag_examples:
        example_lines: list[str] = []
        for src, tgt in rag_examples:
            example_lines.append(f"{source_lang}: {src}")
            example_lines.append(f"{target_lang}: {tgt}")
            example_lines.append("---")
        if example_lines:
            parts.append(
                "Reference translations (use these as style/terminology examples):\n"
                + "\n".join(example_lines)
            )

    return "\n\n".join(parts)


def build_segment_prompt(
    text: str,
    source_lang: str,
    target_lang: str,
) -> str:
    """Build a prompt for translating a single segment.

    Args:
        text: The segment source text.
        source_lang: Source language code.
        target_lang: Target language code.

    Returns:
        A segment-level prompt string.
    """
    return (
        f"Translate the following {source_lang} text to {target_lang}. "
        f"Preserve formatting.\n\n{text}"
    )
