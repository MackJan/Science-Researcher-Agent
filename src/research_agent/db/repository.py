"""Schlanke Repository-Schicht: speichert und lädt Pydantic-Schemas, versteckt die ORM-Zeilen."""

import hashlib
import json
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_agent.db.tables import (
    Base,
    ChunkRow,
    ClaimEvidenceRow,
    ClaimRow,
    DocumentRow,
    ExtractionRow,
    PaperRow,
    ProtocolVersionRow,
    QueryRow,
    RunRow,
    ScreeningDecisionRow,
)
from research_agent.models import (
    Chunk,
    Claim,
    Document,
    Extraction,
    Paper,
    Protocol,
    Query,
    RunStats,
    Schema,
    ScreeningDecision,
)

_TABLES: dict[type[Schema], type[Base]] = {
    Paper: PaperRow,
    Query: QueryRow,
    ScreeningDecision: ScreeningDecisionRow,
    Document: DocumentRow,
    Chunk: ChunkRow,
    Extraction: ExtractionRow,
    Claim: ClaimRow,
}


def _columns(obj: Schema, exclude: set[str] | None = None) -> dict[str, Any]:
    data = obj.model_dump(exclude=exclude)
    return {k: sorted(v) if isinstance(v, set) else v for k, v in data.items()}


class Repository:
    """Arbeitet auf einer Session; Commit/Rollback liegt beim Aufrufer.

    Laufbezogene Schemas (Query, ScreeningDecision, Extraction, Claim) brauchen beim
    Speichern `run_id=...`, da die Schemas selbst keinen Lauf kennen.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    # --- Läufe ----------------------------------------------------------------

    def create_run(self, protocol: Protocol) -> UUID:
        """Legt einen Lauf an; identische Protokolle teilen sich eine Protokollversion."""
        content = protocol.model_dump(mode="json")
        digest = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
        pv_id = self.session.scalar(
            select(ProtocolVersionRow.id).where(ProtocolVersionRow.content_sha256 == digest)
        )
        if pv_id is None:
            pv = ProtocolVersionRow(content=content, content_sha256=digest)
            self.session.add(pv)
            self.session.flush()
            pv_id = pv.id
        run = RunRow(protocol_version_id=pv_id)
        self.session.add(run)
        self.session.flush()
        return run.id

    def get_protocol(self, run_id: UUID) -> Protocol | None:
        content = self.session.scalar(
            select(ProtocolVersionRow.content)
            .join(RunRow, RunRow.protocol_version_id == ProtocolVersionRow.id)
            .where(RunRow.id == run_id)
        )
        return None if content is None else Protocol.model_validate(content)

    def save_stats(self, stats: RunStats) -> None:
        run = self.session.get_one(RunRow, stats.run_id)
        run.stats = stats.model_dump(mode="json")

    def get_stats(self, run_id: UUID) -> RunStats | None:
        run = self.session.get(RunRow, run_id)
        return None if run is None or run.stats is None else RunStats.model_validate(run.stats)

    # --- Generische Schemas ---------------------------------------------------

    def add(self, obj: Schema, **extra: Any) -> None:
        """Speichert ein Schema; `extra` setzt Spalten außerhalb des Schemas (z. B. run_id)."""
        if isinstance(obj, Claim):
            row = ClaimRow(**_columns(obj, exclude={"evidence"}), **extra)
            row.evidence = [ClaimEvidenceRow(**_columns(e)) for e in obj.evidence]
        else:
            row = _TABLES[type(obj)](**_columns(obj), **extra)
        self.session.add(row)
        self.session.flush()

    def get[T: Schema](self, schema: type[T], id: UUID) -> T | None:
        row = self.session.get(_TABLES[schema], id)
        return None if row is None else schema.model_validate(row, from_attributes=True)

    def list[T: Schema](self, schema: type[T], **filters: Any) -> list[T]:
        """Alle Einträge, per Gleichheit gefiltert, z. B. `list(Chunk, paper_id=...)`."""
        rows = self.session.scalars(select(_TABLES[schema]).filter_by(**filters))
        return [schema.model_validate(r, from_attributes=True) for r in rows]
