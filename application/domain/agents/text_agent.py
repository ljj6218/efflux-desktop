from typing import List, Dict, Any

from application.domain.agents.agent import AgentInstance
from application.domain.conversation import DialogSegment, DialogSegmentMetadata, MetadataSource, MetadataType
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from application.domain.generators.generator import LLMGenerator
from application.port.outbound.conversation_port import ConversationPort
from application.port.outbound.generators_port import GeneratorsPort
from application.port.outbound.tools_port import ToolsPort
from application.port.outbound.ws_message_port import WsMessagePort
from common.utils.time_utils import create_from_second_now_to_int


class TextAgent(AgentInstance):

    def __init__(
            self,
            generators_port: GeneratorsPort,
            llm_generator: LLMGenerator,
            ws_message_port: WsMessagePort,
            conversation_port: ConversationPort,
            tools_port: ToolsPort,
    ):
        super().__init__(llm_generator, generators_port, ws_message_port, conversation_port, tools_port)


    async def lazy_init(self, config: Dict[str, Any]) -> None:
        pass

    def execute(self, history_message_list: List[ChatStreamingChunk], payload: Dict[str, Any], client_id: str) -> None:
        dialog_segment = DialogSegment.make_assistant_message(content=payload['plan'].to_show_user_str(),
                                                              id=self.info.dialog_segment_id,
                                                              conversation_id=self.info.conversation_id,
                                                              model=self.llm_generator.model,
                                                              timestamp=create_from_second_now_to_int(),
                                                              payload={'agent_instance_id': self.info.instance_id},
                                                              metadata=DialogSegmentMetadata(
                                                                  source=MetadataSource.AGENT,
                                                                  type=MetadataType.AGENT_RESULT))