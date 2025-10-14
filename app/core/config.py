import os
from functools import lru_cache
from pydantic import BaseModel
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


class Settings(BaseModel):
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    secret_key: str = os.getenv("SECRET_KEY", "change-me")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///data/db.sqlite3")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
    news_feeds: str = os.getenv("NEWS_FEEDS", "")
    schedule_cron_daily: str = os.getenv("SCHEDULE_CRON_DAILY", "0 6 * * *")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
