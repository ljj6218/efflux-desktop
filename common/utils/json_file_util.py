import json
import os
import re
from common.core.logger import get_logger
from typing import Optional, Dict, Any

# 获取logger实例
logger = get_logger(__name__)


class JSONFileUtil:
    def __init__(self, file_path):
        """初始化工具类，指定 JSON 文件路径"""
        self.file_path = file_path
        # 确保文件存在，如果不存在则创建空的 JSON 文件
        if not os.path.exists(self.file_path):
            # 确保文件所在的目录存在
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            logger.debug(f"文件 {self.file_path} 不存在，创建一个空的 JSON 文件.")
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False)  # 初始为空字典
            logger.info(f"已创建空 JSON 文件：{self.file_path}")
        else:
            logger.debug(f"文件 {self.file_path} 已存在，准备操作。")

    def _read_json(self) -> dict:
        """私有方法，读取 JSON 文件内容"""
        logger.debug(f"读取文件 {self.file_path} 中的数据.")
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                # 如果文件为空，返回空字典
                file_content = f.read().strip()
                if not file_content:  # 如果文件内容为空
                    return {}
                data = json.loads(file_content)
                logger.debug(f"成功读取数据: {data}")
                return data
        except Exception as e:
            logger.error(f"读取 JSON 文件失败: {e}")
            raise

    def _write_json(self, data):
        """私有方法，将数据写入 JSON 文件"""
        logger.debug(f"正在将数据写入文件 {self.file_path}: {data}")
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info(f"成功写入数据到文件 {self.file_path}.")
        except Exception as e:
            logger.error(f"写入 JSON 文件失败: {e}")
            raise

    def read(self) -> dict:
        """读取 JSON 文件并返回数据"""
        logger.debug(f"读取文件 {self.file_path} 的内容.")
        return self._read_json()

    def write(self, data):
        """将数据写入 JSON 文件"""
        logger.debug(f"将数据写入文件 {self.file_path}.")
        self._write_json(data)

    def append(self, new_data):
        """向现有 JSON 文件中添加数据"""
        logger.debug(f"尝试向文件 {self.file_path} 追加数据: {new_data}")
        current_data = self._read_json()

        if isinstance(current_data, dict) and isinstance(new_data, dict):
            current_data.update(new_data)
            logger.debug(f"更新字典数据: {current_data}")
        elif isinstance(current_data, list) and isinstance(new_data, list):
            current_data.extend(new_data)
            logger.debug(f"向列表中追加数据: {current_data}")
        else:
            logger.error(f"当前文件内容和追加的数据类型不匹配，无法追加.")
            raise ValueError("当前文件内容和追加的数据类型不匹配")

        self._write_json(current_data)

    def delete(self, key):
        """根据键删除 JSON 文件中的数据"""
        logger.debug(f"尝试删除文件 {self.file_path} 中的键 {key}.")
        data = self._read_json()

        if isinstance(data, dict) and key in data:
            del data[key]
            logger.info(f"成功删除键 {key} 的数据.")
        else:
            logger.error(f"未找到键 {key}")
        self._write_json(data)

    def pretty_print(self):
        """打印出 JSON 文件内容"""
        logger.debug(f"打印文件 {self.file_path} 的内容.")
        data = self._read_json()
        print(json.dumps(data, indent=4, ensure_ascii=False))
        logger.debug(f"打印内容:\n{json.dumps(data, indent=4, ensure_ascii=False)}")

    def read_key(self, key_path):
        """读取指定路径的键的数据，支持递归查找"""
        logger.debug(f"尝试读取文件 {self.file_path} 中的键 {key_path}.")
        data = self._read_json()
        # 只处理一级键
        if isinstance(data, dict) and key_path in data:
            result = data[key_path]
            logger.debug(f"成功读取键 {key_path} 的数据: {result}")
            return result
        else:
            return None

    def update_key(self, key_path, new_value):
        """更新指定路径的键的数据，支持递归更新"""
        logger.debug(f"尝试更新文件 {self.file_path} 中的键 {key_path} 的值为 {new_value}.")
        data = self._read_json()
        # 只处理一级键
        if isinstance(data, dict) and key_path in data:
            data[key_path] = new_value
            logger.info(f"成功更新键 {key_path} 的值为 {new_value}.")
        else:
            logger.info(f"未找到键 {key_path}. 新增 {new_value}.")
            data[key_path] = new_value

        self._write_json(data)

    @staticmethod
    def extract_json_from_string(s: str) -> Optional[Any]:
        """
        Searches for a JSON object within the string and returns the loaded JSON if found, otherwise returns None.
        """
        # Regex to find JSON objects (greedy, matches first { to last })
        match = re.search(r"\{.*\}", s, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                return None
        return None
