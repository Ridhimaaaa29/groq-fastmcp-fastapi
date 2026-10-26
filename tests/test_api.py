import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "langfuse" in data


@pytest.mark.asyncio
async def test_local_ask_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/ask/local", json={"question": "What is 40 + 2?"})
        assert response.status_code == 200
        data = response.json()
        assert "42" in data["answer"]
