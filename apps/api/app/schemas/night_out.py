from decimal import Decimal
from typing import Literal

from pydantic import Field

from app.schemas.common import ApiModel


class FriendQuestionnaire(ApiModel):
    name: str = Field(min_length=1, max_length=120)
    budget: Decimal = Field(gt=0)
    max_entry_price: Decimal = Field(ge=0)
    outing_type: str = Field(min_length=2, max_length=80)
    origin_zone: str = Field(min_length=2, max_length=80)
    transport_type: Literal["walking", "public_transport", "rideshare", "car"]
    consumption_level: Literal["low", "medium", "high", "custom"]


class NightOutQuestionnaire(ApiModel):
    friend_count: int = Field(ge=1, le=8)
    group_mode: Literal["together", "individual"]
    plan_name: str = Field(min_length=2, max_length=120)
    preferred_zone: str = Field(min_length=2, max_length=80)
    friends: list[FriendQuestionnaire] = Field(min_length=1, max_length=8)
