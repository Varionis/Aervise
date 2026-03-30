from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    environment: str
    log_level: str
    log_dir: Path
    trace_dir: Path
    default_lat: float
    default_lon: float
    openaq_api_url: str
    openaq_api_key: str | None
    openaq_radius_meters: int
    openaq_limit: int
    openaq_active_within_minutes: int
    openweather_api_url: str
    openweather_api_key: str | None
    openweather_units: str
    openmeteo_api_url: str
    weather_provider_priority: tuple[str, ...]


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    log_dir = BASE_DIR / _env("AERVISE_LOG_DIR", "logs")
    trace_dir = BASE_DIR / _env("AERVISE_TRACE_DIR", "traces")
    log_dir.mkdir(parents=True, exist_ok=True)
    trace_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        environment=_env("AERVISE_ENV", "development"),
        log_level=_env("AERVISE_LOG_LEVEL", "INFO").upper(),
        log_dir=log_dir,
        trace_dir=trace_dir,
        default_lat=float(_env("AERVISE_DEFAULT_LAT", "43.6532")),
        default_lon=float(_env("AERVISE_DEFAULT_LON", "-79.3832")),
        openaq_api_url=_env("OPENAQ_API_URL", "https://api.openaq.org/v3").rstrip("/"),
        openaq_api_key=os.getenv("OPENAQ_API_KEY") or None,
        openaq_radius_meters=int(_env("OPENAQ_RADIUS_METERS", "25000")),
        openaq_limit=int(_env("OPENAQ_LIMIT", "100")),
        openaq_active_within_minutes=int(_env("OPENAQ_ACTIVE_WITHIN_MINUTES", "360")),
        openweather_api_url=_env("OPENWEATHER_API_URL", "https://api.openweathermap.org/data/2.5").rstrip("/"),
        openweather_api_key=os.getenv("OPENWEATHER_API_KEY") or None,
        openweather_units=_env("OPENWEATHER_UNITS", "metric"),
        openmeteo_api_url=_env("OPENMETEO_API_URL", "https://api.open-meteo.com/v1").rstrip("/"),
        weather_provider_priority=tuple(
            item.strip().lower()
            for item in _env("WEATHER_PROVIDER_PRIORITY", "openweather,openmeteo").split(",")
            if item.strip()
        ),
    )
