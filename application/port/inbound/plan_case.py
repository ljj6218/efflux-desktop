from abc import ABC, abstractmethod

from application.domain.plan import Plan


class PlanCase(ABC):

    @abstractmethod
    async def update(
        self,
        plan: Plan,
        agent_instance_id: str,
        is_update: bool,
        is_replan: bool,
        content: str,
        client_id: str,
        generator_id: str
    ) -> str:
        pass

    @abstractmethod
    async def load(
        self,
        conversation_id: str
    ) -> Plan:
        pass
