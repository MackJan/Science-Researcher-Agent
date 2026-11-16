"""Rechercheprotokoll: beschreibt einen Lauf vollständig und ist als YAML editierbar."""

from typing import Self

from pydantic import Field, model_validator

from research_agent.models.base import Schema, Source


class SubQuestion(Schema):
    """Teilfrage der Forschungsfrage; Aussagen im Bericht werden ihr zugeordnet."""

    id: str = Field(min_length=1)
    text: str = Field(min_length=1)


class Criterion(Schema):
    """Ein- oder Ausschlusskriterium fürs Screening."""

    id: str = Field(min_length=1)
    text: str = Field(min_length=1)


class Query(Schema):
    """Suchanfrage an eine Quelle.

    `filters` enthält quellenspezifische Filter (z. B. OpenAlex-Filterausdrücke).
    """

    source: Source
    text: str = Field(min_length=1)
    sub_question_id: str | None = None
    filters: dict[str, str] = Field(default_factory=dict)
    max_results: int = Field(default=200, gt=0)


class Protocol(Schema):
    """Vollständige Beschreibung eines Laufs; zentrales Reproduzierbarkeits-Artefakt."""

    version: int = Field(default=1, ge=1)
    question: str = Field(min_length=1)
    sub_questions: list[SubQuestion] = Field(min_length=1)
    queries: list[Query] = Field(min_length=1)
    inclusion_criteria: list[Criterion] = Field(default_factory=list)
    exclusion_criteria: list[Criterion] = Field(default_factory=list)
    year_from: int | None = None
    year_to: int | None = None

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        sq_ids = [s.id for s in self.sub_questions]
        if len(sq_ids) != len(set(sq_ids)):
            raise ValueError("Teilfragen-IDs müssen eindeutig sein")
        crit_ids = [c.id for c in self.inclusion_criteria + self.exclusion_criteria]
        if len(crit_ids) != len(set(crit_ids)):
            raise ValueError("Kriterien-IDs müssen eindeutig sein")
        unknown = {q.sub_question_id for q in self.queries if q.sub_question_id} - set(sq_ids)
        if unknown:
            raise ValueError(f"Query verweist auf unbekannte Teilfrage(n): {sorted(unknown)}")
        if self.year_from and self.year_to and self.year_from > self.year_to:
            raise ValueError("year_from darf nicht nach year_to liegen")
        return self
