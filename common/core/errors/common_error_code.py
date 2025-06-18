from common.core.errors.base_error_code import BaseErrorCode


class CommonErrorCode(BaseErrorCode):

    SUCCESS = (200, "成功")
    # ===== HTTP标准错误 (400-499) =====
    BAD_REQUEST = (400, "请求参数错误")
    UNAUTHORIZED = (401, "未授权访问")
    FORBIDDEN = (402, "禁止访问")
    NOT_FOUND = (404, "资源不存在")

    REQUEST_TIMEOUT = (408, "请求超时")
    VALIDATION_ERROR = (422, "数据验证失败")
    INVALID_CREDENTIALS = (432, "用户名或密码错误")
    TOKEN_EXPIRED = (433, "令牌已过期")
    INVALID_TOKEN = (434, "无效令牌")
    PERMISSION_DENIED = (435, "权限不足")

    # ===== 通用错误 (500-519) =====
    INTERNAL_SERVER_ERROR = (500, "未知错误")

    # ===== 数据错误 (520-599)=====
    CACHE_NOT_FOUND = (520, "缓存不存在")
    CACHE_RECORD_NOT_FOUND = (521, "缓存记录不存在")
    DIALOG_SEGMENT_CONTENT_JSON_DECODE_ERROR = (522, "对话片段content json解析失败")
    DIALOG_SEGMENT_NOT_FOUND = (523, "对话片段不存在")
    # ===== 业务错误 (1000-9999) =====