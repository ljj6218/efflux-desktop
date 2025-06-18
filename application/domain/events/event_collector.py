from application.domain.events.event import Event, EventGroupStatus
from typing import Dict, List, Optional, Callable
import threading
import time
import uuid

from common.core.logger import get_logger
logger = get_logger(__name__)

class EventCollector:
    """
    事件收集器，用于收集组事件并在组事件完成后进行处理
    """
    # 事件组映射 {group_id: List[Event]}
    _group_events: Dict[str, List[Event]] = {}
    # 事件组状态映射 {group_id: bool} - True表示已完成
    _group_completed: Dict[str, bool] = {}
    # 事件组最后活动时间 {group_id: float}
    _group_last_activity: Dict[str, float] = {}
    # 事件组处理器映射 {group_id: Callable}
    _group_handlers: Dict[str, Callable[[str, List[Event]], None]] = {}
    # 锁
    _lock = threading.Lock()
    # 清理线程
    _cleanup_thread = None
    # 是否运行中
    _running = False
    # 超时时间（秒）
    _timeout_seconds = 10

    @classmethod
    def initialize(cls, timeout_seconds: int = 10):
        """
        初始化事件收集器
        :param timeout_seconds: 超时时间（秒）
        """
        cls._timeout_seconds = timeout_seconds
        cls._start_cleanup_thread()

    @classmethod
    def _start_cleanup_thread(cls):
        """启动清理线程"""
        if cls._cleanup_thread is None or not cls._cleanup_thread.is_alive():
            cls._running = True
            cls._cleanup_thread = threading.Thread(target=cls._cleanup_expired_groups, daemon=True)
            cls._cleanup_thread.start()
            logger.info("事件收集器清理线程已启动")

    @classmethod
    def _cleanup_expired_groups(cls):
        """清理过期的事件组"""
        while cls._running:
            try:
                # 获取当前时间
                current_time = time.time()
                expired_groups = []

                # 查找过期的事件组
                with cls._lock:
                    for group_id, last_activity in cls._group_last_activity.items():
                        if current_time - last_activity > cls._timeout_seconds:
                            expired_groups.append(group_id)

                # 处理过期的事件组
                for group_id in expired_groups:
                    cls._process_expired_group(group_id)

                # 休眠一段时间
                time.sleep(1)
            except Exception as e:
                logger.error(f"清理过期事件组时发生错误: {str(e)}")

    @classmethod
    def _process_expired_group(cls, group_id: str):
        """
        处理过期的事件组
        :param group_id: 组ID
        """
        with cls._lock:
            if group_id not in cls._group_events:
                return

            events = cls._group_events[group_id].copy()  # 复制事件列表，保持原始顺序
            handler = cls._group_handlers.get(group_id)

            # 从映射中移除
            del cls._group_events[group_id]
            del cls._group_last_activity[group_id]
            cls._group_completed[group_id] = True
            if group_id in cls._group_handlers:
                del cls._group_handlers[group_id]

        # 记录日志
        logger.warning(f"事件组[{group_id}]超过{cls._timeout_seconds}秒无活动，自动完成处理")

        # 调用处理器
        if handler and events:
            try:
                handler(group_id, events)  # 直接传递事件列表，保持原始顺序
            except Exception as e:
                logger.error(f"调用事件组[{group_id}]处理器时发生错误: {str(e)}")

    @classmethod
    def collect_event(cls, event: Event) -> bool:
        """
        收集事件
        :param event: 事件
        :return: 是否成功收集
        """

        # 如果不是组事件，直接返回False
        if not event.group or not event.group.id:
            return False

        group_id = event.group.id
        current_time = time.time()

        with cls._lock:
            # 如果组已完成，不再收集
            if group_id in cls._group_completed and cls._group_completed[group_id]:
                logger.warning(f"事件组[{group_id}]已完成，不再收集事件")
                return False

            # 更新最后活动时间
            cls._group_last_activity[group_id] = current_time

            # 如果是新组，初始化
            if group_id not in cls._group_events:
                cls._group_events[group_id] = []
                cls._group_completed[group_id] = False

            # 添加事件到组
            cls._group_events[group_id].append(event)

            # 如果是结束事件，标记组为已完成
            if event.group.status == EventGroupStatus.ENDED or event.group.status == EventGroupStatus.STOPPED:
                cls._group_completed[group_id] = True
                completed = True
                events = cls._group_events[group_id].copy()  # 复制事件列表，保持原始顺序
                handler = cls._group_handlers.get(group_id)
            else:
                completed = False
                events = None
                handler = None

        # 如果组已完成，调用处理器
        if completed and handler and events:
            try:
                handler(group_id, events)  # 直接传递事件列表，保持原始顺序
            except Exception as e:
                logger.error(f"调用事件组[{group_id}]处理器时发生错误: {str(e)}")

            # 清理组数据
            with cls._lock:
                if group_id in cls._group_events:
                    del cls._group_events[group_id]
                if group_id in cls._group_last_activity:
                    del cls._group_last_activity[group_id]
                if group_id in cls._group_handlers:
                    del cls._group_handlers[group_id]

            logger.info(f"事件组[{group_id}]处理完成，共{len(events)}个事件")

        return True

    @classmethod
    def register_group_handler(cls, group_id: str, handler: Callable[[str, List[Event]], None]):
        """
        注册事件组处理器
        :param group_id: 组ID
        :param handler: 处理器函数，接收组ID和事件列表作为参数
        """
        with cls._lock:
            cls._group_handlers[group_id] = handler
            
            # 如果组已完成，立即调用处理器
            if group_id in cls._group_completed and cls._group_completed[group_id]:
                if group_id in cls._group_events:
                    events = cls._group_events[group_id].copy()  # 复制事件列表，保持原始顺序
                    
                    # 清理组数据
                    del cls._group_events[group_id]
                    if group_id in cls._group_last_activity:
                        del cls._group_last_activity[group_id]
                    del cls._group_handlers[group_id]
                    
                    # 调用处理器
                    try:
                        handler(group_id, events)  # 直接传递事件列表，保持原始顺序
                    except Exception as e:
                        logger.error(f"调用事件组[{group_id}]处理器时发生错误: {str(e)}")
                    
                    logger.info(f"事件组[{group_id}]已完成，立即处理，共{len(events)}个事件")

    @classmethod
    def get_group_events(cls, group_id: str) -> Optional[List[Event]]:
        """
        获取组事件
        :param group_id: 组ID
        :return: 事件列表，如果组不存在则返回None
        """
        with cls._lock:
            if group_id in cls._group_events:
                return cls._group_events[group_id].copy()
            return None

    @classmethod
    def is_group_completed(cls, group_id: str) -> bool:
        """
        检查组是否已完成
        :param group_id: 组ID
        :return: 是否已完成
        """
        with cls._lock:
            if group_id in cls._group_completed:
                return cls._group_completed[group_id]
            return False

    @classmethod
    def shutdown(cls):
        """关闭事件收集器"""
        cls._running = False
        
        # 等待清理线程结束
        if cls._cleanup_thread and cls._cleanup_thread.is_alive():
            cls._cleanup_thread.join(timeout=3)
            logger.info("事件收集器清理线程已关闭")
        
        # 处理所有未完成的事件组
        with cls._lock:
            for group_id, events in cls._group_events.items():
                handler = cls._group_handlers.get(group_id)
                if handler:
                    try:
                        handler(group_id, events)
                    except Exception as e:
                        logger.error(f"关闭时处理事件组[{group_id}]时发生错误: {str(e)}")
            
            # 清空所有映射
            cls._group_events.clear()
            cls._group_completed.clear()
            cls._group_last_activity.clear()
            cls._group_handlers.clear()
