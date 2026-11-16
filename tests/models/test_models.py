from uuid import uuid4

import pytest
from pydantic import ValidationError

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
    RunStats,
    ScreeningDecision,
    Source,
    Verdict,
)

PROTOCOL = {
    "question": "Wie wirkt Reranking auf Retrieval-Qualität?",
    "sub_questions": [{"id": "sq1", "text": "Welche Reranker gibt es?"}],
    "queries": [{"source": "openalex", "text": "neural reranking", "sub_question_id": "sq1"}],
    "inclusion_criteria": [{"id": "in1", "text": "Empirische Studie"}],
    "exclusion_criteria": [{"id": "ex1", "text": "Kein Englisch"}],
    "year_from": 2018,
    "year_to": 2026,
}


# --- Protocol -----------------------------------------------------------------


def test_protocol_roundtrip() -> None:
    p = Protocol.model_validate(PROTOCOL)
    assert p.queries[0].source is Source.OPENALEX
    assert Protocol.model_validate(p.model_dump(mode="json")) == p


@pytest.mark.parametrize(
    "patch",
    [
        {"unknown_field": 1},
        {"queries": []},
        {"year_from": 2027},
        {"sub_questions": [{"id": "sq1", "text": "a"}, {"id": "sq1", "text": "b"}]},
        {"exclusion_criteria": [{"id": "in1", "text": "doppelt"}]},
        {"queries": [{"source": "openalex", "text": "x", "sub_question_id": "nope"}]},
        {"queries": [{"source": "google", "text": "x"}]},
    ],
)
def test_protocol_rejects(patch: dict) -> None:
    with pytest.raises(ValidationError):
        Protocol.model_validate(PROTOCOL | patch)


# --- Paper --------------------------------------------------------------------


def test_paper_normalizes_ids() -> None:
    p = Paper(
        title="X",
        doi="https://doi.org/10.1145/ABC.123",
        openalex_id="https://openalex.org/w123",
        arxiv_id="arXiv:2101.00001v2",
    )
    assert p.doi == "10.1145/abc.123"
    assert p.openalex_id == "W123"
    assert p.arxiv_id == "2101.00001v2"


@pytest.mark.parametrize("kwargs", [{"doi": "abc"}, {"openalex_id": "A123"}, {"title": " "}])
def test_paper_rejects_bad_ids(kwargs: dict) -> None:
    with pytest.raises(ValidationError):
        Paper.model_validate({"title": "X"} | kwargs)


def test_screening_llm_needs_provenance() -> None:
    with pytest.raises(ValidationError):
        ScreeningDecision(paper_id=uuid4(), decision=Decision.INCLUDE, reason="passt")
    d = ScreeningDecision(
        paper_id=uuid4(), decision=Decision.EXCLUDE, reason="Override", decided_by=Decider.HUMAN
    )
    assert d.created_at.tzinfo is not None


def test_screening_needs_reason() -> None:
    with pytest.raises(ValidationError):
        ScreeningDecision(
            paper_id=uuid4(), decision=Decision.INCLUDE, reason="", decided_by=Decider.HUMAN
        )


# --- Document / Chunk ---------------------------------------------------------


def test_full_text_document_needs_pdf() -> None:
    with pytest.raises(ValidationError):
        Document(paper_id=uuid4(), kind=DocumentKind.FULL_TEXT)
    Document(paper_id=uuid4(), kind=DocumentKind.ABSTRACT_ONLY)
    Document(paper_id=uuid4(), kind=DocumentKind.FULL_TEXT, pdf_sha256="a" * 64, parser="grobid")


@pytest.mark.parametrize(
    ("start", "end", "ok"),
    [(1, 2, True), (3, 3, True), (None, None, True), (3, 2, False), (1, None, False)],
)
def test_chunk_pages(start: int | None, end: int | None, ok: bool) -> None:
    kwargs = {"document_id": uuid4(), "paper_id": uuid4(), "ordinal": 0, "text": "t"}
    if ok:
        Chunk(**kwargs, page_start=start, page_end=end)
    else:
        with pytest.raises(ValidationError):
            Chunk(**kwargs, page_start=start, page_end=end)


# --- Extraction / Claim -------------------------------------------------------


def test_extraction_value_needs_quote() -> None:
    pid = uuid4()
    Extraction(paper_id=pid, field=ExtractionField.DATASET)  # leer ist erlaubt
    Extraction(
        paper_id=pid,
        field=ExtractionField.DATASET,
        value="MS MARCO",
        quote="on MS MARCO",
        chunk_id=uuid4(),
    )
    with pytest.raises(ValidationError):
        Extraction(paper_id=pid, field=ExtractionField.DATASET, value="MS MARCO")


def test_claim_needs_evidence() -> None:
    with pytest.raises(ValidationError):
        Claim(sub_question_id="sq1", text="A", evidence=[])
    with pytest.raises(ValidationError):
        Claim(sub_question_id="sq1", text="A", evidence=[Evidence(chunk_id=uuid4())], revision=3)


def test_evidence_verdict_needs_reason() -> None:
    with pytest.raises(ValidationError):
        Evidence(chunk_id=uuid4(), verdict=Verdict.SUPPORTED)


# --- RunStats -----------------------------------------------------------------


def test_run_stats_funnel() -> None:
    RunStats(run_id=uuid4(), found=100, after_dedup=80, screened=80, included=20, with_full_text=15)
    with pytest.raises(ValidationError):
        RunStats(run_id=uuid4(), found=10, after_dedup=20)
