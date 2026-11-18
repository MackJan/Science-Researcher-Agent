from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from research_agent.db import Repository
from research_agent.db.tables import ChunkRow, ProtocolVersionRow
from research_agent.models import (
    Chunk,
    Claim,
    Decider,
    Decision,
    Document,
    DocumentKind,
    Evidence,
    Extraction,
    ExtractionField,
    Paper,
    Protocol,
    Query,
    RunStats,
    ScreeningDecision,
    Source,
    Verdict,
)

from .conftest import TEST_DB_URL

PROTOCOL = Protocol(
    question="Wirkt Reranking?",
    sub_questions=[{"id": "sq1", "text": "Welche Reranker?"}],  # pyright: ignore[reportArgumentType]
    queries=[{"source": "openalex", "text": "neural reranking"}],  # pyright: ignore[reportArgumentType]
)


def test_migrations_match_models(engine: Engine) -> None:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    command.check(cfg)  # schlägt fehl, wenn tables.py und Migrationen auseinanderlaufen


def test_run_and_protocol(repo: Repository, session: Session) -> None:
    run_a = repo.create_run(PROTOCOL)
    run_b = repo.create_run(PROTOCOL)
    assert run_a != run_b
    assert session.scalar(select(func.count()).select_from(ProtocolVersionRow)) == 1
    assert repo.get_protocol(run_a) == PROTOCOL

    stats = RunStats(run_id=run_a, found=10, after_dedup=8, exclusion_reasons={"ex1": 3})
    repo.save_stats(stats)
    assert repo.get_stats(run_a) == stats
    assert repo.get_stats(run_b) is None


def test_paper_roundtrip_and_unique_doi(repo: Repository) -> None:
    paper = Paper(title="BERT Reranking", doi="10.1/abc", sources={Source.OPENALEX}, authors=["A"])
    repo.add(paper)
    assert repo.get(Paper, paper.id) == paper
    assert repo.list(Paper, doi="10.1/abc") == [paper]
    with pytest.raises(IntegrityError):
        repo.add(Paper(title="Duplikat", doi="10.1/abc"))


def _paper_with_chunk(repo: Repository) -> tuple[Paper, Chunk]:
    paper = Paper(title="P")
    repo.add(paper)
    doc = Document(paper_id=paper.id, kind=DocumentKind.ABSTRACT_ONLY)
    repo.add(doc)
    chunk = Chunk(
        document_id=doc.id, paper_id=paper.id, ordinal=0, text="Reranking improves recall"
    )
    repo.add(chunk)
    return paper, chunk


def test_run_scoped_entities(repo: Repository) -> None:
    run_id = repo.create_run(PROTOCOL)
    paper, chunk = _paper_with_chunk(repo)

    repo.add(Query(source=Source.OPENALEX, text="q"), run_id=run_id, result_count=5)
    assert [q.text for q in repo.list(Query, run_id=run_id)] == ["q"]

    decision = ScreeningDecision(
        paper_id=paper.id, decision=Decision.INCLUDE, reason="passt", decided_by=Decider.HUMAN
    )
    repo.add(decision, run_id=run_id)
    assert repo.list(ScreeningDecision, run_id=run_id) == [decision]

    ex = Extraction(
        paper_id=paper.id,
        field=ExtractionField.METHOD,
        value="BERT",
        quote="BERT",
        chunk_id=chunk.id,
    )
    repo.add(ex, run_id=run_id)
    assert repo.get(Extraction, ex.id) == ex


def test_claim_with_evidence(repo: Repository) -> None:
    run_id = repo.create_run(PROTOCOL)
    _, chunk = _paper_with_chunk(repo)
    claim = Claim(
        sub_question_id="sq1",
        text="Reranking hilft.",
        evidence=[
            Evidence(chunk_id=chunk.id, verdict=Verdict.SUPPORTED, verdict_reason="steht da")
        ],
    )
    repo.add(claim, run_id=run_id)
    assert repo.get(Claim, claim.id) == claim


def test_run_scoped_entity_needs_run_id(repo: Repository) -> None:
    with pytest.raises(IntegrityError):
        repo.add(Query(source=Source.OPENALEX, text="q"))


def test_chunk_fulltext_and_vector(repo: Repository, session: Session) -> None:
    _, chunk = _paper_with_chunk(repo)
    hit = session.scalar(
        select(ChunkRow.id).where(ChunkRow.tsv.op("@@")(func.plainto_tsquery("english", "recalls")))
    )
    assert hit == chunk.id

    row = session.get_one(ChunkRow, chunk.id)
    row.embedding = [1.0, 0.0, 0.0]
    session.flush()
    nearest = session.scalar(
        select(ChunkRow.id).order_by(ChunkRow.embedding.cosine_distance([1.0, 0.1, 0.0])).limit(1)
    )
    assert isinstance(nearest, UUID) and nearest == chunk.id
    assert session.scalar(text("SELECT extname FROM pg_extension WHERE extname='vector'"))


def test_get_missing_returns_none(repo: Repository) -> None:
    assert repo.get(Paper, uuid4()) is None
