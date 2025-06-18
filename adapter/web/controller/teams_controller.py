from fastapi import APIRouter, Depends

from adapter.web.vo.base_response import BaseResponse
from adapter.web.vo.teams_vo import TeamsVo
from common.core.container.container import get_container
from application.port.inbound.teams_case import TeamsCase

router = APIRouter(prefix="/api/teams", tags=["TEAMS"])

def team_case() -> TeamsCase:
    return get_container().get(TeamsCase)

@router.post("/chat")
async def chat(teams_vo: TeamsVo, teams_service: TeamsCase = Depends(team_case)) -> BaseResponse:
    conversation_id, dialog_segment_id = await teams_service.on_message(
        client_id=teams_vo.client_id,
        generator_id=teams_vo.generator_id,
        conversation_id=teams_vo.conversation_id,
        content=teams_vo.query
    )
    return BaseResponse.from_success(
        data={"conversation_id": conversation_id, "dialog_segment_id": dialog_segment_id}
    )
