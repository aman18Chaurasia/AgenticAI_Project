from sqlmodel import Session
from ..core.db import engine
from ..services.capsules import build_daily_capsule
from .base import Agent, AgentResult


class ReporterAgent(Agent):
    name = "reporter-agent"

    def run(self) -> AgentResult:
        with Session(engine) as session:
            cap = build_daily_capsule(session)
        return AgentResult(self.name, True, f"Built capsule for {cap.get('date')}")

