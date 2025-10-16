from sqlmodel import create_engine, Session
from .config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)

def get_session():
    """Dependency to get database session"""
    with Session(engine) as session:
        yield session

