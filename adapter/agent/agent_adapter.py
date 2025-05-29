from application.domain.agent import Agent
from application.port.outbound.agent_port import AgentPort
from common.core.container.annotate import component
from common.utils.json_file_util import JSONFileUtil
from typing import Optional

@component
class AgentAdapter(AgentPort):

    agent_file_url = "adapter/agent/agent.json"

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
                return Agent.model_validate(agent_dict)
        return None