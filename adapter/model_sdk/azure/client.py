import os
import traceback
from typing import Iterable, Optional, List, Generator

from openai import AzureOpenAI
from adapter.model_sdk.client import ModelClient
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from application.domain.generators.tools import Tool
from common.utils.auth import Secret
from common.utils.common_utils import create_uuid
from common.utils.time_utils import create_from_second_now_to_int

from common.core.logger import get_logger

logger = get_logger(__name__)


class AzureClient(ModelClient):
    def __init__(self):
        self.client = None
        self.deployment = None

    def _init_azure(self, api_secret: Secret, model_id: str = None):
        try:
            endpoint = api_secret.get('endpoint')
            subscription_key = api_secret.get('subscription_key')
            api_version = api_secret.get('api_version')
            self.deployment = model_id

            self.client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=endpoint,
                api_key=subscription_key,
            )
            logger.info(f"Initialized Azure OpenAI client for endpoint: {endpoint}")
            logger.info(f"Using deployment: {self.deployment}")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            raise

    def generate(
        self,
        model: str = None,
        message_list: Iterable[ChatStreamingChunk] = None,
        api_secret: Secret = None,
        base_url: str = None,
        tools: Optional[List[Tool]] = None,
        **generation_kwargs
    ) -> ChatStreamingChunk:
        pass

    def generate_stream(
        self,
        model: str = None,
        message_list: Iterable[ChatStreamingChunk] = None,
        api_secret: Secret = None,
        base_url: str = None,
        tools: Optional[List[Tool]] = None,
        **generation_kwargs
    ) -> Generator[ChatStreamingChunk, None, None]:
        logger.info("Starting stream generation with Azure OpenAI")
        self._init_azure(api_secret, model)

        messages = []
        for chunk in message_list:
            messages.append({
                "role": chunk.role,
                "content": chunk.content
            })

        try:
            response = self.client.chat.completions.create(
                stream=True,
                messages=messages,
                max_tokens=4096,
                temperature=1.0,
                top_p=1.0,
                model=self.deployment,
            )

            for update in response:
                if update.choices:
                    content = update.choices[0].delta.content or ""
                    finish_reason = update.choices[0].finish_reason or None
                    if content or finish_reason:
                        yield ChatStreamingChunk.from_assistant(
                            id=create_uuid(),
                            model=self.deployment,
                            created=create_from_second_now_to_int(),
                            finish_reason=finish_reason,
                            role="assistant",
                            content=content,
                            reasoning_content='',
                        )
        except Exception as e:
            logger.error(f"Unexpected error during stream generation: {e}")
            logger.error(traceback.format_exc())
            raise

    def generate_test(self, *args, **kwargs):
        logger.info("generate_test method is called")
        return None

    def model_list(self, *args, **kwargs):
        logger.info("model_list method is called")
        self._init_azure(args[0])
        model_obj_list = self.client.models.list().data
        return list(set([model_obj_i.id for model_obj_i in model_obj_list]))
