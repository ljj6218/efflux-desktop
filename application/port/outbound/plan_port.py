from abc import ABC, abstractmethod
from application.domain.plan import Plan
from typing import Optional

class PlanPort(ABC):

    @abstractmethod
    def sava(self, plan: Plan) -> Plan:
        pass

    @abstractmethod
    def load(self, conversation_id: str) -> Optional[Plan]:
        pass