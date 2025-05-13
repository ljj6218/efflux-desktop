from typing import Optional, List

from application.domain.generators.generator import LLMGenerator
from common.core.container.annotate import component
from application.port.outbound.generators_port import GeneratorsPort
from application.port.inbound.model_case import ModelCase
import injector

@component
class GeneratorService(ModelCase):

    @injector.inject
    def __init__(self, generators_port: GeneratorsPort):
        self.generators_port = generators_port


    async def model_list(self, firm: str) -> List[LLMGenerator]:
        return self.generators_port.load_model_by_firm(firm)

    async def enabled_model_list(self, firm: str) -> List[LLMGenerator]:
        return self.generators_port.load_enabled_model_by_firm(firm)

    async def enable_or_disable_model(self, firm: str, model: str, enabled: bool) -> Optional[bool]:
        return self.generators_port.enable_or_disable_model(firm, model, enabled)




