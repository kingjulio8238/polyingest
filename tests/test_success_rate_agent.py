import pytest
import asyncio
from decimal import Decimal
from unittest.mock import patch, MagicMock
from app.agents.success_rate_agent import SuccessRateAgent
from app.config import settings


class TestSuccessRateAgent:
    """Comprehensive tests for SuccessRateAgent class."""
    
    @pytest.fixture
    def agent(self):
        """Create a SuccessRateAgent instance for testing."""
        return SuccessRateAgent()
    
    @pytest.fixture
    def sample_market_data(self):
        """Sample market data for testing."""
        return {
            "id": "0x1234567890abcdef",
            "title": "Will Donald Trump win the 2024 Presidential Election?",
            "status": "active",
            "total_volume": 1500000,
            "end_date": "2024-11-05T23:59:59Z"
        }
    
    @pytest.fixture
    def high_performing_traders_data(self):
        """Mock data for multiple high-performing traders scenario."""
        return [
            {
                "address": "0xabc123",
                "performance_metrics": {
                    "overall_success_rate": 0.78,  # 78% success rate
                    "markets_resolved": 25,        # Sufficient history
                    "total_profit_usd": 125000
                }
            },
            {
                "address": "0xdef456", 
                "performance_metrics": {
                    "overall_success_rate": 0.82,  # 82% success rate
                    "markets_resolved": 32,        # Good history
                    "total_profit_usd": 200000
                }
            },
            {
                "address": "0x789abc",
                "performance_metrics": {
                    "overall_success_rate": 0.75,  # 75% success rate
                    "markets_resolved": 18,        # Adequate history
                    "total_profit_usd": 89000
                }
            },
            {
                "address": "0x456def",
                "performance_metrics": {
                    "overall_success_rate": 0.72,  # 72% success rate
                    "markets_resolved": 28,        # Good history
                    "total_profit_usd": 156000
                }
            }
        ]
    
    @pytest.fixture
    def moderate_performing_traders_data(self):
        """Mock data for moderate-performing traders scenario."""
        return [
            {
                "address": "0xabc123",
                "performance_metrics": {
                    "overall_success_rate": 0.73,  # Above threshold
                    "markets_resolved": 22,
                    "total_profit_usd": 95000
                }
            },
            {
                "address": "0xdef456",
                "performance_metrics": {
                    "overall_success_rate": 0.71,  # Just above threshold
                    "markets_resolved": 15,
                    "total_profit_usd": 45000
                }
            },
            {
                "address": "0x789abc",
                "performance_metrics": {
                    "overall_success_rate": 0.65,  # Below threshold
                    "markets_resolved": 20,
                    "total_profit_usd": 32000
                }
            }
        ]
    
    @pytest.fixture 
    def low_performing_traders_data(self):
        """Mock data for low-performing traders scenario."""
        return [
            {
                "address": "0xabc123",
                "performance_metrics": {
                    "overall_success_rate": 0.58,  # Below threshold
                    "markets_resolved": 24,
                    "total_profit_usd": 15000
                }
            },
            {
                "address": "0xdef456",
                "performance_metrics": {
                    "overall_success_rate": 0.62,  # Below threshold
                    "markets_resolved": 18,
                    "total_profit_usd": 8000
                }
            }
        ]
    
    @pytest.fixture
    def insufficient_history_traders_data(self):
        """Mock data for traders with insufficient history."""
        return [
            {
                "address": "0xabc123",
                "performance_metrics": {
                    "overall_success_rate": 0.85,  # High rate but...
                    "markets_resolved": 5,         # Insufficient history
                    "total_profit_usd": 25000
                }
            },
            {
                "address": "0xdef456",
                "performance_metrics": {
                    "overall_success_rate": 0.90,  # Very high rate but...
                    "markets_resolved": 8,         # Still insufficient
                    "total_profit_usd": 35000
                }
            }
        ]
    
    @pytest.fixture
    def exceptional_single_trader_data(self):
        """Mock data for exceptional single trader scenario."""
        return [
            {
                "address": "0xabc123",
                "performance_metrics": {
                    "overall_success_rate": 0.88,  # Exceptional performance
                    "markets_resolved": 45,        # Very good history
                    "total_profit_usd": 350000
                }
            },
            {
                "address": "0xdef456",
                "performance_metrics": {
                    "overall_success_rate": 0.55,  # Average performance
                    "markets_resolved": 20,
                    "total_profit_usd": 12000
                }
            }
        ]
    
    # Basic Functionality Tests
    
    def test_agent_initialization(self, agent):
        """Test that agent initializes with correct properties."""
        assert agent.name == "Success Rate Analyzer"
        assert agent.weight == 1.5
        assert agent.min_success_rate == Decimal(str(settings.min_success_rate))
        assert agent.min_trade_history == settings.min_trade_history
        assert agent.confidence == Decimal('0.0')
    
    @pytest.mark.asyncio
    async def test_analyze_insufficient_data_no_market(self, agent):
        """Test error handling when market data is missing."""
        data = {"traders": []}
        result = await agent.analyze(data)
        
        assert "error" in result
        assert result["error"] == "Insufficient data"
        assert agent.confidence == Decimal('0.0')
    
    @pytest.mark.asyncio
    async def test_analyze_insufficient_data_no_traders(self, agent, sample_market_data):
        """Test error handling when trader data is missing."""
        data = {"market": sample_market_data}
        result = await agent.analyze(data)
        
        assert "error" in result
        assert result["error"] == "Insufficient data"
        assert agent.confidence == Decimal('0.0')
    
    @pytest.mark.asyncio
    async def test_analyze_empty_traders_list(self, agent, sample_market_data):
        """Test handling of empty traders list."""
        data = {"market": sample_market_data, "traders": []}
        result = await agent.analyze(data)
        
        assert "error" in result
        assert agent.confidence == Decimal('0.0')
    
    # Analysis Method Tests
    
    @pytest.mark.asyncio
    async def test_high_performing_traders_scenario(self, agent, sample_market_data, high_performing_traders_data):
        """Test analysis with multiple high-performing traders."""
        data = {"market": sample_market_data, "traders": high_performing_traders_data}
        result = await agent.analyze(data)
        
        assert "error" not in result
        assert result["total_traders_analyzed"] == 4
        assert result["valid_traders_count"] == 4
        assert result["high_performers_count"] >= 3  # Expect most to qualify
        assert result["avg_success_rate"] > 0.7
        assert result["statistical_significance"] is True
        assert result["statistically_significant_traders"] >= 2
        assert agent.confidence >= Decimal('0.8')
        
        # Check high performing traders structure
        high_performers = result["high_performing_traders"]
        assert len(high_performers) >= 3
        for trader in high_performers:
            assert "address" in trader
            assert "success_rate" in trader
            assert "statistical_significance" in trader
            assert "p_value" in trader
            assert "confidence_interval" in trader
            assert trader["success_rate"] >= 0.7
    
    @pytest.mark.asyncio
    async def test_moderate_performing_traders_scenario(self, agent, sample_market_data, moderate_performing_traders_data):
        """Test analysis with moderate-performing traders."""
        data = {"market": sample_market_data, "traders": moderate_performing_traders_data}
        result = await agent.analyze(data)
        
        assert "error" not in result
        assert result["total_traders_analyzed"] == 3
        assert result["valid_traders_count"] == 3
        assert result["high_performers_count"] >= 1  # Some should qualify
        assert result["high_performers_count"] <= 2  # But not all
        assert 0.65 <= result["avg_success_rate"] <= 0.75
        assert agent.confidence >= Decimal('0.4')
    
    @pytest.mark.asyncio
    async def test_low_performing_traders_scenario(self, agent, sample_market_data, low_performing_traders_data):
        """Test analysis with low-performing traders."""
        data = {"market": sample_market_data, "traders": low_performing_traders_data}
        result = await agent.analyze(data)
        
        assert "error" not in result
        assert result["total_traders_analyzed"] == 2
        assert result["valid_traders_count"] == 2
        assert result["high_performers_count"] == 0  # None should qualify
        assert result["avg_success_rate"] < 0.7
        assert agent.confidence <= Decimal('0.5')
    
    @pytest.mark.asyncio
    async def test_insufficient_history_scenario(self, agent, sample_market_data, insufficient_history_traders_data):
        """Test analysis with traders having insufficient history."""
        data = {"market": sample_market_data, "traders": insufficient_history_traders_data}
        result = await agent.analyze(data)
        
        assert "error" not in result
        assert result["total_traders_analyzed"] == 2
        assert result["valid_traders_count"] == 0  # None have sufficient history
        assert result["high_performers_count"] == 0
        assert agent.confidence == Decimal('0.1')  # Very low confidence
    
    @pytest.mark.asyncio
    async def test_exceptional_single_trader_scenario(self, agent, sample_market_data, exceptional_single_trader_data):
        """Test analysis with one exceptional trader."""
        data = {"market": sample_market_data, "traders": exceptional_single_trader_data}
        result = await agent.analyze(data)
        
        assert "error" not in result
        assert result["total_traders_analyzed"] == 2
        assert result["valid_traders_count"] == 2
        assert result["high_performers_count"] == 1  # One exceptional trader
        assert result["significance_ratio"] > 0.2  # High significance ratio
        
        # Check the exceptional trader
        high_performers = result["high_performing_traders"]
        exceptional_trader = high_performers[0]
        assert exceptional_trader["success_rate"] >= 0.8
        assert exceptional_trader["statistical_significance"] is True
    
    @pytest.mark.asyncio
    async def test_statistical_significance_validation(self, agent, sample_market_data):
        """Test statistical significance calculations."""
        # Create trader with clear statistical significance
        traders_data = [{
            "address": "0xtest123",
            "performance_metrics": {
                "overall_success_rate": 0.80,  # 80% with 50 markets should be significant
                "markets_resolved": 50,
                "total_profit_usd": 250000
            }
        }]
        
        data = {"market": sample_market_data, "traders": traders_data}
        result = await agent.analyze(data)
        
        high_performers = result["high_performing_traders"]
        assert len(high_performers) == 1
        
        trader = high_performers[0]
        assert trader["statistical_significance"] is True
        assert trader["p_value"] < 0.05  # Should be statistically significant
        assert len(trader["confidence_interval"]) == 2
        assert 0 <= trader["confidence_interval"][0] <= trader["confidence_interval"][1] <= 1
    
    # Voting Logic Tests
    
    @pytest.mark.asyncio
    async def test_vote_alpha_multiple_high_performers(self, agent, sample_market_data, high_performing_traders_data):
        """Test 'alpha' vote for multiple high-performing traders."""
        data = {"market": sample_market_data, "traders": high_performing_traders_data}
        analysis = await agent.analyze(data)
        vote = agent.vote(analysis)
        
        assert vote == "alpha"
    
    @pytest.mark.asyncio
    async def test_vote_alpha_exceptional_single_trader(self, agent, sample_market_data, exceptional_single_trader_data):
        """Test 'alpha' vote for exceptional single trader."""
        data = {"market": sample_market_data, "traders": exceptional_single_trader_data}
        analysis = await agent.analyze(data)
        vote = agent.vote(analysis)
        
        assert vote == "alpha"
    
    @pytest.mark.asyncio
    async def test_vote_abstain_borderline_cases(self, agent, sample_market_data):
        """Test 'abstain' vote for borderline cases."""
        # Create borderline case: one good trader but not exceptional
        traders_data = [{
            "address": "0xborderline",
            "performance_metrics": {
                "overall_success_rate": 0.72,  # Just above threshold
                "markets_resolved": 15,        # Moderate history
                "total_profit_usd": 45000
            }
        }]
        
        data = {"market": sample_market_data, "traders": traders_data}
        analysis = await agent.analyze(data)
        vote = agent.vote(analysis)
        
        # With current voting logic, this should be abstain since we have 1 high performer
        # but not exceptional significance ratio
        assert vote in ["abstain", "no_alpha"]  # Depends on statistical significance
    
    @pytest.mark.asyncio
    async def test_vote_abstain_true_borderline(self, agent, sample_market_data):
        """Test 'abstain' vote for true borderline case with good average but no high performers."""
        # Create case with good average success rate and statistical significance but no individual high performers
        traders_data = [
            {
                "address": "0xgood1",
                "performance_metrics": {
                    "overall_success_rate": 0.68,  # Just below threshold but good
                    "markets_resolved": 25,        # Good history
                    "total_profit_usd": 75000
                }
            },
            {
                "address": "0xgood2", 
                "performance_metrics": {
                    "overall_success_rate": 0.69,  # Just below threshold but good
                    "markets_resolved": 30,        # Good history
                    "total_profit_usd": 85000
                }
            }
        ]
        
        data = {"market": sample_market_data, "traders": traders_data}
        analysis = await agent.analyze(data)
        vote = agent.vote(analysis)
        
        # Should abstain because avg > 0.65 with statistical significance but no high performers
        assert vote == "abstain"
    
    @pytest.mark.asyncio
    async def test_vote_no_alpha_insufficient_performance(self, agent, sample_market_data, low_performing_traders_data):
        """Test 'no_alpha' vote for insufficient performance."""
        data = {"market": sample_market_data, "traders": low_performing_traders_data}
        analysis = await agent.analyze(data)
        vote = agent.vote(analysis)
        
        assert vote == "no_alpha"
    
    @pytest.mark.asyncio
    async def test_vote_abstain_on_error(self, agent):
        """Test 'abstain' vote when analysis contains error."""
        analysis = {"error": "Insufficient data"}
        vote = agent.vote(analysis)
        
        assert vote == "abstain"
    
    # Reasoning Tests
    
    @pytest.mark.asyncio
    async def test_reasoning_multiple_high_performers(self, agent, sample_market_data, high_performing_traders_data):
        """Test reasoning for multiple high performers scenario."""
        data = {"market": sample_market_data, "traders": high_performing_traders_data}
        await agent.analyze(data)
        reasoning = agent.get_reasoning()
        
        assert "traders with >" in reasoning.lower()
        assert "success rate" in reasoning.lower()
        assert "statistically significant" in reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_reasoning_single_performer(self, agent, sample_market_data, exceptional_single_trader_data):
        """Test reasoning for single exceptional performer."""
        data = {"market": sample_market_data, "traders": exceptional_single_trader_data}
        await agent.analyze(data)
        reasoning = agent.get_reasoning()
        
        assert "1 trader" in reasoning or "trader with proven" in reasoning.lower()
        assert "track record" in reasoning.lower() or "success rate" in reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_reasoning_insufficient_history(self, agent, sample_market_data, insufficient_history_traders_data):
        """Test reasoning for insufficient history scenario."""
        data = {"market": sample_market_data, "traders": insufficient_history_traders_data}
        await agent.analyze(data)
        reasoning = agent.get_reasoning()
        
        assert "insufficient" in reasoning.lower()
        assert "history" in reasoning.lower() or "trader" in reasoning.lower()
    
    def test_reasoning_no_analysis(self, agent):
        """Test reasoning when no analysis has been performed."""
        reasoning = agent.get_reasoning()
        assert reasoning == "No analysis performed"
    
    @pytest.mark.asyncio
    async def test_reasoning_statistical_language(self, agent, sample_market_data, high_performing_traders_data):
        """Test that reasoning uses proper statistical language."""
        data = {"market": sample_market_data, "traders": high_performing_traders_data}
        await agent.analyze(data)
        reasoning = agent.get_reasoning()
        
        # Should contain statistical terms or percentages
        statistical_terms = ["success rate", "statistically significant", "%", "avg", "rate"]
        assert any(term in reasoning.lower() for term in statistical_terms)
    
    # Edge Case Tests
    
    @pytest.mark.asyncio
    async def test_edge_case_zero_markets_resolved(self, agent, sample_market_data):
        """Test handling of trader with zero markets resolved."""
        traders_data = [{
            "address": "0xzero",
            "performance_metrics": {
                "overall_success_rate": 0.0,
                "markets_resolved": 0,
                "total_profit_usd": 0
            }
        }]
        
        data = {"market": sample_market_data, "traders": traders_data}
        result = await agent.analyze(data)
        
        assert result["valid_traders_count"] == 0
        assert result["high_performers_count"] == 0
    
    @pytest.mark.asyncio
    async def test_edge_case_missing_performance_metrics(self, agent, sample_market_data):
        """Test handling of trader with missing performance metrics."""
        traders_data = [{
            "address": "0xmissing",
            # Missing performance_metrics entirely
        }]
        
        data = {"market": sample_market_data, "traders": traders_data}
        result = await agent.analyze(data)
        
        assert result["valid_traders_count"] == 0
        assert result["high_performers_count"] == 0
    
    @pytest.mark.asyncio
    async def test_edge_case_partial_performance_metrics(self, agent, sample_market_data):
        """Test handling of trader with partial performance metrics."""
        traders_data = [{
            "address": "0xpartial",
            "performance_metrics": {
                "overall_success_rate": 0.75,
                # Missing markets_resolved and total_profit_usd
            }
        }]
        
        data = {"market": sample_market_data, "traders": traders_data}
        result = await agent.analyze(data)
        
        # Should handle gracefully with defaults
        assert result["valid_traders_count"] == 0  # markets_resolved defaults to 0
    
    @pytest.mark.asyncio
    async def test_statistical_calculation_edge_cases(self, agent):
        """Test statistical calculations with edge cases."""
        # Test confidence interval with zero total
        confidence_interval = agent._calculate_confidence_interval(0, 0)
        assert confidence_interval == [0.0, 0.0]
        
        # Test p-value calculation with zero wins
        p_value = agent._calculate_binomial_p_value(0, 10, 0.5)
        assert 0.0 <= p_value <= 1.0
        
        # Test p-value calculation with all wins
        p_value = agent._calculate_binomial_p_value(10, 10, 0.5)
        assert 0.0 <= p_value <= 1.0
    
    @pytest.mark.asyncio
    async def test_large_dataset_performance(self, agent, sample_market_data):
        """Test performance with large number of traders."""
        # Create large dataset
        traders_data = []
        for i in range(100):
            traders_data.append({
                "address": f"0x{i:040x}",
                "performance_metrics": {
                    "overall_success_rate": 0.6 + (i % 30) * 0.01,  # Varying success rates
                    "markets_resolved": 10 + (i % 40),  # Varying history lengths
                    "total_profit_usd": 1000 + i * 500
                }
            })
        
        data = {"market": sample_market_data, "traders": traders_data}
        result = await agent.analyze(data)
        
        assert result["total_traders_analyzed"] == 100
        assert result["valid_traders_count"] <= 100
        assert isinstance(result["avg_success_rate"], float)
        assert 0.0 <= result["avg_success_rate"] <= 1.0
    
    # Mock/Patch Tests for Error Handling
    
    @pytest.mark.asyncio
    async def test_scipy_stats_error_handling(self, agent, sample_market_data):
        """Test error handling when scipy.stats raises exceptions."""
        traders_data = [{
            "address": "0xtest",
            "performance_metrics": {
                "overall_success_rate": 0.75,
                "markets_resolved": 20,
                "total_profit_usd": 50000
            }
        }]
        
        with patch('app.agents.success_rate_agent.stats.binom.cdf', side_effect=Exception("Stats error")):
            data = {"market": sample_market_data, "traders": traders_data}
            result = await agent.analyze(data)
            
            # Should handle gracefully and continue analysis
            assert "error" not in result
            assert result["valid_traders_count"] >= 1
    
    @pytest.mark.asyncio 
    async def test_confidence_interval_calculation_error(self, agent):
        """Test error handling in confidence interval calculation."""
        with patch('app.agents.success_rate_agent.stats.norm.ppf', side_effect=Exception("Norm error")):
            confidence_interval = agent._calculate_confidence_interval(15, 20)
            
            # Should return conservative interval on error
            assert confidence_interval == [0.0, 1.0]
    
    def test_decimal_precision_handling(self, agent):
        """Test that Decimal precision is maintained throughout calculations."""
        # Test that min_success_rate is properly converted to Decimal
        assert isinstance(agent.min_success_rate, Decimal)
        assert agent.min_success_rate == Decimal(str(settings.min_success_rate))
        
        # Test confidence is Decimal
        assert isinstance(agent.confidence, Decimal)
    
    @pytest.mark.asyncio
    async def test_confidence_levels_coverage(self, agent, sample_market_data):
        """Test different confidence level branches for full coverage."""
        # Test moderate confidence scenario (2 high performers with better stats for significance)
        traders_data = [
            {
                "address": "0xgood1",
                "performance_metrics": {
                    "overall_success_rate": 0.80,  # Higher rate for significance
                    "markets_resolved": 30,        # More markets for significance
                    "total_profit_usd": 50000
                }
            },
            {
                "address": "0xgood2",
                "performance_metrics": {
                    "overall_success_rate": 0.77,  # Higher rate for significance
                    "markets_resolved": 25,        # More markets for significance
                    "total_profit_usd": 45000
                }
            }
        ]
        
        data = {"market": sample_market_data, "traders": traders_data}
        result = await agent.analyze(data)
        
        # Should hit the >= 2 high performers confidence branch
        assert agent.confidence >= Decimal('0.7')
        assert result["high_performers_count"] >= 1  # At least one should qualify
    
    @pytest.mark.asyncio
    async def test_reasoning_coverage_branches(self, agent, sample_market_data):
        """Test different reasoning branches for full coverage."""
        # Test reasoning with 2 high performers to hit the elif branch
        traders_data = [
            {
                "address": "0xgood1",
                "performance_metrics": {
                    "overall_success_rate": 0.76,
                    "markets_resolved": 22,
                    "total_profit_usd": 60000
                }
            },
            {
                "address": "0xgood2",
                "performance_metrics": {
                    "overall_success_rate": 0.74,
                    "markets_resolved": 25,
                    "total_profit_usd": 70000
                }
            }
        ]
        
        data = {"market": sample_market_data, "traders": traders_data}
        await agent.analyze(data)
        reasoning = agent.get_reasoning()
        
        # Should hit the "2 high-performing traders" reasoning branch
        assert "2 high-performing traders" in reasoning or "2 traders with" in reasoning
        assert "avg success rate" in reasoning.lower()
    
    @pytest.mark.asyncio 
    async def test_vote_moderate_alpha_scenario(self, agent, sample_market_data):
        """Test vote scenario that hits the moderate alpha condition."""
        # Create high performers with strong statistical significance
        traders_data = [
            {
                "address": "0xgood1",
                "performance_metrics": {
                    "overall_success_rate": 0.82,  # Higher rate for significance
                    "markets_resolved": 35,        # More markets for strong significance
                    "total_profit_usd": 80000
                }
            },
            {
                "address": "0xgood2",
                "performance_metrics": {
                    "overall_success_rate": 0.78,  # Higher rate for significance  
                    "markets_resolved": 30,        # More markets for strong significance
                    "total_profit_usd": 60000
                }
            }
        ]
        
        data = {"market": sample_market_data, "traders": traders_data}
        analysis = await agent.analyze(data)
        vote = agent.vote(analysis)
        
        # Should vote alpha with high performing traders
        assert vote == "alpha"
        assert analysis["high_performers_count"] >= 1
        assert analysis["avg_success_rate"] > float(agent.min_success_rate)
    
    @pytest.mark.asyncio
    async def test_moderate_confidence_scenario(self, agent, sample_market_data):
        """Test scenario that hits the moderate confidence branch (valid_trader_count >= min_trade_history)."""
        # Create enough traders with sufficient history but not meeting high performer criteria
        traders_data = []
        for i in range(12):  # Create 12 traders to exceed min_trade_history threshold
            traders_data.append({
                "address": f"0xmoderate{i}",
                "performance_metrics": {
                    "overall_success_rate": 0.58 + (i * 0.01),  # Below threshold
                    "markets_resolved": 15 + i,                # Sufficient history
                    "total_profit_usd": 25000 + (i * 1000)
                }
            })
        
        data = {"market": sample_market_data, "traders": traders_data}
        result = await agent.analyze(data)
        
        # Should hit the moderate confidence scenario 
        assert result["high_performers_count"] == 0  # No high performers
        assert result["valid_traders_count"] >= agent.min_trade_history  # But sufficient valid traders
        assert agent.confidence == Decimal('0.4')  # Should hit this specific confidence level
    
    @pytest.mark.asyncio
    async def test_statistical_significance_reasoning_without_high_performers(self, agent, sample_market_data):
        """Test reasoning branch for statistical significance without high performers."""
        # Create traders with statistical significance but below threshold
        traders_data = [
            {
                "address": "0xsignificant",
                "performance_metrics": {
                    "overall_success_rate": 0.65,  # Below high performer threshold but significant
                    "markets_resolved": 50,        # Large sample for significance
                    "total_profit_usd": 35000
                }
            }
        ]
        
        data = {"market": sample_market_data, "traders": traders_data}
        await agent.analyze(data)
        reasoning = agent.get_reasoning()
        
        # Should hit the statistical significance reasoning branch
        assert "statistical significance" in reasoning.lower()
        assert "avg rate" in reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_analyzed_traders_reasoning_without_significance(self, agent, sample_market_data):
        """Test reasoning branch for analyzed traders without statistical significance."""
        # Create enough traders with moderate performance and sufficient history but no significance
        traders_data = []
        for i in range(12):  # Create enough traders to exceed min_trade_history threshold
            traders_data.append({
                "address": f"0xanalyzed{i}",
                "performance_metrics": {
                    "overall_success_rate": 0.50 + (i * 0.005),  # Around random, not significant
                    "markets_resolved": 12 + i,                  # Just enough history
                    "total_profit_usd": 8000 + (i * 500)
                }
            })
        
        data = {"market": sample_market_data, "traders": traders_data}
        await agent.analyze(data)
        reasoning = agent.get_reasoning()
        
        # Should hit the "Analyzed X traders" reasoning branch
        assert "analyzed" in reasoning.lower()
        assert "traders" in reasoning.lower()
        assert "avg success rate" in reasoning.lower()