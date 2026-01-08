from __future__ import annotations

import json
import re
from typing import Any

from app.llm_service.providers.base import LLMProvider

_DIALOGUE_SPEAKER_RE = re.compile(r"^\s*([^：]{1,12})：")


class MockProvider(LLMProvider):
    name = "mock"

    def extract_candidates(self, *, prompt: str, normalized_chunk_json: str) -> str:
        data = json.loads(normalized_chunk_json)
        candidates: dict[tuple[str, str], dict[str, Any]] = {}

        for row in data:
            if not isinstance(row, dict):
                continue
            text = str(row.get("text") or "")
            row_type = str(row.get("type") or "")

            if row_type == "dialogue":
                m = _DIALOGUE_SPEAKER_RE.match(text)
                if not m:
                    continue
                raw_name = m.group(1).strip()
                if not raw_name:
                    continue
                candidates.setdefault(
                    (raw_name, "person"),
                    {"raw_name": raw_name, "entity_type": "person", "confidence": 0.6},
                )
            elif row_type == "scene_header":
                raw_name = text.strip()
                if not raw_name:
                    continue
                candidates.setdefault(
                    (raw_name, "scene"),
                    {"raw_name": raw_name, "entity_type": "scene", "confidence": 0.5},
                )

        return json.dumps({"candidates": list(candidates.values())}, ensure_ascii=False)
