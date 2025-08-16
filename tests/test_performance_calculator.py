import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import time

from app.intelligence.performance_calculator import (
    PerformanceCalculator, MarketOutcome, MarketResolution, TraderPosition, PerformanceMetrics
)
from app.intelligence.market_outcome_tracker import (
    MarketOutcomeTracker, MarketResolutionData, PositionOutcome, OutcomeConfidence
)
from app.data.models import MarketOutcomeData, ComprehensivePerformanceMetrics

class TestPerformanceCalculator:
    """Test suite for performance calculator functionality."""
    
    @pytest.fixture
    def performance_calculator(self):
        """Create performance calculator instance for testing."""
        return PerformanceCalculator()
    
    @pytest.fixture
    def sample_trader_data(self):
        """Sample trader data for testing."""
        return {
            "address": "0x123456789abcdef",
            "total_portfolio_value_usd": 100000,
            "positions": [
                {
                    "market_id": "market_1",
                    "outcome_id": "yes",
                    "total_position_size_usd": 1000,
                    "entry_price": 0.6,
                    "first_entry_timestamp": int(time.time()) - 86400,  # 1 day ago
                    "status": "active"
                },
                {
                    "market_id": "market_2", 
                    "outcome_id": "no",
                    "total_position_size_usd": 1500,
                    "entry_price": 0.4,
                    "first_entry_timestamp": int(time.time()) - 172800,  # 2 days ago
                    "status": "closed",
                    "exit_timestamp": int(time.time()) - 86400
                }
            ]
        }
    
    @pytest.fixture
    def sample_market_outcomes(self):
        """Sample market outcomes for testing."""
        return {
            "market_1": MarketOutcome(
                market_id="market_1",
                resolution=MarketResolution.WIN,
                winning_outcome_id="yes",
                resolution_timestamp=int(time.time()),
                resolution_source="test",
                confidence_score=Decimal('0.95')
            ),
            "market_2": MarketOutcome(
                market_id="market_2",
                resolution=MarketResolution.LOSS,
                winning_outcome_id="yes",
                resolution_timestamp=int(time.time()),
                resolution_source="test",
                confidence_score=Decimal('0.90')
            )
        }
    
    @pytest.mark.asyncio
    async def test_calculate_trader_performance_basic(self, performance_calculator, 
                                                    sample_trader_data, sample_market_outcomes):
        """Test basic trader performance calculation."""
        
        # Test with resolved positions
        performance = await performance_calculator.calculate_trader_performance(
            sample_trader_data, sample_market_outcomes
        )
        
        # Basic assertions
        assert isinstance(performance, PerformanceMetrics)
        assert performance.total_trades == 2
        assert performance.winning_trades == 1  # Only market_1 is a win for this trader
        assert performance.losing_trades == 1
        assert 0 <= performance.success_rate <= 1
        assert len(performance.confidence_interval) == 2
        assert performance.total_invested > 0
    
    @pytest.mark.asyncio
    async def test_calculate_trader_performance_empty_data(self, performance_calculator):
        """Test performance calculation with empty data."""
        
        empty_trader_data = {"address": "0x123", "positions": []}
        empty_outcomes = {}
        
        performance = await performance_calculator.calculate_trader_performance(
            empty_trader_data, empty_outcomes
        )
        
        # Should return empty metrics
        assert performance.total_trades == 0
        assert performance.success_rate == Decimal('0')
        assert performance.total_invested == Decimal('0')
    
    @pytest.mark.asyncio 
    async def test_track_market_outcomes(self, performance_calculator):
        """Test market outcome tracking."""
        
        resolution_data = {
            "resolution": "win",
            "winning_outcome_id": "yes",
            "resolution_timestamp": int(time.time()),
            "resolution_source": "official",
            "confidence_score": 0.95
        }
        
        outcome = await performance_calculator.track_market_outcomes("test_market", resolution_data)
        
        assert outcome.market_id == "test_market"
        assert outcome.resolution == MarketResolution.WIN
        assert outcome.winning_outcome_id == "yes"
        assert outcome.confidence_score == Decimal('0.95')
    
    def test_calculate_success_rate(self, performance_calculator):
        """Test success rate calculation with confidence intervals."""
        
        # Create test positions
        positions = [
            TraderPosition(
                market_id="market_1", outcome_id="yes", position_size_usd=Decimal('1000'),
                entry_price=Decimal('0.6'), entry_timestamp=int(time.time())
            ),
            TraderPosition(
                market_id="market_2", outcome_id="no", position_size_usd=Decimal('1500'),
                entry_price=Decimal('0.4'), entry_timestamp=int(time.time())
            ),
            TraderPosition(
                market_id="market_3", outcome_id="yes", position_size_usd=Decimal('800'),
                entry_price=Decimal('0.7'), entry_timestamp=int(time.time())
            )
        ]
        
        # Create outcomes (2 wins, 1 loss)
        outcomes = {
            "market_1": MarketOutcome(
                market_id="market_1", resolution=MarketResolution.WIN,
                winning_outcome_id="yes", resolution_timestamp=int(time.time()),
                resolution_source="test", confidence_score=Decimal('0.95')
            ),
            "market_2": MarketOutcome(
                market_id="market_2", resolution=MarketResolution.WIN,
                winning_outcome_id="yes", resolution_timestamp=int(time.time()),
                resolution_source="test", confidence_score=Decimal('0.90')
            ),
            "market_3": MarketOutcome(
                market_id="market_3", resolution=MarketResolution.WIN,
                winning_outcome_id="yes", resolution_timestamp=int(time.time()),
                resolution_source="test", confidence_score=Decimal('0.85')
            )
        }
        
        result = performance_calculator.calculate_success_rate(positions, outcomes)
        
        assert result["success_rate"] == Decimal('1.0')  # All wins
        assert result["total_trades"] == 3
        assert result["winning_trades"] == 3
        assert len(result["confidence_interval"]) == 2
        assert len(result["wilson_score_interval"]) == 2
    
    def test_calculate_risk_adjusted_returns(self, performance_calculator):
        """Test risk-adjusted returns calculation."""
        
        # Create positions with various outcomes
        positions = [
            TraderPosition(
                market_id="market_1", outcome_id="yes", position_size_usd=Decimal('1000'),
                entry_price=Decimal('0.6'), entry_timestamp=int(time.time()),
                exit_price=Decimal('1.0'), status="closed"
            ),
            TraderPosition(
                market_id="market_2", outcome_id="no", position_size_usd=Decimal('1500'),
                entry_price=Decimal('0.4'), entry_timestamp=int(time.time()),
                exit_price=Decimal('0.0'), status="closed"
            )
        ]
        
        result = performance_calculator.calculate_risk_adjusted_returns(positions)
        
        assert "sharpe_ratio" in result
        assert "sortino_ratio" in result
        assert "volatility" in result
        assert "max_drawdown" in result
        assert isinstance(result["mean_return"], Decimal)
    
    @pytest.mark.asyncio
    async def test_analyze_performance_trends(self, performance_calculator):
        """Test performance trend analysis."""
        
        # Create sample trading history
        trading_history = [
            {
                "timestamp": int(time.time()) - 86400 * 30,  # 30 days ago
                "profit_loss": 100,
                "position_size": 1000,
                "outcome": "win"
            },
            {
                "timestamp": int(time.time()) - 86400 * 20,  # 20 days ago
                "profit_loss": -50,
                "position_size": 800,
                "outcome": "loss"
            },
            {
                "timestamp": int(time.time()) - 86400 * 10,  # 10 days ago
                "profit_loss": 200,
                "position_size": 1200,
                "outcome": "win"
            }
        ]
        
        time_periods = ["30d", "90d"]
        trends = performance_calculator.analyze_performance_trends(trading_history, time_periods)
        
        assert len(trends) > 0
        for trend in trends:
            assert hasattr(trend, 'time_period')
            assert hasattr(trend, 'success_rate')
            assert hasattr(trend, 'trade_count')
            assert hasattr(trend, 'roi_percentage')
            assert hasattr(trend, 'trend_direction')
    
    def test_validate_statistical_significance(self, performance_calculator):
        """Test statistical significance validation."""
        
        # Test with sufficient sample size
        performance_data = {
            "success_rate": 0.75,
            "total_trades": 20,
            "winning_trades": 15
        }
        
        result = performance_calculator.validate_statistical_significance(performance_data)
        
        assert "is_significant" in result
        assert isinstance(result["is_significant"], bool)
        
        if result.get("p_value") is not None:
            assert 0 <= result["p_value"] <= 1
        
        # Test with insufficient sample size
        small_sample_data = {
            "success_rate": 0.8,
            "total_trades": 5,
            "winning_trades": 4
        }
        
        small_result = performance_calculator.validate_statistical_significance(small_sample_data)
        assert small_result["is_significant"] == False
        assert "Insufficient sample size" in small_result["reason"]


class TestMarketOutcomeTracker:
    """Test suite for market outcome tracker functionality."""
    
    @pytest.fixture
    def outcome_tracker(self):
        """Create market outcome tracker instance for testing."""
        return MarketOutcomeTracker()
    
    @pytest.fixture
    def sample_resolution_data(self):
        """Sample resolution data for testing."""
        return {
            "winning_outcome_id": "yes",
            "winning_outcome_name": "Yes",
            "resolution_timestamp": int(time.time()),
            "resolution_source": "official",
            "verification_count": 2,
            "payout_ratio": 1.0,
            "final_price": 1.0,
            "title": "Test Market",
            "description": "Test market description",
            "total_volume": 100000
        }
    
    @pytest.mark.asyncio
    async def test_track_market_resolution(self, outcome_tracker, sample_resolution_data):
        """Test market resolution tracking."""
        
        resolution = await outcome_tracker.track_market_resolution(
            "test_market", sample_resolution_data
        )
        
        assert isinstance(resolution, MarketResolutionData)
        assert resolution.market_id == "test_market"
        assert resolution.winning_outcome_id == "yes"
        assert resolution.confidence_level in [OutcomeConfidence.HIGH, OutcomeConfidence.VERIFIED]
        
        # Verify it's stored
        assert "test_market" in outcome_tracker.market_outcomes
    
    @pytest.mark.asyncio
    async def test_correlate_trader_positions(self, outcome_tracker):
        """Test trader position correlation with outcomes."""
        
        # First add a market resolution
        resolution_data = {
            "winning_outcome_id": "yes",
            "resolution_timestamp": int(time.time()),
            "resolution_source": "test",
            "verification_count": 1,
            "payout_ratio": 1.0,
            "final_price": 1.0,
            "title": "Test Market"
        }
        
        await outcome_tracker.track_market_resolution("market_1", resolution_data)
        
        # Test trader positions
        positions = [
            {
                "market_id": "market_1",
                "outcome_id": "yes",
                "position_size_usd": 1000,
                "entry_price": 0.6
            },
            {
                "market_id": "market_2",  # Unresolved market
                "outcome_id": "no", 
                "position_size_usd": 800,
                "entry_price": 0.4
            }
        ]
        
        outcomes = await outcome_tracker.correlate_trader_positions("test_trader", positions)
        
        assert len(outcomes) == 1  # Only market_1 is resolved
        assert outcomes[0].market_id == "market_1"
        assert outcomes[0].is_winner == True  # Position on "yes", market resolved to "yes"
        assert outcomes[0].profit_loss > 0  # Should be profitable
    
    @pytest.mark.asyncio
    async def test_get_trader_performance_history(self, outcome_tracker):
        """Test comprehensive trader performance history retrieval."""
        
        # Set up some position outcomes
        trader_address = "test_trader"
        position_outcomes = [
            PositionOutcome(
                trader_address=trader_address,
                market_id="market_1",
                position_outcome_id="yes",
                position_size_usd=Decimal('1000'),
                entry_price=Decimal('0.6'),
                final_payout=Decimal('1667'),  # 1000/0.6
                profit_loss=Decimal('667'),
                is_winner=True,
                roi_percentage=Decimal('66.7')
            ),
            PositionOutcome(
                trader_address=trader_address,
                market_id="market_2", 
                position_outcome_id="no",
                position_size_usd=Decimal('800'),
                entry_price=Decimal('0.4'),
                final_payout=Decimal('0'),
                profit_loss=Decimal('-800'),
                is_winner=False,
                roi_percentage=Decimal('-100')
            )
        ]
        
        outcome_tracker.position_outcomes[trader_address] = position_outcomes
        
        history = await outcome_tracker.get_trader_performance_history(trader_address)
        
        assert history["trader_address"] == trader_address
        assert history["total_trades"] == 2
        assert history["winning_trades"] == 1
        assert history["losing_trades"] == 1
        assert history["success_rate"] == 0.5
        assert "confidence_interval" in history
        assert "volatility" in history
        assert "data_quality" in history
    
    def test_get_market_outcome_statistics(self, outcome_tracker):
        """Test market outcome statistics generation."""
        
        # Add some test resolutions
        outcome_tracker.market_outcomes["market_1"] = MarketResolutionData(
            market_id="market_1",
            title="Test Market 1",
            description="Description 1",
            resolution_timestamp=int(time.time()),
            winning_outcome_id="yes",
            winning_outcome_name="Yes",
            resolution_source="official",
            confidence_level=OutcomeConfidence.HIGH,
            payout_ratio=Decimal('1.0'),
            total_volume=Decimal('50000'),
            final_price=Decimal('1.0'),
            verification_count=2
        )
        
        outcome_tracker.market_outcomes["market_2"] = MarketResolutionData(
            market_id="market_2",
            title="Test Market 2", 
            description="Description 2",
            resolution_timestamp=int(time.time()),
            winning_outcome_id="no",
            winning_outcome_name="No",
            resolution_source="verified",
            confidence_level=OutcomeConfidence.VERIFIED,
            payout_ratio=Decimal('1.0'),
            total_volume=Decimal('75000'),
            final_price=Decimal('1.0'),
            verification_count=3
        )
        
        stats = outcome_tracker.get_market_outcome_statistics()
        
        assert stats["total_markets"] == 2
        assert "confidence_distribution" in stats
        assert "resolution_sources" in stats
        assert stats["high_confidence_count"] == 2
        assert stats["total_volume_resolved"] == 125000.0


class TestPerformanceCalculatorIntegration:
    """Integration tests for performance calculator with other components."""
    
    @pytest.fixture
    def integrated_system(self):
        """Create integrated system with performance calculator and outcome tracker."""
        performance_calc = PerformanceCalculator()
        outcome_tracker = MarketOutcomeTracker()
        return performance_calc, outcome_tracker
    
    @pytest.mark.asyncio
    async def test_end_to_end_performance_calculation(self, integrated_system):
        """Test end-to-end performance calculation flow."""
        performance_calc, outcome_tracker = integrated_system
        
        # 1. Track market resolution
        resolution_data = {
            "winning_outcome_id": "yes",
            "winning_outcome_name": "Yes",
            "resolution_timestamp": int(time.time()),
            "resolution_source": "official", 
            "verification_count": 2,
            "payout_ratio": 1.0,
            "final_price": 1.0,
            "title": "Integration Test Market",
            "description": "Test market for integration",
            "total_volume": 100000
        }
        
        await outcome_tracker.track_market_resolution("integration_market", resolution_data)
        
        # 2. Correlate trader positions
        trader_data = {
            "address": "0xintegration_test",
            "total_portfolio_value_usd": 50000,
            "positions": [
                {
                    "market_id": "integration_market",
                    "outcome_id": "yes",
                    "total_position_size_usd": 2000,
                    "entry_price": 0.5,
                    "first_entry_timestamp": int(time.time()) - 86400
                }
            ]
        }
        
        position_outcomes = await outcome_tracker.correlate_trader_positions(
            trader_data["address"], trader_data["positions"]
        )
        
        # 3. Calculate comprehensive performance
        market_outcomes = {
            "integration_market": MarketOutcome(
                market_id="integration_market",
                resolution=MarketResolution.WIN,
                winning_outcome_id="yes",
                resolution_timestamp=int(time.time()),
                resolution_source="official",
                confidence_score=Decimal('0.95')
            )
        }
        
        performance = await performance_calc.calculate_trader_performance(
            trader_data, market_outcomes
        )
        
        # 4. Verify end-to-end results
        assert len(position_outcomes) == 1
        assert position_outcomes[0].is_winner == True
        assert position_outcomes[0].profit_loss > 0
        
        assert performance.total_trades == 1
        assert performance.winning_trades == 1
        assert performance.success_rate == Decimal('1.0')
        assert performance.net_profit > 0
        assert performance.roi_percentage > 0
    
    @pytest.mark.asyncio
    async def test_performance_with_multiple_markets(self, integrated_system):
        """Test performance calculation across multiple markets."""
        performance_calc, outcome_tracker = integrated_system
        
        # Track multiple market resolutions
        markets = [
            ("market_a", "yes", "win"),
            ("market_b", "no", "loss"), 
            ("market_c", "yes", "win")
        ]
        
        market_outcomes = {}
        
        for market_id, outcome_id, resolution in markets:
            resolution_data = {
                "winning_outcome_id": "yes" if resolution == "win" else "no",
                "resolution_timestamp": int(time.time()),
                "resolution_source": "test",
                "verification_count": 1,
                "payout_ratio": 1.0,
                "final_price": 1.0,
                "title": f"Test Market {market_id}"
            }
            
            await outcome_tracker.track_market_resolution(market_id, resolution_data)
            
            market_outcomes[market_id] = MarketOutcome(
                market_id=market_id,
                resolution=MarketResolution.WIN if resolution == "win" else MarketResolution.LOSS,
                winning_outcome_id=resolution_data["winning_outcome_id"],
                resolution_timestamp=int(time.time()),
                resolution_source="test",
                confidence_score=Decimal('0.9')
            )
        
        # Create trader with positions in all markets
        trader_data = {
            "address": "0xmulti_market_trader",
            "total_portfolio_value_usd": 100000,
            "positions": [
                {
                    "market_id": "market_a",
                    "outcome_id": "yes", 
                    "total_position_size_usd": 1000,
                    "entry_price": 0.6
                },
                {
                    "market_id": "market_b",
                    "outcome_id": "no",
                    "total_position_size_usd": 1500, 
                    "entry_price": 0.3
                },
                {
                    "market_id": "market_c",
                    "outcome_id": "yes",
                    "total_position_size_usd": 800,
                    "entry_price": 0.7
                }
            ]
        }
        
        performance = await performance_calc.calculate_trader_performance(
            trader_data, market_outcomes
        )
        
        # Verify multi-market performance calculation
        assert performance.total_trades == 3
        assert performance.winning_trades == 2  # market_a and market_c
        assert performance.losing_trades == 1   # market_b
        assert abs(performance.success_rate - Decimal('0.6667')) < Decimal('0.001')
        assert performance.total_invested > 0
        assert len(performance.confidence_interval) == 2


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.fixture
    def performance_calculator(self):
        return PerformanceCalculator()
    
    @pytest.mark.asyncio
    async def test_invalid_trader_data(self, performance_calculator):
        """Test handling of invalid trader data."""
        
        invalid_data = {"address": "0xinvalid"}  # Missing positions
        outcomes = {}
        
        performance = await performance_calculator.calculate_trader_performance(
            invalid_data, outcomes
        )
        
        # Should return empty metrics without crashing
        assert performance.total_trades == 0
        assert performance.success_rate == Decimal('0')
    
    @pytest.mark.asyncio
    async def test_malformed_position_data(self, performance_calculator):
        """Test handling of malformed position data."""
        
        trader_data = {
            "address": "0xmalformed",
            "positions": [
                {
                    "market_id": "test_market",
                    # Missing required fields
                },
                {
                    "market_id": "test_market_2",
                    "outcome_id": "yes",
                    "total_position_size_usd": "invalid_amount",  # Invalid type
                    "entry_price": 0.5
                }
            ]
        }
        
        outcomes = {}
        
        # Should handle gracefully
        performance = await performance_calculator.calculate_trader_performance(
            trader_data, outcomes
        )
        
        # Should not crash and return valid metrics structure
        assert isinstance(performance, PerformanceMetrics)
    
    def test_statistical_edge_cases(self, performance_calculator):
        """Test statistical calculations with edge cases."""
        
        # Test with zero trades
        result = performance_calculator.validate_statistical_significance({
            "success_rate": 0.5,
            "total_trades": 0,
            "winning_trades": 0
        })
        
        assert result["is_significant"] == False
        
        # Test with perfect success rate
        result = performance_calculator.validate_statistical_significance({
            "success_rate": 1.0,
            "total_trades": 20,
            "winning_trades": 20
        })
        
        assert isinstance(result["is_significant"], bool)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])