from datetime import datetime, time
from decimal import Decimal
from typing import Any

from pydantic import Field

from app.schemas.common import ApiModel, Timestamped


class VenueBase(ApiModel):
    name: str
    zone: str
    latitude: float
    longitude: float
    entry_price: Decimal = Field(ge=0)
    average_drink_price: Decimal = Field(ge=0)
    opening_time: time
    closing_time: time
    minimum_age: int = Field(ge=18)
    music_tags: list[str] = Field(default_factory=list)
    ambience_tags: list[str] = Field(default_factory=list)
    features: dict[str, Any] = Field(default_factory=dict)
    data_updated_at: datetime


class VenueRead(VenueBase, Timestamped):
    id: int
