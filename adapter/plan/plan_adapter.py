from application.domain.plan import Plan
from application.port.outbound.plan_port import PlanPort
from common.core.container.annotate import component
from common.utils.file_util import check_file, check_file_and_create
from typing import Optional

from common.utils.json_file_util import JSONFileUtil


@component
class PlanAdapter(PlanPort):

    plan_file_pre_url = "conversations/plan/"

    def sava(self, plan: Plan) -> Plan:
        plan_file = f"{self.plan_file_pre_url}{plan.conversation_id}.json"
        check_file_and_create(file_url=plan_file)
        plan_file_config = JSONFileUtil(plan_file)
        plan_file_config.update_key(plan.conversation_id, plan.model_dump())
        return plan

    def load(self, conversation_id: str) -> Optional[Plan]:
        plan_file = f"{self.plan_file_pre_url}{conversation_id}.json"
        if check_file(plan_file):
            plan_file_config = JSONFileUtil(plan_file)
            # 遍历所有plan
            for plan_dict_conversation_id in plan_file_config.read().keys():
                # 获取plan
                if plan_dict_conversation_id == conversation_id:
                    plan_dict = plan_file_config.read_key(conversation_id)
                    plan = Plan.model_validate(plan_dict)
                    return plan
        return None