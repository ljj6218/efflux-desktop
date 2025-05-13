from abc import ABC, abstractmethod
from application.domain.generators.firm import GeneratorFirm
from typing import List

class UserSettingsCase(ABC):

    @abstractmethod
    async def load_firm_setting(self, firm_name: str) -> GeneratorFirm:
        """
        获取模型厂商配置
        :param firm_name: 模型厂商名
        :return: 模型厂商对象
        """

    @abstractmethod
    async def set_firm_setting(self, generator_firm: GeneratorFirm) -> bool:
        """
        设置模型厂商配置
        :param generator_firm: 模型厂商对象
        :return:
        """

    @abstractmethod
    async def load_firm_setting_list(self) -> List[GeneratorFirm]:
        """
        获取模型厂商配置集合
        :return: 模型厂商对象集合
        """