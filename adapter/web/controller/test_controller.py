from fastapi import APIRouter, Depends
import asyncio
from common.core.logger import get_logger
from common.core.container.container import get_container
from application.service.test_service import TestService
from application.port.inbound.generators_case import GeneratorsCase
from application.port.inbound.agent_generators_case import AgentGeneratorsCase
from common.core.errors.business_exception import BusinessException
from common.core.errors.business_error_code import GeneratorErrorCode
from common.core.errors.common_exception import CommonException
logger = get_logger(__name__)

router = APIRouter(prefix="/api/test", tags=["Test"])

def get_test_service() -> TestService:
    return get_container().get(TestService)

def get_generators_case() -> GeneratorsCase:
    return get_container().get(GeneratorsCase)

def get_agent_generators_case() -> AgentGeneratorsCase:
    return get_container().get(AgentGeneratorsCase)

@router.get("/welcome")
async def welcome(test_service: TestService = Depends(get_test_service)):
    task = asyncio.create_task(test_service.welcome())
    return await task


@router.get("/test")
async def test(test_service: TestService = Depends(get_test_service)):
    await test_service.test()
    return "aaaa"

@router.get("/test2")
async def test2(generators_case: GeneratorsCase = Depends(get_generators_case)):
    await generators_case.generate()
    return "bbbb"

@router.get("/test3")
async def test3(agent_generators_case: AgentGeneratorsCase = Depends(get_agent_generators_case)):
    await agent_generators_case.generate()
    return "ccccc"