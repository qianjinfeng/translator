"""Translation task, segment, and memory models."""

import uuid
from datetime import datetime, UTC
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from ..database import Base


class TaskStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    TRANSLATING = "translating"
    TRANSLATED = "translated"
    COMPLETED = "completed"
    FAILED = "failed"


class OutputMode(str, enum.Enum):
    BILINGUAL = "bilingual"
    STANDALONE = "standalone"


class TranslationTask(Base):
    __tablename__ = "translation_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_format: Mapped[str] = mapped_column(String(10), nullable=False)  # docx, pdf
    source_languages: Mapped[str] = mapped_column(String(20), nullable=False)  # en, en+de
    target_languages: Mapped[str] = mapped_column(String(20), nullable=False)  # zh, en+zh
    output_mode: Mapped[str] = mapped_column(String(20), default=OutputMode.BILINGUAL.value)

    # Config flags
    rag_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    image_translation_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # AI provider
    ai_provider: Mapped[str] = mapped_column(String(50), default="ollama")

    # Glossary (optional)
    glossary_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("glossaries.id"), nullable=True)

    # Status & progress
    status: Mapped[str] = mapped_column(String(20), default=TaskStatus.UPLOADED.value)
    total_segments: Mapped[int] = mapped_column(Integer, default=0)
    translated_segments: Mapped[int] = mapped_column(Integer, default=0)
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # File paths
    uploaded_file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    parsed_markdown_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    output_file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    segments: Mapped[list["TranslationSegment"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    glossary: Mapped["Glossary | None"] = relationship("Glossary")  # type: ignore[name-defined]  # noqa: F821


class TranslationSegment(Base):
    __tablename__ = "translation_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("translation_tasks.id"), nullable=False)
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    translated_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    segment_type: Mapped[str] = mapped_column(String(20), default="paragraph")  # paragraph, table_cell, header, list_item
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # formatting info, position, etc.

    # Relationships
    task: Mapped["TranslationTask"] = relationship(back_populates="segments")


class TranslationMemory(Base):
    """Stores translation pairs for RAG-based similarity retrieval."""

    __tablename__ = "translation_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # SHA256
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    translated_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_lang: Mapped[str] = mapped_column(String(20), nullable=False)
    target_lang: Mapped[str] = mapped_column(String(20), nullable=False)
    glossary_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
