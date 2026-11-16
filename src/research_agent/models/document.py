"""Volltext-Dokumente und ihre Chunks."""

from enum import StrEnum
from typing import Self
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from research_agent.models.base import Schema


class DocumentKind(StrEnum):
    FULL_TEXT = "full_text"
    ABSTRACT_ONLY = "abstract_only"


class Document(Schema):
    """Geparster Text eines Papers; ohne OA-Volltext nur der Abstract."""

    id: UUID = Field(default_factory=uuid4)
    paper_id: UUID
    kind: DocumentKind
    pdf_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    parser: str | None = None
    parser_version: str | None = None

    @model_validator(mode="after")
    def _full_text_needs_pdf(self) -> Self:
        if self.kind is DocumentKind.FULL_TEXT and not (self.pdf_sha256 and self.parser):
            raise ValueError("Volltext-Dokumente brauchen pdf_sha256 und parser")
        return self


class Chunk(Schema):
    """Textabschnitt, Einheit für Retrieval, Zitate und Belege.

    Seiten sind 1-basiert und inklusiv; bei Abstract-Chunks beide `None`.
    """

    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    paper_id: UUID
    ordinal: int = Field(ge=0)
    text: str = Field(min_length=1)
    section: str | None = None
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _check_pages(self) -> Self:
        if (self.page_start is None) != (self.page_end is None):
            raise ValueError("page_start und page_end nur gemeinsam angeben")
        if self.page_start and self.page_end and self.page_start > self.page_end:
            raise ValueError("page_start darf nicht nach page_end liegen")
        return self
