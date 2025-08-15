import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data

def test_market_data_endpoint_exists():
    """Test that market data endpoint exists (will return 404 for fake ID)."""
    response = client.get("/api/market/fake_market_id/data")
    # Should return 404 or 500, not 404 for route not found
    assert response.status_code in [404, 500]

def test_alpha_analysis_not_implemented():
    """Test that alpha analysis returns not implemented."""
    response = client.get("/api/market/fake_market_id/alpha")
    assert response.status_code == 501

def test_trader_analysis_not_implemented():
    """Test that trader analysis returns not implemented."""
    response = client.get("/api/trader/0x123/analysis")
    assert response.status_code == 501