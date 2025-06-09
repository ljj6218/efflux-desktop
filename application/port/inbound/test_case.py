from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk

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

    @abstractmethod
    async def test_prompts(self, chunks: List[ChatStreamingChunk], generator_id: str) -> Dict[str, Any]:
        pass