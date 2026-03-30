from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from contracts.intent_schema import InteractionLocation, RequestFieldName


class DataSourceName(str, Enum):
    OPENAQ = "openaq"
    WEATHER_PROVIDER = "weather_provider"


class ContextEnrichmentStatus(str, Enum):
    READY_TO_FETCH = "ready_to_fetch"
    BLOCKED = "blocked"


class ForecastSupport(BaseModel):
    air: bool
    weather: bool


class ContextEnrichmentPreview(BaseModel):
    status: ContextEnrichmentStatus
    required_sources: list[DataSourceName]
    location: InteractionLocation
    supports_forecast: ForecastSupport
    missing_requirements: list[RequestFieldName] = Field(default_factory=list)
    next_stage: Literal["context_enrichment"]


class PollutantReading(BaseModel):
    value: float | None = None
    unit: str | None = None
    measured_at_utc: str | None = None
    source: str | None = None


class AirQualityState(BaseModel):
    pm25: PollutantReading | None = None
    no2: PollutantReading | None = None
    o3: PollutantReading | None = None
    confidence: float | None = None
    staleness_minutes: float | None = None


class WeatherState(BaseModel):
    temperature_c: float | None = None
    humidity: float | None = None
    wind_speed: float | None = None
    measured_at_utc: str | None = None
    source: str | None = None
    confidence: float | None = None


class ForecastHour(BaseModel):
    time: str | None = None
    temperature_c: float | None = None
    humidity: float | None = None
    wind_speed: float | None = None


class ForecastCapabilities(BaseModel):
    supports_air_forecast: bool
    supports_weather_forecast: bool
    supports_same_day_timing: Literal["none", "partial", "full"]


class DataQualityState(BaseModel):
    overall_confidence: float | None = None
    aq_source_confidence: float | None = None
    weather_source_confidence: float | None = None
    missing_fields: list[str] = Field(default_factory=list)


class EnvironmentState(BaseModel):
    air_quality: AirQualityState
    weather: WeatherState
    forecast_hours: list[ForecastHour] = Field(default_factory=list)
    time_context: dict
    forecast_capabilities: ForecastCapabilities
    data_quality: DataQualityState
    location: InteractionLocation


class EnvironmentEnrichmentResponse(BaseModel):
    entry_point: dict
    intent_recognition: dict
    environment_state: EnvironmentState
