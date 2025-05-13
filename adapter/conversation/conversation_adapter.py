from typing import List, Dict, Optional
import jsonlines
import json
import os
from common.core.container.annotate import component
from application.domain.conversation import Conversation, DialogSegment
from application.port.outbound.conversation_port import ConversationPort

@component
class ConversationAdapter(ConversationPort):

    async def conversation_add(self, dialog_segment: DialogSegment) -> DialogSegment:
        dialog_segment_file = f'conversations/{dialog_segment.conversation_id}.jsonl'
        with jsonlines.open(dialog_segment_file, mode='a') as writer:
            writer.write(dialog_segment.model_dump())
        return dialog_segment

    async def dialog_segment_remove(self, dialog_segment: DialogSegment) -> DialogSegment:
        dialog_segment_file = f'conversations/{dialog_segment.conversation_id}.jsonl'
        segments = []

        # 读取现有对话段
        with jsonlines.open(dialog_segment_file, mode='r') as reader:
            for obj in reader:
                # 将对象转换为 DialogSegment
                dialog_segment = DialogSegment.model_validate(obj)
                # 检查 ID，跳过待删除的段
                if dialog_segment.id != dialog_segment.conversation_id:
                    segments.append(dialog_segment)

        # 重写文件，排除待删除的段
        with jsonlines.open(dialog_segment_file, mode='w') as writer:
            for segment in segments:
                writer.write(segment.model_dump())  # 写入更新后的数据

    async def conversation_save(self, conversation: Conversation) -> Conversation:
        conversation_file = f'conversations/conversations_list.jsonl'
        with jsonlines.open(conversation_file, mode='a') as writer:
            writer.write(conversation.model_dump())
        return conversation

    async def conversation_load(self, conversation_id: str) -> Optional[Conversation]:
        conversation_file = f'conversations/conversations_list.jsonl'
        conversation: Optional[Conversation] = None
        if not os.path.exists(conversation_file):
            return None
        with jsonlines.open(conversation_file, mode='r') as reader:
            for obj in reader:
                if obj.get("id") == conversation_id:
                    conversation = Conversation.model_validate(obj)
        if not conversation:
            return None

        dialog_segment_file = f'conversations/{conversation_id}.jsonl'
        if not os.path.exists(dialog_segment_file):
            return None
        with jsonlines.open(dialog_segment_file, mode='r') as reader:
            for obj in reader:
                conversation.dialog_segment_list.append(DialogSegment.model_validate(obj))
        return conversation


    async def conversation_load_list(self, conversation_id: str) -> List[Conversation]:
        pass