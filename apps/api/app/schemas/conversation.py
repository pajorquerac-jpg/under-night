from typing import Literal

from pydantic import AliasChoices, Field, field_validator

from app.schemas.common import ApiModel

ChatRole = Literal["system", "user", "assistant"]


class ChatMessage(ApiModel):
    role: ChatRole
    content: str = Field(min_length=1, max_length=4000)


class SuggestedAction(ApiModel):
    label: str
    type: str
    payload: dict[str, object] = Field(default_factory=dict)


ConversationStage = Literal["collecting", "ready_for_recommendations"]


class ConversationState(ApiModel):
    people_count: int | None = Field(default=None, ge=1, le=50)
    budget_per_person: int | None = Field(default=None, ge=0)
    event_date: str | None = None
    origin_zones: list[str] = Field(default_factory=list)
    meeting_point: str | None = None
    outing_type: str | None = None
    music_preferences: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    stage: ConversationStage = "collecting"

    @field_validator(
        "origin_zones",
        "music_preferences",
        "restrictions",
        "missing_fields",
        mode="before",
    )
    @classmethod
    def empty_list_when_null(cls, value: object) -> object:
        return [] if value is None else value


class ExtractedConversationData(ApiModel):
    people_count: int | None = Field(default=None, ge=1, le=50)
    budget_per_person: int | None = Field(default=None, ge=0)
    event_date: str | None = None
    origin_zones: list[str] = Field(default_factory=list)
    meeting_point: str | None = None
    outing_type: str | None = None
    music_preferences: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)

    @field_validator("origin_zones", "music_preferences", "restrictions", mode="before")
    @classmethod
    def empty_list_when_null(cls, value: object) -> object:
        return [] if value is None else value


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
    state: ConversationState
    used_fallback: bool
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)
