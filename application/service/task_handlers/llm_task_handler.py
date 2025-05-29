from application.domain.tasks.task import TaskType, Task
from application.domain.events.event import Event, EventType, EventGroupStatus, EventSubType, EventGroup
from application.port.inbound.task_handler import TaskHandler
from common.core.container.annotate import component
from common.utils.common_utils import create_uuid
from application.port.outbound.event_port import EventPort
from application.domain.generators.firm import GeneratorFirm
from application.port.outbound.user_setting_port import UserSettingPort
from application.port.outbound.generators_port import GeneratorsPort
from application.port.outbound.tools_port import ToolsPort
from application.port.outbound.mcp_server_port import MCPServerPort
from application.domain.generators.generator import LLMGenerator
from application.domain.generators.tools import Tool, ToolInstance, ToolType
from application.port.outbound.conversation_port import ConversationPort
from common.core.errors.business_exception import BusinessException
from common.core.errors.business_error_code import GeneratorErrorCode
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk, ChatCompletionMessageToolCall
from common.core.errors.common_exception import CommonException, handle_exception
from common.utils.markdown_util import read
from typing import List, Dict, Any, Optional
import asyncio
import injector
import json

from common.core.logger import get_logger

logger = get_logger(__name__)

@component
class LLMTaskHandler(TaskHandler):
    """
    默认chat模型调用
    """
    @injector.inject
    def __init__(
        self,
        user_setting_port: UserSettingPort,
        generators_port: GeneratorsPort,
        tools_port: ToolsPort,
        mcp_server_port: MCPServerPort,
        conversation_port: ConversationPort
    ):
        self.user_setting_port = user_setting_port
        self.generators_port = generators_port
        self.tools_port = tools_port
        self.mcp_server_port = mcp_server_port
        self.conversation_port = conversation_port

    # 动态计算 default 值的函数，接收异常对象
    @staticmethod
    def _calculate_default_value(exception: CommonException):
        event = Event.from_init(
            event_type=EventType.SYSTEM,
            event_sub_type=EventSubType.ERROR,
            data={
                'code': "1",
                'message': f"{TaskType.LLM_CALL} 异常：{str(exception)}",
            }
        )
        EventPort.get_event_port().emit_event(event)

    @handle_exception(default_func=_calculate_default_value)
    def execute(self, task: Task):
        tools_call_result = True if 'tools_call_result' in task.data.keys() else False
        task_data: Dict[str, Any]  = task.data
        conversation_id = task_data['conversation_id']
        uuid = create_uuid()
        generator_id = task_data['generator_id']
        mcp_name_list = task_data['mcp_name_list']
        tools_group_name_list = task_data['tools_group_name_list']
        system = task_data['system'] if 'system' in task_data.keys() else None


        # 获取LLMGenerator
        llm_generator: LLMGenerator = self._llm_generator(generator_id)
        # 工具装载
        tools: List[Tool] = []
        for mcp_name in mcp_name_list:
            tools.extend(asyncio.run(self.tools_port.load_tools(group_name=mcp_name, tool_type=ToolType.MCP)))


        # 查询会话历史
        history_conversation = self.conversation_port.conversation_load(conversation_id=conversation_id)
        if not history_conversation:
            raise BusinessException(error_code=GeneratorErrorCode.NO_CONVERSATION_FOUND, dynamics_message=conversation_id)

        # message 封装
        messages: List[ChatStreamingChunk] = []
        # 拼装系统提示词
        if system:
            messages.append(ChatStreamingChunk.from_system(system))
        # 拼装对话上下文
        history_message_list = history_conversation.convert_sort_memory()
        messages.extend(history_message_list)
        # 拼装工具调用历史
        if tools_call_result:
            for history_message in history_message_list:
                # print(f"conversation_id = {conversation_id}, history_message_id = {history_message.id}")
                tool_instance_list = self.tools_port.load_instance(conversation_id=conversation_id, dialog_segment_id=history_message.id)
                if tool_instance_list:
                    # print(f"工具调用历史message：{tool_instance_list}")
                    messages.extend(self._tool_calls_history(tool_instance_list))

        # 生成组事件id
        group_event_id = create_uuid()

        # 记录是否已经发送了STARTED状态的事件
        started_event_sent = False

        for chunk in self.generators_port.generate_event(llm_generator=llm_generator, messages=messages, tools=tools):
            # 确定当前事件的组状态
            group_status = EventGroupStatus.SENDING
            if not started_event_sent:
                group_status = EventGroupStatus.STARTED
                started_event_sent = True
            elif chunk.finish_reason == 'stop':
                group_status = EventGroupStatus.ENDED

            # 工具调用
            if chunk.finish_reason == 'tool_calls':
                event = chunk.to_tool_calls_message_event(
                    id=uuid,
                    conversation_id=conversation_id,
                    generator_id=generator_id,
                    mcp_name_list=mcp_name_list,
                    tools_group_name_list=tools_group_name_list,
                    event_group=EventGroup(id=group_event_id, status=EventGroupStatus.ENDED),
                )
                logger.info(f"任务处理器[{self.type()}]发起[{event.type} - {event.sub_type}]事件：[ID：{event.id}]")
                EventPort.get_event_port().emit_event(event)
                continue

            event = chunk.to_assistant_message_event(
                id=uuid,
                conversation_id=conversation_id,
                generator_id=generator_id,
                mcp_name_list=mcp_name_list,
                tools_group_name_list=tools_group_name_list,
                event_group=EventGroup(id=group_event_id, status=group_status),
            )
            # logger.info(f"任务处理器[{self.type()}]发起[{event.type} - {event.sub_type}]事件：[ID：{event.id}]")
            EventPort.get_event_port().emit_event(event)

    def type(self) -> str:
        return TaskType.LLM_CALL.value

    def _llm_generator(self, generator_id: str) -> LLMGenerator:
        # 获取厂商api key
        llm_generator: LLMGenerator = self.generators_port.load_generate(generator_id)
        firm: GeneratorFirm = self.user_setting_port.load_firm_setting(llm_generator.firm)
        llm_generator.set_api_key_secret(firm.api_key)
        llm_generator.check_firm_api_key()
        return llm_generator

    @staticmethod
    def _tool_calls_history(tool_instance_list: List[ToolInstance]) -> List[ChatStreamingChunk]:
        chunk_list: List[ChatStreamingChunk] = []
        chunk_call_list: List[ChatCompletionMessageToolCall] = []
        # 拼装方法调用请求
        for tool_instance in tool_instance_list:
            chunk_call_list.append(ChatCompletionMessageToolCall(
                id=tool_instance.tool_call_id, mcp_server_name=tool_instance.mcp_server_name, name=tool_instance.name,
                description=tool_instance.description, arguments=json.dumps(tool_instance.arguments)))
        chunk_list.append(ChatStreamingChunk.from_tool_calls(tool_calls=chunk_call_list))

        for tool_instance in tool_instance_list:
            # 拼装方法调用结果
            chunk_list.append(
                ChatStreamingChunk.from_tool_calls_result(content=str(tool_instance.result), tool_call_id=tool_instance.tool_call_id))
        return chunk_list