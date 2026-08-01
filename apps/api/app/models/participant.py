from datetime import time
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Participant(TimestampMixin, Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    budget: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    max_entry_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    origin_zone: Mapped[str] = mapped_column(String(80))
    transport_type: Mapped[str] = mapped_column(String(40))
    consumption_level: Mapped[str] = mapped_column(String(40))
    max_return_time: Mapped[time | None]
    preferences: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    restrictions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    plan = relationship("Plan", back_populates="participants")
    costs = relationship("ParticipantCost", back_populates="participant")
