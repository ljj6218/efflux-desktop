from application.domain.tasks.task import Task, TaskType, TaskState
from application.domain.agent import Agent
from application.domain.generators.tools import ToolType
from application.domain.events.event import Event, EventType, EventSubType
from application.port.inbound.task_handler import TaskHandler
from application.port.outbound.event_port import EventPort
from common.core.container.annotate import component
from application.port.outbound.agent_port import AgentPort
from application.port.outbound.tools_port import ToolsPort
from common.utils.common_utils import create_uuid
from typing import List
import asyncio
from autogen_agentchat.utils import content_to_str, remove_images
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    LLMMessage,
    RequestUsage,
    SystemMessage,
    UserMessage,
)
from common.core.logger import get_logger
import injector
logger = get_logger(__name__)

@component
class AgentTaskHandler(TaskHandler):

    @injector.inject
    def __init__(
        self,
        agent_port: AgentPort,
        tools_port: ToolsPort,
        event_port: EventPort,
    ):
        self.agent_port = agent_port
        self.tools_port = tools_port
        self.event_port = event_port


    def execute(self, task: Task):
        print(f"agent task handler ->{task.data['agent_id']}")
        agent_id = task.data['agent_id']
        conversation_id = task.data['conversation_id']
        generator_id = task.data['generator_id']

        # 获取agent
        agent: Agent = self.agent_port.load(agent_id)
        mcp_name_list = []
        tools_group_name_list = []
        for tools_group in agent.tools_group_list:
            if tools_group['type'] == ToolType.MCP.value:
                mcp_name_list.append(tools_group['group_name'])
            if tools_group['type'] == ToolType.LOCAL.value:
                tools_group_name_list.append(tools_group['group_name'])

        # 动态提示词
        event = Event.from_init(
            event_type=EventType.AGENT,
            event_sub_type=EventSubType.LLM_CALL,
            data={
                "id": create_uuid(),
                "conversation_id": conversation_id,
                "agent_id": agent_id,
                "generator_id": generator_id,
                "system": "",
                "mcp_name_list": mcp_name_list,
                "tools_group_name_list": tools_group_name_list,
            }
        )
        logger.info(f"任务处理器[{self.type()}]发起[{EventType.AGENT} - {EventSubType.LLM_CALL}]事件：[ID：{event.id}]")
        return self.event_port.emit_event(event)

        # # 加在agent配置的所有工具
        # tool_list: List[Tool] = []
        # if agent.tools_group_list:
        #     for tools_group in agent.tools_group_list:
        #         tools = asyncio.run(self.tools_port.load_tools(group_name=tools_group['group_name'], tool_type=ToolType[tools_group['type']]))
        #         tool_list.extend(tools)
        # print(f"agent tool list -> {tool_list}")
        # task 中包含上下文唯一键，获取上下文（planning情况）

        # 获取当前agent上下文

        # 执行agent

        # 阶段投递llm返回的json事件

    def state(self) -> TaskState:
        pass

    def set_state(self, state: TaskState):
        pass

    def check_stop_flag(self) -> bool:
        pass



    def type(self) -> str:
        return TaskType.AGENT_CALL.value