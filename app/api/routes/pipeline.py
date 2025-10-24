from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from ...core.db import get_session
from ...models.user import User
from ...services.ingest import fetch_and_parse_feeds, save_news_items
from ...services.capsules import build_daily_capsule
from ...services.notifier import send_bulk_capsule_emails
from ...core.deps import require_admin
import json

router = APIRouter()

@router.post("/run")
def run_full_pipeline(session: Session = Depends(get_session), _: User = Depends(require_admin)):
    """Run the complete pipeline: ingest -> capsule -> email"""
    
    # Step 1: Ingest news
    fetched = fetch_and_parse_feeds()
    saved = save_news_items(session, fetched)
    
    # Step 2: Build capsule
    capsule = build_daily_capsule(session)
    
    # Step 3: Send emails to subscribers
    subscribers = session.exec(
        select(User.email).where(User.daily_capsule_subscribed == True)
    ).all()
    
    if subscribers:
        results = send_bulk_capsule_emails(list(subscribers), capsule)
        return {
            "message": "Pipeline completed successfully",
            "news_items": len(saved),
            "capsule_items": len(capsule["items"]),
            "emails_sent": results["sent"],
            "emails_failed": results["failed"]
        }
    else:
        return {
            "message": "Pipeline completed, no subscribers to email",
            "news_items": len(saved),
            "capsule_items": len(capsule["items"])
        }
