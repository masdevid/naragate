import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self):
        with patch("app.main.check_ollama", new_callable=AsyncMock) as mock_ollama, \
             patch("app.main.check_sectors", new_callable=AsyncMock) as mock_sectors:
            
            mock_ollama.return_value = {"status": "ok", "models": ["gemma4:12b"]}
            mock_sectors.return_value = {"status": "ok", "key_length": 64}

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "version" in data
            assert "services" in data

    @pytest.mark.asyncio
    async def test_health_reports_degraded_when_ollama_down(self):
        with patch("app.main.check_ollama", new_callable=AsyncMock) as mock_ollama, \
             patch("app.main.check_sectors", new_callable=AsyncMock) as mock_sectors:
            
            mock_ollama.return_value = {"status": "error", "error": "connection refused"}
            mock_sectors.return_value = {"status": "ok", "key_length": 64}

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/health")

            data = response.json()
            assert data["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_health_includes_config(self):
        with patch("app.main.check_ollama", new_callable=AsyncMock) as mock_ollama, \
             patch("app.main.check_sectors", new_callable=AsyncMock) as mock_sectors:
            
            mock_ollama.return_value = {"status": "ok", "models": []}
            mock_sectors.return_value = {"status": "ok", "key_length": 64}

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/health")

            data = response.json()
            assert "config" in data
            assert "credit_budget" in data["config"]
            assert "curated_stocks" in data["config"]


class TestClaimsEndpoint:
    """Tests for the claims CRUD endpoint."""

    @pytest.mark.asyncio
    async def test_list_claims_returns_array(self):
        with patch("app.api.v1.endpoints.claims.claims_store") as mock_store:
            mock_store.list_claims = AsyncMock(return_value=[])

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/claims/")

            assert response.status_code == 200
            assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_claim_returns_404_for_missing(self):
        with patch("app.api.v1.endpoints.claims.claims_store") as mock_store:
            mock_store.get_claim = AsyncMock(return_value=None)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/claims/nonexistent")

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_claim_returns_claim(self):
        with patch("app.api.v1.endpoints.claims.claims_store") as mock_store:
            mock_store.get_claim = AsyncMock(return_value={
                "claim_id": "test-123",
                "status": "completed",
                "claim": {"ticker": "BBCA"},
            })

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/claims/test-123")

            assert response.status_code == 200
            data = response.json()
            assert data["claim_id"] == "test-123"
