from typing import List, Optional

from application.domain.generators.firm import GeneratorFirm
from common.core.container.annotate import component
from application.port.outbound.user_setting_port import UserSettingPort
from application.port.inbound.user_settings_case import UserSettingsCase
import injector

@component
class UserSettingsService(UserSettingsCase):

    @injector.inject
    def __init__(self, user_setting_port: UserSettingPort):
        self.user_setting_port = user_setting_port

    async def load_firm_setting(self, firm_name: str) -> Optional[GeneratorFirm]:
        return self.user_setting_port.load_firm_setting(firm_name)

    async def set_firm_setting(self, generator_firm: GeneratorFirm) -> bool:
        return self.user_setting_port.set_firm_setting(generator_firm)

    async def load_firm_setting_list(self) -> List[GeneratorFirm]:
        return self.user_setting_port.load_firm_setting_list()