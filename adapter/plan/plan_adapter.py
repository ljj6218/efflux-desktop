from application.domain.plan import Plan
from application.port.outbound.plan_port import PlanPort
from common.utils.file_util import check_file_and_create, check_file
from common.core.container.annotate import component
from typing import Optional
import jsonlines

@component
class PlanAdapter(PlanPort):

    plan_file_pre_url = "conversations/plan/"

    def sava(self, plan: Plan) -> Plan:
        plan_file = f"{self.plan_file_pre_url}{plan.conversation_id}.jsonl"
        check_file_and_create(plan_file)
        with jsonlines.open(plan_file, mode='a') as writer:
            writer.write(plan.model_dump())
        return plan

    def load(self, conversation_id: str) -> Optional[Plan]:
        plan_file = f"{self.plan_file_pre_url}{conversation_id}.jsonl"
        if check_file(plan_file):
            with jsonlines.open(plan_file, mode='r') as reader:
                for obj in reader:
                    if obj['conversation_id'] == conversation_id:
                        plan = Plan.model_validate(obj)
                        return plan
        return None