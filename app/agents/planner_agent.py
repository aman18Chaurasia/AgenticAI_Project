from sqlmodel import Session
from ..core.db import engine
from ..services.planner import generate_plan_for_default_user
from .base import Agent, AgentResult


class PlannerAgent(Agent):
    name = "planner-agent"

    def run(self) -> AgentResult:
        with Session(engine) as session:
            generate_plan_for_default_user(session)
        return AgentResult(self.name, True, "Plan generated/updated")

