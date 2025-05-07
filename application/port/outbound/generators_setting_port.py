from abc import ABC, abstractmethod

class GeneratorsSettingPort(ABC):

    @abstractmethod
    def model_list(self, firm: str = None):
        """
        获取指定模型厂商的模型列表
        :param firm: 模型厂商
        :return:
        """
        pass