from __future__ import annotations

from functools import lru_cache
from typing import Any
from uuid import uuid4

from config import get_settings
from observability.logger import get_logger
from observability.trace_schema import TraceRecorder


LOGGER = get_logger("aervise.observability")


@lru_cache(maxsize=1)
def get_trace_recorder() -> TraceRecorder:
    return TraceRecorder(get_settings().trace_dir)


def begin_trace(*, trace_id: str | None, name: str, metadata: dict[str, Any] | None = None) -> str:
    recorder = get_trace_recorder()
    if trace_id:
        recorder.write(
            {
                "trace_id": trace_id,
                "event": "trace_continued",
                "name": name,
                "metadata": metadata or {},
            }
        )
        return trace_id
    return recorder.start(name=name, metadata=metadata or {})


def write_trace(*, trace_id: str, event: str, payload: dict[str, Any] | None = None) -> None:
    get_trace_recorder().write(
        {
            "trace_id": trace_id,
            "event": event,
            **(payload or {}),
        }
    )


def log_info(message: str, *, trace_id: str, **context: Any) -> None:
    LOGGER.info(message, extra={"extra_payload": {"trace_id": trace_id, **context}})


def log_error(message: str, *, trace_id: str, **context: Any) -> None:
    LOGGER.error(message, extra={"extra_payload": {"trace_id": trace_id, **context}})


def new_trace_id() -> str:
    return str(uuid4())
