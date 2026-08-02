from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.common import ApiModel
from app.schemas.participant import ParticipantRead
from app.schemas.venue import VenueRead


class ParticipantCostRead(ApiModel):
    id: int
    recommendation_id: int
    participant_id: int
    entry_cost: Decimal
    consumption_cost: Decimal
    transport_cost: Decimal
    total_cost: Decimal
    remaining_budget: Decimal
    within_budget: bool
    participant: ParticipantRead


class RecommendationRead(ApiModel):
    id: int
    plan_id: int
    venue_id: int
    created_at: datetime
    score: float = Field(ge=0, le=100)
    category: str
    estimated_average_cost: Decimal
    all_within_budget: bool
    average_travel_minutes: int
    reasons: list[str]
    tradeoffs: list[str]
    venue: VenueRead
    participant_costs: list[ParticipantCostRead]
