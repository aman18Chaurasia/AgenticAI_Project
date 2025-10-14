import argparse
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from .core.config import Settings, get_settings
from .core.db import engine
from .api.routes.health import router as health_router
from .api.routes.news import router as news_router
from .api.routes.capsule import router as capsule_router
from .api.routes.schedule import router as schedule_router
from .api.routes.users import router as users_router

logger = logging.getLogger(__name__)

settings: Settings = get_settings()

app = FastAPI(title="CivicBriefs.ai", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(news_router, prefix="/ingest", tags=["ingest"])
app.include_router(capsule_router, prefix="/capsule", tags=["capsule"])
app.include_router(schedule_router, prefix="/schedule", tags=["schedule"])


@app.on_event("startup")
def on_startup() -> None:
    if settings.database_url.startswith("sqlite"):  # ensure folder
        os.makedirs("data", exist_ok=True)
    SQLModel.metadata.create_all(engine)


def _init_db() -> None:
    from .services.bootstrap import seed_basics
    SQLModel.metadata.create_all(engine)
    seed_basics()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--init-db", action="store_true")
    args = parser.parse_args()
    if args.init_db:
        _init_db()
        print("DB initialized and seeded.")

## Just to test