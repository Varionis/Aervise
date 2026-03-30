from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class HttpClient:
    timeout_seconds: int = 20

    def get(self, url: str, *, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None) -> dict:
        response = requests.get(url, headers=headers, params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()
