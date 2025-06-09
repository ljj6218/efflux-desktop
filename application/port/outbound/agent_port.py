from abc import ABC, abstractmethod
from application.domain.agents.agent import Agent, AgentInstance, AgentInfo
from application.domain.conversation import DialogSegment
from typing import Optional, List
from application.domain.generators.generator import LLMGenerator
from application.port.outbound.generators_port import GeneratorsPort
from application.port.outbound.ws_message_port import WsMessagePort


class AgentPort(ABC):

    @abstractmethod
    def save(self, agent: Agent) -> str:
        pass

    @abstractmethod
    def load(self, agent_id: str) -> Optional[Agent]:
        pass

    @abstractmethod
    def make_instance(
        self,
        agent_info: AgentInfo,
        llm_generator: LLMGenerator,
        generators_port: GeneratorsPort,
        ws_message_port: WsMessagePort,
    ) -> Optional[AgentInstance]:
        pass

    @abstractmethod
    def load_instance_info(self, instance_id: str, conversation_id: str) -> Optional[AgentInfo]:
        pass

    @abstractmethod
    def save_instance_info(self, instance_info: AgentInfo) -> AgentInfo:
        pass

    @abstractmethod
    def load_record(self, agent_instance_id: str) -> List[DialogSegment]:
        pass

    @abstractmethod
    def add_record(self, dialog_segment: DialogSegment) -> DialogSegment:
        pass