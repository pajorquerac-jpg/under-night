from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DbSession
from app.repositories.participants import create_participant, list_participants_for_plan
from app.repositories.plans import get_plan
from app.schemas.participant import ParticipantCreate, ParticipantRead

router = APIRouter()


@router.post(
    "/{plan_id}/participants",
    response_model=ParticipantRead,
    status_code=status.HTTP_201_CREATED,
)
def create(plan_id: int, payload: ParticipantCreate, db: DbSession) -> ParticipantRead:
    if get_plan(db, plan_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return create_participant(db, plan_id, payload)


@router.get("/{plan_id}/participants", response_model=list[ParticipantRead])
def list_for_plan(plan_id: int, db: DbSession) -> list[ParticipantRead]:
    if get_plan(db, plan_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return list_participants_for_plan(db, plan_id)
