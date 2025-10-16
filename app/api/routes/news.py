from typing import List, Optional
from fastapi import APIRouter
from sqlmodel import Session
from ...core.db import engine
from ...schemas.news import NewsIn, NewsOut
from ...services.ingest import save_news_items, fetch_and_parse_feeds

router = APIRouter()


@router.post("/news", response_model=List[NewsOut])
def ingest_news(items: Optional[List[NewsIn]] = None):
    if items:
        with Session(engine) as session:
            saved = save_news_items(session, items)
            return saved
    fetched = fetch_and_parse_feeds()
    with Session(engine) as session:
        saved = save_news_items(session, fetched)
    return saved

