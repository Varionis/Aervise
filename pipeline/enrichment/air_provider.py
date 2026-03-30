from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from config import Settings
from pipeline.enrichment.http import HttpClient


SUPPORTED_POLLUTANTS = ("pm25", "no2", "o3")


@dataclass
class OpenAQProvider:
    settings: Settings
    http_client: HttpClient

    def fetch_current(self, *, lat: float, lon: float) -> dict[str, Any]:
        if not self.settings.openaq_api_key:
            raise ValueError("OPENAQ_API_KEY is required")

        headers = {"X-API-Key": self.settings.openaq_api_key}
        params = {
            "coordinates": f"{lat},{lon}",
            "radius": self.settings.openaq_radius_meters,
            "limit": self.settings.openaq_limit,
        }
        payload = self.http_client.get(f"{self.settings.openaq_api_url}/locations", headers=headers, params=params)
        locations = payload.get("results", [])
        selected_location = self._pick_best_location(locations)
        if not selected_location:
            raise ValueError(
                "OpenAQ returned no active non-mobile locations with PM2.5, NO2, or O3 in the configured radius"
            )

        latest_cutoff = self._cutoff_iso()
        latest_payload = self.http_client.get(
            f"{self.settings.openaq_api_url}/locations/{selected_location['id']}/latest",
            headers=headers,
            params={"limit": self.settings.openaq_limit, "datetime_min": latest_cutoff},
        )
        measurements = latest_payload.get("results", [])

        pollutants: dict[str, dict[str, Any] | None] = {}
        missing: list[str] = []
        timestamps: list[datetime] = []
        location_sensors = self._supported_sensor_map(selected_location)

        for parameter in SUPPORTED_POLLUTANTS:
            sensor = location_sensors.get(parameter)
            selected = self._pick_latest_measurement(parameter, measurements, sensor_id=sensor.get("id") if sensor else None)
            if not selected:
                pollutants[parameter] = None
                missing.append(parameter)
                continue

            measured_at_raw = selected.get("datetime", {}).get("utc")
            if not measured_at_raw:
                pollutants[parameter] = None
                missing.append(parameter)
                continue

            measured_at = self._parse_datetime(measured_at_raw)
            timestamps.append(measured_at)
            pollutants[parameter] = {
                "value": selected.get("value"),
                "unit": sensor.get("parameter", {}).get("units") if sensor else None,
                "measured_at_utc": measured_at_raw,
                "location_id": selected_location.get("id"),
                "location_name": selected_location.get("name"),
                "coordinates": selected.get("coordinates") or selected_location.get("coordinates"),
                "sensor_id": selected.get("sensorsId"),
                "source": "openaq",
            }

        latest_timestamp = max(timestamps) if timestamps else None
        staleness_minutes = None
        if latest_timestamp:
            staleness_minutes = round((datetime.now(UTC) - latest_timestamp).total_seconds() / 60, 2)

        completeness = (len(SUPPORTED_POLLUTANTS) - len(missing)) / len(SUPPORTED_POLLUTANTS)
        freshness_score = 1.0
        if staleness_minutes is not None:
            freshness_score = max(0.0, 1.0 - (staleness_minutes / 180.0))

        return {
            "air": pollutants,
            "meta": {
                "source": "openaq",
                "missing_pollutants": missing,
                "data_confidence": round(completeness * freshness_score, 3),
                "staleness_minutes": staleness_minutes,
                "station_count": len(locations),
                "location": {
                    "id": selected_location.get("id"),
                    "name": selected_location.get("name"),
                    "distance_meters": selected_location.get("distance"),
                    "is_mobile": selected_location.get("isMobile"),
                    "supported_parameters": sorted(location_sensors.keys()),
                },
                "search": {
                    "lat": lat,
                    "lon": lon,
                    "radius_meters": self.settings.openaq_radius_meters,
                    "active_within_minutes": self.settings.openaq_active_within_minutes,
                    "latest_cutoff_utc": latest_cutoff,
                },
            },
        }

    def _pick_best_location(self, entries: list[dict[str, Any]]) -> dict[str, Any] | None:
        eligible = []
        for location in entries:
            if location.get("isMobile"):
                continue
            supported = self._supported_sensor_map(location)
            if not supported:
                continue
            if not self._is_active_location(location, supported):
                continue
            eligible.append(location)
        if not eligible:
            return None
        return min(eligible, key=lambda item: item.get("distance") if item.get("distance") is not None else float("inf"))

    def _is_active_location(self, location: dict[str, Any], supported: dict[str, dict[str, Any]]) -> bool:
        if not supported:
            return False
        datetime_last = (location.get("datetimeLast") or {}).get("utc")
        if not datetime_last:
            return False
        cutoff = datetime.now(UTC).timestamp() - (self.settings.openaq_active_within_minutes * 60)
        return self._parse_datetime(datetime_last).timestamp() >= cutoff

    @staticmethod
    def _supported_sensor_map(location: dict[str, Any]) -> dict[str, dict[str, Any]]:
        sensors = location.get("sensors") or []
        supported: dict[str, dict[str, Any]] = {}
        for sensor in sensors:
            sensor_parameter = ((sensor.get("parameter") or {}).get("name") or "").lower()
            if sensor_parameter not in SUPPORTED_POLLUTANTS:
                continue
            if sensor_parameter not in supported:
                supported[sensor_parameter] = sensor
        return supported

    @staticmethod
    def _pick_latest_measurement(
        parameter: str,
        measurements: list[dict[str, Any]],
        *,
        sensor_id: int | None,
    ) -> dict[str, Any] | None:
        eligible = []
        for measurement in measurements:
            measurement_parameter = ((measurement.get("parameter") or {}).get("name") or "").lower()
            if measurement_parameter and measurement_parameter != parameter:
                continue
            if sensor_id is not None and measurement.get("sensorsId") != sensor_id:
                continue
            eligible.append(measurement)
        if not eligible:
            return None
        return max(eligible, key=lambda item: item.get("datetime", {}).get("utc", ""))

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)

    def _cutoff_iso(self) -> str:
        cutoff = datetime.now(UTC).timestamp() - (self.settings.openaq_active_within_minutes * 60)
        return datetime.fromtimestamp(cutoff, UTC).isoformat().replace("+00:00", "Z")
