from pydantic import BaseModel

from common.utils.common_utils import create_uuid


class Ppt(BaseModel):
    id: str
    conversation_id: str
    agent_instance_id: str
    html_code: str

    @classmethod
    def from_init(cls, conversation_id: str, agent_instance_id: str, html_code: str) -> "Ppt":
        return cls(
            id=create_uuid(),
            conversation_id=conversation_id,
            agent_instance_id=agent_instance_id,
            html_code=html_code
        )