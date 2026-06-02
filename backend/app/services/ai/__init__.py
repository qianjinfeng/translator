"""AI translation provider registry and factory."""

from __future__ import annotations

from app.config import settings
from app.services.ai.base import TranslationProvider
from app.services.ai.mock import MockProvider
from app.services.ai.ollama import OllamaProvider

__all__ = [
    "MockProvider",
    "OllamaProvider",
    "TranslationProvider",
    "get_provider",
]


def get_provider(name: str) -> TranslationProvider:
    """Return a translation provider by name.

    Args:
        name: Provider identifier (``"mock"`` or ``"ollama"``).

    Returns:
        An instance of the requested provider.

    Raises:
        ValueError: If *name* is not recognised.
    """
    if name == "mock":
        return MockProvider()
    if name == "ollama":
        return OllamaProvider(settings)
    raise ValueError(f"Unknown translation provider: {name!r}")
