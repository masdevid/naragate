import pytest
import os
from unittest.mock import AsyncMock, MagicMock

# Set test environment before importing app
os.environ["SECTORS_API_KEY"] = "test_key_123456789012345678901234567890123456789012345678901234567890"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
os.environ["OLLAMA_MODEL"] = "gemma4:12b"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["PI_AGENT_URL"] = "http://localhost:3000"
os.environ["DATABASE_URL"] = "sqlite:///./test_data/naragate.db"


@pytest.fixture
def mock_sectors_response():
    """Sample Sectors API response."""
    return {
        "symbol": "BBCA",
        "company_name": "Bank Central Asia",
        "valuation": {
            "pe_ratio": 25.5,
            "pb_ratio": 3.2,
            "ps_ratio": 8.1,
            "pcf_ratio": 18.3,
        },
        "financials": {
            "revenue": 120_000_000_000,
            "net_income": 45_000_000_000,
            "gross_margin": 0.62,
            "net_margin": 0.375,
        },
        "market": {
            "price": 9_500,
            "volume": 15_000_000,
            "market_cap": 1_140_000_000_000,
        },
    }


@pytest.fixture
def sample_narrative():
    """Sample Indonesian market narrative."""
    return "BBCA labanya jeblok, PE-nya masih mahal banget, mending pindah ke BBRI"


@pytest.fixture
def sample_claims():
    """Sample parsed claims."""
    return [
        {
            "ticker": "BBCA",
            "category": "fundamental",
            "assertion": "profits declined",
            "direction": "negative",
            "confidence": 0.9,
        },
        {
            "ticker": "BBCA",
            "category": "valuation",
            "assertion": "PE ratio is expensive",
            "direction": "negative",
            "confidence": 0.85,
        },
        {
            "ticker": "BBRI",
            "category": "peer_comparison",
            "assertion": "better than BBCA",
            "direction": "positive",
            "confidence": 0.7,
        },
    ]
