from abc import ABC, abstractmethod

class GeneratorsCase(ABC):

    @abstractmethod
    async def generate(self):
        pass