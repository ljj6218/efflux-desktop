from common.core.container.annotate import component
from application.port.outbound.generators_port import GeneratorsPort
from application.port.outbound.cache_port import CachePort
from application.port.outbound.tools_port import ToolsPort
from application.port.outbound.user_setting_port import UserSettingPort
from application.port.outbound.mcp_server_port import MCPServerPort
from application.domain.generators.agent import AgentGenerator
from application.domain.generators.generator import LLMGenerator
from application.domain.generators.tools import Tool
from application.domain.generators.firm import GeneratorFirm
from application.port.inbound.agent_generators_case import AgentGeneratorsCase
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from common.core.errors.business_exception import BusinessException
from common.core.errors.business_error_code import GeneratorErrorCode
from common.core.errors.common_exception import CommonException, handle_async_exception
from application.port.outbound.conversation_port import ConversationPort
from application.domain.conversation import Conversation, DialogSegment
from common.utils.auth import ApiKeySecret
from typing import List, AsyncGenerator, Optional, Dict, Any
import asyncio
from common.utils.file_util import open_and_base64, extract_pdf_text, extract_table_like_text
import injector
from common.core.logger import get_logger
logger = get_logger(__name__)

@component
class DefaultAgentService(AgentGeneratorsCase):

    CACHE_NAME = "tool_calls_cache"

    @injector.inject
    def __init__(self,
                 generators_port: GeneratorsPort,
                 tools_port: ToolsPort,
                 conversation_port: ConversationPort,
                 user_setting_port: UserSettingPort,
                 mcp_server_port: MCPServerPort,
                 cache_port: CachePort
                 ):
        self.generators_port = generators_port
        self.conversation_port = conversation_port
        self.mcp_server_port = mcp_server_port
        self.tools_port = tools_port
        self.user_setting_port = user_setting_port
        self.cache_port = cache_port

    def _llm_generator(self, generator_id: str) -> LLMGenerator:
        # 获取厂商api key
        llm_generator: LLMGenerator = self.generators_port.load_generate(generator_id)
        firm: GeneratorFirm = self.user_setting_port.load_firm_setting(llm_generator.firm)
        llm_generator.set_api_key_secret(firm.api_key)
        llm_generator.check_firm_api_key()
        return llm_generator

    async def generate(
            self,
            generator_id: str,
            system: str,
            query: str,
            conversation_id: str,
            mcp_name_list: List[str],
            user_confirm: Optional[Dict[str, Any]] = None,
    ) -> ChatStreamingChunk:
        # 获取LLMGenerator
        llm_generator: LLMGenerator = self._llm_generator(generator_id)
        # 初始化agent
        agent: AgentGenerator = AgentGenerator(
            generator_port=self.generators_port,
            tools_port=self.tools_port,
            mcp_server_port=self.mcp_server_port,
            llm_generator=llm_generator
        )
        # 工具装载
        tools: List[Tool] = []
        for mcp_name in mcp_name_list:
            tools.extend(await self.tools_port.load_tools(mcp_name))
        # await asyncio.sleep(10)
        if tools:
            agent.add_tool(tools)
        #
        # file_name = "2502.01142v1.pdf"
        #
        # # file_base64 = open_and_base64(f"uploads/{file_name}")
        #
        # text = extract_table_like_text(f"uploads/{file_name}")
        #
        # print(text)
        # query_message = {"role": "user", "content": query}

        # --短时记忆装载
        conversation = Conversation()
        conversation.init()
        # 判断是否是历史会话
        if conversation_id:
            history_conversation = await self.conversation_port.conversation_load(conversation_id=conversation_id)
            if history_conversation:
                conversation = history_conversation
                # 加入短时记忆
                agent.set_short_memory(conversation.convert_sort_memory())
                # 删除会话对话记录最后的工具调用对话片段
                last_dialog_segment: DialogSegment = conversation.dialog_segment_list.pop()
                if last_dialog_segment.finish_reason == "tool_calls":
                    await self.conversation_port.dialog_segment_remove(last_dialog_segment)
            else:
                raise BusinessException(error_code=GeneratorErrorCode.NO_CONVERSATION_FOUND,
                                        dynamics_message=conversation_id)
        else:
            # 初始化会话
            await self._init_conversation(conversation=conversation, query=query)

        query_chat_chunk: ChatStreamingChunk
        if user_confirm:
            # 用户确认调用拒绝
            if not user_confirm['user_confirmation_result']:
                # 删除用户确认请求缓存
                self.cache_port.delete_from_cache(name=self.CACHE_NAME, key=f"{conversation.id}-user_confirm")
                # 删除工具调用请求缓存
                self.cache_port.delete_from_cache(name=self.CACHE_NAME, key=f"{conversation.id}-tool_call")
                return
            user_confirm_cache: DialogSegment = self.cache_port.get_from_cache(name=self.CACHE_NAME,
                                                                               key=f"{conversation.id}-user_confirm")
            if not user_confirm_cache:
                raise BusinessException(error_code=GeneratorErrorCode.TOOL_AUTH_NOT_MATCH,
                                        dynamics_message=f"user_confirm_cache not found")
            if not user_confirm_cache.user_confirm.id == user_confirm['id']:
                raise BusinessException(error_code=GeneratorErrorCode.TOOL_AUTH_NOT_MATCH,
                                        dynamics_message=f"{user_confirm_cache.user_confirm.id} and {user_confirm['id']}")
            # 删除用户确认请求缓存
            self.cache_port.delete_from_cache(name=self.CACHE_NAME, key=f"{conversation.id}-user_confirm")
            # 获取缓存的工具调用请求片段
            agent.add_short_memory(
                self.cache_port.pop_from_cache(name=self.CACHE_NAME, key=f"{conversation.id}-tool_call"))
            # 用户确认消息不需要保存
            query_chat_chunk = ChatStreamingChunk.from_user_confirm_result(confirm_id=user_confirm['id'],
                                                                           user_confirmation_result=user_confirm[
                                                                               'user_confirmation_result'])
        else:
            # 删除用户确认请求缓存
            self.cache_port.delete_from_cache(name=self.CACHE_NAME, key=f"{conversation.id}-user_confirm")
            # 删除工具调用请求缓存
            self.cache_port.delete_from_cache(name=self.CACHE_NAME, key=f"{conversation.id}-tool_call")
            # 保存用户输入
            user_dialog_segment = DialogSegment(conversation_id=conversation.id)
            user_dialog_segment.make_user_message(content=query)
            await self.conversation_port.conversation_add(dialog_segment=user_dialog_segment)
            query_chat_chunk = ChatStreamingChunk.from_user(query)

        if system:
            agent.set_system(system)
        # 记录AI返回结果拼接
        collected_reasoning_content, collected_content, is_finish, created = [], [], False, 0
        return await agent.run(query_chat_chunk)

    # 动态计算 default 值的函数，接收异常对象
    @staticmethod
    async def _calculate_default_value(exception: CommonException)-> AsyncGenerator[ChatStreamingChunk, None]:
        yield ChatStreamingChunk.from_exception(exception=exception).model_dump_json()

    @handle_async_exception(default_func=_calculate_default_value)
    async def generate_stream(
            self,
            generator_id: str,
            system: str,
            query: str,
            conversation_id: str,
            mcp_name_list: List[str],
            user_confirm: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[ChatStreamingChunk, None]:
        # 获取LLMGenerator
        llm_generator: LLMGenerator = self._llm_generator(generator_id)
        # 初始化agent
        agent: AgentGenerator = AgentGenerator(
            generator_port=self.generators_port,
            tools_port=self.tools_port,
            mcp_server_port=self.mcp_server_port,
            llm_generator=llm_generator
        )
        # 工具装载
        tools: List[Tool] = []
        for mcp_name in mcp_name_list:
            tools.extend(await self.tools_port.load_tools(mcp_name))
        # await asyncio.sleep(10)
        if tools:
            agent.add_tool(tools)
        #
        # file_name = "2502.01142v1.pdf"
        #
        # # file_base64 = open_and_base64(f"uploads/{file_name}")
        #
        # text = extract_table_like_text(f"uploads/{file_name}")
        #
        # print(text)
        # query_message = {"role": "user", "content": query}



        # --短时记忆装载
        conversation = Conversation()
        conversation.init()
        # 判断是否是历史会话
        if conversation_id:
            history_conversation = await self.conversation_port.conversation_load(conversation_id=conversation_id)
            if history_conversation:
                conversation = history_conversation
                # 加入短时记忆
                agent.set_short_memory(conversation.convert_sort_memory())
                # 删除会话对话记录最后的工具调用对话片段
                last_dialog_segment: DialogSegment = conversation.dialog_segment_list.pop()
                if last_dialog_segment.finish_reason == "tool_calls":
                    await self.conversation_port.dialog_segment_remove(last_dialog_segment)
            else:
                raise BusinessException(error_code=GeneratorErrorCode.NO_CONVERSATION_FOUND, dynamics_message=conversation_id)
        else:
            # 初始化会话
            await self._init_conversation(conversation=conversation, query=query)

        query_chat_chunk: ChatStreamingChunk
        if user_confirm:
            # 用户确认调用拒绝
            if not user_confirm['user_confirmation_result']:
                # 删除用户确认请求缓存
                self.cache_port.delete_from_cache(name=self.CACHE_NAME, key=f"{conversation.id}-user_confirm")
                # 删除工具调用请求缓存
                self.cache_port.delete_from_cache(name=self.CACHE_NAME, key=f"{conversation.id}-tool_call")
                return
            user_confirm_cache: DialogSegment = self.cache_port.get_from_cache(name=self.CACHE_NAME, key=f"{conversation.id}-user_confirm")
            if not user_confirm_cache:
                raise BusinessException(error_code=GeneratorErrorCode.TOOL_AUTH_NOT_MATCH,
                                        dynamics_message=f"user_confirm_cache not found")
            if not user_confirm_cache.user_confirm.id == user_confirm['id']:
                raise BusinessException(error_code=GeneratorErrorCode.TOOL_AUTH_NOT_MATCH, dynamics_message=f"{user_confirm_cache.user_confirm.id} and {user_confirm['id']}")
            # 删除用户确认请求缓存
            self.cache_port.delete_from_cache(name=self.CACHE_NAME, key=f"{conversation.id}-user_confirm")
            # 获取缓存的工具调用请求片段
            agent.add_short_memory(self.cache_port.pop_from_cache(name=self.CACHE_NAME, key=f"{conversation.id}-tool_call"))
            # 用户确认消息不需要保存
            query_chat_chunk = ChatStreamingChunk.from_user_confirm_result(confirm_id=user_confirm['id'],
                                                                           user_confirmation_result=user_confirm['user_confirmation_result'])
        else:
            # 删除用户确认请求缓存
            self.cache_port.delete_from_cache(name=self.CACHE_NAME, key=f"{conversation.id}-user_confirm")
            # 删除工具调用请求缓存
            self.cache_port.delete_from_cache(name=self.CACHE_NAME, key=f"{conversation.id}-tool_call")
            # 保存用户输入
            user_dialog_segment = DialogSegment(conversation_id=conversation.id)
            user_dialog_segment.make_user_message(content=query)
            await self.conversation_port.conversation_add(dialog_segment=user_dialog_segment)
            query_chat_chunk = ChatStreamingChunk.from_user(query)

        if system:
            agent.set_system(system)
        # 记录AI返回结果拼接
        collected_reasoning_content, collected_content, is_finish, created= [], [], False, 0
        async for chunk in agent.run_stream(query_chat_chunk):
            # 返回统一设置会话id
            chunk.conversation_id = conversation.id
            if chunk.finish_reason == 'tool_calls':
                logger.info(f"tools 请求调用：{chunk}")
                assistant_tool_calls_dialog_segment = DialogSegment(conversation_id=conversation.id)
                assistant_tool_calls_dialog_segment.make_tool_calls(model=llm_generator.model, timestamp=chunk.created, tool_calls=chunk.tool_calls)
                self.cache_port.set_data(name=self.CACHE_NAME, key=f"{conversation.id}-tool_call", value=assistant_tool_calls_dialog_segment)
            if chunk.role == 'assistant' and chunk.finish_reason == 'user_confirm':
                logger.info(f"用户确认请求：{chunk}")
                user_confirm_dialog_segment = DialogSegment(conversation_id=conversation.id)
                user_confirm_dialog_segment.make_user_confirm(user_confirm_id=chunk.user_confirm.id, confirm_type=chunk.user_confirm.type, message=chunk.user_confirm.message)
                self.cache_port.set_data(name=self.CACHE_NAME, key=f"{conversation.id}-user_confirm", value=user_confirm_dialog_segment)
            if chunk.content:
                collected_content.append(chunk.content)
            if chunk.reasoning_content:
                collected_reasoning_content.append(chunk.reasoning_content)
            if chunk.finish_reason == "stop":
                created = chunk.created
                is_finish = True
            yield chunk.model_dump_json()
            # AI返回结束记录AI返回
            if is_finish:
                assistant_dialog_segment = DialogSegment(conversation_id=conversation.id)
                assistant_dialog_segment.make_assistant_message(content="".join(collected_content),
                                                                reasoning_content= None if len(collected_reasoning_content)==0 else "".join(collected_reasoning_content),
                                                                model=llm_generator.model, timestamp=created)
                await self.conversation_port.conversation_add(dialog_segment=assistant_dialog_segment)


    async def _init_conversation(self, conversation: Conversation, query: str) -> Conversation:
        conversation.theme = query
        return await self.conversation_port.conversation_save(conversation=conversation)
        # TODO 异步总结会话主题

