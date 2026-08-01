from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


Money = Decimal


class ErrorResponse(BaseModel):
    detail: str


class Timestamped(ApiModel):
    created_at: datetime
    updated_at: datetime
