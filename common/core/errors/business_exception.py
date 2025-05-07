from common.core.errors.common_exception import CommonException
from common.core.errors.base_error_code import BaseErrorCode
from typing import Optional

class BusinessException(CommonException):

    def __init__(self, error_code: BaseErrorCode, dynamics_message: Optional[str]):
        # 调用父类的构造函数
        super().__init__(error_code=error_code, dynamics_message=dynamics_message)

    def __str__(self):
        return f"{self.code} - {self.message} - {self.dynamics_message}"

