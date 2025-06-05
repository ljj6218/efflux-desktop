from application.domain.tasks.task import Task, TaskType, TaskState
from application.domain.generators.tools import Tool
from application.domain.agent import Agent, AgentInstance
from application.domain.generators.tools import ToolType
from application.domain.events.event import Event, EventType, EventSubType
from application.port.inbound.task_handler import TaskHandler
from application.port.outbound.event_port import EventPort
from common.core.container.annotate import component
from application.port.outbound.agent_port import AgentPort
from application.port.outbound.tools_port import ToolsPort
from application.port.outbound.generators_port import GeneratorsPort
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from application.domain.generators.generator import LLMGenerator
from application.port.outbound.user_setting_port import UserSettingPort
from application.domain.generators.firm import GeneratorFirm
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

from common.utils.playwright import LocalPlaywrightBrowser

from common.core.logger import get_logger
import asyncio
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
        generators_port: GeneratorsPort,
            user_setting_port: UserSettingPort,
    ):
        self.agent_port = agent_port
        self.tools_port = tools_port
        self.event_port = event_port
        self.generators_port = generators_port
        self.user_setting_port = user_setting_port

    def execute(self, task: Task):
        print(f"agent task handler ->{task.data['agent_id']}")
        agent_id = task.data['agent_id']
        conversation_id = task.data['conversation_id']
        generator_id = task.data['generator_id']
        content = task.data['content']

        # 获取agent
        agent: Agent = self.agent_port.load(agent_id)
        # 获取agent所有配置的工具
        mcp_name_list = []
        tools_group_name_list = []
        for tools_group in agent.tools_group_list:
            if tools_group['type'] == ToolType.MCP.value:
                mcp_name_list.append(tools_group['group_name'])
            if tools_group['type'] == ToolType.LOCAL.value:
                tools_group_name_list.append(tools_group['group_name'])

        # 加在agent配置的所有工具
        tool_list: List[Tool] = []
        if agent.tools_group_list:
            for tools_group in agent.tools_group_list:
                tools = asyncio.run(self.tools_port.load_tools(group_name=tools_group['group_name'],
                                                               tool_type=ToolType[tools_group['type']]))
                tool_list.extend(tools)
        print(f"agent tool list -> {tool_list}")
        # 获取agent实例
        agent_instance: AgentInstance = agent.make_instance()
        agent_instance.tools = tool_list
        logger.info(f"agent instance -> {agent_instance.instance_id}")
        # 动态提示词 ====
        # 系统提示词
        # if prompt_key == "WEB_SURFER_TOOL_PROMPT":
        #     return WEB_SURFER_TOOL_PROMPT.format(
        #         tabs_information=kwargs["tabs_information"],
        #         last_outside_message=kwargs['last_outside_message'],
        #         webpage_text=kwargs['webpage_text'],
        #         url=kwargs['url'],
        #         visible_targets=kwargs['visible_targets'],
        #         consider_screenshot="Consider the following screenshot of a web browser,"
        #         # if self.is_multimodal
        #         # else "Consider the following webpage",
        #         # other_targets_str=other_targets_str,
        #         # focused_hint=focused_hint,
        #         # tool_names=tool_names,
        #     ).strip()

        # agent_instance.load_prompt(prompt_key="WEB_SURFER_SYSTEM_MESSAGE").format(
        #
        # ).strip()

        browser = LocalPlaywrightBrowser(headless=False)
        agent_instance.browser = browser
        agent_instance._last_outside_message = content
        # 初始化
        asyncio.run(agent_instance.lazy_init())
        # 确保页面可访问
        asyncio.run(agent_instance.check_page_accessible())

        messages = []

        system =  ChatStreamingChunk.from_system(message=agent_instance.system_prompt)
        messages.append(system)
        chunk: ChatStreamingChunk = asyncio.run(agent_instance.load_pagr_info())
        messages.append(chunk)


        use_tools = []
        for tool in tool_list:
            tool_name = "TOOL_" +  tool.name.upper()
            if tool_name in agent_instance.use_tools_name_list:
                use_tools.append(tool)

        generator = self._llm_generator(generator_id=generator_id)

        for chunk in self.generators_port.generate_event(llm_generator=generator, messages=messages, tools=use_tools, tool_choice="required"):
            print(chunk)
        # # 发送agent调用AI事件
        # event = Event.from_init(
        #     event_type=EventType.AGENT,
        #     event_sub_type=EventSubType.LLM_CALL,
        #     data={
        #         "id": create_uuid(),
        #         "conversation_id": conversation_id,
        #         "agent_id": agent_instance.instance_id,
        #         "generator_id": generator_id,
        #         "system": "",
        #         "mcp_name_list": mcp_name_list,
        #         "tools_group_name_list": tools_group_name_list,
        #     }
        # )
        # logger.info(f"任务处理器[{self.type()}]发起[{EventType.AGENT} - {EventSubType.LLM_CALL}]事件：[ID：{event.id}]")
        # return self.event_port.emit_event(event)


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

    def _llm_generator(self, generator_id: str) -> LLMGenerator:
        # 获取厂商api key
        llm_generator: LLMGenerator = self.generators_port.load_generate(generator_id)
        firm: GeneratorFirm = self.user_setting_port.load_firm_setting(llm_generator.firm)
        llm_generator.set_api_key_secret(firm.api_key)
        llm_generator.check_firm_api_key()
        return llm_generator