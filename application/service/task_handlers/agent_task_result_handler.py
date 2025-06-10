from datetime import datetime
from typing import Dict, Any, List, Optional

from application.domain.agents.agent import Agent, AgentInfo, AgentState
from application.domain.events.event import Event, EventType, EventSubType, EventSource
from application.domain.generators.chat_chunk.chunk import ChatStreamingChunk
from application.domain.plan import PlanState, PlanStep, Plan
from application.domain.tasks.task import Task, TaskType, TaskState
from application.port.inbound.task_handler import TaskHandler
from application.port.outbound.conversation_port import ConversationPort
from application.port.outbound.event_port import EventPort
from application.port.outbound.plan_port import PlanPort
from application.port.outbound.ws_message_port import WsMessagePort
from common.core.container.annotate import component
from application.port.outbound.agent_port import AgentPort
from application.port.outbound.tools_port import ToolsPort
from application.port.outbound.generators_port import GeneratorsPort
from application.domain.generators.generator import LLMGenerator
from application.port.outbound.user_setting_port import UserSettingPort
from application.domain.generators.firm import GeneratorFirm
from application.service.prompts.orchestration import ORCHESTRATOR_PROGRESS_LEDGER_PROMPT, ORCHESTRATOR_SYSTEM_MESSAGE_EXECUTION, validate_ledger_json

from common.core.logger import get_logger
import injector

from common.utils.common_utils import create_uuid

logger = get_logger(__name__)

@component
class AgentTaskResultHandler(TaskHandler):

    @injector.inject
    def __init__(
        self,
        agent_port: AgentPort,
        tools_port: ToolsPort,
        event_port: EventPort,
        conversation_port: ConversationPort,
        generators_port: GeneratorsPort,
        ws_message_port: WsMessagePort,
        user_setting_port: UserSettingPort,
        plan_port: PlanPort,
    ):
        self.agent_port = agent_port
        self.tools_port = tools_port
        self.event_port = event_port
        self.generators_port = generators_port
        self.ws_message_port = ws_message_port
        self.user_setting_port = user_setting_port
        self.conversation_port = conversation_port
        self.plan_port = plan_port

    def execute(self, task: Task):
        print("AgentTaskResultHandler")
        agent_instance_id = task.data['agent_instance_id']
        conversation_id = task.data['conversation_id']
        generator_id = task.data['generator_id']
        dialog_segment_id = task.data['dialog_segment_id']
        client_id = task.client_id
        # 更新agent状态
        agent_info = self.agent_port.load_instance_info(instance_id=agent_instance_id, conversation_id=conversation_id)
        agent_info.state = task.payload['agent_state']
        self.agent_port.save_instance_info(instance_info=agent_info)
        # 如果agent是clarification类型
        if agent_info.name == "clarification" and agent_info.state == AgentState.DONE:  # 更新计划状态
            # 根据重新规划的结果调用agent
            self._call_agent(agent_name='plan',
                             client_id=client_id,
                             conversation_id= conversation_id,
                             generator_id = generator_id,
                             payload = {'update': False})
            logger.info(f"需求澄清结束，调用计划Agent")


        # 如果agent是plan类型
        if agent_info.name == "plan": # 更新计划状态
            self.plan_port.sava(task.payload['plan'])
            if agent_info.state == AgentState.DONE and task.payload['plan'].state == PlanState.RUNNING:
                # 获取运行第一个step
                first_step = task.payload['plan'].steps[0]
                # 查询会话历史
                history_conversation = self.conversation_port.conversation_load(conversation_id=conversation_id)
                message_list = self._thread_to_context(history_message_list=history_conversation.convert_sort_memory())
                message_list.append(ChatStreamingChunk.from_system(message=self._redesign_step_prompt(plan=task.payload['plan'], step=first_step)))
                # 重新规划step
                result_dict = self._redesign_step(generator_id=generator_id, message_list=message_list)
                logger.info(f"重新规划结果：--->{result_dict}")
                # 根据重新规划的结果调用agent
                # self._call_agent()


        # 判读是否需要用户确认
        if 'confirm_data' in task.payload:
            print(f"需用户确认-》[{task.payload['confirm_data']}]")
            event = Event.from_init(
                client_id=task.client_id,
                event_type=EventType.INTERACTIVE,
                event_sub_type=EventSubType.CALL_USER,
                source=EventSource.AGENT,
                data=task.data,
                payload=task.payload,
            )
            EventPort.get_event_port().emit_event(event)

    def state(self) -> TaskState:
        pass

    def set_state(self, state: TaskState):
        pass

    def check_stop_flag(self) -> bool:
        pass



    def type(self) -> str:
        return TaskType.AGENT_CALL_RESULT.value

    def _llm_generator(self, generator_id: str) -> LLMGenerator:
        # 获取厂商api key
        llm_generator: LLMGenerator = self.generators_port.load_generate(generator_id)
        firm: GeneratorFirm = self.user_setting_port.load_firm_setting(llm_generator.firm)
        llm_generator.set_api_key_secret(firm.api_key)
        llm_generator.check_firm_api_key()
        return llm_generator

    def _call_agent(
        self,
        agent_name: str,
        client_id: str,
        conversation_id: str,
        generator_id: str,
        payload: Dict[str, Any],
        dialog_segment_id: Optional[str] = None,
    ):
        dialog_segment_id = dialog_segment_id if dialog_segment_id else create_uuid()
        """Agent 调用方法"""
        # 创建并保存agent instance info 实体
        agent: Agent = self.agent_port.load_by_name(agent_name=agent_name)
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
            source=EventSource.AGENT,
            payload=payload,
            data={
                "id": create_uuid(),
                "dialog_segment_id": dialog_segment_id,
                "conversation_id": conversation_id,
                "generator_id": generator_id,
                "content": f"call {agent_info.name} agent",
            },
        )
        logger.info(f"[AgentTaskResultHandler]发起[{EventType.AGENT} - {EventSubType.AGENT_CALL}]事件：[ID：{event.id}]")
        EventPort.get_event_port().emit_event(event)

    def _redesign_step(self, generator_id: str, message_list:List[ChatStreamingChunk]) -> Dict[str, Any]:
        """重新检查计划执行"""
        return self.generators_port.generate_json(llm_generator=self._llm_generator(generator_id=generator_id),
                  validate_json=None, messages=message_list)

    def _redesign_step_prompt(self, step: PlanStep, plan: Plan):
        agents, team_desc = self.agent_port.load_agent_teams()
        names = [agent.name for agent in agents]
        return ORCHESTRATOR_PROGRESS_LEDGER_PROMPT.format(
            task=plan.task,
            plan=str(plan),
            step_index=step.index,
            step_title=step.title,
            step_details=step.details,
            agent_name=step.agent_name,
            team=team_desc,
            names=", ".join(names),
            additional_instructions="",
        )

    def _thread_to_context(self, history_message_list: List[ChatStreamingChunk]) -> List[ChatStreamingChunk]:
        """拼装基础system提示词和会话历史信息"""
        date_today = datetime.now().strftime("%Y-%m-%d")
        # 拼装系统提示词
        messages: List[ChatStreamingChunk] = [ChatStreamingChunk.from_system(
            message=ORCHESTRATOR_SYSTEM_MESSAGE_EXECUTION.format(
                date_today=date_today
            )
        )]
        # 拼装对话上下文
        messages.extend(history_message_list)
        return messages