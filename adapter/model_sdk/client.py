from abc import ABC, abstractmethod

from openai.types.chat import ChatCompletionMessageParam

from application.domain.generators.generator import LLMGenerator
from common.utils.auth import Secret
from typing import Any, Dict, Iterable, Optional, List, Generator
from application.domain.generators.tools import Tool
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk


class ModelClient(ABC):

    @abstractmethod
    def generate(self,
                model: str = None,
                message_list: Iterable[ChatStreamingChunk] = None,
                api_secret: Secret = None,
                base_url: str = None,
                tools: Optional[List[Tool]] = None,
                **generation_kwargs,
                ) -> ChatStreamingChunk:
        pass

    @abstractmethod
    def generate_stream(self,
                model: str = None,
                message_list: Iterable[ChatStreamingChunk] = None,
                api_secret: Secret = None,
                base_url: str = None,
                tools: Optional[List[Tool]] = None,
                **generation_kwargs,
                ) -> Generator[ChatStreamingChunk, None, None]:
        pass

    @abstractmethod
    def generate_test(self,
                model: str = None,
                message_list: Iterable[ChatStreamingChunk] = None,
                api_secret: Secret = None,
                base_url: str = None,
                tools: Optional[List[Tool]] = None,
                **generation_kwargs,
                ):
        pass

    @abstractmethod
    def model_list(
                self,
                api_key: str = None,
                base_url: str = None) -> List[LLMGenerator]:
        pass