from application.domain.events.event import EventType, Event, EventSubType
from application.port.outbound.ws_message_port import WsMessagePort
from application.port.inbound.event_handler import EventHandler
from common.core.container.annotate import component
import injector

@component
class SystemEventHandler(EventHandler):

    @injector.inject
    def __init__(
        self,
        ws_message_port: WsMessagePort,
    ):
        self.ws_message_port = ws_message_port


    def handle(self, event: Event) -> None:
        if event.sub_type == EventSubType.STOP:
            print(f"======停止====={event}")

        self.ws_message_port.send(event.model_dump_json())

    def type(self) -> str:
        return EventType.SYSTEM.value