import pytest
import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

from app.agents.voting_system import VotingSystem, VotingResult
from app.agents.base_agent import BaseAgent
from app.agents.portfolio_agent import PortfolioAnalyzerAgent
from app.agents.success_rate_agent import SuccessRateAgent


class MockAgent(BaseAgent):
    """Mock agent for testing purposes."""
    
    def __init__(self, name: str, weight: float = 1.0, vote: str = "alpha", confidence: float = 0.8):
        super().__init__(name, weight)
        self._test_vote = vote
        self._test_confidence = confidence
        self._test_analysis = {"mock_analysis": True}
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock analysis that returns test data."""
        self.confidence = Decimal(str(self._test_confidence))
        return self._test_analysis
    
    def vote(self, analysis: Dict[str, Any]) -> str:
        """Return predetermined vote."""
        return self._test_vote
    
    def get_reasoning(self) -> str:
        """Return mock reasoning."""
        return f"Mock reasoning for {self.name} voting {self._test_vote}"


class TestVotingSystem:
    """Test suite for VotingSystem class."""
    
    @pytest.fixture
    def voting_system(self):
        """Create a fresh voting system for each test."""
        return VotingSystem(vote_threshold=0.6)
    
    @pytest.fixture
    def sample_data(self):
        """Sample market and trader data for testing."""
        return {
            "market": {
                "id": "0x1234...",
                "title": "Test Market",
                "end_date": "2024-12-01T00:00:00Z"
            },
            "traders": [
                {
                    "address": "0xabc...",
                    "total_portfolio_value_usd": 100000,
                    "positions": [
                        {
                            "market_id": "0x1234...",
                            "position_size_usd": 15000
                        }
                    ],
                    "performance_metrics": {
                        "overall_success_rate": 0.75,
                        "markets_resolved": 20,
                        "total_profit_usd": 10000
                    }
                }
            ]
        }
    
    def test_voting_system_initialization(self, voting_system):
        """Test VotingSystem initialization."""
        assert voting_system.vote_threshold == 0.6
        assert voting_system.min_participation_ratio == 0.5
        assert len(voting_system.agents) == 0
    
    def test_agent_registration(self, voting_system):
        """Test agent registration functionality."""
        agent = MockAgent("TestAgent", weight=1.5)
        
        # Register agent
        voting_system.register_agent(agent)
        
        assert len(voting_system.agents) == 1
        assert "TestAgent" in voting_system.agents
        assert voting_system.agents["TestAgent"].weight == 1.5
    
    def test_agent_unregistration(self, voting_system):
        """Test agent unregistration."""
        agent = MockAgent("TestAgent")
        voting_system.register_agent(agent)
        
        # Unregister agent
        result = voting_system.unregister_agent("TestAgent")
        assert result is True
        assert len(voting_system.agents) == 0
        
        # Try to unregister non-existent agent
        result = voting_system.unregister_agent("NonExistent")
        assert result is False
    
    def test_invalid_agent_registration(self, voting_system):
        """Test registration with invalid agent type."""
        with pytest.raises(ValueError, match="Agent must be instance of BaseAgent"):
            voting_system.register_agent("not_an_agent")
    
    @pytest.mark.asyncio
    async def test_unanimous_alpha_vote(self, voting_system, sample_data):
        """Test voting with unanimous alpha decision."""
        # Register agents that all vote alpha
        agents = [
            MockAgent("Agent1", weight=1.0, vote="alpha", confidence=0.9),
            MockAgent("Agent2", weight=1.5, vote="alpha", confidence=0.8),
            MockAgent("Agent3", weight=1.2, vote="alpha", confidence=0.85)
        ]
        
        for agent in agents:
            voting_system.register_agent(agent)
        
        # Conduct vote
        result = await voting_system.conduct_vote(sample_data)
        
        assert isinstance(result, VotingResult)
        assert result.has_alpha is True
        assert result.votes_for_alpha == 3
        assert result.votes_against_alpha == 0
        assert result.abstentions == 0
        assert result.consensus_reached is True
        assert result.confidence_score > 0.8
    
    @pytest.mark.asyncio
    async def test_unanimous_no_alpha_vote(self, voting_system, sample_data):
        """Test voting with unanimous no-alpha decision."""
        # Register agents that all vote no_alpha
        agents = [
            MockAgent("Agent1", weight=1.0, vote="no_alpha", confidence=0.7),
            MockAgent("Agent2", weight=1.5, vote="no_alpha", confidence=0.8)
        ]
        
        for agent in agents:
            voting_system.register_agent(agent)
        
        # Conduct vote
        result = await voting_system.conduct_vote(sample_data)
        
        assert result.has_alpha is False
        assert result.votes_for_alpha == 0
        assert result.votes_against_alpha == 2
        assert result.consensus_reached is True
    
    @pytest.mark.asyncio
    async def test_split_vote_below_threshold(self, voting_system, sample_data):
        """Test voting where alpha votes don't meet threshold."""
        # Register agents with split decision (40% alpha, 60% no-alpha)
        agents = [
            MockAgent("Agent1", weight=1.0, vote="alpha", confidence=0.8),
            MockAgent("Agent2", weight=1.0, vote="no_alpha", confidence=0.7),
            MockAgent("Agent3", weight=1.0, vote="no_alpha", confidence=0.9)
        ]
        
        for agent in agents:
            voting_system.register_agent(agent)
        
        # Conduct vote
        result = await voting_system.conduct_vote(sample_data)
        
        assert result.has_alpha is False  # Below 0.6 threshold
        assert result.votes_for_alpha == 1
        assert result.votes_against_alpha == 2
        assert result.consensus_reached is True
    
    @pytest.mark.asyncio
    async def test_abstention_handling(self, voting_system, sample_data):
        """Test handling of agent abstentions."""
        # Register agents with some abstentions
        agents = [
            MockAgent("Agent1", weight=1.0, vote="alpha", confidence=0.9),
            MockAgent("Agent2", weight=1.0, vote="abstain", confidence=0.1),
            MockAgent("Agent3", weight=1.0, vote="alpha", confidence=0.8)
        ]
        
        for agent in agents:
            voting_system.register_agent(agent)
        
        # Conduct vote
        result = await voting_system.conduct_vote(sample_data)
        
        assert result.votes_for_alpha == 2
        assert result.abstentions == 1
        assert result.has_alpha is True  # 100% of participating agents voted alpha
    
    @pytest.mark.asyncio
    async def test_insufficient_participation(self, voting_system, sample_data):
        """Test scenario with too many abstentions."""
        # Register agents where most abstain (below 50% participation)
        agents = [
            MockAgent("Agent1", weight=1.0, vote="alpha", confidence=0.9),
            MockAgent("Agent2", weight=1.0, vote="abstain", confidence=0.1),
            MockAgent("Agent3", weight=1.0, vote="abstain", confidence=0.2)
        ]
        
        for agent in agents:
            voting_system.register_agent(agent)
        
        # Conduct vote
        result = await voting_system.conduct_vote(sample_data)
        
        # Should still reach consensus since 1/3 = 33% participation meets minimum
        # (our min is 50%, so this might not reach consensus)
        assert result.abstentions == 2
        assert result.confidence_score < 0.7  # Lower confidence due to abstentions
    
    @pytest.mark.asyncio
    async def test_weighted_voting_calculation(self, voting_system, sample_data):
        """Test that agent weights properly affect voting outcomes."""
        # Register agents with different weights
        agents = [
            MockAgent("HighWeight", weight=2.0, vote="alpha", confidence=0.8),  # effective: 1.6
            MockAgent("LowWeight", weight=0.5, vote="no_alpha", confidence=0.8)  # effective: 0.4
        ]
        
        for agent in agents:
            voting_system.register_agent(agent)
        
        # Conduct vote
        result = await voting_system.conduct_vote(sample_data)
        
        # High weight agent should dominate: 1.6/(1.6+0.4) = 0.8 > 0.6 threshold
        assert result.has_alpha is True
        assert result.weighted_alpha_score > 1.5
    
    @pytest.mark.asyncio
    async def test_agent_failure_handling(self, voting_system, sample_data):
        """Test handling of agent analysis failures."""
        # Create agent that will raise exception
        failing_agent = MockAgent("FailingAgent", weight=1.0, vote="alpha", confidence=0.8)
        failing_agent.analyze = AsyncMock(side_effect=Exception("Analysis failed"))
        
        working_agent = MockAgent("WorkingAgent", weight=1.0, vote="alpha", confidence=0.8)
        
        voting_system.register_agent(failing_agent)
        voting_system.register_agent(working_agent)
        
        # Conduct vote
        result = await voting_system.conduct_vote(sample_data)
        
        # Should handle failure gracefully
        assert len(result.agent_results) == 2
        
        # Find results for each agent
        failing_result = next(r for r in result.agent_results if r["agent_name"] == "FailingAgent")
        working_result = next(r for r in result.agent_results if r["agent_name"] == "WorkingAgent")
        
        assert failing_result["success"] is False
        assert failing_result["vote"] == "abstain"
        assert working_result["success"] is True
        assert working_result["vote"] == "alpha"
    
    @pytest.mark.asyncio
    async def test_empty_voting_system(self, voting_system, sample_data):
        """Test voting with no registered agents."""
        # Conduct vote with no agents
        result = await voting_system.conduct_vote(sample_data)
        
        assert result.has_alpha is False
        assert result.confidence_score == 0.0
        assert result.consensus_reached is False
        assert len(result.agent_results) == 0
        assert "No agents available" in result.reasoning_summary
    
    def test_voting_summary(self, voting_system):
        """Test get_voting_summary method."""
        # Register some agents
        agents = [
            MockAgent("Agent1", weight=1.0),
            MockAgent("Agent2", weight=1.5)
        ]
        
        for agent in agents:
            voting_system.register_agent(agent)
        
        summary = voting_system.get_voting_summary()
        
        assert summary["total_agents"] == 2
        assert summary["vote_threshold"] == 0.6
        assert summary["total_weight"] == 2.5
        assert len(summary["registered_agents"]) == 2
    
    def test_agent_weight_updates(self, voting_system):
        """Test updating agent weights based on performance."""
        agent = MockAgent("TestAgent", weight=1.0)
        voting_system.register_agent(agent)
        
        # Update weights
        performance_data = {"TestAgent": 0.85}
        voting_system.update_agent_weights(performance_data)
        
        assert voting_system.agents["TestAgent"].weight == 0.85
    
    def test_agent_weight_reset(self, voting_system):
        """Test resetting all agent weights."""
        agents = [
            MockAgent("Agent1", weight=1.5),
            MockAgent("Agent2", weight=0.8)
        ]
        
        for agent in agents:
            voting_system.register_agent(agent)
        
        # Reset weights
        voting_system.reset_agent_weights()
        
        for agent in voting_system.agents.values():
            assert agent.weight == 1.0
    
    def test_voting_result_to_dict(self):
        """Test VotingResult conversion to dictionary."""
        # Create mock agent results
        agent_results = [
            {
                "agent_name": "TestAgent",
                "vote": "alpha",
                "confidence": 0.8,
                "reasoning": "Test reasoning"
            }
        ]
        
        result = VotingResult(
            has_alpha=True,
            confidence_score=0.85,
            consensus_reached=True,
            votes_for_alpha=1,
            votes_against_alpha=0,
            abstentions=0,
            total_weight=1.0,
            weighted_alpha_score=0.8,
            agent_results=agent_results,
            reasoning_summary="Test summary",
            voting_duration=1.5
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["has_alpha"] is True
        assert result_dict["confidence_score"] == 0.85
        assert result_dict["agent_consensus"]["votes_for_alpha"] == 1
        assert result_dict["metadata"]["voting_duration_seconds"] == 1.5
        assert "timestamp" in result_dict["metadata"]


@pytest.mark.asyncio
async def test_integration_with_real_agents():
    """Integration test with actual PortfolioAnalyzerAgent and SuccessRateAgent."""
    voting_system = VotingSystem(vote_threshold=0.6)
    
    # Register real agents
    portfolio_agent = PortfolioAnalyzerAgent()
    success_rate_agent = SuccessRateAgent()
    
    voting_system.register_agent(portfolio_agent)
    voting_system.register_agent(success_rate_agent)
    
    # Sample data that should trigger alpha detection
    data = {
        "market": {
            "id": "0x1234...",
            "title": "Test Market"
        },
        "traders": [
            {
                "address": "0xabc...",
                "total_portfolio_value_usd": 100000,
                "positions": [
                    {
                        "market_id": "0x1234...",
                        "position_size_usd": 20000  # 20% allocation
                    }
                ],
                "performance_metrics": {
                    "overall_success_rate": 0.8,  # 80% success rate
                    "markets_resolved": 25,
                    "total_profit_usd": 15000
                }
            },
            {
                "address": "0xdef...",
                "total_portfolio_value_usd": 200000,
                "positions": [
                    {
                        "market_id": "0x1234...",
                        "position_size_usd": 30000  # 15% allocation
                    }
                ],
                "performance_metrics": {
                    "overall_success_rate": 0.75,
                    "markets_resolved": 20,
                    "total_profit_usd": 20000
                }
            }
        ]
    }
    
    # Conduct vote
    result = await voting_system.conduct_vote(data)
    
    # Both agents should vote alpha based on good data
    assert result.votes_for_alpha >= 1  # At least one agent should vote alpha
    assert result.consensus_reached is True
    assert result.confidence_score > 0.5
    assert len(result.agent_results) == 2
    
    # Check that both agents provided reasoning
    for agent_result in result.agent_results:
        assert len(agent_result["reasoning"]) > 0
        assert agent_result["confidence"] > 0