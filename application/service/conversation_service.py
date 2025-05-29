from typing import List

from application.domain.conversation import Conversation, DialogSegment
from common.core.container.annotate import component
from application.port.inbound.conversation_case import ConversationCase
from application.port.outbound.conversation_port import ConversationPort
import injector
from common.core.logger import get_logger

logger = get_logger(__name__)

@component
class ConversationService(ConversationCase):

    @injector.inject
    def __init__(self, conversation_port: ConversationPort):
        self.conversation_port = conversation_port

    async def conversation_load_list(self) -> List[Conversation]:
        return self.conversation_port.conversation_load_list()

    async def conversation_load(self, conversation_id: str) -> Conversation:
        return self.conversation_port.conversation_load(conversation_id)

    async def conversation_update_theme(self, conversation_id: str, theme: str) -> Conversation:
        return self.conversation_port.conversation_update(Conversation.from_update_theme(id=conversation_id, theme=theme))

    async def conversation_remove_dialog_segment(self, dialog_segment: DialogSegment):
        logger.info(f"删除会话片段 ---> [dialog_segment_id={dialog_segment.id}, conversation_id={dialog_segment.conversation_id}]")
        return self.conversation_port.dialog_segment_remove(dialog_segment)

    async def conversation_remove(self, conversation_id_list: List[str]) -> int:
        logger.info(f"删除会话集合 ---> {conversation_id_list}")
        count = 0
        for conversation_id in conversation_id_list:
            self.conversation_port.conversation_remove(conversation_id)
            count += 1
        return count
