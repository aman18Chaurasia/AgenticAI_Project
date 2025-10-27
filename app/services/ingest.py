from typing import List
import os
from sqlmodel import Session, select
from ..core.config import get_settings
from ..models.content import NewsItem
from ..schemas.news import NewsIn, NewsOut
from .content_extract import extract_article_text
from .summarizer import summarize_text, summarize_news_article


def fetch_and_parse_feeds() -> List[NewsIn]:
    import feedparser  # type: ignore
    settings = get_settings()
    feeds = [u.strip() for u in settings.news_feeds.split(",") if u.strip()]
    items: List[NewsIn] = []
    for url in feeds:
        try:
            parsed = feedparser.parse(url)
            for e in parsed.entries[:20]:
                items.append(
                    NewsIn(
                        source=url,
                        title=e.get("title", "Untitled"),
                        url=e.get("link", "http://example.com"),
                        published_at=str(e.get("published", "")),
                        content=e.get("summary", ""),
                    )
                )
        except Exception:
            continue
    return items


def save_news_items(session: Session, items: List[NewsIn]) -> List[NewsOut]:
    saved: List[NewsOut] = []
    for it in items:
        exists = session.exec(select(NewsItem).where(NewsItem.url == str(it.url))).first()
        if exists:
            continue
        entity = NewsItem(
            source=it.source,
            title=it.title,
            url=str(it.url),
            published_at=it.published_at,
            content=it.content,
        )
        session.add(entity)
        session.commit()
        session.refresh(entity)

        # Enrich: fetch full article text and compute high‑quality summary
        try:
            full = extract_article_text(entity.url)
            if full and len(full) > 500:
                entity.content = full
        except Exception:
            pass
        try:
            base = entity.content or it.content or ""
            if base:
                # Prefer news‑style summary when using LLM backend
                if (os.getenv("SUMMARIZER_BACKEND", "textrank").lower() == "hf"):
                    entity.summary = summarize_news_article(entity.title, base, url=entity.url)
                else:
                    entity.summary = summarize_text(base, max_sentences=7)
        except Exception:
            pass
        session.add(entity)
        session.commit()
        session.refresh(entity)
        saved.append(
            NewsOut(
                id=entity.id or 0,
                source=entity.source,
                title=entity.title,
                url=entity.url,
                published_at=entity.published_at,
                summary=entity.summary,
            )
        )
    return saved
