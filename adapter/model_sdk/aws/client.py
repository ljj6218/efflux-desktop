import base64
import boto3
import json
import os
import re
import traceback
from typing import Iterable, Optional, List, Generator, Iterator

from adapter.model_sdk.client import ModelClient
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk, ChatCompletionContentPartParam, \
    ChatCompletionMessageToolCall
from application.domain.generators.tools import Tool
from common.utils.auth import Secret
from common.utils.common_utils import create_uuid
from common.utils.time_utils import create_from_timestamp_to_int, create_from_second_now_to_int

from common.core.logger import get_logger

logger = get_logger(__name__)


class AmazonClient(ModelClient):
    def __init__(self):
        self.bedrock_runtime = None
        self.model_id = None

    def _init_env(self, api_secret: Secret):
        # 临时设置环境变量
        aws_access_key_id = api_secret.get('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = api_secret.get('AWS_SECRET_ACCESS_KEY')
        if aws_access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key_id
        if aws_secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_access_key


    def _init_bedrock(self, api_secret: Secret, model_id: str):
        try:
            self._init_env(api_secret)
            region_name = api_secret.get('AWS_REGION')
            self.model_id = model_id
            self.bedrock_runtime = boto3.client(
                service_name='bedrock-runtime',
                region_name=region_name
            )
            logger.info(f"Initialized Bedrock client for region: {region_name}")
            logger.info(f"Using model: {self.model_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise

    def generate(
        self,
        model: str = None,
        message_list: Iterable[ChatStreamingChunk] = None,
        api_secret: Secret = None,
        base_url: str = None,
        tools: Optional[List[Tool]] = None,
        **generation_kwargs) -> ChatStreamingChunk:
        pass

    def generate_stream(
        self,
        model: str = None,
        message_list: Iterable[ChatStreamingChunk] = None,
        api_secret: Secret = None,
        base_url: str = None,
        tools: Optional[List[Tool]] = None,
        **generation_kwargs) -> Generator[ChatStreamingChunk, None, None]:
        self._init_bedrock(api_secret, model)

        system_instruction = ""
        user_messages = []
        for chunk in message_list:
            if chunk.role == "system":
                system_instruction += chunk.content
            elif chunk.role == "user":
                user_messages.append(chunk.content)

        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0.1,
                "messages": [
                    {
                        "role": "user",
                        "content": "\n".join([system_instruction] + user_messages)
                    }
                ]
            }
            response = self.bedrock_runtime.invoke_model_with_response_stream(
                body=json.dumps(body),
                modelId=self.model_id,
                accept='application/json',
                contentType='application/json'
            )

            for event in response.get('body'):
                chunk = event.get('chunk')
                if not chunk:
                    break
                # 解析每个数据块
                chunk_data = json.loads(chunk.get('bytes').decode())
                # 检查是否是文本增量
                chunk_finish_reason = None
                if chunk_data.get('type') == 'content_block_delta':
                    delta = chunk_data.get('delta', {})
                    if delta.get('type') == 'text_delta':
                        text = delta.get('text', '')
                        if text:
                            yield ChatStreamingChunk.from_assistant(
                                id=create_uuid(),
                                model=self.model_id,
                                created=create_from_second_now_to_int(),
                                finish_reason=chunk_finish_reason,
                                role="assistant",
                                content=text,
                                reasoning_content='',
                            )

                # 检查是否是流结束
                elif chunk_data.get('type') == 'message_stop':
                    chunk_finish_reason = "stop"
                    yield ChatStreamingChunk.from_assistant(
                        id=create_uuid(),
                        model=self.model_id,
                        created=create_from_second_now_to_int(),
                        finish_reason=chunk_finish_reason,
                        role="assistant",
                        content='',
                        reasoning_content='',
                    )
                    break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.error(traceback.format_exc())

    # 实现 generate_test 方法
    def generate_test(self, *args, **kwargs):
        # 这里可以添加具体的测试逻辑
        logger.info("generate_test method is called")
        return None

    # 实现 model_list 方法
    def model_list(self, *args, **kwargs):
        # 这里可以添加获取模型列表的逻辑
        try:
            self._init_env(args[0])
            bedrock_client = boto3.client(
                service_name="bedrock",
                region_name=args[0].get('AWS_REGION'))
            response = bedrock_client.list_foundation_models()
            models = response["modelSummaries"]
            return list(set([i.get('modelName') for i in models]))
        except Exception as e:
            logger.error(f"Failed to get model list: {e}")
            return []
