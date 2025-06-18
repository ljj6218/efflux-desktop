from fastapi import APIRouter, Depends

from adapter.web.vo import mcp_server_vo
from common.core.logger import get_logger
from common.core.container.container import get_container
from application.port.inbound.mcp_server_case import McpServerCase
from application.domain.mcp_server import MCPServer
from adapter.web.vo.mcp_server_vo import MCPServerVo, MCPServerResultVo, MCPServerAppliedResultVo
from adapter.web.vo.base_response import BaseResponse
from typing import Optional, List
logger = get_logger(__name__)

router = APIRouter(prefix="/api/mcp_server", tags=["MCP_SERVER"])

def mcp_server_case() -> McpServerCase:
    return get_container().get(McpServerCase)

@router.post("/apply")
async def apply_mcp_server(mcp_server_vo: MCPServerVo, mcp_server_service: McpServerCase = Depends(mcp_server_case)) -> BaseResponse:
    mcp_server: MCPServer = mcp_server_vo.convert_mcp_server()
    return BaseResponse.from_success(data=await mcp_server_service.apply(mcp_server))

@router.put("/execute_authorization")
async def apply_mcp_server(server_name: str, execute_authorization: bool, mcp_server_service: McpServerCase = Depends(mcp_server_case)) -> BaseResponse:
    return BaseResponse.from_success(data=await mcp_server_service.execute_authorization(server_name=server_name, execute_authorization=execute_authorization))

@router.put("/enabled")
async def enabled(server_name: str, mcp_enabled: bool, mcp_server_service: McpServerCase = Depends(mcp_server_case)) -> BaseResponse:
    return BaseResponse.from_success(data=await mcp_server_service.enabled(server_name=server_name, enabled=mcp_enabled))

@router.delete("/cancel")
async def cancel_apply_mcp_server(server_name: str, mcp_server_service: McpServerCase = Depends(mcp_server_case)) -> BaseResponse:
    return BaseResponse.from_success(data=await mcp_server_service.cancel_apply(server_name=server_name))

@router.get("")
async def load_mcp_server(server_name: Optional[str] = None, mcp_server_service: McpServerCase = Depends(mcp_server_case)) -> BaseResponse:
    mcp_server: MCPServer = await mcp_server_service.load(server_name)
    return BaseResponse.from_success(data=MCPServerAppliedResultVo.from_mcp_server(mcp_server) if mcp_server else None)

@router.post("")
async def add_mcp_server(mcp_server_vo: MCPServerVo, mcp_server_service: McpServerCase = Depends(mcp_server_case)):
    mcp_server: MCPServer = await mcp_server_service.add(mcp_server_vo.convert_mcp_server())
    return BaseResponse.from_success(data=mcp_server)

@router.delete("")
async def remove_mcp_server(server_name: Optional[str] = None, mcp_server_service: McpServerCase = Depends(mcp_server_case)) ->BaseResponse:
    return BaseResponse.from_success(data=await mcp_server_service.remove(server_name=server_name))

@router.get("/applied")
async def load_applied_mcp_server(server_name: Optional[str] = None, mcp_server_service: McpServerCase = Depends(mcp_server_case)) -> BaseResponse:
    mcp_server: MCPServer = await mcp_server_service.load_applied(server_name)
    return BaseResponse.from_success(data=MCPServerAppliedResultVo.from_mcp_server(mcp_server) if mcp_server else None)

@router.get("/applied_list")
async def load_applied_list(server_name: Optional[str] = None, mcp_server_service: McpServerCase = Depends(mcp_server_case)) -> BaseResponse:
    mcp_server_applied_result_vo_list: List[MCPServerAppliedResultVo] = []
    for applied_mcp_server in await mcp_server_service.load_applied_list(server_name):
        mcp_server_applied_result_vo_list.append(MCPServerAppliedResultVo.from_mcp_server(applied_mcp_server))
    return BaseResponse.from_success(data=mcp_server_applied_result_vo_list)

@router.get("/enabled_list")
async def load_enabled_list(server_name: Optional[str] = None, mcp_server_service: McpServerCase = Depends(mcp_server_case)) -> BaseResponse:
    mcp_server_enabled_result_vo_list: List[MCPServerAppliedResultVo] = []
    for enabled_mcp_server in await mcp_server_service.load_enabled_list(server_name):
        mcp_server_enabled_result_vo_list.append(MCPServerAppliedResultVo.from_mcp_server(enabled_mcp_server))
    return BaseResponse.from_success(data=mcp_server_enabled_result_vo_list)

@router.get("/list")
async def load_list(server_name: Optional[str] = None, server_tag: Optional[str] = None, mcp_server_service: McpServerCase = Depends(mcp_server_case)) -> BaseResponse:
    mcp_server_result_vo_list: List[MCPServerResultVo] = []
    for applied_mcp_server in await mcp_server_service.load_list(server_name=server_name, server_tag=server_tag):
        mcp_server_result_vo_list.append(MCPServerResultVo.from_mcp_server(applied_mcp_server))
    return BaseResponse.from_success(data=mcp_server_result_vo_list)