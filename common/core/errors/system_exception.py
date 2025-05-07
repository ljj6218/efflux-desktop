from common.core.errors.common_exception import CommonException
from common.core.errors.base_error_code import BaseErrorCode
from typing import Optional

class ThirdPartyServiceException(CommonException):

    def __init__(self, error_code: BaseErrorCode, dynamics_message: Optional[str]):
        # 调用父类的构造函数
        super().__init__(error_code=error_code, dynamics_message=dynamics_message)

class ThirdPartyServiceApiCode(BaseErrorCode):
    # ===== mcp_server错误 (600-999) =====
    LLM_SERVICE_API_ERROR = (601, "LLM模型服务api错误")
    MCP_SERVER_API_ERROR = (602, "mcp server 接口错误")