from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


class TraceRecorder:
    def __init__(self, trace_dir: Path) -> None:
        self.trace_dir = trace_dir
        self.trace_file = trace_dir / "aervise_trace.jsonl"

    def start(self, name: str, metadata: dict | None = None) -> str:
        trace_id = str(uuid4())
        self.write(
            {
                "trace_id": trace_id,
                "event": "trace_started",
                "name": name,
                "metadata": metadata or {},
            }
        )
        return trace_id

    def write(self, payload: dict) -> None:
        record = {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            **payload,
        }
        with self.trace_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=str) + "\n")
