from enum import Enum, auto


class BaseErrorCode(Enum):
    """错误码枚举"""

    def __init__(self, num, desc):
        self._value_ = num  # 错误码数值
        self.desc = desc  # 错误描述文本

    def get_value(self):
        """返回错误码的数值"""
        return self.value

    def get_desc(self):
        """返回错误描述"""
        return self.desc