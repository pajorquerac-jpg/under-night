from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.recommendation import ParticipantCost, Recommendation
from app.recommendation.engine import rank_venues
from app.repositories.participants import list_participants_for_plan
from app.repositories.plans import get_plan
from app.repositories.recommendations import clear_for_plan, list_for_plan
from app.repositories.venues import list_venues


def generate_recommendations(db: Session, plan_id: int) -> list[Recommendation]:
    if get_plan(db, plan_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    participants = list_participants_for_plan(db, plan_id)
    venues = list_venues(db)
    if not participants:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="At least one participant is required to generate recommendations",
        )

    clear_for_plan(db, plan_id)
    for estimate in rank_venues(participants, venues):
        recommendation = Recommendation(
            plan_id=plan_id,
            venue_id=estimate.venue.id,
            score=estimate.score,
            category=estimate.category,
            estimated_average_cost=estimate.estimated_average_cost,
            all_within_budget=estimate.all_within_budget,
            average_travel_minutes=estimate.average_travel_minutes,
            reasons=estimate.reasons,
            tradeoffs=estimate.tradeoffs,
        )
        db.add(recommendation)
        db.flush()
        for cost in estimate.participant_costs:
            db.add(ParticipantCost(recommendation_id=recommendation.id, **cost.__dict__))
    db.commit()
    return list_for_plan(db, plan_id)
