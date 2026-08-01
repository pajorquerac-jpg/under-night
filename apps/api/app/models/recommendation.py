from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"))
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id", ondelete="CASCADE"))
    score: Mapped[float]
    category: Mapped[str] = mapped_column(String(60))
    estimated_average_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    all_within_budget: Mapped[bool] = mapped_column(Boolean)
    average_travel_minutes: Mapped[int]
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    tradeoffs: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    plan = relationship("Plan", back_populates="recommendations")
    venue = relationship("Venue", back_populates="recommendations")
    participant_costs = relationship(
        "ParticipantCost",
        back_populates="recommendation",
        cascade="all, delete-orphan",
    )


class ParticipantCost(Base):
    __tablename__ = "participant_costs"

    id: Mapped[int] = mapped_column(primary_key=True)
    recommendation_id: Mapped[int] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE")
    )
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"))
    entry_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    consumption_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    transport_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    remaining_budget: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    within_budget: Mapped[bool] = mapped_column(Boolean)

    recommendation = relationship("Recommendation", back_populates="participant_costs")
    participant = relationship("Participant", back_populates="costs")
