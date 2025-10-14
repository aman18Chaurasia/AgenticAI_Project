from sqlmodel import Session
from ..core.db import engine
from ..services.ingest import fetch_and_parse_feeds, save_news_items
from .base import Agent, AgentResult


class NewsAgent(Agent):
    name = "news-agent"

    def run(self) -> AgentResult:
        items = fetch_and_parse_feeds()
        with Session(engine) as session:
            saved = save_news_items(session, items)
        return AgentResult(self.name, True, f"Fetched {len(items)}; saved {len(saved)}")

