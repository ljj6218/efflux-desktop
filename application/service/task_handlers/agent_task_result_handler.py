from application.domain.agents.agent import Agent, AgentInfo, AgentState
from application.domain.events.event import Event, EventType, EventSubType, EventSource
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
from common.core.errors.business_error_code import GeneratorErrorCode
from common.core.errors.business_exception import BusinessException

from common.core.logger import get_logger
import injector

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
        # 判断agent的类型，
        agent_info = self.agent_port.load_instance_info(instance_id=agent_instance_id, conversation_id=conversation_id)


        if task.payload['type'] == 'plan_create': # 保存计划
            self.plan_port.sava(task.payload['confirm_data'])
            del task.payload['json_result_data'] # agent请求的删除json返回
            del task.payload['json_result']

        print(task.payload)
        if task.payload['user_confirm']:
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