from enum import Enum
from typing import List, Optional
from common.utils.common_utils import create_uuid

from pydantic import BaseModel

class PlanState(Enum):
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    DONE = "DONE"

class PlanStep(BaseModel):
    index: int
    title: str
    details: str
    need_confirm: Optional[bool] = False
    agent_name: str

class Plan(BaseModel):
    id: str
    conversation_id: str
    task: str
    plan_summary: str
    current_step: int
    state: PlanState
    steps: List[PlanStep]

    def __str__(self) -> str:
        """Return the string representation of the plan."""
        plan_str = ""
        if self.task is not None:
            plan_str += f"Task: {self.task}\n"
        for i, step in enumerate(self.steps):
            plan_str += f"{i}. {step.agent_name}: {step.title}\n   {step.details}\n"
        return plan_str

    def model_dump(self, **kwargs):
        # 使用 super() 获取字典格式
        data = super().model_dump()
        # 转换 为字符串
        data['state'] = self.state.value if self.state else None
        return data

    @classmethod
    def model_validate(cls, obj, **kwargs):
        # 字符串转枚举
        if 'state' in obj and isinstance(obj['state'], PlanState):
            obj['state'] = PlanState(value=obj['state'])
        return super().model_validate(obj)

    @classmethod
    def from_init(cls, conversation_id: str, task: str, plan_summary: str,  steps: List[PlanStep]) -> "Plan":
        return cls(
            id = create_uuid(),
            conversation_id = conversation_id,
            task = task,
            plan_summary = plan_summary,
            steps = steps,
            state=PlanState.INITIALIZING,
            current_step=0
        )
