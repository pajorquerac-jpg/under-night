from datetime import time
from decimal import Decimal
from typing import Any

from pydantic import Field

from app.schemas.common import ApiModel, Timestamped


class ParticipantBase(ApiModel):
    name: str = Field(min_length=2, max_length=120)
    budget: Decimal = Field(gt=0)
    max_entry_price: Decimal = Field(ge=0)
    origin_zone: str = Field(min_length=2, max_length=80)
    transport_type: str = Field(pattern="^(walking|public_transport|rideshare|car)$")
    consumption_level: str = Field(pattern="^(low|medium|high|custom)$")
    max_return_time: time | None = None
    preferences: dict[str, Any] = Field(default_factory=dict)
    restrictions: dict[str, Any] = Field(default_factory=dict)


class ParticipantCreate(ParticipantBase):
    pass


class ParticipantRead(ParticipantBase, Timestamped):
    id: int
    plan_id: int
