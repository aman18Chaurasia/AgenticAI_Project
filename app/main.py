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
from .api.routes.subscription import router as subscription_router
from .api.routes.frontend import router as frontend_router
from .api.routes.pipeline import router as pipeline_router
from .api.routes.auth import router as auth_router
from .api.routes.admin import router as admin_router
from .api.routes.chat import router as chat_router
from .api.routes.reports import router as reports_router
from .api.routes.password import router as password_router
from .api.routes.tests import router as tests_router
from .api.routes.maintenance import router as maintenance_router
from .api.routes.plan import router as plan_router

logger = logging.getLogger(__name__)

settings: Settings = get_settings()

app = FastAPI(title="CivicBriefs.ai", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(frontend_router)
app.include_router(health_router)
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(news_router, prefix="/ingest", tags=["ingest"])
app.include_router(capsule_router, prefix="/capsule", tags=["capsule"])
app.include_router(schedule_router, prefix="/schedule", tags=["schedule"])
app.include_router(subscription_router, prefix="/subscription", tags=["subscription"])
app.include_router(pipeline_router, prefix="/pipeline", tags=["pipeline"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(chat_router)
app.include_router(reports_router)
app.include_router(password_router)
app.include_router(maintenance_router)
app.include_router(plan_router)
app.include_router(tests_router)


@app.on_event("startup")
def on_startup() -> None:
    if settings.database_url.startswith("sqlite"):  # ensure folder
        os.makedirs("data", exist_ok=True)
    # Ensure all models are imported so SQLModel sees them
    try:
        from .models import user as _mu  # noqa: F401
        from .models import content as _mc  # noqa: F401
        from .models import tests as _mt  # noqa: F401
    except Exception:
        # Safe to continue; create_all will handle present models
        pass
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
