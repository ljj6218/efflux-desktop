from abc import ABC, abstractmethod
from typing import Optional

class TestCase(ABC):

    @abstractmethod
    async def test_task(self):
        pass

    @abstractmethod
    async def test_task_stop(self, task_id:str) -> bool:
        pass

    @abstractmethod
    async def test_call_agent(self, query: str, generator_id: str, conversation_id: Optional[str] = None) -> tuple[str | None, str]:
        pass