from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str
    weather_provider_priority: list[str]
    capabilities: dict[str, Any]
