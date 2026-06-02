"""Tests for the AI prompt builder module."""

from __future__ import annotations

from app.services.ai.prompt import build_segment_prompt, build_translation_prompt


class TestBuildTranslationPrompt:
    """System-level prompt builder tests."""

    def test_basic_prompt(self) -> None:
        prompt = build_translation_prompt("EN", "ZH")
        assert "Translate EN text to ZH" in prompt
        assert "medical terminology accuracy" in prompt

    def test_glossary_injected(self) -> None:
        glossary = {"fever": "发热", "blood pressure": "血压"}
        prompt = build_translation_prompt("EN", "ZH", glossary=glossary)
        assert "Use these term mappings:" in prompt
        assert "fever→发热" in prompt
        assert "blood pressure→血压" in prompt

    def test_glossary_empty(self) -> None:
        prompt = build_translation_prompt("EN", "ZH", glossary={})
        assert "Use these term mappings:" not in prompt

    def test_glossary_none(self) -> None:
        prompt = build_translation_prompt("EN", "ZH", glossary=None)
        assert "Use these term mappings:" not in prompt

    def test_document_context(self) -> None:
        prompt = build_translation_prompt(
            "EN", "ZH", document_context="Cardiology report."
        )
        assert "Document context: Cardiology report." in prompt

    def test_all_options(self) -> None:
        prompt = build_translation_prompt(
            "DE",
            "EN",
            glossary={"Blutdruck": "blood pressure"},
            document_context="General check-up",
        )
        assert "Translate DE text to EN" in prompt
        assert "Use these term mappings: Blutdruck→blood pressure" in prompt
        assert "Document context: General check-up" in prompt


class TestBuildSegmentPrompt:
    """Segment-level prompt builder tests."""

    def test_basic_segment_prompt(self) -> None:
        prompt = build_segment_prompt("The patient has a fever.", "EN", "ZH")
        assert "Translate the following EN text to ZH" in prompt
        assert "Preserve formatting." in prompt
        assert prompt.endswith("The patient has a fever.")

    def test_segment_prompt_german(self) -> None:
        prompt = build_segment_prompt("Patient hat Fieber.", "DE", "EN")
        assert "Translate the following DE text to EN" in prompt
        assert prompt.endswith("Patient hat Fieber.")
