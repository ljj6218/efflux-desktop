from application.domain.conversation import DialogSegment, DialogSegmentMetadata, MetadataSource, MetadataType
from application.domain.events.event import Event, EventType
from application.port.inbound.event_handler import EventHandler
from application.port.outbound.conversation_port import ConversationPort
from application.port.outbound.ws_message_port import WsMessagePort
from common.core.container.annotate import component

import injector

from common.utils.time_utils import create_from_second_now_to_int


@component
class InteractiveEventHandler(EventHandler):

    @injector.inject
    def __init__(
        self,
        ws_message_port: WsMessagePort,
        conversation_port: ConversationPort,
    ):
        self.ws_message_port = ws_message_port
        self.conversation_port = conversation_port

    def handle(self, event: Event) -> None:
        conversation_id = event.data['conversation_id']
        dialog_segment_id = event.data['dialog_segment_id']
        print('InteractiveEventHandler')
        # 记录用户确认消息
        dialog_segment = DialogSegment.make_assistant_message(content="", id=dialog_segment_id,
                                                              conversation_id=conversation_id,
                                                              model="",
                                                              timestamp=create_from_second_now_to_int(),
                                                              payload=event.payload,
                                                              metadata=DialogSegmentMetadata(
                                                                  source=MetadataSource.AGENT,
                                                                  type=MetadataType.USER_CONFIRMATION))
        self.conversation_port.add_agent_record(dialog_segment)
        # 发送ws消息
        self.ws_message_port.send(event)

    def type(self) -> str:
        return EventType.INTERACTIVE.value