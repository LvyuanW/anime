import httpx
import pytest

from app.llm_service.llm_client.client import LLMClient
from app.llm_service.llm_client.errors import LLMClientError


def test_llm_client_parses_content_from_openai_style_response() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]},
        )
    )
    client = LLMClient(
        api_base_url="https://example.test/v1/chat/completions",
        api_key="k",
        transport=transport,
        max_retries=1,
    )
    result = client.chat_completions(model="m", messages=[{"role": "user", "content": "hi"}])
    assert result.content == "ok"


def test_llm_client_raises_on_http_error() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(401, json={"error": {"message": "no"}}))
    client = LLMClient(
        api_base_url="https://example.test/v1/chat/completions",
        api_key="k",
        transport=transport,
        max_retries=1,
    )
    with pytest.raises(LLMClientError) as e:
        client.chat_completions(model="m", messages=[{"role": "user", "content": "hi"}])
    assert e.value.status_code == 401


def test_llm_client_retries_on_5xx_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:  # noqa: ARG001
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, json={"error": {"message": "busy"}})
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    transport = httpx.MockTransport(handler)
    client = LLMClient(
        api_base_url="https://example.test/v1/chat/completions",
        api_key="k",
        transport=transport,
        max_retries=2,
    )
    result = client.chat_completions(model="m", messages=[{"role": "user", "content": "hi"}])
    assert result.content == "ok"
    assert calls["n"] == 2
