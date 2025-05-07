from abc import ABC, abstractmethod
from common.utils.auth import ApiKeySecret

class UserSettingPort(ABC):

    @abstractmethod
    def load_firm_model_key(self, firm_name) -> ApiKeySecret:
        """
        获取制定模型厂商的api key
        :param firm_name: 厂商名
        :return: api key 密匙对象
        """
        pass
