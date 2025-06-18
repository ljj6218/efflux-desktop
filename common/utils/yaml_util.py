import yaml
from typing import Dict
from common.utils.file_util import get_resource_path

# 读取 YAML 文件并解析为字典
def load_yaml(filename: str) -> Dict:
    with open(get_resource_path(filename), 'r') as file:
        return yaml.safe_load(file)


# 根据渠道获取模型类型，并将其保存在字典中
def get_model_types_by_channel(yaml_data: Dict) -> Dict:
    model_dict = {}

    # 遍历 YAML 数据中的每个渠道
    for channel, models in yaml_data.items():
        model_dict[channel] = models  # 将渠道的模型列表保存在字典中

    return model_dict