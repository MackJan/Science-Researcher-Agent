"""Kennzahlen eines Laufs (PRISMA-Stufen, Kosten)."""

from itertools import pairwise
from typing import Self
from uuid import UUID

from pydantic import Field, model_validator

from research_agent.models.base import Schema


class RunStats(Schema):
    """Aggregierte Zahlen eines Laufs; jede PRISMA-Stufe ist höchstens so groß wie die vorige."""

    run_id: UUID
    found: int = Field(default=0, ge=0)
    after_dedup: int = Field(default=0, ge=0)
    screened: int = Field(default=0, ge=0)
    included: int = Field(default=0, ge=0)
    with_full_text: int = Field(default=0, ge=0)
    exclusion_reasons: dict[str, int] = Field(default_factory=dict)
    overrides: int = Field(default=0, ge=0)
    api_calls: int = Field(default=0, ge=0)
    llm_cost_usd: float = Field(default=0.0, ge=0)

    @model_validator(mode="after")
    def _check_funnel(self) -> Self:
        stages = [self.found, self.after_dedup, self.screened, self.included, self.with_full_text]
        if any(a < b for a, b in pairwise(stages)):
            raise ValueError(f"PRISMA-Stufen müssen monoton fallen: {stages}")
        return self
