from __future__ import annotations

from typing import Protocol


class LLMProvider(Protocol):
    name: str

    def extract_candidates(self, *, prompt: str, normalized_chunk_json: str) -> str: ...

