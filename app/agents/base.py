from dataclasses import dataclass


@dataclass
class AgentResult:
    name: str
    success: bool
    detail: str = ""


class Agent:
    name: str = "agent"

    def run(self) -> AgentResult:
        raise NotImplementedError

