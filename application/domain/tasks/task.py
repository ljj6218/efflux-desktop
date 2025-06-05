from enum import Enum
from typing import Optional, List, Any
from pydantic import BaseModel
from common.utils.common_utils import create_uuid
from common.core.logger import get_logger

logger = get_logger(__name__)

class TaskState(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class TaskType(Enum):
    LLM_CALL = "LLM_CALL"
    TOOL_CALL = "TOOL_CALL"
    AGENT_CALL = "AGENT_CALL"
    AGENT_LLM_CALL = "AGENT_LLM_CALL"


class Task(BaseModel):

    id: str
    type: TaskType
    data: Any
    sub_data: Optional[Any] = None
    depends_on: Optional[List[Any]]
    state: TaskState

    @classmethod
    def from_singleton(cls, task_type: TaskType, data: Any, sub_data: Optional[Any] = None) -> "Task":
        task = cls(id=create_uuid(), type=task_type, data=data, sub_data=sub_data, depends_on=None, state=TaskState.PENDING)
        logger.info(f"创建单例任务 ---> [{task.id}]")
        return task

    def is_ready(self, completed_tasks):
        return all(dep in completed_tasks for dep in self.depends_on)