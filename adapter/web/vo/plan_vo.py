from pydantic import BaseModel
from application.domain.plan import Plan
from typing import Optional

class PlanVO(BaseModel):
    plan: Plan
    agent_instance_id: str
    is_update: bool
    is_replan: Optional[bool] = False
    content: Optional[str] = None
    client_id: str
    generator_id: str