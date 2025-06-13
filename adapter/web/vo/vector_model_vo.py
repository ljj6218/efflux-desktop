from pydantic import BaseModel

class CreateVectorModelRequest(BaseModel):
    firm: str  # 厂商名称
    model_name: str  # 模型名称
    api_key: str  # API Key

class DeleteVectorModelRequest(BaseModel):
    id: str
