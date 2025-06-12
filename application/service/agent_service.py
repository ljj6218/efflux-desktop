from application.domain.agents.agent import Agent
from application.port.inbound.agent_case import AgentCase
from application.port.outbound.agent_port import AgentPort
from common.core.container.annotate import component
from common.utils.common_utils import create_uuid
from application.port.outbound.tools_port import ToolsPort
from typing import Optional, Dict, Any, List
import injector

@component
class AgentService(AgentCase):

    @injector.inject
    def __init__(
        self,
        agent_port: AgentPort,
        tools_port: ToolsPort,
    ):
        self.agent_port = agent_port
        self.tools_port = tools_port

    async def save(self, agent_dict: Dict[str, Any]) -> str:
        if 'id' not in agent_dict:
            agent_dict['id'] = create_uuid()
        # tool_list: List[Tool] = []
        # if 'tools_group' in agent_dict:
        #     for tools_group in agent_dict.pop('tools_group'):
        #         tools = await self.tools_port.load_tools(group_name=tools_group['name'], tool_type=ToolType[tools_group['type']])
        #         tool_list.extend(tools)
        # # agent: Optional[Agent] = None
        # if 'id' in agent_dict and agent_dict['id']:
        #     agent = Agent(id=agent_dict['id'], name=agent_dict['name'], description=agent_dict['description'],tools=tool_list)
        # else:
        #     agent = Agent.from_init(name=agent_dict['name'], description=agent_dict['description'],tools=tool_list)
        return self.agent_port.save(Agent.model_validate(agent_dict))

    async def load(self, agent_id: str) -> Optional[Agent]:
        return self.agent_port.load(agent_id)

    async def load_all(self) -> List[Agent]:
        return self.agent_port.load_all()

    async def load_by_name(self, agent_name: str) -> Optional[Agent]:
        return self.agent_port.load_by_name(agent_name)