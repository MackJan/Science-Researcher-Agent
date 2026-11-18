import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from research_agent.db import Repository

# Eigene Test-DB, da die Fixture das Schema komplett neu aufsetzt. Passt zum CI-Service.
TEST_DB_URL = os.environ.get(
    "RA_TEST_DATABASE_URL", "postgresql+psycopg://research:research@localhost:5432/research_test"
)


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    engine = create_engine(TEST_DB_URL)
    try:
        engine.connect().close()
    except OperationalError:
        if os.environ.get("CI"):
            raise
        pytest.skip(f"Keine Test-Datenbank unter {TEST_DB_URL} erreichbar")
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    """Jeder Test läuft in einer Transaktion, die am Ende zurückgerollt wird."""
    with engine.connect() as conn, conn.begin() as tx:
        with Session(bind=conn, join_transaction_mode="create_savepoint") as s:
            yield s
        tx.rollback()


@pytest.fixture
def repo(session: Session) -> Repository:
    return Repository(session)
