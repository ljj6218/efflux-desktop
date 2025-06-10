from typing import List, Dict, Any

from adapter.agent.prompts.clarification import SYSTEM_MESSAGE_CLARIFICATION
from application.domain.agents.agent import AgentInstance, Agent, AgentState
from application.domain.events.event import Event, EventType, EventSubType, EventSource
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from application.domain.generators.generator import LLMGenerator
from application.port.outbound.event_port import EventPort
from application.port.outbound.generators_port import GeneratorsPort
from application.port.outbound.ws_message_port import WsMessagePort
from common.core.logger import get_logger
from common.utils.common_utils import create_uuid

logger = get_logger(__name__)

class ClarificationAgent(AgentInstance):

    def __init__(
        self,
        generators_port: GeneratorsPort,
        llm_generator: LLMGenerator,
        ws_message_port: WsMessagePort
    ):
        super().__init__(llm_generator, generators_port, ws_message_port)

    async def lazy_init(self, config: Dict[str, Any]) -> None:
        pass

    def execute(self, history_message_list: List[ChatStreamingChunk], payload: Dict[str, Any], client_id: str) -> None:
        # 拼接生成Clarification的提示词
        context_message_list = self._thread_to_context(history_message_list=history_message_list)

        if "json_result_data" in payload: # 模型返回json结果
            json_result_data = payload["json_result_data"]
            if json_result_data['needs_clarification']:
                logger.info("需要用户继续澄清需求")
            else:
                self._send_agent_result_event(client_id=client_id, payload=payload, agent_state=AgentState.DONE)
        else:
            # 请求大模型澄清用户需求
            self._send_llm_event(client_id=client_id, context_message_list=context_message_list)


    def _thread_to_context(self, history_message_list: List[ChatStreamingChunk]) -> List[ChatStreamingChunk]:
        """拼装基础system提示词和会话历史信息"""
        # 拼装系统提示词
        messages: List[ChatStreamingChunk] = [ChatStreamingChunk.from_system(
            message=SYSTEM_MESSAGE_CLARIFICATION
        )]
        # 拼装对话上下文
        messages.extend(history_message_list)
        return messages

    def _send_agent_result_event(self, client_id: str, payload: Dict[str, Any], agent_state: AgentState) -> None:
        payload['agent_state'] = agent_state
        payload['update'] = False
        event = Event.from_init(
            client_id=client_id,
            event_type=EventType.AGENT,
            event_sub_type=EventSubType.AGENT_CALL_RESULT,
            source=EventSource.AGENT,
            data={
                "id": create_uuid(),
                "agent_instance_id": self.info.instance_id,
                "dialog_segment_id": self.info.dialog_segment_id,
                "conversation_id": self.info.conversation_id,
                "generator_id": self.info.generator_id,
            },
            payload=payload
        )
        EventPort.get_event_port().emit_event(event)

    def _send_llm_event(self, client_id: str, context_message_list: List[ChatStreamingChunk]):
        """发送大模型请求事件"""
        event = Event.from_init(
            event_type=EventType.USER_MESSAGE,
            event_sub_type=EventSubType.MESSAGE,
            client_id=client_id,
            source=EventSource.AGENT,
            data={
                "id": create_uuid(),
                "dialog_segment_id": self.info.dialog_segment_id,
                "conversation_id": self.info.conversation_id,
                "generator_id": self.info.generator_id,
            },
            payload={
                "agent_instance_id": self.info.instance_id,
                "json_result": True,
                "mcp_name_list": [],
                "tools_group_name_list": [],
                "context_message_list": context_message_list,
            }
        )
        EventPort.get_event_port().emit_event(event)
        logger.info(
            f"[{self.info.name}]Agent实例[{self.info.instance_id}],发送LLM请求事件[{self.info.dialog_segment_id}]")