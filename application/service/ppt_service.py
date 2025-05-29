from typing import List, Optional, Dict, Any

from application.domain.events.event import Event, EventType
from application.port.inbound.ppt_case import PPTCase
from common.core.container.annotate import component
from application.port.outbound.event_port import EventPort
import injector

@component
class PPTService(PPTCase):

    @injector.inject
    def __init__(self, event_port: EventPort):
        self.event_port = event_port

    async def generate(self, generator_id: str, query: str, conversation_id: str, mcp_name_list: List[str],
                       task_confirm: Optional[Dict[str, Any]] = None) -> str:

        # if task_confirm:
        #     event_data: Dict[str, Any] = {
        #         'generator_id': generator_id,
        #         'conversation_id': conversation_id,
        #         'mcp_name_list': mcp_name_list,
        #     }
        #     return self.event_port.emit_event(Event.from_init(event_type=EventType.TOOL_CALL_CONFiRM, event_data=event_data))
        # else:
        #     return self.event_port.emit_event(
        #         Event.from_init(
        #             event_type=EventType.USER_MESSAGE,
        #             event_data=MessageEventData.from_user_message(
        #                 content=query, generator_id=generator_id,
        #                 conversation_id=conversation_id, mcp_name_list=mcp_name_list
        #             )
        #         )
        #     )

        return 'ok'