from abc import ABC, abstractmethod

class TestCase(ABC):

    @abstractmethod
    async def test_task(self):
        pass

    @abstractmethod
    async def test_task_stop(self, task_id:str) -> bool:
        pass