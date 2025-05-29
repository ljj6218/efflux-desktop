from abc import ABC, abstractmethod
from application.domain.agent import Agent
from typing import Optional

class AgentPort(ABC):

    @abstractmethod
    def save(self, agent: Agent) -> str:
        pass

    @abstractmethod
    def load(self, agent_id: str) -> Optional[Agent]:
        pass