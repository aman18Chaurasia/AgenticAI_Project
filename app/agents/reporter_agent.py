from sqlmodel import Session, select
from ..core.db import engine
from ..services.capsules import build_daily_capsule
from ..services.notifier import send_bulk_capsule_emails
from ..models.user import User
from .base import Agent, AgentResult


class ReporterAgent(Agent):
    name = "reporter-agent"

    def run(self) -> AgentResult:
        with Session(engine) as session:
            # Build daily capsule
            cap = build_daily_capsule(session)
            
            # Get subscribed users
            subscribers = session.exec(
                select(User.email).where(User.daily_capsule_subscribed == True)
            ).all()
            
            if subscribers:
                # Send emails to subscribers
                results = send_bulk_capsule_emails(list(subscribers), cap)
                return AgentResult(
                    self.name, 
                    True, 
                    f"Built capsule for {cap.get('date')}. Emails sent: {results['sent']}, failed: {results['failed']}"
                )
            else:
                return AgentResult(
                    self.name, 
                    True, 
                    f"Built capsule for {cap.get('date')}. No subscribers found."
                )

