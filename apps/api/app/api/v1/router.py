from fastapi import APIRouter

from app.api.v1.endpoints import (
    agent,
    health,
    night_out,
    ollama,
    participants,
    plans,
    recommendations,
    venues,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(ollama.router, prefix="/ollama", tags=["ollama"])
api_router.include_router(venues.router, prefix="/venues", tags=["venues"])
api_router.include_router(night_out.router, prefix="/night-out", tags=["night-out"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(participants.router, prefix="/plans", tags=["participants"])
api_router.include_router(recommendations.router, prefix="/plans", tags=["recommendations"])
