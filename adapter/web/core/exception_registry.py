from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from common.core.errors.common_exception import CommonException
from common.core.errors.business_exception import BusinessException
from .exception_handlers import (
    common_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    business_exception_handler
)


def register_exception_handlers(app: FastAPI):
    """
    注册所有异常处理器到 FastAPI 应用

    Args:
        app: FastAPI 应用实例
    """
    # 注册自定义异常处理器
    app.add_exception_handler(CommonException, common_exception_handler)
    app.add_exception_handler(BusinessException, business_exception_handler)

    # 注册 FastAPI 内置异常处理器
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # 注册默认异常处理器（处理所有未被捕获的异常）
    app.add_exception_handler(Exception, unhandled_exception_handler)