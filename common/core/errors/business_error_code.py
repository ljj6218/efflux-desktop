from common.core.errors.base_error_code import BaseErrorCode


class GeneratorErrorCode(BaseErrorCode):
    # ===== mcp_server错误 (1000-1099) =====
    NO_APIKEY_FOUND = (1001, "未找到指定厂商的apikey")
    NO_CONVERSATION_FOUND = (1002, "未找到指定的会话信息")
    TOOL_AUTH_NOT_MATCH = (1003, "工具授权不匹配")

class ToolsErrorCode(BaseErrorCode):
    NO_APIKEY_FOUND = (1001, "未找到指定厂商的apikey")

class MCPServerErrorCode(BaseErrorCode):
    NO_APIKEY_FOUND = (1001, "未找到指定厂商的apikey")