from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChatCompletionResult:
    response_json: dict[str, Any]
    content: str | None

