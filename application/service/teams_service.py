from typing import Optional, List, Dict, Any

from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from application.domain.generators.firm import GeneratorFirm
from application.domain.generators.generator import LLMGenerator
from application.port.outbound.user_setting_port import UserSettingPort
from common.core.errors.business_exception import BusinessException
from common.core.errors.business_error_code import GeneratorErrorCode
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
from common.utils.common_utils import create_uuid, CONVERSATION_STOP_FLAG_KEY
from common.core.logger import get_logger

# from application.service.prompts.orchestration import (
#     ORCHESTRATOR_SYSTEM_MESSAGE_PLANNING, ORCHESTRATOR_SYSTEM_MESSAGE_EXECUTION, ORCHESTRATOR_PLAN_PROMPT_JSON,
#     validate_plan_json
# )


from datetime import datetime
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
        # agents, _team_description = self._load_agent()
        # self.agents: List[Agent] = agents
        # self._team_description = _team_description
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
                print("任务初始化中")
                # agent_id = "1"
                # payload = {
                #     "update": True,
                #     "replan": False,
                #     "plan": payload['plan'] if 'plan' in payload else None,
                # }
                # # 调用任务规划agent
                # await self._call_agent(agent_id, client_id, conversation_id, dialog_segment_id, generator_id, payload)
        else:
            agent_id = "0"
            payload = {}
            # 调用用户需求澄清Agent
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



    # def _choose_agent(self, agent_id: str) -> Optional[Agent]:
    #     for agent in self.agents:
    #         if agent.id == agent_id:
    #             return agent
    #     return None

    def _conversation_check(self, conversation_id: str, query_str: str) -> str:
        # 创建会话
        if not conversation_id:
            conversation = Conversation()
            conversation.init()
            conversation.theme = query_str
            conversation.dialog_segment_list = []
            self.conversation_port.conversation_save(conversation=conversation)
            conversation_id = conversation.id
            logger.info(f"首次发送消息创建会话：[ID：{conversation.id} - 主题：{conversation.theme}]")
        else:
            logger.info(f"历史会话消息：[ID：{conversation_id}]")
        return conversation_id

    # def _thread_to_context(self, conversation_id: str) -> List[ChatStreamingChunk]:
    #     """拼装基础system提示词和会话历史信息"""
    #     # 查询会话历史
    #     history_conversation = self.conversation_port.conversation_load(conversation_id=conversation_id)
    #     if not history_conversation:
    #         raise BusinessException(error_code=GeneratorErrorCode.NO_CONVERSATION_FOUND, dynamics_message=conversation_id)
    #     date_today = datetime.now().strftime("%Y-%m-%d")
    #     # message 封装
    #     messages: List[ChatStreamingChunk] = []
    #     # 拼装系统提示词
    #     if self._state.in_planning_mode: # 规划
    #         messages.append(ChatStreamingChunk.from_system(
    #             message=ORCHESTRATOR_SYSTEM_MESSAGE_PLANNING.format(
    #                 date_today=date_today,
    #                 team=self._team_description,
    #             )
    #         ))
    #     else: # 执行
    #         messages.append(ChatStreamingChunk.from_system(
    #             message=ORCHESTRATOR_SYSTEM_MESSAGE_EXECUTION.format(
    #                 date_today=date_today
    #             )
    #         ))
    #
    #     # 拼装对话上下文
    #     history_message_list = history_conversation.convert_sort_memory()
    #     messages.extend(history_message_list)
    #     return messages

    # def _get_make_plan_prompt(self) -> str:
    #     return ORCHESTRATOR_PLAN_PROMPT_JSON.format(
    #         team=self._team_description, additional_instructions=""
    #     )
    #
    # def _llm_generator(self, generator_id: str) -> LLMGenerator:
    #     # 获取厂商api key
    #     llm_generator: LLMGenerator = self.generators_port.load_generate(generator_id)
    #     firm: GeneratorFirm = self.user_setting_port.load_firm_setting(llm_generator.firm)
    #     llm_generator.set_api_key_secret(firm.api_key)
    #     llm_generator.check_firm_api_key()
    #     return llm_generator
