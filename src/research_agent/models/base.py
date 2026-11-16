"""Gemeinsame Basis für alle Schemas."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Schema(BaseModel):
    """Basisklasse: unbekannte Felder sind ein Fehler (fängt Tippfehler in Protokolldateien)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Source(StrEnum):
    """Externe Datenquelle für Paper-Metadaten."""

    OPENALEX = "openalex"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    ARXIV = "arxiv"
