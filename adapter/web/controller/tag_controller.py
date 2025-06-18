from common.utils.yaml_util import load_yaml
from typing import Dict, Any
from adapter.web.vo.base_response import BaseResponse
from fastapi import APIRouter

router = APIRouter(prefix="/api/tag", tags=["TAG"])

@router.get("")
async def load_mcp_server(tag_type: str) -> BaseResponse:
    tag_list= {
        "mcp_server_tag":[
            "tools", "server"
        ]
    }
    return BaseResponse.from_success(data=tag_list[tag_type])