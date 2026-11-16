"""Extraktionen pro Paper sowie Aussagen (Claims) mit Belegen."""

from enum import StrEnum
from typing import Self
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from research_agent.models.base import Schema


class ExtractionField(StrEnum):
    METHOD = "method"
    DATASET = "dataset"
    METRIC = "metric"
    RESULT = "result"
    LIMITATION = "limitation"


class Extraction(Schema):
    """Ein Feld der Paper-Matrix.

    Entweder leer (`value is None`) oder mit wörtlichem Zitat und Chunk-ID belegt.
    """

    id: UUID = Field(default_factory=uuid4)
    paper_id: UUID
    field: ExtractionField
    value: str | None = None
    quote: str | None = None
    chunk_id: UUID | None = None
    needs_review: bool = False
    """Wert stammt z. B. aus einer Tabelle und muss manuell geprüft werden."""

    @model_validator(mode="after")
    def _value_needs_quote(self) -> Self:
        if self.value is not None and not (self.quote and self.chunk_id):
            raise ValueError("Ein Wert braucht ein Zitat und eine Chunk-ID")
        return self


class Verdict(StrEnum):
    SUPPORTED = "supported"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"


class Evidence(Schema):
    """Beleg für eine Aussage: verweist auf einen Chunk, optional mit Prüfurteil."""

    chunk_id: UUID
    quote: str | None = None
    abstract_only: bool = False
    verdict: Verdict | None = None
    verdict_reason: str | None = None

    @model_validator(mode="after")
    def _verdict_needs_reason(self) -> Self:
        if self.verdict is not None and not self.verdict_reason:
            raise ValueError("Ein Urteil braucht eine Begründung")
        return self


class Claim(Schema):
    """Einzelne Aussage der Synthese; ohne Beleg nicht zulässig."""

    id: UUID = Field(default_factory=uuid4)
    sub_question_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)
    revision: int = Field(default=0, ge=0, le=2)
    """Überarbeitungsrunde nach der Belegprüfung (höchstens zwei)."""
