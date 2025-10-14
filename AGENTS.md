# AGENTS.md

Scope: Entire repository

- Python style: prefer explicit modules, type hints, small functions. No one-letter variable names.
- API design: RESTful, nouns for resources, verbs for actions only where needed (`/schedule/generate`).
- Config: all runtime settings via env or `.env`. Do not hardcode secrets.
- DB: SQLModel with `create_all` for dev; migrations recommended (Alembic) for prod.
- Agents: keep I/O boundaries in `services/*`. Agents orchestrate services, do not embed business logic.
- Logging: use module logger, no print. Avoid inline comments unless clarifying a non-obvious choice.
- Tests (future): `tests/` mirrors `app/` modules.

