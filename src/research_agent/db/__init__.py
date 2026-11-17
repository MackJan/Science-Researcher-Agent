"""Datenbankzugriff: Tabellen, Session und Repository."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from research_agent.config import get_settings
from research_agent.db.repository import Repository


def make_session_factory(url: str | None = None) -> sessionmaker[Session]:
    return sessionmaker(create_engine(url or get_settings().database_url))


__all__ = ["Repository", "make_session_factory"]
