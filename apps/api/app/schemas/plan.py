from datetime import date, datetime, time

from pydantic import Field

from app.schemas.common import ApiModel, Timestamped


class PlanBase(ApiModel):
    name: str = Field(min_length=2, max_length=120)
    event_date: date
    start_time: time
    decision_deadline: datetime
    preferred_zone: str = Field(min_length=2, max_length=80)
    plan_type: str = Field(min_length=2, max_length=80)


class PlanCreate(PlanBase):
    pass


class PlanRead(PlanBase, Timestamped):
    id: int
    status: str
