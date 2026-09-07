import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app
from app.models.schemas import PipelineEvent


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


class TestEvaluateEndpoint:
    """Tests for the streaming evaluate endpoint."""

    @pytest.mark.asyncio
    async def test_evaluate_streams_filings_evidence(self):
        from datetime import datetime

        async def fake_pipeline(narrative):
            yield PipelineEvent(
                event_type="evidence_ready",
                claim_id="test-claim-id",
                data={
                    "filings": {
                        "claim_ticker": "BBCA",
                        "category": "insider_trading",
                        "filings": [
                            {"date": "2025-08-15", "insider_name": "Budi", "insider_title": "Direktur", "transaction_type": "sell", "shares": 50000, "price": 9500, "total_value": 475_000_000}
                        ],
                        "summary": "Terdapat 1 transaksi insider: 0 pembelian, 1 penjualan. Pola: net_selling.",
                        "recent_bias": "net_selling",
                        "evidence_freshness": "2024-01-01",
                        "cache_hit": False,
                    }
                },
                timestamp=datetime.now().isoformat(),
            )

        with patch("app.api.v1.endpoints.stream.missing_setup_items", return_value=[]), \
             patch("app.api.v1.endpoints.stream.run_pipeline", new=fake_pipeline):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                async with client.stream(
                    "POST",
                    "/api/v1/stream/evaluate",
                    json={"narrative": "BBCA insiders are dumping shares"},
                ) as response:
                    assert response.status_code == 200
                    body = ""
                    async for chunk in response.aiter_text():
                        body += chunk

            assert "evidence_ready" in body
            assert "filings" in body
            assert "net_selling" in body

    @pytest.mark.asyncio
    async def test_evaluate_returns_409_when_setup_incomplete(self):
        with patch("app.api.v1.endpoints.stream.missing_setup_items", return_value=["sectors_api_key"]):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/stream/evaluate",
                    json={"narrative": "BBCA insiders are dumping shares"},
                )

            assert response.status_code == 409
            assert response.json()["detail"]["code"] == "setup_incomplete"
