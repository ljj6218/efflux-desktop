from abc import ABC, abstractmethod
from application.domain.agents.agent import Agent, AgentInstance, AgentInfo
from application.domain.conversation import DialogSegment
from typing import Optional, List
from application.domain.generators.generator import LLMGenerator
from application.port.outbound.conversation_port import ConversationPort
from application.port.outbound.generators_port import GeneratorsPort
from application.port.outbound.tools_port import ToolsPort
from application.port.outbound.ws_message_port import WsMessagePort


class AgentPort(ABC):

    @abstractmethod
    def save(self, agent: Agent) -> str:
        pass

    @abstractmethod
    def load(self, agent_id: str) -> Optional[Agent]:
        pass

    @abstractmethod
    def load_by_name(self, agent_name: str) -> Optional[Agent]:
        pass

    @abstractmethod
    def make_instance(
        self,
        agent_info: AgentInfo,
        llm_generator: LLMGenerator,
        generators_port: GeneratorsPort,
        conversation_port: ConversationPort,
        ws_message_port: WsMessagePort,
        tools_port: ToolsPort,
    ) -> Optional[AgentInstance]:
        pass

    @abstractmethod
    def load_instance_info(self, instance_id: str, conversation_id: str) -> Optional[AgentInfo]:
        pass

    @abstractmethod
    def save_instance_info(self, instance_info: AgentInfo) -> AgentInfo:
        pass

    @abstractmethod
    def load_agent_teams(self) -> tuple[List[Agent], str]:
        pass

    @abstractmethod
    def check_agent_in_teams(self, agent_name: str) -> bool:
        pass
