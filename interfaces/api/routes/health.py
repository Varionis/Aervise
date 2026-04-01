from __future__ import annotations

from fastapi import APIRouter

from config import get_settings
from interfaces.api.schemas import HealthResponse


router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="aervise-api",
        environment=settings.environment,
        weather_provider_priority=list(settings.weather_provider_priority),
        capabilities={
            "supports_air_forecast": False,
            "supports_weather_forecast": True,
            "supports_same_day_timing": "partial",
        },
    )
