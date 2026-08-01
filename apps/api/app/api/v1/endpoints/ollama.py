# app/api/v1/endpoints/ollama.py

import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def ollama_health() -> dict[str, object]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{settings.ollama_base_url}/api/tags"
            )
            response.raise_for_status()

        return {
            "status": "ok",
            "provider": "ollama",
            "model": settings.ollama_model,
            "available_models": response.json().get("models", []),
        }

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail="Ollama no está disponible desde el backend.",
        ) from exc
