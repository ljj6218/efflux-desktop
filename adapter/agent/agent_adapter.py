from application.domain.agent import Agent
from application.domain.conversation import DialogSegment
from application.port.outbound.agent_port import AgentPort
from common.core.container.annotate import component
from common.utils.file_util import check_file_and_create, check_file
from common.utils.json_file_util import JSONFileUtil
from typing import Optional, Dict, List

import jsonlines

# from adapter.agent.prompts.browser import (
#     WEB_SURFER_OCR_PROMPT,
#     WEB_SURFER_QA_PROMPT,
#     WEB_SURFER_QA_SYSTEM_MESSAGE,
#     WEB_SURFER_TOOL_PROMPT,
#     WEB_SURFER_SYSTEM_MESSAGE,
#     WEB_SURFER_NO_TOOLS_PROMPT,
# )


@component
class AgentAdapter(AgentPort):

    agent_file_url = "adapter/agent/agent.json"

    def load_record(self, agent_instance_id: str) -> List[DialogSegment]:
        dialog_segment_list = []
        dialog_segment_file = f'conversations/agent/{agent_instance_id}.jsonl'
        if not check_file(dialog_segment_file): # 不存在，返回空列表
            return dialog_segment_list
        with jsonlines.open(dialog_segment_file, mode='r') as reader:
            for obj in reader:
                dialog_segment_list.append(DialogSegment.model_validate(obj))
        return dialog_segment_list

    def add_record(self, dialog_segment: DialogSegment) -> DialogSegment:
        dialog_segment_file = f'conversations/agent/{dialog_segment.agent_id}.jsonl'
        check_file_and_create(dialog_segment_file)
        with jsonlines.open(dialog_segment_file, mode='a') as writer:
            writer.write(dialog_segment.model_dump())
        return dialog_segment

    def save(self, agent: Agent) -> str:
        # check_file_and_create(self.agent_file_url, init_str="{}")
        agent_config = JSONFileUtil(self.agent_file_url)
        agent_config.update_key(agent.id, agent.model_dump())
        return agent.id

    def load(self, agent_id: str) -> Optional[Agent]:
        agent_config = JSONFileUtil(self.agent_file_url)
        # 遍历所有agent
        for agent_dict_id in agent_config.read().keys():
            # 获取agent
            if agent_dict_id == agent_id:
                agent_dict = agent_config.read_key(agent_id)
                agent = Agent.model_validate(agent_dict)
                # 加载所有提示词 TODO 后面可能会持久化，统一返回
                # agent.agent_prompts = self._load_prompt_list(agent.name)
                return agent
        return None

    # @staticmethod
    # def _load_prompt_list(type: str) -> List[Dict[str, str]]:
    #     prompt_list = []
    #     if type == "browser":
    #         prompt_list.append({'WEB_SURFER_OCR_PROMPT': WEB_SURFER_OCR_PROMPT})
    #         prompt_list.append({'WEB_SURFER_QA_PROMPT': WEB_SURFER_QA_PROMPT})
    #         prompt_list.append({'WEB_SURFER_QA_SYSTEM_MESSAGE': WEB_SURFER_QA_SYSTEM_MESSAGE})
    #         prompt_list.append({'WEB_SURFER_TOOL_PROMPT': WEB_SURFER_TOOL_PROMPT})
    #         prompt_list.append({'WEB_SURFER_SYSTEM_MESSAGE': WEB_SURFER_SYSTEM_MESSAGE})
    #         prompt_list.append({'WEB_SURFER_NO_TOOLS_PROMPT': WEB_SURFER_NO_TOOLS_PROMPT})
    #
    #     return prompt_list