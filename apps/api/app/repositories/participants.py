from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.participant import Participant
from app.schemas.participant import ParticipantCreate


def create_participant(db: Session, plan_id: int, payload: ParticipantCreate) -> Participant:
    participant = Participant(plan_id=plan_id, **payload.model_dump())
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def list_participants_for_plan(db: Session, plan_id: int) -> list[Participant]:
    return list(db.scalars(select(Participant).where(Participant.plan_id == plan_id)).all())
