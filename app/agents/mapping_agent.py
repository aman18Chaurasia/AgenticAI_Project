from sqlmodel import Session
from ..core.db import engine
from ..services.mapping import map_news_to_syllabus
from .base import Agent, AgentResult


class MappingAgent(Agent):
    name = "mapping-agent"

    def run(self) -> AgentResult:
        with Session(engine) as session:
            created = map_news_to_syllabus(session)
        return AgentResult(self.name, True, f"Created {created} mappings")

