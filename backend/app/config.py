"""Application configuration via pydantic-settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    app_name: str = "Medical Document Translator"
    debug: bool = True

    # Database
    database_url: str = "sqlite:///./data/translator.db"

    # Ollama
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "qwen3:14b"

    # Cloud AI (optional)
    anthropic_api_key: str = ""
    deepl_api_key: str = ""

    # File storage
    upload_dir: str = "./data/uploads"
    output_dir: str = "./data/outputs"

    # RAG
    rag_enabled_by_default: bool = False
    rag_similarity_threshold: float = 0.85
    rag_max_examples: int = 5

    # Image translation
    image_translation_enabled_by_default: bool = False

    # Limits
    max_upload_size_mb: int = 50
    translation_timeout_seconds: int = 300


settings = Settings()

# Ensure data directories exist
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.output_dir).mkdir(parents=True, exist_ok=True)
Path(settings.database_url).parent.mkdir(parents=True, exist_ok=True)
