"""Paper-Metadaten und Screening-Entscheidungen."""

import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Self
from uuid import UUID, uuid4

from pydantic import Field, field_validator, model_validator

from research_agent.models.base import Schema, Source

_DOI_PREFIX = re.compile(r"^(https?://(dx\.)?doi\.org/|doi:)", re.IGNORECASE)


class Paper(Schema):
    """Ein Paper mit seinen Identifikatoren aus allen Quellen.

    IDs werden normalisiert, damit die Deduplizierung sie direkt vergleichen kann:
    DOI kleingeschrieben ohne URL-Präfix, OpenAlex-ID ohne URL, arXiv-ID ohne `arXiv:`.
    """

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(min_length=1)
    abstract: str | None = None
    authors: list[str] = Field(default_factory=list)
    year: int | None = Field(default=None, ge=1000, le=2100)
    venue: str | None = None
    doi: str | None = None
    openalex_id: str | None = None
    s2_id: str | None = None
    arxiv_id: str | None = None
    sources: set[Source] = Field(default_factory=set)
    oa_pdf_url: str | None = None
    cited_by_count: int | None = Field(default=None, ge=0)

    @field_validator("doi")
    @classmethod
    def _normalize_doi(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = _DOI_PREFIX.sub("", v.strip()).lower()
        if not v.startswith("10."):
            raise ValueError(f"Ungültige DOI: {v!r}")
        return v

    @field_validator("openalex_id")
    @classmethod
    def _normalize_openalex(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.rsplit("/", 1)[-1].upper()
        if not re.fullmatch(r"W\d+", v):
            raise ValueError(f"Ungültige OpenAlex-Work-ID: {v!r}")
        return v

    @field_validator("arxiv_id")
    @classmethod
    def _normalize_arxiv(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return re.sub(r"^arxiv:", "", v.strip(), flags=re.IGNORECASE)


class Decision(StrEnum):
    INCLUDE = "include"
    EXCLUDE = "exclude"
    UNCERTAIN = "uncertain"


class Decider(StrEnum):
    LLM = "llm"
    HUMAN = "human"


class ScreeningDecision(Schema):
    """Screening-Urteil zu einem Paper, vom LLM oder als menschlicher Override.

    Eine Begründung ist immer Pflicht, auch bei Overrides.
    """

    paper_id: UUID
    decision: Decision
    reason: str = Field(min_length=1)
    criteria_met: dict[str, bool | None] = Field(default_factory=dict)
    decided_by: Decider = Decider.LLM
    model: str | None = None
    prompt_version: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def _llm_needs_provenance(self) -> Self:
        if self.decided_by is Decider.LLM and not (self.model and self.prompt_version):
            raise ValueError("LLM-Entscheidungen brauchen model und prompt_version")
        return self
