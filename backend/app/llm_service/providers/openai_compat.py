from __future__ import annotations

import json

from app.core.config import settings
from app.llm_service.llm_client.client import LLMClient
from app.llm_service.providers.base import LLMProvider


class OpenAICompatProvider(LLMProvider):
    name = "gpt"

    def __init__(self) -> None:
        if not settings.GPT_API_BASE_URL or not settings.GPT_MODEL or not settings.GPT_API_KEY:
            raise ValueError("GPT configuration is missing")
        self._client = LLMClient(
            api_base_url=settings.GPT_API_BASE_URL,
            api_key=settings.GPT_API_KEY.get_secret_value(),
        )
        self._model = settings.GPT_MODEL

    def extract_candidates(self, *, prompt: str, normalized_chunk_json: str) -> str:
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": normalized_chunk_json},
        ]
        result = self._client.chat_completions(
            model=self._model,
            messages=messages,
            temperature=0,
        )
        content = result.content
        if content is None:
            raise ValueError("LLM returned empty content")
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("LLM output must be a JSON object")
        return json.dumps(parsed, ensure_ascii=False)
