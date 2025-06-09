from enum import Enum
from typing import Dict, Any, List

from application.domain.agents.agent import Agent, AgentInstance, AgentState
from application.domain.events.event import Event, EventType, EventSubType, EventSource
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from application.domain.plan import Plan, PlanStep, PlanState
from application.port.outbound.generators_port import GeneratorsPort
from application.domain.generators.generator import LLMGenerator
from application.port.outbound.ws_message_port import WsMessagePort
from application.port.outbound.event_port import EventPort
from common.utils.common_utils import create_uuid
from application.service.prompts.orchestration import (
    ORCHESTRATOR_PLAN_PROMPT_JSON,
    validate_plan_json, ORCHESTRATOR_SYSTEM_MESSAGE_PLANNING
)

from datetime import datetime
import json

from common.core.logger import get_logger

logger = get_logger(__name__)


class PlanAgentAction(Enum):
    PLANNING = "PLANNING"
    RE_PLANNING = "RE-PLANNING"

class PlanAgent(AgentInstance):

    def __init__(
        self,
        generators_port: GeneratorsPort,
        llm_generator: LLMGenerator,
        ws_message_port: WsMessagePort
    ):
        super().__init__(llm_generator, generators_port, ws_message_port)
        self._agents: List[Agent] = []
        self._team_description = None

    async def lazy_init(self, config: Dict[str, Any]) -> None:
        # agent集合及描述字符串
        self._agents: List[Agent] = config['agents']
        self._team_description = config['team_description']


    def execute(self, history_message_list: List[ChatStreamingChunk], payload: Dict[str, Any], client_id: str) -> None:
        # 拼接生成plan的提示词
        context_message_list = self._thread_to_context(history_message_list=history_message_list)
        # 请求大模型返回计划列表
        # rs = self.generators_port.generate_json(llm_generator=self.llm_generator, messages=context_message_list,
        #                                         validate_json=validate_plan_json, json_object=True)
        # print(json.dumps(rs, ensure_ascii=False))

        if "json_result_data" in payload: # 模型返回json结果
            json_result_data = payload["json_result_data"]
            if json_result_data['needs_plan']:
                steps = []
                for index, step in enumerate(json_result_data['steps']):
                    plan_step = PlanStep(index=index, title=step['title'], details=step['details'], agent_name=step['agent_name'])
                    steps.append(plan_step)
                new_plan = Plan.from_init(conversation_id=self.info.conversation_id, task=json_result_data['task'], plan_summary=json_result_data['plan_summary'], steps=steps)
                payload['user_confirm'] = True
                payload['confirm_data'] = new_plan
                event = Event.from_init(
                    client_id=client_id,
                    event_type=EventType.AGENT,
                    event_sub_type=EventSubType.AGENT_CALL_RESULT,
                    source=EventSource.AGENT,
                    data={
                        "id": create_uuid(),
                        "agent_instance_id": self.info.instance_id,
                        "dialog_segment_id": self.info.dialog_segment_id,
                        "conversation_id": self.info.conversation_id,
                        "generator_id": self.info.generator_id,
                    },
                    payload=payload
                )
                EventPort.get_event_port().emit_event(event)
                self.info.state = AgentState.RUNNING
        else:
            if payload['replan']:
                print("重新规划")
            else:
                print("新建规划")
                # 请求大模型生成计划
                self._send_llm_event(client_id=client_id, context_message_list=context_message_list)

        #     if rs['needs_plan']:
        #         steps = []
        #         for index, step in enumerate(rs['steps']):
        #             plan_step = PlanStep(index=index, title=step['title'], details=step['details'], agent_name=step['agent_name'])
        #             steps.append(plan_step)
        #         new_plan = Plan.from_init(conversation_id=self.info.conversation_id, task=rs['task'], plan_summary=rs['plan_summary'], steps=steps)
        #         payload['user_confirm'] = True
        #         payload['confirm_data'] = new_plan
        # event = Event.from_init(
        #     client_id=client_id,
        #     event_type=EventType.AGENT,
        #     event_sub_type=EventSubType.AGENT_CALL_RESULT,
        #     source=EventSource.AGENT,
        #     data={
        #         "id": create_uuid(),
        #         "agent_instance_id": self.info.instance_id,
        #         "dialog_segment_id": self.info.dialog_segment_id,
        #         "conversation_id": self.info.conversation_id,
        #         "generator_id": self.info.generator_id,
        #     },
        #     payload=payload
        # )
        # EventPort.get_event_port().emit_event(event)

    def _thread_to_context(self, history_message_list: List[ChatStreamingChunk]) -> List[ChatStreamingChunk]:
        """拼装基础system提示词和会话历史信息"""
        date_today = datetime.now().strftime("%Y-%m-%d")
        # 拼装系统提示词
        messages: List[ChatStreamingChunk] = [ChatStreamingChunk.from_system(
            message=ORCHESTRATOR_SYSTEM_MESSAGE_PLANNING.format(
                date_today=date_today,
                team=self._team_description,
            )
        )]
        # 拼装对话上下文
        messages.extend(history_message_list)
        # 拼接生成计划的提示词
        make_plan_message = ChatStreamingChunk.from_user(message=ORCHESTRATOR_PLAN_PROMPT_JSON.format(
            team=self._team_description, additional_instructions=""))
        messages.append(make_plan_message)
        return messages

    def _send_llm_event(self, client_id: str, context_message_list: List[ChatStreamingChunk]):
        """发送大模型请求事件"""
        event = Event.from_init(
            event_type=EventType.USER_MESSAGE,
            event_sub_type=EventSubType.MESSAGE,
            client_id=client_id,
            source=EventSource.AGENT,
            data={
                "id": create_uuid(),
                "dialog_segment_id": self.info.dialog_segment_id,
                "conversation_id": self.info.conversation_id,
                "generator_id": self.info.generator_id,
            },
            payload={
                "agent_instance_id": self.info.instance_id,
                "json_result": True,
                "mcp_name_list": [],
                "tools_group_name_list": [],
                "context_message_list": context_message_list,
            }
        )
        EventPort.get_event_port().emit_event(event)
        logger.info(
            f"[{self.info.name}]Agent实例[{self.info.instance_id}],发送LLM请求事件[{self.info.dialog_segment_id}]")