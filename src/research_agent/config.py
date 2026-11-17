"""Zentrale Konfiguration aus Umgebungsvariablen bzw. `.env`."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RA_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    data_dir: Path = Path("data")
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://research:research@localhost:5432/research"


@lru_cache
def get_settings() -> Settings:
    return Settings()
