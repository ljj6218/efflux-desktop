from abc import ABC, abstractmethod
from application.domain.events.event import Event
from application.port.inbound.event_handler import EventHandler
from common.core.container.container import get_container

class EventPort(ABC):
    
    @abstractmethod
    def emit_event(self, event: Event) -> str:
        """发布事件"""
        pass
    
    @abstractmethod
    def register_handler(self, handler: EventHandler):
        """动态注册事件处理器"""
        pass
    
    @abstractmethod
    def shutdown(self):
        """关闭事件处理"""
        pass

    @classmethod
    def get_event_port(cls) -> "EventPort":
        return get_container().get(EventPort)