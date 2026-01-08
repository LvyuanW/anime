from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LLMClientError(Exception):
    message: str
    status_code: int | None = None
    response_json: dict[str, Any] | None = None

    def __str__(self) -> str:
        if self.status_code is None:
            return self.message
        return f"{self.message} (status_code={self.status_code})"

