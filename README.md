# Science Researcher Agent

Agent für systematische Literaturrecherchen: von der Forschungsfrage über Suche, Screening und Evidenz-Extraktion bis zum belegten Bericht.

## Schnellstart

Voraussetzungen: [uv](https://docs.astral.sh/uv/) (installiert Python 3.12 bei Bedarf selbst).

```bash
uv sync
uv run pre-commit install
cp .env.example .env
uv run pytest
```

### Datenbank

Postgres mit pgvector (bis Docker Compose aus #3 steht, z. B. per Einzelcontainer):

```bash
docker run -d --name ra-pg -p 5432:5432 -e POSTGRES_USER=research -e POSTGRES_PASSWORD=research \
  -e POSTGRES_DB=research pgvector/pgvector:pg16
docker exec ra-pg createdb -U research research_test   # für die DB-Tests
uv run alembic upgrade head
```

Schemaänderung: `tables.py` anpassen, dann `uv run alembic revision --autogenerate -m "..."` und die erzeugte Datei prüfen. Ein Test schlägt fehl, wenn Tabellen und Migrationen auseinanderlaufen. DB-Tests werden lokal übersprungen, wenn keine Test-DB läuft (in CI nicht).

## Struktur

| Pfad | Inhalt |
|---|---|
| `src/research_agent/` | Anwendungscode |
| `tests/` | Tests (pytest) |
| `prompts/` | Prompt-Vorlagen |
| `protocols/` | Rechercheprotokolle der Läufe |
| `eval/` | Evaluationsdaten und -skripte |
| `docs/adr/` | Architekturentscheidungen |
| `migrations/` | Alembic-Migrationen |

Mitarbeit: siehe [CONTRIBUTING.md](CONTRIBUTING.md). Roadmap: Issue #60.
