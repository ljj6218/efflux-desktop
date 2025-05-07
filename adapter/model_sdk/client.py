from abc import ABC, abstractmethod
from common.utils.auth import Secret
from typing import Any, Dict, Iterable, Optional, List, Generator
from application.domain.generators.tools import Tool
from application.domain.generators.chat_chunk.chunk import ChatChunk, ChatStreamingChunk
from application.domain.generators.chat_completion.chat_completion_message_param import ChatCompletionMessageParam


class ModelClient(ABC):

    @abstractmethod
    def generate(self,
                model: str = None,
                messages: Iterable[ChatCompletionMessageParam] = None,
                api_secret: Secret = None,
                base_url: str = None,
                generation_kwargs: Optional[Dict[str, Any]] = None,
                # *,
                tools: Optional[List[Tool]] = None,
                ) -> ChatChunk:
        pass

    @abstractmethod
    def generate_stream(self,
                model: str = None,
                messages: Iterable[ChatCompletionMessageParam] = None,
                api_secret: Secret = None,
                base_url: str = None,
                tools: Optional[List[Tool]] = None,
                generation_kwargs: Optional[Dict[str, Any]] = None,

                ) -> Generator[ChatStreamingChunk, None, None]:
        pass
