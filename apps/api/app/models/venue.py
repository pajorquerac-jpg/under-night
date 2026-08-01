from datetime import datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Venue(TimestampMixin, Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(140))
    zone: Mapped[str] = mapped_column(String(80))
    latitude: Mapped[float]
    longitude: Mapped[float]
    entry_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    average_drink_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    opening_time: Mapped[time]
    closing_time: Mapped[time]
    minimum_age: Mapped[int]
    music_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    ambience_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    features: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    data_updated_at: Mapped[datetime]

    recommendations = relationship("Recommendation", back_populates="venue")
