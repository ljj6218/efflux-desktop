from typing import Any, Dict, Optional, Union, List
from pydantic import BaseModel
from common.core.errors.common_error_code import CommonErrorCode


class BaseResponse(BaseModel):
    """统一的HTTP响应体结构"""
    code: int = 200  # 统一响应体状态码
    message: str = "success"  # 响应消息
    data: Optional[Any] = None  # 响应数据，可以是任何类型
    success: bool = True  # 操作是否成功
    error: Optional[str] = None # 报错信息

    @classmethod
    def from_success(cls, data: Any = None, message: str = CommonErrorCode.SUCCESS.desc, code: int = CommonErrorCode.SUCCESS.value) -> "BaseResponse":
        """
        创建成功响应

        Args:
            data: 响应数据
            message: 成功消息
            code: 状态码

        Returns:
            HttpResponse: 成功的响应对象
        """
        return cls(
            code=code,
            message=message,
            data=data,
            success=True
        )

    @classmethod
    def from_error(cls, message: str = CommonErrorCode.INTERNAL_SERVER_ERROR.desc, code: int = CommonErrorCode.INTERNAL_SERVER_ERROR.value, error_message: str = "", data: Any = None) -> "BaseResponse":
        """
        创建错误响应

        Args:
            message: 错误消息
            code: 错误状态码 默认500
            data: 额外的错误数据
            error_message: 报错信息
        Returns:
            HttpResponse: 错误的响应对象
        """
        return cls(
            code=code,
            message=message,
            data=data,
            error=error_message,
            success=False
        )

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """重写dict方法，确保返回的字典格式一致"""
        result = super().dict(*args, **kwargs)
        return result