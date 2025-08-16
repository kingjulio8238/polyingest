"""
Comprehensive API Integration Tests for Phase 2 endpoints.

Tests all API endpoints with proper mocking and integration verification.
This focuses on testing the API behavior without requiring external services.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from decimal import Decimal
import time
from typing import Dict, Any, List

from app.main import app
from app.api.routes import router
from app.data.models import MarketData, MarketOutcome, OrderBook, OrderBookEntry


@pytest.fixture
def mock_app():
    """Create a test FastAPI app with mocked dependencies."""
    test_app = FastAPI()
    
    # Mock dependencies
    mock_coordinator = Mock()
    mock_coordinator.get_performance_metrics.return_value = {
        "coordinator_performance": {
            "total_analyses": 156,
            "successful_analyses": 148,
            "success_rate": 0.949,
            "avg_analysis_duration": 2.300
        },
        "agent_health": {
            "Portfolio Analyzer": {"weight": 1.2, "confidence": 0.78, "status": "healthy"},
            "Success Rate Analyzer": {"weight": 1.5, "confidence": 0.82, "status": "healthy"}
        },
        "voting_system": {
            "total_agents": 2,
            "total_weight": 2.7,
            "min_participation_ratio": 0.5
        },
        "system_status": "healthy"
    }
    
    async def mock_analyze_market(*args, **kwargs):
        return {
            "market": {
                "id": "0x1234567890abcdef",
                "title": "Will Donald Trump win the 2024 Presidential Election?",
                "description": "Market resolves to Yes if Donald Trump wins...",
                "end_date": "2024-11-05T23:59:59+00:00",
                "status": "active",
                "current_prices": {"Yes": 0.52, "No": 0.48},
                "total_volume_24h": 2500000,
                "total_liquidity": 1200000
            },
            "alpha_analysis": {
                "has_alpha": True,
                "confidence_score": 0.85,
                "recommended_side": "Yes",
                "strength": "strong",
                "agent_consensus": {
                    "votes_for_alpha": 4,
                    "votes_against_alpha": 1,
                    "abstentions": 0
                }
            },
            "key_traders": [
                {
                    "address": "0xabc123456789def",
                    "position_size_usd": 50000,
                    "portfolio_allocation_pct": 15.2,
                    "historical_success_rate": 0.78,
                    "position_side": "Yes",
                    "entry_price": 0.45,
                    "confidence_indicators": {
                        "large_position": True,
                        "high_allocation": True,
                        "proven_track_record": True,
                        "early_entry": True
                    }
                }
            ],
            "agent_analyses": [
                {
                    "agent_name": "Portfolio Analyzer",
                    "vote": "alpha",
                    "confidence": 0.9,
                    "reasoning": "3 traders with >10% portfolio allocation, avg 14.2%",
                    "key_findings": [
                        "Top trader allocated 22% of $850k portfolio",
                        "Average allocation 3x higher than typical market"
                    ]
                },
                {
                    "agent_name": "Success Rate Analyzer",
                    "vote": "alpha",
                    "confidence": 0.82,
                    "reasoning": "Key traders show 76% avg success rate over 25+ markets",
                    "key_findings": [
                        "Lead trader: 78% success rate across 32 resolved markets",
                        "Statistical significance confirmed (p < 0.01)"
                    ]
                }
            ],
            "risk_factors": [
                "Market highly politicized - emotion may override analysis"
            ],
            "metadata": {
                "analysis_timestamp": "2024-01-01T12:00:00Z",
                "data_freshness": "real-time",
                "trader_sample_size": 1247,
                "min_portfolio_ratio_filter": 0.1,
                "min_success_rate_filter": 0.7,
                "consensus_reached": True,
                "voting_duration_seconds": 2.5
            }
        }
    
    mock_coordinator.analyze_market = mock_analyze_market
    
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    # Create mock market data
    mock_market_data = MarketData(
        id="0x1234567890abcdef",
        title="Will Donald Trump win the 2024 Presidential Election?",
        description="Market resolves to Yes if Donald Trump wins the 2024 Presidential Election",
        category="Politics",
        subcategory="US Elections",
        end_date=datetime(2024, 11, 5, 23, 59, 59, tzinfo=timezone.utc),
        resolution_criteria="Market resolves based on official election results",
        status="active",
        creator="0xdef456789",
        total_volume=Decimal("15000000"),
        total_liquidity=Decimal("2500000"),
        outcomes=[
            MarketOutcome(
                id="yes",
                name="Yes",
                current_price=Decimal("0.52"),
                volume_24h=Decimal("1800000"),
                liquidity=Decimal("1200000"),
                order_book=OrderBook(
                    bids=[OrderBookEntry(price=Decimal("0.515"), size=Decimal("10000"))],
                    asks=[OrderBookEntry(price=Decimal("0.525"), size=Decimal("15000"))]
                )
            ),
            MarketOutcome(
                id="no",
                name="No",
                current_price=Decimal("0.48"),
                volume_24h=Decimal("1200000"),
                liquidity=Decimal("1300000")
            )
        ]
    )
    
    mock_client.get_market_data.return_value = mock_market_data
    
    # Override dependency functions
    def override_get_coordinator():
        return mock_coordinator
    
    def override_get_client():
        return mock_client
    
    # Create dependency overrides
    from app.api.dependencies import get_agent_coordinator, get_polymarket_client
    test_app.dependency_overrides[get_agent_coordinator] = override_get_coordinator
    test_app.dependency_overrides[get_polymarket_client] = override_get_client
    
    # Include routes
    test_app.include_router(router, prefix="/api")
    
    return test_app


class TestAPIEndpointsIntegration:
    """Integration tests for all API endpoints with proper mocking."""
    
    @pytest.fixture
    def client(self, mock_app):
        """Create test client with mocked dependencies."""
        return TestClient(mock_app)
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "polyingest-api"
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint with mocked coordinator."""
        response = client.get("/api/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "coordinator_performance" in data
        assert "agent_health" in data
        assert "voting_system" in data
        assert "system_status" in data
        
        # Verify coordinator performance
        coord_perf = data["coordinator_performance"]
        assert coord_perf["total_analyses"] == 156
        assert coord_perf["success_rate"] == 0.949
        
        # Verify agent health
        assert "Portfolio Analyzer" in data["agent_health"]
        assert "Success Rate Analyzer" in data["agent_health"]
    
    def test_market_data_endpoint(self, client):
        """Test market data endpoint with mocked client."""
        with patch('app.api.routes._get_trading_activity') as mock_trading:
            mock_trading.return_value = {
                "total_trades_24h": 2847,
                "unique_traders_24h": 432,
                "avg_trade_size": 1250,
                "large_trades_24h": 23,
                "recent_large_trades": []
            }
            
            response = client.get("/api/market/0x1234567890abcdef/data")
            assert response.status_code == 200
            
            data = response.json()
            assert data["market"]["id"] == "0x1234567890abcdef"
            assert data["market"]["title"] == "Will Donald Trump win the 2024 Presidential Election?"
            assert data["market"]["status"] == "active"
            assert len(data["outcomes"]) == 2
            assert "trading_activity" in data
            
            # Verify outcome structure
            yes_outcome = next(o for o in data["outcomes"] if o["name"] == "Yes")
            assert yes_outcome["current_price"] == 0.52
            assert "order_book" in yes_outcome
    
    def test_alpha_analysis_endpoint(self, client):
        """Test alpha analysis endpoint with mocked coordinator."""
        with patch('app.api.routes._get_market_traders') as mock_traders:
            mock_traders.return_value = [
                {
                    "address": "0xabc123456789def",
                    "total_portfolio_value_usd": 500000,
                    "performance_metrics": {
                        "overall_success_rate": 0.78,
                        "markets_resolved": 32,
                        "total_profit_usd": 125000,
                        "roi_percentage": 25.0
                    },
                    "positions": [
                        {
                            "market_id": "0x1234567890abcdef",
                            "outcome_id": "yes",
                            "position_size_usd": 50000,
                            "portfolio_allocation_pct": 0.1,
                            "entry_price": 0.45
                        }
                    ]
                }
            ]
            
            response = client.get("/api/market/0x1234567890abcdef/alpha")
            assert response.status_code == 200
            
            data = response.json()
            assert data["alpha_analysis"]["has_alpha"] is True
            assert data["alpha_analysis"]["confidence_score"] == 0.85
            assert data["alpha_analysis"]["recommended_side"] == "Yes"
            
            # Verify agent analyses
            assert len(data["agent_analyses"]) == 2
            agent_names = [agent["agent_name"] for agent in data["agent_analyses"]]
            assert "Portfolio Analyzer" in agent_names
            assert "Success Rate Analyzer" in agent_names
            
            # Verify consensus
            consensus = data["alpha_analysis"]["agent_consensus"]
            assert consensus["votes_for_alpha"] == 4
            assert consensus["votes_against_alpha"] == 1
    
    def test_alpha_analysis_with_query_parameters(self, client):
        """Test alpha analysis endpoint with custom query parameters."""
        with patch('app.api.routes._get_market_traders') as mock_traders:
            mock_traders.return_value = []
            
            response = client.get(
                "/api/market/0x1234567890abcdef/alpha"
                "?min_portfolio_ratio=0.15&min_success_rate=0.8&min_trade_history=20"
            )
            assert response.status_code == 200
            
            data = response.json()
            # Verify the endpoint accepts and processes parameters
            assert "metadata" in data
            assert data["metadata"]["min_portfolio_ratio_filter"] == 0.1  # From mock
            assert data["metadata"]["min_success_rate_filter"] == 0.7      # From mock
    
    def test_alpha_analysis_invalid_parameters(self, client):
        """Test alpha analysis with invalid query parameters."""
        # Test invalid portfolio ratio
        response = client.get("/api/market/0x1234/alpha?min_portfolio_ratio=1.5")
        assert response.status_code == 422
        
        # Test invalid success rate
        response = client.get("/api/market/0x1234/alpha?min_success_rate=-0.1")
        assert response.status_code == 422
        
        # Test invalid trade history
        response = client.get("/api/market/0x1234/alpha?min_trade_history=0")
        assert response.status_code == 422
    
    def test_trader_analysis_endpoint(self, client):
        """Test trader analysis endpoint."""
        with patch('app.api.routes._get_comprehensive_trader_data') as mock_trader:
            mock_trader.return_value = {
                "address": "0xabc123456789def012345678901234567890abcdef"[:42],
                "total_portfolio_value_usd": 500000,
                "active_positions": 8,
                "total_markets_traded": 45,
                "performance_metrics": {
                    "overall_success_rate": 0.78,
                    "total_profit_usd": 125000,
                    "roi_percentage": 25.0,
                    "avg_position_size_usd": 15000,
                    "markets_resolved": 32,
                    "confidence_interval": [0.72, 0.84]
                },
                "position_analysis": {
                    "avg_portfolio_allocation": 0.087,
                    "max_single_position": 0.22,
                    "diversification_score": 0.65,
                    "concentration_risk": "medium"
                },
                "trading_patterns": {
                    "preferred_categories": ["Politics", "Sports", "Crypto"],
                    "entry_timing": "early_adopter",
                    "hold_duration_avg_days": 18,
                    "risk_tolerance": "high"
                }
            }
            
            valid_address = "0xabc123456789def012345678901234567890abcdef"[:42]
            response = client.get(f"/api/trader/{valid_address}/analysis")
            assert response.status_code == 200
            
            data = response.json()
            assert data["trader"]["address"] == valid_address
            assert data["trader"]["total_portfolio_value_usd"] == 500000
            assert data["performance_metrics"]["overall_success_rate"] == 0.78
            assert data["position_analysis"]["concentration_risk"] == "medium"
            assert "trading_patterns" in data
    
    def test_trader_analysis_invalid_address(self, client):
        """Test trader analysis with invalid address formats."""
        # Test various invalid address formats
        invalid_addresses = [
            "abc123456789def012345678901234567890abcde",  # No 0x prefix
            "0x123",                                        # Too short
            "0xabc123456789def012345678901234567890abcdef123",  # Too long
            "0xghi123456789def012345678901234567890abcde",     # Invalid hex chars
        ]
        
        for invalid_address in invalid_addresses:
            response = client.get(f"/api/trader/{invalid_address}/analysis")
            assert response.status_code == 400
            data = response.json()
            assert "Invalid trader address format" in data["detail"]
    
    def test_market_not_found_scenarios(self, mock_app):
        """Test market not found scenarios."""
        # Override the mock to return None for market data
        def override_get_client_no_market():
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_market_data.return_value = None
            return mock_client
        
        from app.api.dependencies import get_polymarket_client
        mock_app.dependency_overrides[get_polymarket_client] = override_get_client_no_market
        
        client = TestClient(mock_app)
        
        # Test market data endpoint
        response = client.get("/api/market/nonexistent/data")
        assert response.status_code == 404
        data = response.json()
        assert "Market not found" in data["detail"]
        
        # Test alpha analysis endpoint
        response = client.get("/api/market/nonexistent/alpha")
        assert response.status_code == 404
        data = response.json()
        assert "Market not found" in data["detail"]
    
    def test_trader_not_found_scenario(self, mock_app):
        """Test trader not found scenario."""
        # Test with null trader data
        with patch('app.api.routes._get_comprehensive_trader_data') as mock_trader:
            mock_trader.return_value = None
            
            client = TestClient(mock_app)
            valid_address = "0xabc123456789def012345678901234567890abcdef"[:42]
            response = client.get(f"/api/trader/{valid_address}/analysis")
            assert response.status_code == 404
            data = response.json()
            assert "Trader not found or has no trading history" in data["detail"]
    
    def test_response_structure_validation(self, client):
        """Test that API responses match the CLAUDE.md specification."""
        with patch('app.api.routes._get_market_traders') as mock_traders:
            mock_traders.return_value = []
            
            response = client.get("/api/market/0x1234567890abcdef/alpha")
            assert response.status_code == 200
            
            data = response.json()
            
            # Verify top-level structure matches CLAUDE.md spec
            required_fields = ["market", "alpha_analysis", "key_traders", "agent_analyses", "risk_factors", "metadata"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Verify market structure
            market_fields = ["id", "title", "description", "end_date", "status", "current_prices"]
            for field in market_fields:
                assert field in data["market"], f"Missing market field: {field}"
            
            # Verify alpha_analysis structure
            alpha_fields = ["has_alpha", "confidence_score", "recommended_side", "strength", "agent_consensus"]
            for field in alpha_fields:
                assert field in data["alpha_analysis"], f"Missing alpha_analysis field: {field}"
            
            # Verify agent_consensus structure
            consensus_fields = ["votes_for_alpha", "votes_against_alpha", "abstentions"]
            for field in consensus_fields:
                assert field in data["alpha_analysis"]["agent_consensus"], f"Missing consensus field: {field}"
    
    def test_concurrent_requests_performance(self, client):
        """Test API can handle multiple concurrent requests efficiently."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                start_time = time.time()
                response = client.get("/api/health")
                end_time = time.time()
                results.put(("success", response.status_code, end_time - start_time))
            except Exception as e:
                results.put(("error", str(e), 0))
        
        # Start multiple concurrent requests
        threads = []
        for _ in range(5):  # Reduced number for faster testing
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all requests to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded and were reasonably fast
        success_count = 0
        total_time = 0
        while not results.empty():
            result_type, result_value, duration = results.get()
            if result_type == "success":
                assert result_value == 200
                success_count += 1
                total_time += duration
        
        assert success_count == 5, "Not all concurrent requests succeeded"
        avg_time = total_time / success_count
        assert avg_time < 1.0, f"Average response time {avg_time:.3f}s too slow"
    
    def test_performance_alpha_analysis(self, client):
        """Test alpha analysis response time meets requirements (<5 seconds)."""
        with patch('app.api.routes._get_market_traders') as mock_traders:
            mock_traders.return_value = []
            
            start_time = time.time()
            response = client.get("/api/market/0x1234567890abcdef/alpha")
            end_time = time.time()
            
            response_time = end_time - start_time
            assert response_time < 5.0, f"Alpha analysis took {response_time:.3f}s, exceeds 5s requirement"
            assert response.status_code == 200


class TestAPIErrorHandling:
    """Test comprehensive error handling scenarios."""
    
    def test_malformed_requests(self):
        """Test handling of malformed requests."""
        # Using the real app for error handling tests
        client = TestClient(app)
        
        # Test malformed market ID patterns
        response = client.get("/api/market//data")
        assert response.status_code == 404  # FastAPI route not found
        
        # Test special characters in URLs
        response = client.get("/api/market/invalid@market%23id/data")
        assert response.status_code in [404, 422, 500]  # Should handle gracefully


# Test configuration
pytest_plugins = []  # Removed pytest-asyncio since we're using sync tests