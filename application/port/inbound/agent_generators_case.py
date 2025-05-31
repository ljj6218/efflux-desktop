# from abc import ABC, abstractmethod
# from typing import AsyncGenerator, List, Dict, Any, Optional
# from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
#
# class AgentGeneratorsCase(ABC):
#
#     @abstractmethod
#     async def generate(
#             self,
#             generator_id: str,
#             system: str,
#             query: str,
#             conversation_id: str,
#             mcp_name_list: List[str],
#             user_confirm: Optional[Dict[str, Any]] = None,
#     ) -> ChatStreamingChunk:
#         """
#         默认agent生成
#         :param user_confirm: 用户确认块
#         :param generator_id: 模型id
#         :param system: 系统提示词
#         :param query: 当前问题
#         :param conversation_id: 会话id
#         :param mcp_name_list: mcp server 名字集合
#         :return: 流式chunk
#         """
#         pass
#
#     @abstractmethod
#     async def generate_stream(
#             self,
#             generator_id: str,
#             system: str,
#             query: str,
#             conversation_id: str,
#             mcp_name_list: List[str],
#             user_confirm: Optional[Dict[str, Any]] = None,
#     ) -> AsyncGenerator[ChatStreamingChunk, None]:
#         """
#         默认agent生成（流式）
#         :param user_confirm: 用户确认块
#         :param generator_id: 模型id
#         :param system: 系统提示词
#         :param query: 当前问题
#         :param conversation_id: 会话id
#         :param mcp_name_list: mcp server 名字集合
#         :return: 流式chunk
#         """
#         pass