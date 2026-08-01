from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DbSession
from app.repositories.venues import get_venue, list_venues
from app.schemas.venue import VenueRead

router = APIRouter()


@router.get("", response_model=list[VenueRead])
def list_all(db: DbSession) -> list[VenueRead]:
    return list_venues(db)


@router.get("/{venue_id}", response_model=VenueRead)
def get(venue_id: int, db: DbSession) -> VenueRead:
    venue = get_venue(db, venue_id)
    if venue is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")
    return venue
