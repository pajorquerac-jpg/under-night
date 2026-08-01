from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import DbSession
from app.repositories.plans import create_plan, get_plan
from app.schemas.plan import PlanCreate, PlanRead

router = APIRouter()


@router.post("", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
def create(payload: PlanCreate, db: DbSession) -> PlanRead:
    return create_plan(db, payload)


@router.get("/{plan_id}", response_model=PlanRead)
def get(plan_id: int, db: DbSession) -> PlanRead:
    plan = get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan
