from application.domain.tasks.task import Task, TaskType
from application.domain.agent import Agent
from application.domain.generators.tools import Tool, ToolType
from application.port.inbound.task_handler import TaskHandler
from common.core.container.annotate import component
from application.port.outbound.agent_port import AgentPort
from application.port.outbound.tools_port import ToolsPort
from typing import List
import asyncio

from common.core.logger import get_logger
import injector
logger = get_logger(__name__)

@component
class AgentTaskHandler(TaskHandler):

    @injector.inject
    def __init__(
        self,
        agent_port: AgentPort,
        tools_port: ToolsPort
    ):
        self.agent_port = agent_port
        self.tools_port = tools_port


    def execute(self, task: Task):
        print(f"agent task handler ->{task.data['agent_id']}")
        agent_id = task.data['agent_id']
        # 获取agent
        agent: Agent = self.agent_port.load(agent_id)
        # 加在agent配置的所有工具
        tool_list: List[Tool] = []
        if agent.tools_group_list:
            for tools_group in agent.tools_group_list:
                tools = asyncio.run(self.tools_port.load_tools(group_name=tools_group['group_name'], tool_type=ToolType[tools_group['type']]))
                tool_list.extend(tools)
        print(f"agent tool list -> {tool_list}")
        # task 中包含上下文唯一键，获取上下文（planning情况）

        # 获取当前agent上下文

        # 执行agent

        # 阶段投递llm返回的json事件




    def type(self) -> str:
        return TaskType.AGENT_CALL.value