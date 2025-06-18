from abc import ABC, abstractmethod
from application.domain.generators.firm import GeneratorFirm
from typing import List, Optional


class UserSettingPort(ABC):

    @abstractmethod
    def load_firm_setting(self, firm_name: str) -> Optional[GeneratorFirm]:
        """
        获取指定模型厂商的api key
        :param firm_name: 厂商名
        :return: api key 密匙对象
        """

    @abstractmethod
    def set_firm_setting(self, generator_firm: GeneratorFirm) -> bool:
        """
        获取指定模型厂商的api key
        :param generator_firm: 模型厂商对象
        :return:
        """

    @abstractmethod
    def load_firm_setting_list(self) -> List[GeneratorFirm]:
        """
        获取模型厂商配置集合
        :return: 模型厂商对象集合
        """