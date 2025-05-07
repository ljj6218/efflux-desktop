from abc import ABC, abstractmethod

class TestCase(ABC):
    @abstractmethod
    async def test_add(self):
        pass
    @abstractmethod
    def test_del(self):
        pass