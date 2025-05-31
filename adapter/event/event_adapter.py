from application.domain.events.event import Event, EventGroupStatus
from application.port.inbound.event_handler import EventHandler
from application.port.outbound.event_port import EventPort
from common.core.container.annotate import component
from common.core.container.container import get_container
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Type, Optional
import injector
import threading
import queue
import time

from common.core.logger import get_logger
logger = get_logger(__name__)

@component
class EventAdapter(EventPort):
    # 主事件队列（用于非组事件）
    _event_queue = queue.Queue()
    # 事件组队列映射 {group_id: Queue}
    _group_queues: Dict[str, queue.Queue] = {}
    # 事件组线程映射 {group_id: Thread}
    _group_threads: Dict[str, threading.Thread] = {}
    # 主事件处理线程
    _event_thread = None
    # 是否运行中
    _running = False
    # 事件处理器锁
    _lock = threading.Lock()
    # 事件组锁
    _group_lock = threading.Lock()

    @injector.inject
    def __init__(self, event_handlers_cls: List[Type[EventHandler]]):
        self.event_handlers_map: Dict[str, List[EventHandler]] = {}
        
        # 初始化事件处理器映射
        for cls in event_handlers_cls:
            event_handler = get_container().get(cls)
            event_type = event_handler.type()
            
            with self._lock:
                if event_type not in self.event_handlers_map:
                    self.event_handlers_map[event_type] = []
                self.event_handlers_map[event_type].append(event_handler)

        # 创建处理器执行线程池
        self.handler_executor = ThreadPoolExecutor(max_workers=10)
        
        # 启动事件处理线程
        self._start_event_thread()

    def _start_event_thread(self):
        """启动主事件处理线程"""
        if self._event_thread is None or not self._event_thread.is_alive():
            self._running = True
            self._event_thread = threading.Thread(target=self._process_events, daemon=True)
            self._event_thread.start()
            logger.info("主事件处理线程已启动")

    def _start_group_thread(self, group_id: str):
        """启动事件组处理线程"""
        with self._group_lock:
            if group_id not in self._group_queues:
                self._group_queues[group_id] = queue.Queue()
            
            if group_id not in self._group_threads or not self._group_threads[group_id].is_alive():
                thread = threading.Thread(
                    target=self._process_group_events,
                    args=(group_id,),
                    daemon=True
                )
                self._group_threads[group_id] = thread
                thread.start()
                logger.info(f"事件组[{group_id}]处理线程已启动")

    def _process_events(self):
        """主事件处理线程函数"""
        while self._running:
            event: Optional[Event] = None
            try:
                # 从队列获取事件，超时2秒
                event = self._event_queue.get(timeout=2)
                self._dispatch_event(event)
                self._event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                if event:
                    logger.error(f"处理事件[{event.id}]时发生错误: {str(e)}")
                else:
                    logger.error(f"处理事件[未知]时发生错误: {str(e)}")

    def _process_group_events(self, group_id: str):
        """事件组处理线程函数"""
        group_queue = self._group_queues[group_id]
        
        # 添加最后活动时间记录
        last_activity_time = time.time()
        # 设置超时时间（秒）
        timeout_seconds = 10  # 可以根据实际需求调整
        
        while self._running:
            try:
                # 从组队列获取事件，使用较短的超时时间以便检查组超时
                try:
                    event = group_queue.get(timeout=2)
                    # 更新最后活动时间
                    last_activity_time = time.time()
                    
                    # 处理事件
                    self._dispatch_event(event)
                    group_queue.task_done()
                    
                    # 如果是组结束事件，则退出线程
                    if event.group and (event.group.status == EventGroupStatus.ENDED or event.group.status == EventGroupStatus.STOPPED):
                        logger.info(f"事件组[{group_id}]处理完成{event.group.status}，线程退出")
                        with self._group_lock:
                            if group_id in self._group_threads:
                                del self._group_threads[group_id]
                            if group_id in self._group_queues:
                                del self._group_queues[group_id]
                        break
                except queue.Empty:
                    # 检查是否超时
                    current_time = time.time()
                    if current_time - last_activity_time > timeout_seconds:
                        logger.warning(f"事件组[{group_id}]超过{timeout_seconds}秒无活动，自动关闭")
                        with self._group_lock:
                            if group_id in self._group_threads:
                                del self._group_threads[group_id]
                            if group_id in self._group_queues:
                                del self._group_queues[group_id]
                        break
                    
                    # 检查组是否已被清理（可能由其他线程处理了结束事件）
                    with self._group_lock:
                        if group_id not in self._group_queues:
                            break
                    continue
                    
            except Exception as e:
                logger.error(f"处理事件组[{group_id}]事件时发生错误: {str(e)}")
                # 更新最后活动时间，避免因错误导致过早超时
                last_activity_time = time.time()

    def _dispatch_event(self, event: Event):
        """分发事件到对应的处理器"""
        event_type = event.type.value

        with self._lock:
            handlers = self.event_handlers_map.get(event_type, [])
        
        if not handlers:
            logger.warning(f"没有找到事件类型 [{event_type}] 的处理器")
            return
        
        # 使用线程池并行处理所有处理器
        futures = []
        for handler in handlers:
            future = self.handler_executor.submit(self._execute_handler, handler, event)
            futures.append(future)

    @staticmethod
    def _execute_handler(handler: EventHandler, event: Event):
        """在线程池中执行事件处理器"""
        try:
            handler.handle(event)
        except Exception as e:
            logger.error(f"事件处理器 {handler.__class__.__name__} 处理事件 {event} 时发生错误: {str(e)}")

    def emit_event(self, event: Event) -> str:
        """发布事件"""
        # 只有非组内事件或组的开始/结束事件才打印日志
        if not event.group or event.group.status in [EventGroupStatus.STARTED, EventGroupStatus.ENDED, EventGroupStatus.STOPPED]:
            logger.info(f"事件发布 ---> [{event.id} - {event.type.value}]")
        
        # 如果是组事件，放入对应的组队列
        if event.group and event.group.id:
            group_id = event.group.id
            
            # 如果是组开始事件，启动组处理线程
            if event.group.status == EventGroupStatus.STARTED:
                self._start_group_thread(group_id)

            # 将事件放入组队列
            with self._group_lock:
                if group_id in self._group_queues:
                    self._group_queues[group_id].put(event)
                else:
                    # 如果组队列不存在（可能是已经处理完毕），则放入主队列
                    logger.warning(f"事件组[{group_id}]队列不存在，事件将放入主队列")
                    self._event_queue.put(event)
        else:
            # 非组事件放入主队列
            self._event_queue.put(event)
            
        return event.id
    
    def register_handler(self, handler: EventHandler):
        """动态注册事件处理器"""
        event_type = handler.type()
        
        with self._lock:
            if event_type not in self.event_handlers_map:
                self.event_handlers_map[event_type] = []
            self.event_handlers_map[event_type].append(handler)
        
        logger.info(f"已注册事件处理器 {handler.__class__.__name__} 用于事件类型 {event_type}")
    
    def shutdown(self):
        """关闭事件处理线程"""
        self._running = False
        
        # 关闭主事件线程
        if self._event_thread and self._event_thread.is_alive():
            self._event_thread.join(timeout=5)
            logger.warning("主事件处理线程已关闭")
        
        # 关闭所有组线程
        with self._group_lock:
            for group_id, thread in self._group_threads.items():
                if thread.is_alive():
                    thread.join(timeout=2)
            self._group_threads.clear()
            self._group_queues.clear()
            logger.warning("所有事件组处理线程已关闭")
        
        # 关闭线程池
        self.handler_executor.shutdown(wait=False)
        logger.warning("事件处理器线程池已关闭")