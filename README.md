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

## Struktur

| Pfad | Inhalt |
|---|---|
| `src/research_agent/` | Anwendungscode |
| `tests/` | Tests (pytest) |
| `prompts/` | Prompt-Vorlagen |
| `protocols/` | Rechercheprotokolle der Läufe |
| `eval/` | Evaluationsdaten und -skripte |
| `docs/adr/` | Architekturentscheidungen |

Mitarbeit: siehe [CONTRIBUTING.md](CONTRIBUTING.md). Roadmap: Issue #60.
