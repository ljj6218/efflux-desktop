import time
from common.core.container.annotate import component
from application.port.outbound.test_case import TestCase
import injector
from application.port.outbound.tools_port import ToolsPort
from typing import Dict, Any

@component
class TestService(object):
    @injector.inject
    def __init__(self, test_case: TestCase, tools_port: ToolsPort):
        self.t : int = 123
        self.test_case : TestCase = test_case
        self.tools_port : ToolsPort = tools_port

    async def test(self) -> int:
        await self.test_case.test_add()
        return self.t

    async def test2(self) -> int:
        await self.tools_port.load_tools("amap-maps")
        return self.t

    async def welcome(self) -> Dict[str, Any]:
        async def aa():
            return {
                "code": 200,
                "message": "success",
                "sub_code": 200,
                "sub_message": "success",
                "data": {
                    "welcome_msg": "我是浙能锦江环境AI小助手，我已经学习了《行政管理类制度》知识，欢迎提问",
            }}
        return await aa()