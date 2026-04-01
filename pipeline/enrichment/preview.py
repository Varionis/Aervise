from __future__ import annotations

from dataclasses import dataclass

from contracts.environment_schema import ContextEnrichmentStatus, DataSourceName
from contracts.intent_schema import ActivityType, RequestFieldName


@dataclass
class EnrichmentPreviewService:
    def preview(self, *, entry_point: dict, intent_recognition: dict) -> dict:
        missing_requirements = []
        if intent_recognition["activity"] == ActivityType.UNKNOWN:
            missing_requirements.append(RequestFieldName.ACTIVITY)
        if entry_point["location"].get("lat") is None or entry_point["location"].get("lon") is None:
            missing_requirements.append(RequestFieldName.LOCATION)

        ready = not missing_requirements
        return {
            "status": ContextEnrichmentStatus.READY_TO_FETCH if ready else ContextEnrichmentStatus.BLOCKED,
            "required_sources": [DataSourceName.OPENAQ, DataSourceName.WEATHER_PROVIDER],
            "location": entry_point["location"],
            "supports_forecast": {
                "air": False,
                "weather": True,
            },
            "missing_requirements": missing_requirements,
            "next_stage": "context_enrichment",
        }
