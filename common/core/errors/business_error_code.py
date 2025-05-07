from common.core.errors.base_error_code import BaseErrorCode


class GeneratorErrorCode(BaseErrorCode):
    # ===== mcp_server错误 (1000-1099) =====
    NO_APIKEY_FOUND = (1001, "未找到指定厂商的apikey")


class ToolsErrorCode(BaseErrorCode):
    NO_APIKEY_FOUND = (1001, "未找到指定厂商的apikey")

class MCPServerErrorCode(BaseErrorCode):
    NO_APIKEY_FOUND = (1001, "未找到指定厂商的apikey")