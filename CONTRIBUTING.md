# Mitarbeit

## Setup

```bash
uv sync
uv run pre-commit install
cp .env.example .env
uv run pytest
```

## Issues

- Wer ein Issue anfängt, weist es sich sofort zu. Eine Aufgabe = eine Person.
- Abhängigkeiten stehen im Issue; Übersicht in #60.

## Branches und Commits

- Branch pro Issue: `<issue-nr>-kurzer-name`, z. B. `8-openalex-client`.
- Commit-Nachrichten im Imperativ, Issue-Referenz im PR (`Closes #8`).
- Kein direkter Push auf `main` außer für triviale Fixes.

## Reviews

- Jeder PR wird von mindestens einer anderen Person reviewt.
- Merge per Squash, nachdem CI grün ist.

## Definition of Done

- Akzeptanzkriterien des Issues erfüllt
- Tests für neue Logik vorhanden, `uv run pytest` grün
- `uv run pre-commit run --all-files` grün (ruff, pyright)
- Relevante Entscheidungen als ADR in `docs/adr/` (Vorlage: `0000-vorlage.md`)
- PR reviewt und gemergt
