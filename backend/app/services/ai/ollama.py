"""Ollama-based translation provider."""

from __future__ import annotations

from copy import deepcopy

import httpx

from app.config import Settings
from app.services.ai.base import TranslationProvider
from app.services.ai.prompt import build_segment_prompt, build_translation_prompt
from app.services.segment import DocumentSegment


class OllamaProvider(TranslationProvider):
    """Translation provider backed by an Ollama local LLM.

    Connects to the Ollama API at *ollama_base_url* and uses the configured
    model (default *qwen3:14b*) to translate medical document segments.
    Supports configurable timeouts and graceful error handling.
    """

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model
        self._timeout = settings.translation_timeout_seconds

    async def translate(
        self,
        segments: list[DocumentSegment],
        source_lang: str,
        target_lang: str,
        glossary: dict[str, str] | None = None,
        rag_examples: list[tuple[str, str]] | None = None,
    ) -> list[DocumentSegment]:
        system_prompt = build_translation_prompt(
            source_lang, target_lang, glossary, rag_examples=rag_examples,
        )
        result: list[DocumentSegment] = []

        async with httpx.AsyncClient(timeout=httpx.Timeout(self._timeout)) as client:
            for seg in segments:
                segment_prompt = build_segment_prompt(
                    seg.source_text, source_lang, target_lang
                )
                full_prompt = f"{system_prompt}\n\n{segment_prompt}"

                try:
                    response = await client.post(
                        f"{self._base_url}/api/generate",
                        json={
                            "model": self._model,
                            "prompt": full_prompt,
                            "stream": False,
                            "options": {
                                "num_predict": 2048,
                                "temperature": 0.1,
                            },
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    translated_text = data.get("response", seg.source_text)

                except (
                    httpx.ConnectError,
                    httpx.TimeoutException,
                    httpx.HTTPStatusError,
                ) as exc:
                    translated_text = f"[OllamaError: {type(exc).__name__}] {seg.source_text}"

                result.append(
                    DocumentSegment(
                        index=seg.index,
                        source_text=translated_text,
                        segment_type=seg.segment_type,
                        metadata=deepcopy(seg.metadata),
                    )
                )

        return result
