from pathlib import Path

import pytest

from research_agent.config import Settings


def test_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RA_DATA_DIR", raising=False)
    assert Settings(_env_file=None).data_dir == Path("data")  # pyright: ignore[reportCallIssue]


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RA_DATA_DIR", "/tmp/ra")
    monkeypatch.setenv("RA_LOG_LEVEL", "DEBUG")
    s = Settings(_env_file=None)  # pyright: ignore[reportCallIssue]
    assert s.data_dir == Path("/tmp/ra")
    assert s.log_level == "DEBUG"
