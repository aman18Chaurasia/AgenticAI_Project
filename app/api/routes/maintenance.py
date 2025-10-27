from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlmodel import Session, select
from ...core.db import get_session
from ...core.deps import require_admin
from ...models.user import User
from ...models.content import NewsItem, Capsule
from ...services.content_extract import extract_article_text
from ...services.summarizer import summarize_text, summarize_news_article
import os


router = APIRouter(prefix="/maintenance", tags=["maintenance"])


class ReSummaryBody(BaseModel):
    limit: int = 50
    force_extract: bool = False


@router.post("/resummarize")
def resummarize_news(payload: ReSummaryBody, _: User = Depends(require_admin), session: Session = Depends(get_session)):
    items: List[NewsItem] = session.exec(select(NewsItem)).all() or []
    if not items:
        return {"updated": 0, "note": "No news items found"}
    # Work from most recent
    items = list(reversed(items))[: max(1, payload.limit)]
    backend = os.getenv("SUMMARIZER_BACKEND", "textrank").lower()
    updated = 0
    failures = 0
    samples = []
    for n in items:
        try:
            base_text = n.content or ""
            if payload.force_extract or len(base_text) < 500:
                full = extract_article_text(n.url)
                if full and len(full) > 500:
                    base_text = full
                    n.content = full
            if not base_text:
                continue
            if backend == "hf":
                n.summary = summarize_news_article(n.title, base_text, url=n.url)
            else:
                n.summary = summarize_text(base_text, max_sentences=7)
            session.add(n)
            session.commit()
            updated += 1
            if len(samples) < 3:
                samples.append({"title": n.title, "summary": n.summary[:260]})
        except Exception:
            failures += 1
            continue
    return {"backend": backend, "updated": updated, "failures": failures, "samples": samples}


@router.post("/rebuild-capsule")
def rebuild_capsule(_: User = Depends(require_admin), session: Session = Depends(get_session)):
    from datetime import date
    from ...services.capsules import build_daily_capsule
    today = str(date.today())
    cap = session.exec(select(Capsule).where(Capsule.date == today)).first()
    if cap:
        session.delete(cap)
        session.commit()
    new_cap = build_daily_capsule(session)
    return {"date": new_cap.get("date"), "items": len(new_cap.get("items", []))}
