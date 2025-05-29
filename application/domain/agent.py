from abc import ABC, abstractmethod
from pydantic import BaseModel, model_validator
from common.utils.common_utils import create_uuid
from typing import Optional, List, Dict, Any

class AgentState(BaseModel):
    def type(self) -> str:
        pass

class Agent(BaseModel):

    id: str
    name: str
    tools_group_list: List[Dict[str, Any]]
    description: str

    @model_validator(mode='after')
    def check_dict_keys(cls, values):
        """
        验证tools_group_list的key格式
        :param values:
        :return:
        """
        tools_group_list = values.tools_group_list
        for tools_group in tools_group_list:
            for key in tools_group.keys():
                if key not in ["group_name", "type"]:
                    raise ValueError(f"Invalid key '{key}', only 'group_name' and 'type' are allowed.")
            return values

    def make_instance(self) -> "AgentInstance":
        return AgentInstance(
            id=self.id,
            name=self.name,
            tools_group_list=self.tools_group_list,
            description=self.description,
            instance_id=create_uuid(),
        )

    @abstractmethod
    def state(self) -> AgentState:
        pass

    # def model_dump(self, **kwargs):
        #     # 使用 super() 获取字典格式
        #     data = super().model_dump()
        #
        #     # 用于存储已经遇到的 (group_name, type) 或 (mcp_server_name, type) 组合
        #     seen_combinations = set()
        #
        #     # 筛选出不重复的工具
        #     filtered_tools = []
        #
        #     # 持久化只保存tools组的名字和类型
        #     if 'tools' in data:
        #         # dict_tools: List[Dict[str, Any]] = []
        #         for tool in data['tools']:
        #             combination = None
        #             if tool['group_name']:
        #                 combination = (tool['group_name'], tool['type'])
        #             elif tool['mcp_server_name']:
        #                 combination = (tool['mcp_server_name'], tool['type'])
        #             # 如果该组合未被遇到过，则添加到结果列表中
        #             if combination and combination not in seen_combinations:
        #                 filtered_tools.append({
        #                     "group_name": tool['group_name'] if tool['group_name'] else tool['mcp_server_name'],
        #                     "type": tool['type'].value
        #                 })
        #                 seen_combinations.add(combination)
        #         data['tools'] = filtered_tools
        #
        #     return data

        # @classmethod
        # def from_init(cls, name: str, tools: List[Tool], description: str) -> "Agent":
        #     return cls(id=create_uuid(), tools=tools, name=name, description=description)
class AgentInstance(Agent):

    instance_id: str
    system_prompt: str


    def state(self) -> AgentState:
        return None



    def run(self) -> Dict[str, Any]:
        pass

