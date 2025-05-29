from application.domain.events.event import EventType, Event
from application.domain.tasks.task import Task, TaskType
from application.port.inbound.event_handler import EventHandler


class UserConfirmEvent(EventHandler):


    def handle(self, event: Event) -> None:
        pass





    def type(self) -> str:
        return EventType.USER_CONFIRM.value