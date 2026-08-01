from datetime import date, datetime, time

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Plan(TimestampMixin, Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    event_date: Mapped[date]
    start_time: Mapped[time]
    decision_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    preferred_zone: Mapped[str] = mapped_column(String(80))
    plan_type: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), default="draft")

    participants = relationship("Participant", back_populates="plan", cascade="all, delete-orphan")
    recommendations = relationship(
        "Recommendation",
        back_populates="plan",
        cascade="all, delete-orphan",
    )
