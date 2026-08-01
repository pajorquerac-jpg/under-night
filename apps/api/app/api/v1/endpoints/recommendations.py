from fastapi import APIRouter

from app.api.dependencies import DbSession
from app.repositories.recommendations import list_for_plan
from app.schemas.recommendation import RecommendationRead
from app.services.recommendations import generate_recommendations

router = APIRouter()


@router.post("/{plan_id}/recommendations", response_model=list[RecommendationRead])
def create(plan_id: int, db: DbSession) -> list[RecommendationRead]:
    return generate_recommendations(db, plan_id)


@router.get("/{plan_id}/recommendations", response_model=list[RecommendationRead])
def list_existing(plan_id: int, db: DbSession) -> list[RecommendationRead]:
    return list_for_plan(db, plan_id)
