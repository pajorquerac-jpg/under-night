from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.schemas.plan import PlanCreate


def create_plan(db: Session, payload: PlanCreate) -> Plan:
    plan = Plan(**payload.model_dump(), status="draft")
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_plan(db: Session, plan_id: int) -> Plan | None:
    return db.get(Plan, plan_id)
