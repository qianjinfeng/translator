"""Glossary and glossary entry models."""

import uuid
from datetime import datetime, UTC
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Glossary(Base):
    __tablename__ = "glossaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    department: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    entries: Mapped[list["GlossaryEntry"]] = relationship(
        back_populates="glossary", cascade="all, delete-orphan"
    )


class GlossaryEntry(Base):
    __tablename__ = "glossary_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    glossary_id: Mapped[str] = mapped_column(String(36), ForeignKey("glossaries.id"), nullable=False)
    source_term: Mapped[str] = mapped_column(String(500), nullable=False)
    target_term: Mapped[str] = mapped_column(String(500), nullable=False)
    context_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    glossary: Mapped["Glossary"] = relationship(back_populates="entries")
