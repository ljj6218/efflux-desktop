from application.domain.events.event import Event, EventType
from application.port.inbound.event_handler import EventHandler
from application.port.outbound.ws_message_port import WsMessagePort
from common.core.container.annotate import component

import injector

@component
class InteractiveEventHandler(EventHandler):

    @injector.inject
    def __init__(
        self,
        ws_message_port: WsMessagePort,
    ):
        self.ws_message_port = ws_message_port

    def handle(self, event: Event) -> None:
        print('InteractiveEventHandler')
        self.ws_message_port.send(event)




    def type(self) -> str:
        return EventType.INTERACTIVE.value