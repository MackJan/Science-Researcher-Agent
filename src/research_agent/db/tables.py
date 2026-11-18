"""SQLAlchemy-Tabellen. Spaltennamen entsprechen den Feldern in `research_agent.models`.

Enums werden als Text gespeichert (keine PG-Enums), damit neue Werte keine Migration brauchen.
"""

import uuid
from datetime import datetime
from typing import Any, ClassVar

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    type_annotation_map: ClassVar = {dict[str, Any]: JSONB, list[str]: ARRAY(String)}


def _pk() -> Mapped[uuid.UUID]:
    return mapped_column(primary_key=True, default=uuid.uuid4)


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


def _run_fk() -> Mapped[uuid.UUID]:
    return mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), index=True)


class ProtocolVersionRow(Base):
    """Unveränderliche Protokollversion; gleicher Inhalt wird über den Hash wiederverwendet."""

    __tablename__ = "protocol_versions"
    id: Mapped[uuid.UUID] = _pk()
    content: Mapped[dict[str, Any]]
    content_sha256: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = _created_at()


class RunRow(Base):
    __tablename__ = "runs"
    id: Mapped[uuid.UUID] = _pk()
    protocol_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("protocol_versions.id"))
    status: Mapped[str] = mapped_column(default="created")
    stats: Mapped[dict[str, Any] | None]
    created_at: Mapped[datetime] = _created_at()


class QueryRow(Base):
    __tablename__ = "queries"
    id: Mapped[uuid.UUID] = _pk()
    run_id: Mapped[uuid.UUID] = _run_fk()
    source: Mapped[str]
    text: Mapped[str] = mapped_column(Text)
    sub_question_id: Mapped[str | None]
    filters: Mapped[dict[str, Any]]
    max_results: Mapped[int]
    result_count: Mapped[int | None]
    created_at: Mapped[datetime] = _created_at()


class ApiResponseRow(Base):
    """Rohantwort einer externen API; Cache-Key ist `request_key` (Hash aus URL + Parametern)."""

    __tablename__ = "api_responses"
    id: Mapped[uuid.UUID] = _pk()
    source: Mapped[str]
    request_key: Mapped[str] = mapped_column(String(64), unique=True)
    url: Mapped[str] = mapped_column(Text)
    params: Mapped[dict[str, Any]]
    status_code: Mapped[int]
    body: Mapped[dict[str, Any]]
    fetched_at: Mapped[datetime] = _created_at()


class PaperRow(Base):
    """Paper sind laufübergreifend, damit Metadaten und Volltexte wiederverwendet werden."""

    __tablename__ = "papers"
    id: Mapped[uuid.UUID] = _pk()
    title: Mapped[str] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text)
    authors: Mapped[list[str]]
    year: Mapped[int | None]
    venue: Mapped[str | None]
    doi: Mapped[str | None] = mapped_column(unique=True)
    openalex_id: Mapped[str | None] = mapped_column(unique=True)
    s2_id: Mapped[str | None] = mapped_column(unique=True)
    arxiv_id: Mapped[str | None] = mapped_column(unique=True)
    sources: Mapped[list[str]]
    oa_pdf_url: Mapped[str | None] = mapped_column(Text)
    cited_by_count: Mapped[int | None]


class ScreeningDecisionRow(Base):
    __tablename__ = "screening_decisions"
    id: Mapped[uuid.UUID] = _pk()
    run_id: Mapped[uuid.UUID] = _run_fk()
    paper_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("papers.id"), index=True)
    decision: Mapped[str]
    reason: Mapped[str] = mapped_column(Text)
    criteria_met: Mapped[dict[str, Any]]
    decided_by: Mapped[str]
    model: Mapped[str | None]
    prompt_version: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DocumentRow(Base):
    __tablename__ = "documents"
    id: Mapped[uuid.UUID] = _pk()
    paper_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("papers.id"), index=True)
    kind: Mapped[str]
    pdf_sha256: Mapped[str | None] = mapped_column(String(64))
    parser: Mapped[str | None]
    parser_version: Mapped[str | None]


class ChunkRow(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "ordinal"),
        Index("ix_chunks_tsv", "tsv", postgresql_using="gin"),
    )
    id: Mapped[uuid.UUID] = _pk()
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    paper_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("papers.id"), index=True)
    ordinal: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    section: Mapped[str | None]
    page_start: Mapped[int | None]
    page_end: Mapped[int | None]
    # shortcut: ohne Dimension bis das Embedding-Modell feststeht (#24), dann + HNSW-Index
    embedding: Mapped[Any] = mapped_column(Vector(), nullable=True)
    tsv: Mapped[Any] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', text)", persisted=True)
    )


class ExtractionRow(Base):
    __tablename__ = "extractions"
    id: Mapped[uuid.UUID] = _pk()
    run_id: Mapped[uuid.UUID] = _run_fk()
    paper_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("papers.id"), index=True)
    field: Mapped[str]
    value: Mapped[str | None] = mapped_column(Text)
    quote: Mapped[str | None] = mapped_column(Text)
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("chunks.id"))
    needs_review: Mapped[bool] = mapped_column(default=False)


class ClaimRow(Base):
    __tablename__ = "claims"
    id: Mapped[uuid.UUID] = _pk()
    run_id: Mapped[uuid.UUID] = _run_fk()
    sub_question_id: Mapped[str]
    text: Mapped[str] = mapped_column(Text)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    evidence: Mapped[list["ClaimEvidenceRow"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class ClaimEvidenceRow(Base):
    __tablename__ = "claim_evidence"
    id: Mapped[uuid.UUID] = _pk()
    claim_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"), index=True
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chunks.id"))
    quote: Mapped[str | None] = mapped_column(Text)
    abstract_only: Mapped[bool] = mapped_column(default=False)
    verdict: Mapped[str | None]
    verdict_reason: Mapped[str | None] = mapped_column(Text)


class LlmCallRow(Base):
    """Jeder LLM-Aufruf; `cache_key` macht Replay ohne erneuten Aufruf möglich (#10)."""

    __tablename__ = "llm_calls"
    id: Mapped[uuid.UUID] = _pk()
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("runs.id", ondelete="SET NULL"), index=True
    )
    cache_key: Mapped[str] = mapped_column(String(64), unique=True)
    model: Mapped[str]
    prompt_version: Mapped[str | None]
    request: Mapped[dict[str, Any]]
    response: Mapped[dict[str, Any]]
    input_tokens: Mapped[int | None]
    output_tokens: Mapped[int | None]
    cost_usd: Mapped[float | None]
    latency_ms: Mapped[int | None]
    created_at: Mapped[datetime] = _created_at()
