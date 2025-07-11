from application.domain.agents.agent import Agent
from application.domain.events.event import EventType, EventSubType, Event, EventSource
from application.domain.plan import Plan, PlanState
from application.domain.conversation import DialogSegment, DialogSegmentMetadata, MetadataType, MetadataSource
from application.port.inbound.plan_case import PlanCase
from application.port.outbound.agent_port import AgentPort
from application.port.outbound.conversation_port import ConversationPort
from application.port.outbound.event_port import EventPort
from application.port.outbound.plan_port import PlanPort
from common.core.container.annotate import component
from common.utils.common_utils import create_uuid

import injector
from common.core.logger import get_logger

logger = get_logger(__name__)

@component
class PlanService(PlanCase):

    @injector.inject
    def __init__(
        self,
        plan_port: PlanPort,
        agent_port: AgentPort,
        conversation_port: ConversationPort,
    ):
        self.plan_port = plan_port
        self.agent_port = agent_port
        self.conversation_port = conversation_port

    async def update(
        self,
        plan: Plan,
        agent_instance_id: str,
        is_update: bool,
        is_replan: bool,
        content: str,
        client_id: str,
        generator_id: str
    ) -> str:
        old_plan = self.plan_port.load(conversation_id=plan.conversation_id)
        if old_plan.state == PlanState.RUNNING:
            # TODO 已经运行的计划不能修改
            print("err")
        
        payload = {
            "agent_instance_id": agent_instance_id,
            "plan": plan.model_dump(),
            "is_replan": is_replan,
        }
        dialog_segment_id = create_uuid()
        agent: Agent = self.agent_port.load(agent_id="1")
        # 保存用户确认记录
        dialog_states = DialogSegment.make_user_message(
            content=content, conversation_id=plan.conversation_id,
            metadata=DialogSegmentMetadata(source=MetadataSource.USER, type=MetadataType.USER_CONFIRMATION),
            payload=payload)
        self.conversation_port.conversation_add(dialog_states)
        # 发送agent call事件
        event = Event.from_init(
            client_id=client_id,
            event_type=EventType.AGENT,
            event_sub_type=EventSubType.AGENT_CALL,
            source=EventSource.TEAMS_SVC,
            payload={
                "agent_instance_id": agent_instance_id,
                "old_plan": old_plan,
                "plan": plan,
                "update": True,
                "replan": is_replan,
                'content': content,
            },
            data={
                "id": create_uuid(),
                "dialog_segment_id": dialog_segment_id,
                "conversation_id": plan.conversation_id,
                "generator_id": generator_id,
                "content": f"call {agent.name} agent",
            },
        )

        logger.info(f"[PlanService]发起[{EventType.AGENT} - {EventSubType.AGENT_CALL}]事件：[ID：{event.id}]")
        EventPort.get_event_port().emit_event(event)
        return plan.conversation_id

    async def load(self, conversation_id: str) -> Plan:
        return self.plan_port.load(conversation_id=conversation_id)