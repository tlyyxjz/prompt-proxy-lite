"""Smoke tests for PromptProxy Lite."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import pytest
from httpx import ASGITransport, AsyncClient

os.environ["UPSTREAM_BASE_URL"] = "http://mock-upstream.invalid/v1"
os.environ["UPSTREAM_API_KEY"] = "sk-mock"
os.environ["CLIENT_API_KEYS"] = "sk-test-key-one,sk-test-key-two"

from app.main import app  # noqa: E402
from app.config import settings  # noqa: E402


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealth:
    @pytest.mark.asyncio
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestAuth:
    @pytest.mark.asyncio
    async def test_missing_auth_rejected(self, client):
        resp = await client.post(
            "/v1/chat/completions",
            json={"model": "deepseek-chat", "messages": []},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_key_rejected(self, client):
        resp = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": "Bearer wrong-key"},
            json={"model": "deepseek-chat", "messages": []},
        )
        assert resp.status_code == 401


class TestPromptInjection:
    def test_system_prompt_prepend(self):
        from app.proxy import _inject_system_prompt
        messages = [{"role": "user", "content": "hi"}]
        result = _inject_system_prompt(messages)
        assert result[0]["role"] == "system"
        assert "concise" in result[0]["content"].lower()
        assert result[1] == messages[0]

    def test_existing_system_prompt_merged(self):
        from app.proxy import _inject_system_prompt
        messages = [
            {"role": "system", "content": "Be terse."},
            {"role": "user", "content": "hi"},
        ]
        result = _inject_system_prompt(messages)
        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert "concise" in result[0]["content"].lower()
        assert "terse" in result[0]["content"]


class TestConfig:
    def test_client_keys_parsed(self):
        keys = settings.client_keys
        assert "sk-test-key-one" in keys
        assert "sk-test-key-two" in keys
        assert len(keys) == 2
