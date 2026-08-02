from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.recommendation import ParticipantCost, Recommendation


def clear_for_plan(db: Session, plan_id: int) -> None:
    db.execute(delete(Recommendation).where(Recommendation.plan_id == plan_id))
    db.commit()


def list_for_plan(db: Session, plan_id: int) -> list[Recommendation]:
    statement = (
        select(Recommendation)
        .where(Recommendation.plan_id == plan_id)
        .options(
            selectinload(Recommendation.venue),
            selectinload(Recommendation.participant_costs).selectinload(
                ParticipantCost.participant
            ),
        )
        .order_by(Recommendation.score.desc())
    )
    return list(db.scalars(statement).all())
