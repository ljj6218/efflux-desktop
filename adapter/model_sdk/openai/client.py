from typing import Optional, Dict, Any, Iterable, List, Generator
import os
from openai import OpenAI
from adapter.model_sdk.client import ModelClient
from common.utils.auth import Secret
from common.core.errors.system_exception import ThirdPartyServiceException, ThirdPartyServiceApiCode
from application.domain.generators.chat_chunk.chunk import ChatChunk, ChatStreamingChunk, CompletionUsage, ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from application.domain.generators.tools import Tool
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion import ChatCompletion
from common.core.logger import get_logger
logger = get_logger(__name__)

class OpenAIClient(ModelClient):

    def __init__(self):
        self.timeout = float(os.environ.get("OPENAI_TIMEOUT", 120.0)) # 接口超时时间
        self.max_retries = int(os.environ.get("OPENAI_MAX_RETRIES", 3)) # 接口最啊重试次数

    def generate(
            self,
            model: str = None,
            message_list: Iterable[ChatStreamingChunk] = None,
            api_secret: Secret = None,
            base_url: str = None,
            tools: Optional[Iterable[Tool]] = None,
            generation_kwargs: Optional[Dict[str, Any]] = None
    ) -> ChatStreamingChunk:
        # openAI client 构建
        client: OpenAI = self._get_client(api_key=api_secret.resolve_value(),
                                          api_base_url=base_url)
        # 转换为 openAI 接口风格的工具
        openai_tools: List[ChatCompletionToolParam] = self._convert_openai_tools(tools)
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=self._convert_openai_stream_chunk(message_list),
                tools=None if len(openai_tools) == 0 else openai_tools,
                tool_choice=None if len(openai_tools) == 0 else "auto",
            )
            return self._convert_chunk(stream)
        except Exception as exc:
            # 抛出三方调用异常
            raise ThirdPartyServiceException(error_code=ThirdPartyServiceApiCode.LLM_SERVICE_API_ERROR, dynamics_message=f"model:{model} - exception:{str(exc)}")


    @staticmethod
    def _convert_chunk(completion: ChatCompletion) -> ChatStreamingChunk:
        tool_calls: List[ChatCompletionMessageToolCall] = []
        if completion.choices[0].message.tool_calls:
            for openai_tool_call in completion.choices[0].message.tool_calls:
                tool_calls.append(
                    ChatCompletionMessageToolCall(id=openai_tool_call.id, name=openai_tool_call.function.name,
                                                  arguments=openai_tool_call.function.arguments))
        return ChatStreamingChunk(id=completion.id, model=completion.model, created=completion.created,
                         usage=CompletionUsage(prompt_tokens=completion.usage.prompt_tokens,
                                               completion_tokens=completion.usage.completion_tokens,
                                               total_tokens=completion.usage.total_tokens),
                         finish_reason=completion.choices[0].finish_reason,
                         content=completion.choices[0].message.content,
                         reasoning_content=None if not hasattr(completion.choices[0].message, "reasoning_content") else completion.choices[0].message.reasoning_content,
                         # reasoning_content=completion.choices[0].message.reasoning_content,
                         role=completion.choices[0].message.role, tool_calls=tool_calls)

    def generate_stream(
            self,
            model: str = None,
            message_list: Iterable[ChatStreamingChunk] = None,
            api_secret: Secret = None,
            base_url: str = None,
            tools: Optional[List[Tool]] = None,
            generation_kwargs: Optional[Dict[str, Any]] = None
    ) -> Generator[ChatStreamingChunk, None, None]:
        # openAI client 构建
        client: OpenAI = self._get_client(api_key=api_secret.resolve_value(),
                                          api_base_url=base_url)
        # 转换为 openAI 接口风格的工具
        openai_tools: List[ChatCompletionToolParam] = self._convert_openai_tools(tools)
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=self._convert_openai_stream_chunk(message_list),
                stream=True,
                tools=None if len(openai_tools) == 0 else openai_tools,
                tool_choice=None if len(openai_tools) == 0 else "auto",
            )
        except Exception as exc:
            # 抛出三方调用异常
            raise ThirdPartyServiceException(error_code=ThirdPartyServiceApiCode.LLM_SERVICE_API_ERROR, dynamics_message=f"model:{model} - exception:{str(exc)}")

        tool_calls: List[ChatCompletionMessageToolCall] = []
        current_role = ""
        for event in stream:
            logger.debug("=======")
            logger.debug(f"原始chunk返回：{event}")
            logger.debug("=======")
            if hasattr(event, "type") and event.type == 'ping': # claude sse ping 兼容
                logger.debug("LLM API SSE Pong")
            else:
                # 补充每个chunk的role
                if event.choices[0].delta.role:
                    current_role = event.choices[0].delta.role
                else:
                    event.choices[0].delta.role = current_role

                chunk: ChatStreamingChunk = self._convert_stream_chunk(event, tool_calls, tools)
                if chunk is not None:
                    yield chunk

    @staticmethod
    def _convert_openai_stream_chunk(chat_streaming_chunk_list: Iterable[ChatStreamingChunk]) -> List[ChatCompletionMessageParam]:
        """转换openai的chunk输入"""
        message_list: List[ChatCompletionMessageParam] = []
        for chat_streaming_chunk in chat_streaming_chunk_list:
            # 工具调用请求
            if chat_streaming_chunk.role == "assistant" and chat_streaming_chunk.finish_reason == "tool_calls":
                # 封装tool_calls集合
                tool_calls = []
                for tool_call in chat_streaming_chunk.tool_calls:
                    tool_calls.append(
                        {
                            "function": {
                                "arguments": tool_call.arguments,
                                "name": tool_call.name
                            },
                            "id": tool_call.id,
                            "type": "function"
                        }
                    )
                message_list.append({
                    "role": "assistant",
                    "tool_calls": tool_calls
                })
            # 工具调用结果
            elif chat_streaming_chunk.role == "tool":
                # 封装tool_calls结果集合
                message_list.append({
                    "role": "tool",
                    "tool_call_id": chat_streaming_chunk.tool_call_id,
                    # "content": [{
                    #     "type": "text",
                    #     "text": str(tool_call_result['result'])
                    # }]
                    "content": chat_streaming_chunk.content,
                })
            # 跳过用户确认信息
            elif chat_streaming_chunk.user_confirm and chat_streaming_chunk.user_confirm.id:
                continue
            # 一般消息
            else:
                message = {"role": chat_streaming_chunk.role, "content": chat_streaming_chunk.content}
                message_list.append(message)
        return message_list


    def _convert_stream_chunk(self, completion_chunk: ChatCompletionChunk, tool_calls: List[ChatCompletionMessageToolCall], tools: List[Tool]) -> Optional[ChatStreamingChunk]:
        """
        convert stream chunk to ChatStreamingChunk
        :param completion_chunk: openai api completion
        :param tool_calls: tools call list
        :param tools: efflux tools list
        :return:
        """
        usage: Optional[CompletionUsage] = None
        # usage append
        if completion_chunk.usage:
            usage = CompletionUsage(prompt_tokens=completion_chunk.usage.prompt_tokens,
                                    completion_tokens=completion_chunk.usage.completion_tokens,
                                    total_tokens=completion_chunk.usage.total_tokens)
        # 拼接tools_call的请求参数
        if completion_chunk.choices[0].delta.tool_calls:
            self._append_stream_tool_args(completion=completion_chunk, tool_calls=tool_calls, tools=tools)
            # 拼接完成
            if completion_chunk.choices[0].finish_reason == "function_calls":
                completion_chunk.role = "assistant"
                return self._make_stream_chunk(completion=completion_chunk, tool_calls=tool_calls, usage=usage)
        else:
            return self._make_stream_chunk(completion=completion_chunk, tool_calls=tool_calls, usage=usage)

    @staticmethod
    def _make_stream_chunk(completion: ChatCompletionChunk, tool_calls: List[ChatCompletionMessageToolCall], usage: CompletionUsage):
        return ChatStreamingChunk(id=completion.id, model=completion.model, created=completion.created,
                                  usage=usage,
                                  finish_reason=completion.choices[0].finish_reason,
                                  content=completion.choices[0].delta.content,
                                  reasoning_content=None if not hasattr(completion.choices[0].delta,
                                                                        "reasoning_content") else completion.choices[
                                      0].delta.reasoning_content,
                                  role=completion.choices[0].delta.role, tool_calls=tool_calls)

    def _append_stream_tool_args(self, completion: ChatCompletionChunk, tool_calls: List[ChatCompletionMessageToolCall], tools: List[Tool]):
        """
        Call parameters for the tool that concatenates stream returns
        :param completion: stream chunk
        :param tool_calls:
        :return:
        """
        for openai_tool_call in completion.choices[0].delta.tool_calls:
            # If there is an ID, it means starting a tool parameter stream return
            if openai_tool_call.id:
                # create a tools_call chunk
                current_tool = ChatCompletionMessageToolCall(id=openai_tool_call.id,
                                                             name=openai_tool_call.function.name,
                                                             arguments=openai_tool_call.function.arguments)
                self._match_mcp_server_name(chunk_tools_call=current_tool, tools=tools)
                tool_calls.append(current_tool)
            else:
                # If there is no ID, it means that the streaming parameter is being returned
                if openai_tool_call.function.arguments:
                    tool_calls[openai_tool_call.index].arguments += openai_tool_call.function.arguments

    @staticmethod
    def _match_mcp_server_name(chunk_tools_call: ChatCompletionMessageToolCall, tools: Iterable[Tool]) -> None:
        """
        match mcp.server name
        :param chunk_tools_call: the call tools
        :param tools: mcp server tools
        :return:
        """
        for tool in tools:
            if chunk_tools_call.name == tool.name:
                chunk_tools_call.mcp_server_name = tool.server_name

    @staticmethod
    def _convert_openai_tools(tools: Iterable[Tool]) -> List[ChatCompletionToolParam]:
        """
        convert openai param tools into a list of efflux tools
        :param tools:
        :return:
        """
        openai_tools: List[ChatCompletionToolParam] = []
        for tool in tools:
            openai_tools.append(
                {
                    "type": "function",
                    "function": {"name": tool.name, "description": tool.description, "parameters": tool.inputSchema}
                }
            )
        return openai_tools

    def _get_client(
            self,
            api_key: str,
            api_base_url: str,
            organization: str = None,
            timeout: float = None,
            max_retries: int = None
    ) -> OpenAI:
        """
        get an OpenAI API client
        :param api_key: api key
        :param api_base_url: api base url
        :param organization: organization
        :param timeout: timeout
        :param max_retries: max retries
        :return:
        """
        if timeout is not None:
            self.timeout = timeout
        if max_retries is not None:
            self.max_retries = max_retries

        return OpenAI(
                api_key=api_key,
                organization=organization,
                base_url=api_base_url,
                timeout=self.timeout,
                max_retries=self.max_retries
            )