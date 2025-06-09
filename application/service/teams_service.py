from typing import Optional, List, Dict, Any

from application.port.outbound.user_setting_port import UserSettingPort
from application.domain.agents.agent import Agent, AgentInstance, AgentInfo
from application.domain.conversation import DialogSegmentContent, Conversation, DialogSegment
from application.domain.events.event import Event, EventType, EventSubType, EventSource
from application.port.inbound.teams_case import TeamsCase
from application.port.outbound.agent_port import AgentPort
from application.port.outbound.cache_port import CachePort
from application.port.outbound.conversation_port import ConversationPort
from application.port.outbound.event_port import EventPort
from application.port.outbound.plan_port import PlanPort
from application.domain.plan import Plan, PlanState, PlanStep
from application.port.outbound.generators_port import GeneratorsPort
from common.core.container.annotate import component
from common.utils.common_utils import create_uuid
from common.core.logger import get_logger

import injector

logger = get_logger(__name__)

class TeamsState:
    in_planning_mode: bool = True
    is_paused: bool = False

@component
class TeamsService(TeamsCase):

    @injector.inject
    def __init__(
        self,
        conversation_port: ConversationPort,
        event_port: EventPort,
        cache_port: CachePort,
        agent_port: AgentPort,
        plan_port: PlanPort,
        generators_port: GeneratorsPort,
        user_setting_port: UserSettingPort,
    ):
        self.event_port = event_port
        self.conversation_port = conversation_port
        self.cache_port = cache_port
        self.agent_port = agent_port
        self.plan_port = plan_port
        self.generators_port = generators_port
        self.user_setting_port = user_setting_port
        # agent集合及描述字符串
        agents, _team_description = self._load_agent()
        self.agents: List[Agent] = agents
        self._team_description = _team_description
        # 状态
        self._state = TeamsState()

    async def on_message(
        self,
        client_id: str,
        generator_id: str,
        content: Optional[str | List[DialogSegmentContent]],
        conversation_id: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:
        # 保存会话记录
        query_str = None
        if isinstance(content, List):
            for item in content:
                if item.type == 'text':
                    query_str = item.content
        else:
            query_str = content
        # 会话检查
        conversation_id = self._conversation_check(conversation_id=conversation_id, query_str=query_str)
        # 保存用户输入
        user_dialog_segment = DialogSegment.make_user_message(
            content=query_str, conversation_id=conversation_id)
        self.conversation_port.conversation_add(dialog_segment=user_dialog_segment)
        logger.info(f"保存用户对话片段：[ID：{user_dialog_segment.id} - 内容：{user_dialog_segment.content}]")

        dialog_segment_id = create_uuid()
        # 查询当前会话是否存在未完成的 plan
        plan = self.plan_port.load(conversation_id)
        if plan:
            if plan.state == PlanState.DONE:
                print("任务结束")
            if plan.state == PlanState.RUNNING:
                print("执行任务")
            if plan.state == PlanState.INITIALIZING:
                agent_id = "1"
                payload = {
                    "update": True,
                    "replan": False,
                    "plan": payload['plan'] if 'plan' in payload else None,
                }
                # 调用任务规划agent
                await self._call_agent(agent_id, client_id, conversation_id, dialog_segment_id, generator_id, payload)
        else:
            agent_id = "1"
            payload = {
                "update": False,
            }
            # 调用任务规划agent
            await self._call_agent(agent_id, client_id, conversation_id, dialog_segment_id, generator_id, payload)

        # 未存在计划/存在已完成的计划。 TODO system_agent?
        # - 引导生成计划
        # - 生成计划

        # 存在未完成的计划
        # - 是否需要中断计划
        # - 重新规划计划


        return conversation_id, dialog_segment_id

    async def _call_agent(
        self,
        agent_id: str,
        client_id: str,
        conversation_id: str,
        dialog_segment_id: str,
        generator_id: str,
        payload: Dict[str, Any]
    ):
        """Agent 调用方法"""
        # 创建并保存agent instance info 实体
        agent: Agent = self.agent_port.load(agent_id=agent_id)
        agent_info: AgentInfo = agent.info(
            conversation_id=conversation_id,
            dialog_segment_id=dialog_segment_id,
            generator_id=generator_id,
        )
        # 默认负载值
        payload['agent_instance_id'] = agent_info.instance_id
        # 保存
        self.agent_port.save_instance_info(instance_info=agent_info)
        event = Event.from_init(
            client_id=client_id,
            event_type=EventType.AGENT,
            event_sub_type=EventSubType.AGENT_CALL,
            source=EventSource.TEAMS_SVC,
            payload=payload,
            data={
                "id": create_uuid(),
                "dialog_segment_id": dialog_segment_id,
                "conversation_id": conversation_id,
                "generator_id": generator_id,
                "content": f"call {agent_info.name} agent",
            },
        )
        logger.info(f"[TeamsService]发起[{EventType.AGENT} - {EventSubType.AGENT_CALL}]事件：[ID：{event.id}]")
        EventPort.get_event_port().emit_event(event)