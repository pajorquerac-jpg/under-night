from fastapi import APIRouter

from app.api.dependencies import DbSession
from app.schemas.conversation import AgentChatRequest, AgentChatResponse
from app.services.conversation_agent import answer_chat

router = APIRouter()


def _health_response() -> dict[str, str]:
    return {"status": "ok", "service": "undernight-agent"}


@router.get("/health")
def health() -> dict[str, str]:
    return _health_response()


@router.get("/chat/health")
def chat_health() -> dict[str, str]:
    return _health_response()


@router.post("/chat", response_model=AgentChatResponse)
async def chat(payload: AgentChatRequest, db: DbSession) -> AgentChatResponse:
    return await answer_chat(db, payload)
