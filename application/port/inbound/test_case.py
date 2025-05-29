from abc import ABC, abstractmethod

class TestCase(ABC):

    @abstractmethod
    async def test_task(self):
        pass