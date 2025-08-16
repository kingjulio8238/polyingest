import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, Any, List

from app.agents.coordinator import AgentCoordinator
from app.config import settings

class TestAgentCoordinator:
    """Test suite for AgentCoordinator functionality."""
    
    @pytest.fixture
    def coordinator(self):
        """Create a test coordinator instance."""
        return AgentCoordinator()
    
    @pytest.fixture
    def sample_market_data(self) -> Dict[str, Any]:
        """Sample market data for testing."""
        return {
            "id": "0x1234567890abcdef",
            "title": "Will AI achieve AGI by 2030?",
            "description": "Market resolves to Yes if artificial general intelligence is achieved by December 31, 2030",
            "category": "Technology",
            "subcategory": "AI",
            "end_date": "2030-12-31T23:59:59Z",
            "resolution_criteria": "Based on consensus of AI researchers",
            "status": "active",
            "creator": "0xmarket_creator",
            "total_volume": 500000,
            "total_liquidity": 125000,
            "current_prices": {"Yes": 0.45, "No": 0.55},
            "outcomes": [
                {"id": "yes", "name": "Yes", "current_price": 0.45},
                {"id": "no", "name": "No", "current_price": 0.55}
            ]
        }
    
    @pytest.fixture
    def sample_traders_data(self) -> List[Dict[str, Any]]:
        """Sample traders data for testing."""
        return [
            {
                "address": "0xtrader1",
                "total_portfolio_value_usd": 100000,
                "performance_metrics": {
                    "overall_success_rate": 0.75,
                    "markets_resolved": 15,
                    "total_profit_usd": 25000,
                    "roi_percentage": 25.0
                },
                "positions": [
                    {
                        "market_id": "0x1234567890abcdef",
                        "outcome_id": "yes",
                        "position_size_usd": 15000,
                        "entry_price": 0.42,
                        "current_value_usd": 16000,
                        "portfolio_allocation_pct": 0.15
                    }
                ]
            },
            {
                "address": "0xtrader2", 
                "total_portfolio_value_usd": 250000,
                "performance_metrics": {
                    "overall_success_rate": 0.82,
                    "markets_resolved": 22,
                    "total_profit_usd": 75000,
                    "roi_percentage": 30.0
                },
                "positions": [
                    {
                        "market_id": "0x1234567890abcdef",
                        "outcome_id": "yes",
                        "position_size_usd": 35000,
                        "entry_price": 0.38,
                        "current_value_usd": 38000,
                        "portfolio_allocation_pct": 0.14
                    }
                ]
            },
            {
                "address": "0xtrader3",
                "total_portfolio_value_usd": 50000,
                "performance_metrics": {
                    "overall_success_rate": 0.45,  # Below threshold
                    "markets_resolved": 8,
                    "total_profit_usd": -5000,
                    "roi_percentage": -10.0
                },
                "positions": [
                    {
                        "market_id": "0x1234567890abcdef",
                        "outcome_id": "no",
                        "position_size_usd": 5000,
                        "entry_price": 0.62,
                        "current_value_usd": 4800,
                        "portfolio_allocation_pct": 0.10
                    }
                ]
            }
        ]
    
    def test_coordinator_initialization(self, coordinator):
        """Test that coordinator initializes properly with agents."""
        assert coordinator is not None
        assert coordinator.voting_system is not None
        assert len(coordinator.voting_system.agents) >= 2  # Portfolio + Success Rate agents
        
        # Check that specific agents are registered
        agent_names = coordinator.voting_system.get_registered_agents()
        assert "Portfolio Analyzer" in agent_names
        assert "Success Rate Analyzer" in agent_names
    
    def test_prepare_market_data(self, coordinator, sample_market_data):
        """Test market data preparation and validation."""
        prepared_data = coordinator.prepare_market_data(sample_market_data)
        
        assert prepared_data["id"] == sample_market_data["id"]
        assert prepared_data["title"] == sample_market_data["title"]
        assert prepared_data["status"] == "active"
        assert prepared_data["total_volume"] == 500000
        assert prepared_data["total_liquidity"] == 125000
        
        # Test with invalid data
        invalid_data = {"invalid": "data"}
        prepared_invalid = coordinator.prepare_market_data(invalid_data)
        assert prepared_invalid == {}
    
    def test_filter_traders(self, coordinator, sample_traders_data):
        """Test trader filtering functionality."""
        # Test default filtering
        filtered_traders = coordinator.filter_traders(sample_traders_data)
        
        # Should include trader1 and trader2 (good success rates), exclude trader3 (poor performance)
        assert len(filtered_traders) == 2
        
        addresses = [t["address"] for t in filtered_traders]
        assert "0xtrader1" in addresses
        assert "0xtrader2" in addresses
        assert "0xtrader3" not in addresses  # Below success rate threshold
        
        # Test with custom filters
        strict_filters = {
            "min_success_rate": 0.8,
            "min_portfolio_ratio": 0.12,
            "min_trade_history": 20
        }
        
        strict_filtered = coordinator.filter_traders(sample_traders_data, strict_filters)
        assert len(strict_filtered) == 1  # Only trader2 meets all strict criteria
        assert strict_filtered[0]["address"] == "0xtrader2"
    
    @pytest.mark.asyncio
    async def test_analyze_market_success(self, coordinator, sample_market_data, sample_traders_data):
        """Test successful market analysis workflow."""
        result = await coordinator.analyze_market(sample_market_data, sample_traders_data)
        
        # Verify response structure
        assert "market" in result
        assert "alpha_analysis" in result
        assert "key_traders" in result
        assert "agent_analyses" in result
        assert "risk_factors" in result
        assert "metadata" in result
        
        # Verify market section
        market = result["market"]
        assert market["id"] == sample_market_data["id"]
        assert market["title"] == sample_market_data["title"]
        assert market["status"] == "active"
        
        # Verify alpha analysis section
        alpha_analysis = result["alpha_analysis"]
        assert "has_alpha" in alpha_analysis
        assert "confidence_score" in alpha_analysis
        assert isinstance(alpha_analysis["confidence_score"], (int, float))
        assert 0 <= alpha_analysis["confidence_score"] <= 1
        
        # Verify agent consensus
        consensus = alpha_analysis["agent_consensus"]
        assert "votes_for_alpha" in consensus
        assert "votes_against_alpha" in consensus
        assert "abstentions" in consensus
        
        # Verify metadata
        metadata = result["metadata"]
        assert "analysis_timestamp" in metadata
        assert "trader_sample_size" in metadata
        assert metadata["trader_sample_size"] >= 0
    
    @pytest.mark.asyncio
    async def test_analyze_market_with_filters(self, coordinator, sample_market_data, sample_traders_data):
        """Test market analysis with custom filters."""
        filters = {
            "min_portfolio_ratio": 0.05,
            "min_success_rate": 0.6,
            "min_trade_history": 5
        }
        
        result = await coordinator.analyze_market(sample_market_data, sample_traders_data, filters)
        
        # Should have more traders included with relaxed filters
        assert result["metadata"]["trader_sample_size"] >= 2
        
        # Verify filters are recorded in metadata
        metadata = result["metadata"]
        assert metadata["min_portfolio_ratio_filter"] == 0.05
        assert metadata["min_success_rate_filter"] == 0.6
    
    @pytest.mark.asyncio
    async def test_analyze_market_no_traders(self, coordinator, sample_market_data):
        """Test market analysis with no qualifying traders."""
        empty_traders = []
        result = await coordinator.analyze_market(sample_market_data, empty_traders)
        
        # Should return no-alpha result
        assert result["alpha_analysis"]["has_alpha"] is False
        assert result["alpha_analysis"]["confidence_score"] == 0.0
        assert len(result["key_traders"]) == 0
        assert "No qualifying traders found" in result["risk_factors"][0]
    
    @pytest.mark.asyncio
    async def test_analyze_market_invalid_data(self, coordinator):
        """Test market analysis with invalid market data."""
        invalid_market = {}
        sample_traders = [{"address": "0xtest", "total_portfolio_value_usd": 1000}]
        
        result = await coordinator.analyze_market(invalid_market, sample_traders)
        
        # Should return error result
        assert "error" in result["metadata"]
        assert result["alpha_analysis"]["has_alpha"] is False
    
    def test_determine_recommended_side(self, coordinator, sample_traders_data):
        """Test recommended side determination logic."""
        from app.agents.voting_system import VotingResult
        
        # Mock voting result
        voting_result = VotingResult(
            has_alpha=True,
            confidence_score=0.8,
            consensus_reached=True,
            votes_for_alpha=2,
            votes_against_alpha=0,
            abstentions=0,
            total_weight=2.0,
            weighted_alpha_score=1.6,
            agent_results=[],
            reasoning_summary="Test",
            voting_duration=1.0
        )
        
        recommended_side = coordinator._determine_recommended_side(sample_traders_data, voting_result)
        
        # Should recommend "Yes" since most positions are on yes side
        assert recommended_side == "Yes"
    
    def test_calculate_strength(self, coordinator):
        """Test alpha signal strength calculation."""
        # Strong signal
        assert coordinator._calculate_strength(0.9, 3) == "strong"
        
        # Moderate signal
        assert coordinator._calculate_strength(0.7, 2) == "moderate"
        
        # Weak signal
        assert coordinator._calculate_strength(0.5, 1) == "weak"
    
    def test_extract_key_traders(self, coordinator, sample_market_data, sample_traders_data):
        """Test key trader extraction and formatting."""
        from app.agents.voting_system import VotingResult
        
        # Mock voting result
        voting_result = VotingResult(
            has_alpha=True,
            confidence_score=0.8,
            consensus_reached=True,
            votes_for_alpha=2,
            votes_against_alpha=0,
            abstentions=0,
            total_weight=2.0,
            weighted_alpha_score=1.6,
            agent_results=[],
            reasoning_summary="Test",
            voting_duration=1.0
        )
        
        key_traders = coordinator._extract_key_traders(sample_traders_data, sample_market_data, voting_result)
        
        assert len(key_traders) >= 2
        
        # Check first trader (should be highest performing)
        top_trader = key_traders[0]
        assert "address" in top_trader
        assert "position_size_usd" in top_trader
        assert "portfolio_allocation_pct" in top_trader
        assert "historical_success_rate" in top_trader
        assert "confidence_indicators" in top_trader
        
        # Verify confidence indicators structure
        indicators = top_trader["confidence_indicators"]
        assert "large_position" in indicators
        assert "high_allocation" in indicators
        assert "proven_track_record" in indicators
        assert "early_entry" in indicators
    
    def test_generate_risk_factors(self, coordinator, sample_market_data, sample_traders_data):
        """Test risk factor generation."""
        from app.agents.voting_system import VotingResult
        
        # Mock voting result with low consensus
        voting_result = VotingResult(
            has_alpha=False,
            confidence_score=0.3,
            consensus_reached=False,
            votes_for_alpha=1,
            votes_against_alpha=0,
            abstentions=2,
            total_weight=2.0,
            weighted_alpha_score=0.5,
            agent_results=[],
            reasoning_summary="Test",
            voting_duration=1.0
        )
        
        risk_factors = coordinator._generate_risk_factors(sample_market_data, sample_traders_data, voting_result)
        
        assert len(risk_factors) > 0
        assert any("consensus not reached" in factor.lower() for factor in risk_factors)
        assert any("abstention" in factor.lower() for factor in risk_factors)
    
    def test_get_performance_metrics(self, coordinator):
        """Test performance metrics retrieval."""
        metrics = coordinator.get_performance_metrics()
        
        assert "coordinator_performance" in metrics
        assert "agent_health" in metrics
        assert "voting_system" in metrics
        assert "system_status" in metrics
        
        # Check coordinator performance structure
        perf = metrics["coordinator_performance"]
        assert "total_analyses" in perf
        assert "successful_analyses" in perf
        assert "success_rate" in perf
        assert "avg_analysis_duration" in perf
        
        # Check agent health structure
        agent_health = metrics["agent_health"]
        assert len(agent_health) >= 2  # At least Portfolio and Success Rate agents
        
        for agent_name, health in agent_health.items():
            assert "weight" in health
            assert "confidence" in health
            assert "status" in health
    
    def test_update_agent_performance(self, coordinator):
        """Test agent performance weight updates."""
        initial_weights = {
            name: agent.weight 
            for name, agent in coordinator.voting_system.agents.items()
        }
        
        # Update performance
        performance_data = {
            "Portfolio Analyzer": 0.9,
            "Success Rate Analyzer": 0.8
        }
        
        coordinator.update_agent_performance(performance_data)
        
        # Verify weights were updated
        for agent_name, accuracy in performance_data.items():
            if agent_name in coordinator.voting_system.agents:
                agent = coordinator.voting_system.agents[agent_name]
                # Weight should be influenced by accuracy (clamped between 0.1 and 2.0)
                assert 0.1 <= agent.weight <= 2.0
    
    def test_get_agent_status(self, coordinator):
        """Test agent status retrieval."""
        status = coordinator.get_agent_status()
        
        assert "registered_agents" in status
        assert "voting_config" in status
        assert "agent_details" in status
        
        # Verify registered agents
        agents = status["registered_agents"]
        assert "Portfolio Analyzer" in agents
        assert "Success Rate Analyzer" in agents
        
        # Verify voting config
        config = status["voting_config"]
        assert "threshold" in config
        assert "min_participation" in config
        
        # Verify agent details
        details = status["agent_details"]
        for agent_name in agents:
            assert agent_name in details
            agent_detail = details[agent_name]
            assert "type" in agent_detail
            assert "weight" in agent_detail
            assert "last_confidence" in agent_detail

if __name__ == "__main__":
    pytest.main([__file__, "-v"])