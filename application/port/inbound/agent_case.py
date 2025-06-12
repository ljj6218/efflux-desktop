from abc import ABC, abstractmethod
from application.domain.agents.agent import Agent
from typing import Optional, Dict, Any, List


class AgentCase(ABC):

    @abstractmethod
    async def save(self, agent_dict: Dict[str, Any]) -> str:
        """
        Save the agent to the file.
        :param agent: agent domain
        :return:
        """

    @abstractmethod
    async def load(self, agent_id: str) -> Optional[Agent]:
        """
        Load the agent from the file.
        :param agent_id: agent id
        :return:
        """

    @abstractmethod
    async def load_all(self, ) -> List[Agent]:
        """
        Load all agent from the file.
        :return:
        """

    @abstractmethod
    async def load_by_name(self, agent_name: str) -> Optional[Agent]:
        """
        Load the agent from the file.
        :param agent_name: agent name
        :return:
        """