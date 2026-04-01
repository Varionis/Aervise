# Stage 2 Environment Schema

This document locks the Stage 2 context enrichment output contract.

Stage 2 owns:

- provider fetch
- fallback handling
- normalization
- source confidence
- forecast capability flags

It must not perform policy logic.

---

## Canonical Environment State

```json
{
  "air_quality": {
    "pm25": {
      "value": 12.0,
      "unit": "ug/m3",
      "measured_at_utc": "2026-03-29T22:00:00Z",
      "source": "openaq"
    },
    "no2": {
      "value": 0.008,
      "unit": "ppm",
      "measured_at_utc": "2026-03-29T22:00:00Z",
      "source": "openaq"
    },
    "o3": {
      "value": 0.043,
      "unit": "ppm",
      "measured_at_utc": "2026-03-29T22:00:00Z",
      "source": "openaq"
    },
    "confidence": 0.711,
    "staleness_minutes": 52.01
  },
  "weather": {
    "temperature_c": 8.5,
    "humidity": 47,
    "wind_speed": 2.96,
    "measured_at_utc": "2026-03-29T22:45:00+00:00",
    "source": "openmeteo",
    "confidence": 0.95
  },
  "forecast_hours": [],
  "time_context": {
    "snapshot_timestamp_utc": "2026-03-29T22:52:01.078223+00:00",
    "forecast_window_available": true
  },
  "forecast_capabilities": {
    "supports_air_forecast": false,
    "supports_weather_forecast": true,
    "supports_same_day_timing": "partial"
  },
  "data_quality": {
    "overall_confidence": 0.831,
    "aq_source_confidence": 0.711,
    "weather_source_confidence": 0.95,
    "missing_fields": []
  },
  "location": {
    "lat": 43.6532,
    "lon": -79.3832
  }
}
```

---

## Design Notes

- `air_quality` includes only the MVP pollutants: `pm25`, `no2`, `o3`
- `weather` includes only the MVP weather fields: `temperature_c`, `humidity`, `wind_speed`
- `forecast_hours` is weather-only for now
- `forecast_capabilities` must explicitly state that AQ forecast is not available
- `data_quality` must remain explicit even when data looks good

---

## Implementation Source

The Stage 2 contract is implemented in:

- [contracts/environment_schema.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/contracts/environment_schema.py#L1)
- [pipeline/enrichment/service.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/pipeline/enrichment/service.py#L1)
- [pipeline/enrichment/normalization.py](/d:/Users/arnav/Documents/Github_Repos/Aervise/pipeline/enrichment/normalization.py#L1)
