from typing import Optional, Dict, List, Literal, Any
from application.domain.agents.agent import Agent
from anthropic import BaseModel


class AgentVo(BaseModel):

    id: Optional[str] = None
    name: Optional[str] = None
    generator_id: Optional[str] = None
    tools_group_list: Optional[List[Dict[str, Any]]] = None
    description: Optional[str] = None
    agent_prompts: Optional[Dict[str, str]] = None
    result_type: Optional[Literal["text", "html", "svg", "code"]] = None

    def convert_agent(self):
        return Agent(
            id=self.id,
            name=self.name,
            generator_id=self.generator_id,
            tools_group_list=self.tools_group_list,
            description=self.description,
            agent_prompts=self.agent_prompts,
            result_type=self.result_type
        )
