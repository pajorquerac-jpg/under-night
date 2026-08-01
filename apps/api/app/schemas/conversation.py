from typing import Literal

from pydantic import AliasChoices, Field

from app.schemas.common import ApiModel

ChatRole = Literal["system", "user", "assistant"]


class ChatMessage(ApiModel):
    role: ChatRole
    content: str = Field(min_length=1, max_length=4000)


class SuggestedAction(ApiModel):
    label: str
    type: str
    payload: dict[str, object] = Field(default_factory=dict)


class AgentChatRequest(ApiModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = Field(default=None, max_length=120)
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=20,
        validation_alias=AliasChoices("history", "conversation"),
    )
    plan_id: int | None = None
    use_llm: bool = True


class AgentChatResponse(ApiModel):
    conversation_id: str
    reply: str
    provider: str
    model: str | None = None
    used_fallback: bool
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)
