from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.llm_service.llm_client.errors import LLMClientError
from app.llm_service.llm_client.models import ChatCompletionResult


def _extract_first_content(response_json: dict[str, Any]) -> str | None:
    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0]
    if not isinstance(first, dict):
        return None
    message = first.get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if content is None:
        return None
    return str(content)


def _is_retryable_status(status_code: int) -> bool:
    return status_code in {408, 409, 429} or 500 <= status_code <= 599


class LLMClient:
    def __init__(
        self,
        *,
        api_base_url: str,
        api_key: str,
        timeout_s: float = 30.0,
        max_retries: int = 3,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._api_base_url = api_base_url
        self._api_key = api_key
        self._timeout_s = timeout_s
        self._max_retries = max_retries
        self._transport = transport

    def _build_http_client(self) -> httpx.Client:
        return httpx.Client(timeout=self._timeout_s, transport=self._transport)

    def _raise_for_response(self, response: httpx.Response) -> None:
        if 200 <= response.status_code <= 299:
            return
        response_json: dict[str, Any] | None
        try:
            payload = response.json()
            response_json = payload if isinstance(payload, dict) else {"raw": payload}
        except Exception:
            response_json = None
        message = "LLM request failed"
        raise LLMClientError(message=message, status_code=response.status_code, response_json=response_json)

    def _should_retry(self, e: LLMClientError) -> bool:
        if e.status_code is None:
            return False
        return _is_retryable_status(e.status_code)

    def _make_retry_decorator(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return retry(
            reraise=True,
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential_jitter(initial=0.5, max=8.0),
            retry=retry_if_exception_type(LLMClientError),
        )

    def chat_completions(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        extra_body: dict[str, Any] | None = None,
    ) -> ChatCompletionResult:
        decorator = self._make_retry_decorator()

        @decorator
        def _call() -> ChatCompletionResult:
            body: dict[str, Any] = {"model": model, "messages": messages}
            if temperature is not None:
                body["temperature"] = temperature
            if max_tokens is not None:
                body["max_tokens"] = max_tokens
            if extra_body:
                body.update(extra_body)

            headers = {"Authorization": f"Bearer {self._api_key}"}
            with self._build_http_client() as client:
                try:
                    response = client.post(self._api_base_url, json=body, headers=headers)
                except httpx.TimeoutException as e:
                    raise LLMClientError(message="LLM request timed out") from e
                except httpx.RequestError as e:
                    raise LLMClientError(message="LLM request failed") from e

            try:
                self._raise_for_response(response)
            except LLMClientError as e:
                if self._should_retry(e):
                    raise
                raise

            payload = response.json()
            if not isinstance(payload, dict):
                raise LLMClientError(message="LLM response is not a JSON object", status_code=response.status_code)

            return ChatCompletionResult(response_json=payload, content=_extract_first_content(payload))

        return cast(ChatCompletionResult, _call())
