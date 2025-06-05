from abc import ABC, abstractmethod
from application.domain.agent import Agent
from application.domain.conversation import DialogSegment
from typing import Optional, List

class AgentPort(ABC):

    @abstractmethod
    def save(self, agent: Agent) -> str:
        pass

    @abstractmethod
    def load(self, agent_id: str) -> Optional[Agent]:
        pass

    @abstractmethod
    def load_record(self, agent_instance_id: str) -> List[DialogSegment]:
        pass

    @abstractmethod
    def add_record(self, dialog_segment: DialogSegment) -> DialogSegment:
        pass