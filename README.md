# CivicBriefs.ai — The Autonomous UPSC Preparation Mentor

An agentic AI system that continuously ingests UPSC-relevant news, maps items to the UPSC syllabus, links PYQs, personalizes study schedules, adapts using mock-test feedback, and delivers daily capsules and weekly reports automatically.

## Objectives
- Automate daily news analysis and summarization from trusted sources (PIB, PRS India, The Hindu, DTE via RSS/APIs).
- Map news to syllabus topics (GS1–GS4) and surface relevant PYQs (2013–2024).
- Generate and adapt study plans based on exam target, time availability, and performance.
- Deliver daily capsules and weekly progress reports via email/Telegram (integrations pluggable).
- Demonstrate end-to-end agentic automation (scheduled, autonomous runs).

## Tech Stack
- Language: Python 3.11+
- API: FastAPI + Uvicorn
- Data: SQLModel (SQLAlchemy) with SQLite (dev) / Postgres (prod)
- Vector/Semantic Search: Pluggable service (scikit-learn TF-IDF fallback, FAISS/pgvector optional)
- Scheduling: APScheduler (local) and GitHub Actions (cloud)
- Messaging/Background: In-process queue defaults; Redis/Celery optional for prod
- HTTP/Feeds: httpx + feedparser
- Auth: JWT (fastapi-jwt), simple role model
- Config: python-dotenv (12-factor style)
- Container: Docker + docker-compose
- CI/CD: GitHub Actions (lint/test/build/scheduled runs)
- Telemetry: Structured logging (logging), OpenTelemetry ready (optional)

## Monorepo Layout
```
app/
  main.py                 # FastAPI app
  core/                   # config, db, security
  models/                 # SQLModel ORM entities
  schemas/                # Pydantic I/O models
  services/               # domain services (ingest, summarize, map, pyq, planner, reporter)
  agents/                 # agent classes + orchestrator
  api/routes/             # REST routes
  worker/                 # task queue abstractions (inproc; redis optional)
data/
  seed/                   # syllabus, pyqs, sample users
.github/workflows/        # CI + scheduler
Dockerfile.api
Dockerfile.worker
docker-compose.yml
requirements.txt
.env.example
AGENTS.md
```

## Quick Start (Local Dev)
1) Create virtualenv and install deps
```
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: . .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Configure env
```
copy .env.example .env
# edit .env (DB, secrets). Defaults use SQLite locally.
```

3) Seed DB and run API
```
python -m app.main --init-db
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4) Try endpoints
- GET http://localhost:8000/health
- POST http://localhost:8000/ingest/news (body optional) to simulate ingest
- GET http://localhost:8000/capsule/daily to generate a daily capsule
- POST http://localhost:8000/schedule/generate to generate a plan

5) Run scheduler (dev)
```
python -m app.agents.orchestrator --run-once  # one full pipeline pass
python -m app.agents.orchestrator --schedule  # APScheduler daily 06:00
```

## Production (Docker)
```
docker compose up --build -d
# API: http://localhost:8000
```
Edit `docker-compose.yml` to enable Postgres + Redis in production.

## Data Model Overview
- User, TestResult, StudyPlan
- NewsItem, Capsule, Mapping (News→Syllabus)
- SyllabusTopic (GS1–GS4), PyqQuestion

## Agentic Flow
1) NewsAgent: fetch feeds, deduplicate, store
2) MappingAgent: map news→syllabus & link PYQs (semantic + keyword)
3) PlannerAgent: update personalized study plan using availability + performance
4) ReporterAgent: build daily capsule + weekly report artifacts
5) Orchestrator: schedules agents (APScheduler/CI) and handles retries

## Extending
- Replace summarization with your preferred LLM via `services/summarizer.py` client abstraction.
- Swap TF-IDF with FAISS/pgvector in `services/semantic.py`.
- Add Telegram/email webhooks in `services/notifier.py`.

## Security & Ops
- JWT auth (bearer) with role claims.
- CORS restricted by env.
- Parameterized DB credentials; prefer least-privileged DB role.
- Structured logs; readiness/liveness endpoints.

## License
Proprietary by default. Add a license if needed.

