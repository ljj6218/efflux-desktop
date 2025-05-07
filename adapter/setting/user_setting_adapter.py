from typing import Optional

from application.port.outbound.user_setting_port import UserSettingPort
from common.core.container.annotate import component
from common.utils.auth import ApiKeySecret, Secret
from common.utils.json_file_util import JSONFileUtil

@component
class UserSettingAdapter(UserSettingPort):

    def load_firm_model_key(self, firm_name) -> Optional[ApiKeySecret]:
        user_setting_file_url = "user_setting.json"
        user_setting = JSONFileUtil(user_setting_file_url)
        llm_settings = user_setting.read_key("llm_key")
        if firm_name in llm_settings:
            return Secret.from_api_key(llm_settings[firm_name])
        return None