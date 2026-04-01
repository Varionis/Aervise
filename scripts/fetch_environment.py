from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import get_settings
from observability.logger import configure_logging, get_logger
from observability.trace_schema import TraceRecorder
from pipeline.enrichment.air_provider import OpenAQProvider
from pipeline.enrichment.http import HttpClient
from pipeline.enrichment.normalization import EnvironmentAggregator
from pipeline.enrichment.openmeteo_provider import OpenMeteoProvider
from pipeline.enrichment.weather_provider import OpenWeatherProvider
from pipeline.enrichment.weather_service import WeatherService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch normalized environmental data for Aervise.")
    parser.add_argument("--lat", type=float, help="Latitude override.")
    parser.add_argument("--lon", type=float, help="Longitude override.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional file path to write the normalized environment snapshot JSON.",
    )
    return parser.parse_args()


def main() -> int:
    settings = get_settings()
    configure_logging(settings.log_dir, settings.log_level)
    logger = get_logger("aervise.fetch_environment")
    trace = TraceRecorder(settings.trace_dir)
    args = parse_args()

    lat = args.lat if args.lat is not None else settings.default_lat
    lon = args.lon if args.lon is not None else settings.default_lon

    trace_id = trace.start("fetch_environment", {"lat": lat, "lon": lon})
    logger.info(
        "Starting environment fetch",
        extra={"extra_payload": {"trace_id": trace_id, "lat": lat, "lon": lon}},
    )

    try:
        http_client = HttpClient()
        aggregator = EnvironmentAggregator(
            settings=settings,
            air_provider=OpenAQProvider(settings=settings, http_client=http_client),
            weather_service=WeatherService(
                settings=settings,
                openweather_provider=OpenWeatherProvider(settings=settings, http_client=http_client),
                openmeteo_provider=OpenMeteoProvider(settings=settings, http_client=http_client),
            ),
        )
        snapshot = aggregator.fetch_snapshot(lat=lat, lon=lon)
        trace.write(
            {
                "trace_id": trace_id,
                "event": "snapshot_created",
                "snapshot_meta": snapshot["meta"],
                "weather_summary": snapshot["environment"]["weather"],
                "air_summary": snapshot["environment"]["air"],
            }
        )

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        else:
            print(json.dumps(snapshot, indent=2))

        logger.info(
            "Environment fetch completed",
            extra={
                "extra_payload": {
                    "trace_id": trace_id,
                    "data_confidence": snapshot["meta"]["data_confidence"],
                }
            },
        )
        return 0
    except Exception as exc:
        trace.write({"trace_id": trace_id, "event": "fetch_failed", "error": str(exc)})
        logger.exception(
            "Environment fetch failed",
            extra={"extra_payload": {"trace_id": trace_id, "error": str(exc)}},
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
