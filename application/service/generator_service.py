from common.core.container.annotate import component
from application.port.outbound.generators_port import GeneratorsPort
from common.utils.auth import Secret
from application.port.inbound.generators_case import GeneratorsCase
import injector

from common.core.errors.business_exception import BusinessException
from common.core.errors.business_error_code import GeneratorErrorCode
from common.core.errors.common_exception import CommonException

@component
class GeneratorService(GeneratorsCase):

    @injector.inject
    def __init__(self, generators_port: GeneratorsPort):
        self.generators_port = generators_port

    async def generate(self):
        raise CommonException(GeneratorErrorCode.NO_APIKEY_FOUND)
        self.generators_port.generate_stream(model="deepseek-r1",
                                       api_secret=Secret.from_api_key("sk-e14209fb643f4d13bfb4f64701dec076"),
                                       firm="tongyi")

