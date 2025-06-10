from enum import Enum
from typing import Dict, Any, List, Optional

from application.domain.agents.agent import Agent, AgentInstance, AgentState
from application.domain.events.event import Event, EventType, EventSubType, EventSource
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from application.domain.plan import Plan, PlanStep, PlanState
from application.port.outbound.conversation_port import ConversationPort
from application.port.outbound.generators_port import GeneratorsPort
from application.domain.generators.generator import LLMGenerator
from application.port.outbound.ws_message_port import WsMessagePort
from application.domain.conversation import DialogSegment, DialogSegmentMetadata, MetadataSource, MetadataType
from application.port.outbound.event_port import EventPort
from common.utils.common_utils import create_uuid
from common.utils.time_utils import create_from_second_now_to_int

from datetime import datetime

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
        ws_message_port: WsMessagePort,
        conversation_port: ConversationPort,
    ):
        super().__init__(llm_generator, generators_port, ws_message_port, conversation_port)
        self._agents: List[Agent] = []
        self._team_description = None

    async def lazy_init(self, config: Dict[str, Any]) -> None:
        # agent集合及描述字符串
        self._agents: List[Agent] = config['agents']
        self._team_description = config['team_description']


    def execute(self, history_message_list: List[ChatStreamingChunk], payload: Dict[str, Any], client_id: str) -> None:

        if "json_result_data" in payload: # 接受模型返回json结果
            json_result_data = payload["json_result_data"]
            if json_result_data['needs_plan']:
                steps = []
                for index, step in enumerate(json_result_data['steps']):
                    plan_step = PlanStep(index=index, title=step['title'], details=step['details'], agent_name=step['agent_name'])
                    steps.append(plan_step)
                new_plan = Plan.from_init(conversation_id=self.info.conversation_id, agent_instance_id=self.info.instance_id, task=json_result_data['task'], plan_summary=json_result_data['plan_summary'], steps=steps)
                #payload['user_confirm'] = True
                payload['confirm_data'] = new_plan
                payload['plan'] = new_plan
                del payload['json_result_data']  # agent请求的删除json返回
                del payload['json_result']
                self._send_agent_result_event(client_id=client_id, payload=payload, agent_state=AgentState.RUNNING)
        else: # plan创建/修改/确认
            if payload['update']: # 修改任务规划
                if payload['replan']: # 重新规划任务
                    logger.info("重新规划plan")
                    # 拼接重新生成plan的提示词
                    context_message_list = self._thread_to_context(history_message_list=history_message_list, old_plan=payload['old_plan'], content=payload['content'])
                    # 请求大模型生成计划
                    self._send_llm_event(client_id=client_id, context_message_list=context_message_list)
                    # 保存agent记录
                    dialog_segment = DialogSegment.make_user_message(content=f"重新生成计划：{payload['content']}", conversation_id=self.info.conversation_id,
                                                                     payload={'agent_instance_id': self.info.instance_id},
                                                    metadata=DialogSegmentMetadata(source=MetadataSource.AGENT, type=MetadataType.USER_CONFIRMATION))
                    self.conversation_port.add_agent_record(dialog_segment=dialog_segment)
                else:
                    logger.info("人工修改任务或确认plan")
                    payload['plan'].state = PlanState.RUNNING # 设置plan进入运行状态
                    self._send_agent_result_event(client_id=client_id, payload=payload, agent_state=AgentState.DONE)
                    # 保存agent结果
                    dialog_segment = DialogSegment.make_assistant_message(content="", id=self.info.dialog_segment_id, conversation_id=self.info.conversation_id,
                                                                          model=self.llm_generator.model, timestamp=create_from_second_now_to_int(),
                                                                          payload={'agent_instance_id': self.info.instance_id},
                                                                          metadata=DialogSegmentMetadata(source=MetadataSource.AGENT, type=MetadataType.AGENT_RESULT))
                    self.conversation_port.conversation_add(dialog_segment=dialog_segment)
            else: # 新建任务规划
                # 拼接生成plan的提示词
                context_message_list = self._thread_to_context(history_message_list=history_message_list)
                # 请求大模型生成计划
                self._send_llm_event(client_id=client_id, context_message_list=context_message_list)

    def _thread_to_context(self, history_message_list: List[ChatStreamingChunk], old_plan: Optional[Plan] = None, content: Optional[str] = None ) -> List[ChatStreamingChunk]:
        """拼装基础system提示词和会话历史信息"""
        date_today = datetime.now().strftime("%Y-%m-%d")
        orchestrator_system_message_planning = self.info.agent_prompts['ORCHESTRATOR_SYSTEM_MESSAGE_PLANNING']
        orchestrator_plan_prompt_json = self.info.agent_prompts['ORCHESTRATOR_PLAN_PROMPT_JSON']
        orchestrator_plan_replan_json = self.info.agent_prompts['ORCHESTRATOR_PLAN_REPLAN_JSON']
        # 拼装系统提示词
        messages: List[ChatStreamingChunk] = [ChatStreamingChunk.from_system(
            message=orchestrator_system_message_planning.format(
                date_today=date_today,
                team=self._team_description,
            )
        )]
        # 拼装对话上下文
        messages.extend(history_message_list)
        if old_plan:
            # 拼接重新生成计划的提示词
            make_replan_message = ChatStreamingChunk.from_user(message=orchestrator_plan_replan_json.format(
                task=old_plan.task,
                plan=f"Previous plan:\n{str(old_plan)}", # TODO 此处如果是执行任务途中重新规划，需要增加plan目前执行的情况描述（比如已执行step列表）
                team=self._team_description,
                additional_instructions=content if content else ""
            ))
            messages.append(make_replan_message)
        else:
            # 拼接生成计划的提示词
            make_plan_message = ChatStreamingChunk.from_user(message=orchestrator_plan_prompt_json.format(
                team=self._team_description, additional_instructions=""))
            messages.append(make_plan_message)
        return messages

    def _send_agent_result_event(self, client_id: str, payload: Dict[str, Any], agent_state: AgentState) -> None:
        payload['agent_state'] = agent_state
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