from typing import List
from sqlmodel import Session, select
from ..core.config import get_settings
from ..models.content import NewsItem
from ..schemas.news import NewsIn, NewsOut


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

