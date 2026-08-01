from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.venue import Venue


def list_venues(db: Session) -> list[Venue]:
    return list(db.scalars(select(Venue).order_by(Venue.name)).all())


def get_venue(db: Session, venue_id: int) -> Venue | None:
    return db.get(Venue, venue_id)
