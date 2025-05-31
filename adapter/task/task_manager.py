from concurrent.futures import ThreadPoolExecutor, Future
from application.domain.tasks.task import Task
from application.domain.events.event import Event, EventType, EventSubType
from common.core.container.annotate import component
from common.core.container.container import get_container
from application.port.inbound.task_handler import TaskHandler
from application.port.outbound.task_port import TaskPort
from application.port.outbound.event_port import EventPort
from typing import List, Dict, Type
import injector
import time
import traceback
import asyncio
from common.core.logger import get_logger

logger = get_logger(__name__)


@component
class TaskManager(TaskPort):

    @injector.inject
    def __init__(self, task_handler_cls: List[Type[TaskHandler]]):
        self.task_handler_map: Dict[str, TaskHandler] = {}
        for cls in task_handler_cls:
            task_handler = get_container().get(cls)  # TODO 貌似自动注入的bug，目前注入进来的是类，这里暂时手动解决
            self.task_handler_map[task_handler.type()] = task_handler

        # 存储任务Future的字典，用于跟踪任务状态
        self.task_futures: Dict[str, Future] = {}

    # 初始化线程池
    executor = ThreadPoolExecutor(max_workers=5)

    # 一个简单的长耗时任务模拟
    def _long_task(self, task: Task, task_handler: TaskHandler):
        try:
            logger.info(f"开始执行任务 {task.id} 类型: {task.type}")
            result = task_handler.execute(task)

            # 检查返回值是否是协程对象
            if asyncio.iscoroutine(result):
                # 如果是协程，使用事件循环运行它
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(result)
                finally:
                    loop.close()

            logger.info(f"任务 {task.id} 执行完成")
            return f"Task {task.id} completed successfully"
        except Exception as e:
            error_msg = f"任务 {task.id} 执行失败: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())  # 记录完整的堆栈跟踪
            # 重新抛出异常，让Future知道任务失败了
            raise

    def execute_task(self, task: Task):
        logger.info(f"提交任务 {task.id} 类型: {task.type}")

        if task.type.value not in self.task_handler_map:
            error_msg = f"找不到处理任务类型 {task.type.value} 的处理器"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 提交任务到线程池并保存Future对象
        future = self.executor.submit(self._long_task, task, self.task_handler_map[task.type.value])
        self.task_futures[task.id] = future

        # 添加回调函数来处理任务完成或失败
        future.add_done_callback(lambda f: self._task_completed_callback(task.id, f))

        return task.id

    def _task_completed_callback(self, task_id: str, future: Future):
        """处理任务完成的回调函数"""
        try:
            # 尝试获取结果，如果任务失败，这里会抛出异常
            result = future.result()
            logger.info(f"任务 {task_id} 回调: {result}")
        except Exception as e:
            logger.error(f"任务 {task_id} 在回调中检测到失败: {str(e)}")
            EventPort.get_event_port().emit_event(
                Event.from_init(
                    event_type=EventType.SYSTEM,
                    event_sub_type=EventSubType.ERROR,
                    data={
                        "code": "1",
                        "message": str(e)
                    }
                )
            )
        finally:
            # 清理完成的任务
            if task_id in self.task_futures:
                del self.task_futures[task_id]

    def get_task_status(self, task_id: str) -> str:
        """获取任务状态"""
        if task_id not in self.task_futures:
            return "NOT_FOUND"

        future = self.task_futures[task_id]
        if future.done():
            try:
                future.result()  # 检查是否有异常
                return "COMPLETED"
            except Exception:
                return "FAILED"
        elif future.running():
            return "RUNNING"
        else:
            return "PENDING"

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id not in self.task_futures:
            logger.warning(f"任务 {task_id} 未找到，无法取消")
            return False

        future = self.task_futures[task_id]

        # 如果任务正在运行，尝试取消
        if future.running():
            success = future.cancel()
            if success:
                logger.info(f"任务 {task_id} 被取消")
                # 在任务取消后，确保清理任务
                del self.task_futures[task_id]
                return True
            else:
                logger.warning(f"任务 {task_id} 无法取消")
                return False
        else:
            logger.warning(f"任务 {task_id} 不是在运行状态，无法取消")
            return False

    def shutdown(self):
        """关闭任务管理器"""
        logger.info("正在关闭任务管理器...")
        self.executor.shutdown(wait=True)
        logger.info("任务管理器已关闭")
