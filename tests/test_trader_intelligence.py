import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import datetime, timedelta
from app.intelligence.trader_analyzer import (
    TraderAnalyzer, TraderProfile, PortfolioMetrics, 
    TradingPatternAnalysis, RiskAssessment
)
from app.data.blockchain_client import BlockchainClient

class TestTraderAnalyzer:
    """Comprehensive test suite for trader intelligence module."""
    
    @pytest.fixture
    def mock_blockchain_client(self):
        """Create mock blockchain client."""
        client = Mock(spec=BlockchainClient)
        client.get_trader_portfolio = AsyncMock()
        client.get_transaction_history = AsyncMock()
        client.is_connected = Mock(return_value=True)
        return client
    
    @pytest.fixture
    def trader_analyzer(self, mock_blockchain_client):
        """Create trader analyzer with mocked dependencies."""
        return TraderAnalyzer(mock_blockchain_client)
    
    @pytest.fixture
    def sample_portfolio_data(self):
        """Sample portfolio data for testing."""
        return {
            "address": "0x123456789abcdef",
            "total_portfolio_value_usd": 100000,
            "active_positions": 5,
            "positions": [
                {
                    "market_id": "market_1",
                    "total_position_size_usd": 25000,
                    "current_value_usd": 27000,
                    "first_entry_timestamp": 1640995200,  # Jan 1, 2022
                    "last_entry_timestamp": 1640995200
                },
                {
                    "market_id": "market_2", 
                    "total_position_size_usd": 15000,
                    "current_value_usd": 14000,
                    "first_entry_timestamp": 1641081600,  # Jan 2, 2022
                    "last_entry_timestamp": 1641081600
                },
                {
                    "market_id": "market_3",
                    "total_position_size_usd": 20000,
                    "current_value_usd": 22000,
                    "first_entry_timestamp": 1641168000,  # Jan 3, 2022
                    "last_entry_timestamp": 1641168000
                },
                {
                    "market_id": "market_4",
                    "total_position_size_usd": 10000,
                    "current_value_usd": 9500,
                    "first_entry_timestamp": 1641254400,  # Jan 4, 2022
                    "last_entry_timestamp": 1641254400
                },
                {
                    "market_id": "market_5",
                    "total_position_size_usd": 30000,
                    "current_value_usd": 32000,
                    "first_entry_timestamp": 1641340800,  # Jan 5, 2022
                    "last_entry_timestamp": 1641340800
                }
            ],
            "eth_balance_usd": 5000,
            "usdc_balance": 2000,
            "last_updated": 1673036400
        }
    
    @pytest.fixture
    def sample_transaction_history(self):
        """Sample transaction history for testing."""
        return [
            {
                "hash": "0xtx1",
                "to": "0x4d97dcd97ec945f40cf65f87097ace5ea0476045",
                "value": "1000000000000000000",  # 1 ETH
                "timeStamp": "1640995200",
                "isError": "0",
                "gasUsed": "150000"
            },
            {
                "hash": "0xtx2", 
                "to": "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e",
                "value": "500000000000000000",  # 0.5 ETH
                "timeStamp": "1641081600",
                "isError": "0",
                "gasUsed": "120000"
            },
            {
                "hash": "0xtx3",
                "to": "0x4d97dcd97ec945f40cf65f87097ace5ea0476045", 
                "value": "2000000000000000000",  # 2 ETH
                "timeStamp": "1641168000",
                "isError": "0",
                "gasUsed": "180000"
            }
        ]

class TestPortfolioMetrics(TestTraderAnalyzer):
    """Test portfolio composition analysis."""
    
    def test_calculate_portfolio_metrics_basic(self, trader_analyzer, sample_portfolio_data):
        """Test basic portfolio metrics calculation."""
        positions = sample_portfolio_data["positions"]
        total_value = Decimal(str(sample_portfolio_data["total_portfolio_value_usd"]))
        
        metrics = trader_analyzer.calculate_portfolio_metrics(positions, total_value)
        
        assert isinstance(metrics, PortfolioMetrics)
        assert metrics.total_value_usd == total_value
        assert metrics.position_count == 5
        assert 0 <= metrics.diversification_score <= 1
        assert metrics.concentration_risk in ["minimal", "low", "moderate", "high"]
    
    def test_portfolio_allocation_ratios(self, trader_analyzer, sample_portfolio_data):
        """Test portfolio allocation ratio calculations."""
        positions = sample_portfolio_data["positions"]
        total_value = Decimal(str(sample_portfolio_data["total_portfolio_value_usd"]))
        
        metrics = trader_analyzer.calculate_portfolio_metrics(positions, total_value)
        
        # Largest position is 30,000 / 100,000 = 0.30 (30%)
        assert metrics.max_single_allocation == Decimal('0.30')
        
        # Average allocation should be 1/5 = 0.20 (20%)
        expected_avg = Decimal('0.20')
        assert abs(metrics.avg_allocation_per_position - expected_avg) < Decimal('0.01')
    
    def test_diversification_score_calculation(self, trader_analyzer):
        """Test diversification score calculation with different scenarios."""
        # Scenario 1: Perfectly diversified (equal allocations)
        positions_equal = [
            {"market_id": f"market_{i}", "total_position_size_usd": 20000}
            for i in range(5)
        ]
        total_value = Decimal('100000')
        
        metrics_equal = trader_analyzer.calculate_portfolio_metrics(positions_equal, total_value)
        assert metrics_equal.diversification_score > Decimal('0.8')  # High diversification
        
        # Scenario 2: Concentrated portfolio
        positions_concentrated = [
            {"market_id": "market_1", "total_position_size_usd": 80000},
            {"market_id": "market_2", "total_position_size_usd": 20000}
        ]
        
        metrics_concentrated = trader_analyzer.calculate_portfolio_metrics(positions_concentrated, total_value)
        assert metrics_concentrated.diversification_score < Decimal('0.5')  # Low diversification
    
    def test_concentration_risk_assessment(self, trader_analyzer):
        """Test concentration risk classification."""
        total_value = Decimal('100000')
        
        # High concentration (50%+ in one position)
        positions_high_risk = [
            {"market_id": "market_1", "total_position_size_usd": 60000},
            {"market_id": "market_2", "total_position_size_usd": 40000}
        ]
        
        metrics_high = trader_analyzer.calculate_portfolio_metrics(positions_high_risk, total_value)
        assert metrics_high.concentration_risk in ["high", "moderate"]
        
        # Low concentration (well diversified)
        positions_low_risk = [
            {"market_id": f"market_{i}", "total_position_size_usd": 10000}
            for i in range(10)
        ]
        
        metrics_low = trader_analyzer.calculate_portfolio_metrics(positions_low_risk, total_value)
        assert metrics_low.concentration_risk in ["minimal", "low"]
    
    def test_empty_positions_handling(self, trader_analyzer):
        """Test handling of empty positions list."""
        metrics = trader_analyzer.calculate_portfolio_metrics([], Decimal('0'))
        
        assert metrics.total_value_usd == Decimal('0')
        assert metrics.position_count == 0
        assert metrics.diversification_score == Decimal('0')
        assert metrics.concentration_risk == "unknown"

class TestTradingPatterns(TestTraderAnalyzer):
    """Test trading pattern analysis."""
    
    @pytest.mark.asyncio
    async def test_assess_trading_patterns_basic(self, trader_analyzer, sample_portfolio_data):
        """Test basic trading pattern assessment."""
        patterns = await trader_analyzer.assess_trading_patterns(sample_portfolio_data)
        
        assert isinstance(patterns, TradingPatternAnalysis)
        assert patterns.entry_timing_preference in ["early", "mixed", "late", "unknown"]
        assert patterns.hold_duration_avg_days >= 0
        assert patterns.position_sizing_style in ["consistent", "moderate", "variable", "unknown"]
        assert patterns.market_selection_pattern in ["specialist", "focused", "generalist"]
        assert patterns.risk_adjustment_behavior in ["static", "dynamic", "unknown"]
    
    @pytest.mark.asyncio
    async def test_position_sizing_style_analysis(self, trader_analyzer):
        """Test position sizing style classification."""
        # Consistent sizing
        consistent_data = {
            "positions": [
                {"total_position_size_usd": 10000} for _ in range(5)
            ]
        }
        
        patterns_consistent = await trader_analyzer.assess_trading_patterns(consistent_data)
        assert patterns_consistent.position_sizing_style == "consistent"
        
        # Variable sizing
        variable_data = {
            "positions": [
                {"total_position_size_usd": 1000},
                {"total_position_size_usd": 50000},
                {"total_position_size_usd": 5000},
                {"total_position_size_usd": 25000}
            ]
        }
        
        patterns_variable = await trader_analyzer.assess_trading_patterns(variable_data)
        assert patterns_variable.position_sizing_style in ["variable", "moderate"]
    
    @pytest.mark.asyncio 
    async def test_market_selection_pattern(self, trader_analyzer):
        """Test market selection pattern classification."""
        # Specialist (single sector)
        specialist_data = {
            "positions": [
                {"market_id": "trump_election_1"},
                {"market_id": "biden_election_2"},
                {"market_id": "election_outcome_3"}
            ]
        }
        
        patterns_specialist = await trader_analyzer.assess_trading_patterns(specialist_data)
        # Should classify as specialist since all are political markets
        assert patterns_specialist.market_selection_pattern in ["specialist", "focused"]
        
        # Generalist (multiple sectors)
        generalist_data = {
            "positions": [
                {"market_id": "trump_election"},
                {"market_id": "btc_price"},
                {"market_id": "nfl_superbowl"},
                {"market_id": "fed_rates"}
            ]
        }
        
        patterns_generalist = await trader_analyzer.assess_trading_patterns(generalist_data)
        assert patterns_generalist.market_selection_pattern == "generalist"

class TestRiskAssessment(TestTraderAnalyzer):
    """Test risk assessment calculations."""
    
    def test_calculate_risk_profile_basic(self, trader_analyzer, sample_portfolio_data):
        """Test basic risk profile calculation."""
        risk_assessment = trader_analyzer.calculate_risk_profile(sample_portfolio_data)
        
        assert isinstance(risk_assessment, RiskAssessment)
        assert 0 <= risk_assessment.overall_risk_score <= 1
        assert risk_assessment.risk_level in ["low", "moderate", "high", "extreme", "unknown"]
        assert 0 <= risk_assessment.portfolio_concentration_risk <= 1
        assert 0 <= risk_assessment.position_sizing_risk <= 1
    
    def test_concentration_risk_calculation(self, trader_analyzer):
        """Test portfolio concentration risk calculation."""
        # High concentration scenario
        high_concentration_data = {
            "total_portfolio_value_usd": 100000,
            "positions": [
                {"total_position_size_usd": 70000},  # 70% concentration
                {"total_position_size_usd": 30000}
            ]
        }
        
        risk_high = trader_analyzer.calculate_risk_profile(high_concentration_data)
        assert risk_high.portfolio_concentration_risk >= Decimal('0.7')
        
        # Low concentration scenario
        low_concentration_data = {
            "total_portfolio_value_usd": 100000,
            "positions": [
                {"total_position_size_usd": 10000} for _ in range(10)
            ]
        }
        
        risk_low = trader_analyzer.calculate_risk_profile(low_concentration_data)
        assert risk_low.portfolio_concentration_risk <= Decimal('0.5')
    
    def test_position_sizing_risk_calculation(self, trader_analyzer):
        """Test position sizing risk calculation."""
        # Consistent position sizing (low risk)
        consistent_data = {
            "total_portfolio_value_usd": 100000,
            "positions": [
                {"total_position_size_usd": 20000} for _ in range(5)
            ]
        }
        
        risk_consistent = trader_analyzer.calculate_risk_profile(consistent_data)
        assert risk_consistent.position_sizing_risk <= Decimal('0.4')
        
        # Highly variable position sizing (high risk)
        variable_data = {
            "total_portfolio_value_usd": 100000,
            "positions": [
                {"total_position_size_usd": 1000},
                {"total_position_size_usd": 80000},
                {"total_position_size_usd": 5000},
                {"total_position_size_usd": 14000}
            ]
        }
        
        risk_variable = trader_analyzer.calculate_risk_profile(variable_data)
        assert risk_variable.position_sizing_risk >= Decimal('0.5')
    
    def test_overall_risk_score_calculation(self, trader_analyzer):
        """Test overall risk score weighting."""
        # Low risk scenario
        low_risk_data = {
            "total_portfolio_value_usd": 100000,
            "positions": [
                {"total_position_size_usd": 20000, "first_entry_timestamp": 1640995200} 
                for _ in range(5)
            ]
        }
        
        risk_low = trader_analyzer.calculate_risk_profile(low_risk_data)
        assert risk_low.overall_risk_score <= Decimal('0.6')
        assert risk_low.risk_level in ["low", "moderate"]
        
        # High risk scenario
        high_risk_data = {
            "total_portfolio_value_usd": 100000,
            "positions": [
                {"total_position_size_usd": 90000, "first_entry_timestamp": 1640995200},
                {"total_position_size_usd": 10000, "first_entry_timestamp": 1640995200}
            ]
        }
        
        risk_high = trader_analyzer.calculate_risk_profile(high_risk_data)
        assert risk_high.overall_risk_score >= Decimal('0.6')

class TestConvictionSignals(TestTraderAnalyzer):
    """Test conviction signal identification."""
    
    def test_identify_conviction_signals_basic(self, trader_analyzer, sample_portfolio_data):
        """Test basic conviction signal identification."""
        positions = sample_portfolio_data["positions"]
        total_value = Decimal(str(sample_portfolio_data["total_portfolio_value_usd"]))
        
        signals = trader_analyzer.identify_conviction_signals(positions, total_value)
        
        assert isinstance(signals, list)
        for signal in signals:
            assert "type" in signal
            assert "market_id" in signal
            assert "confidence" in signal
            assert "reasoning" in signal
            assert signal["type"] in [
                "high_allocation", "significant_position", 
                "early_entry", "sustained_position"
            ]
    
    def test_high_allocation_signal_detection(self, trader_analyzer):
        """Test detection of high allocation signals."""
        positions = [
            {
                "market_id": "market_high_conviction",
                "total_position_size_usd": 25000,  # 25% of 100k portfolio
                "first_entry_timestamp": 1640995200
            },
            {
                "market_id": "market_normal",
                "total_position_size_usd": 5000,   # 5% of portfolio
                "first_entry_timestamp": 1641081600
            }
        ]
        total_value = Decimal('100000')
        
        signals = trader_analyzer.identify_conviction_signals(positions, total_value)
        
        # Should detect high allocation signal for first position
        high_allocation_signals = [s for s in signals if s["type"] == "high_allocation"]
        assert len(high_allocation_signals) >= 1
        assert high_allocation_signals[0]["market_id"] == "market_high_conviction"
        assert high_allocation_signals[0]["confidence"] == "high"
    
    def test_early_entry_signal_detection(self, trader_analyzer):
        """Test detection of early entry signals."""
        # Mock the early entry detection
        with patch.object(trader_analyzer, '_is_early_entry', return_value=True):
            positions = [
                {
                    "market_id": "market_early",
                    "total_position_size_usd": 8000,  # 8% - significant but not high
                    "first_entry_timestamp": 1640995200
                }
            ]
            total_value = Decimal('100000')
            
            signals = trader_analyzer.identify_conviction_signals(positions, total_value)
            
            early_signals = [s for s in signals if s["type"] == "early_entry"]
            assert len(early_signals) >= 1
    
    def test_sustained_position_signal_detection(self, trader_analyzer):
        """Test detection of sustained position signals."""
        # Mock sustained position detection
        with patch.object(trader_analyzer, '_is_sustained_position', return_value=True):
            positions = [
                {
                    "market_id": "market_sustained",
                    "total_position_size_usd": 6000,  # 6% - significant
                    "first_entry_timestamp": 1640995200,
                    "last_entry_timestamp": 1640995200
                }
            ]
            total_value = Decimal('100000')
            
            signals = trader_analyzer.identify_conviction_signals(positions, total_value)
            
            sustained_signals = [s for s in signals if s["type"] == "sustained_position"]
            assert len(sustained_signals) >= 1

class TestTraderBehaviorAnalysis(TestTraderAnalyzer):
    """Test comprehensive trader behavior analysis."""
    
    @pytest.mark.asyncio
    async def test_analyze_trader_behavior_success(self, trader_analyzer, sample_portfolio_data):
        """Test successful trader behavior analysis."""
        trader_analyzer.blockchain_client.get_trader_portfolio.return_value = sample_portfolio_data
        
        result = await trader_analyzer.analyze_trader_behavior("0x123456789abcdef")
        
        assert "error" not in result
        assert result["address"] == "0x123456789abcdef"
        assert "trader_profile" in result
        assert "portfolio_metrics" in result
        assert "trading_patterns" in result
        assert "risk_assessment" in result
        assert "conviction_signals" in result
        assert "intelligence_score" in result
        assert "key_insights" in result
        assert "confidence_level" in result
    
    @pytest.mark.asyncio
    async def test_analyze_trader_behavior_blockchain_error(self, trader_analyzer):
        """Test handling of blockchain errors."""
        trader_analyzer.blockchain_client.get_trader_portfolio.return_value = {
            "error": "Invalid address or blockchain connection issue"
        }
        
        result = await trader_analyzer.analyze_trader_behavior("0xinvalid")
        
        assert "error" in result
        assert result["address"] == "0xinvalid"
    
    @pytest.mark.asyncio
    async def test_analyze_trader_behavior_insufficient_data(self, trader_analyzer):
        """Test handling of insufficient data scenarios."""
        insufficient_data = {
            "address": "0x123456789abcdef",
            "total_portfolio_value_usd": 0,
            "active_positions": 0,
            "positions": []
        }
        
        trader_analyzer.blockchain_client.get_trader_portfolio.return_value = insufficient_data
        
        result = await trader_analyzer.analyze_trader_behavior("0x123456789abcdef")
        
        assert "error" in result
        assert "Insufficient portfolio data" in result["error"]
    
    @pytest.mark.asyncio
    async def test_intelligence_score_calculation(self, trader_analyzer, sample_portfolio_data):
        """Test intelligence score calculation."""
        trader_analyzer.blockchain_client.get_trader_portfolio.return_value = sample_portfolio_data
        
        result = await trader_analyzer.analyze_trader_behavior("0x123456789abcdef")
        
        intelligence_score = result["intelligence_score"]
        assert 0 <= intelligence_score <= 1
        
        # High portfolio value and good diversification should yield higher score
        assert intelligence_score > 0.3  # Should be above baseline for good portfolio
    
    @pytest.mark.asyncio
    async def test_key_insights_generation(self, trader_analyzer, sample_portfolio_data):
        """Test generation of key insights."""
        trader_analyzer.blockchain_client.get_trader_portfolio.return_value = sample_portfolio_data
        
        result = await trader_analyzer.analyze_trader_behavior("0x123456789abcdef")
        
        insights = result["key_insights"]
        assert isinstance(insights, list)
        assert len(insights) <= 5  # Should limit to top 5 insights
        
        for insight in insights:
            assert isinstance(insight, str)
            assert len(insight) > 10  # Should be meaningful insights
    
    @pytest.mark.asyncio
    async def test_confidence_level_assessment(self, trader_analyzer, sample_portfolio_data):
        """Test confidence level assessment."""
        trader_analyzer.blockchain_client.get_trader_portfolio.return_value = sample_portfolio_data
        
        result = await trader_analyzer.analyze_trader_behavior("0x123456789abcdef")
        
        confidence_level = result["confidence_level"]
        assert 0 <= confidence_level <= 1
        
        # Sample data has good portfolio value and multiple positions
        assert confidence_level >= 0.5  # Should have reasonable confidence

class TestHelperMethods(TestTraderAnalyzer):
    """Test helper methods and edge cases."""
    
    def test_is_early_entry(self, trader_analyzer):
        """Test early entry detection logic."""
        # Recent timestamp (not early)
        recent_timestamp = int(datetime.utcnow().timestamp()) - (5 * 24 * 60 * 60)  # 5 days ago
        assert not trader_analyzer._is_early_entry(recent_timestamp)
        
        # Old timestamp (early)
        old_timestamp = int(datetime.utcnow().timestamp()) - (60 * 24 * 60 * 60)  # 60 days ago
        assert trader_analyzer._is_early_entry(old_timestamp)
        
        # Invalid timestamp
        assert not trader_analyzer._is_early_entry(0)
    
    def test_calculate_hold_duration_days(self, trader_analyzer):
        """Test hold duration calculation."""
        # Position with specific start and end time
        position_closed = {
            "first_entry_timestamp": 1640995200,  # Jan 1, 2022
            "last_entry_timestamp": 1641600000    # Jan 8, 2022 (7 days later)
        }
        
        duration = trader_analyzer._calculate_hold_duration_days(position_closed)
        assert abs(duration - 7.0) < 0.1  # Should be approximately 7 days
        
        # Position still active (no end timestamp)
        position_active = {
            "first_entry_timestamp": int(datetime.utcnow().timestamp()) - (3 * 24 * 60 * 60),  # 3 days ago
            "last_entry_timestamp": 0
        }
        
        duration_active = trader_analyzer._calculate_hold_duration_days(position_active)
        assert 2.5 <= duration_active <= 3.5  # Should be approximately 3 days
    
    def test_determine_conviction_level(self, trader_analyzer):
        """Test conviction level determination."""
        # High conviction
        assert trader_analyzer._determine_conviction_level(Decimal('0.30'), 3) == "high"
        
        # Medium conviction  
        assert trader_analyzer._determine_conviction_level(Decimal('0.20'), 2) == "medium"
        
        # Low conviction
        assert trader_analyzer._determine_conviction_level(Decimal('0.08'), 1) == "low"
        
        # Minimal conviction
        assert trader_analyzer._determine_conviction_level(Decimal('0.02'), 0) == "minimal"
    
    def test_categorize_market_sector(self, trader_analyzer):
        """Test market sector categorization."""
        # Political markets
        political_position = {"market_id": "trump_election_2024"}
        assert trader_analyzer._categorize_market_sector(political_position) == "politics"
        
        # Crypto markets
        crypto_position = {"market_id": "btc_price_prediction"}
        assert trader_analyzer._categorize_market_sector(crypto_position) == "crypto"
        
        # Sports markets
        sports_position = {"market_id": "nfl_superbowl_winner"}
        assert trader_analyzer._categorize_market_sector(sports_position) == "sports"
        
        # Unknown markets
        unknown_position = {"market_id": "random_market_123"}
        assert trader_analyzer._categorize_market_sector(unknown_position) == "other"

class TestIntegrationScenarios(TestTraderAnalyzer):
    """Test real-world integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_high_conviction_trader_scenario(self, trader_analyzer):
        """Test analysis of a high-conviction trader."""
        high_conviction_data = {
            "address": "0xhighconviction123",
            "total_portfolio_value_usd": 500000,
            "active_positions": 3,
            "positions": [
                {
                    "market_id": "trump_election_2024",
                    "total_position_size_usd": 200000,  # 40% allocation
                    "current_value_usd": 220000,
                    "first_entry_timestamp": 1640995200
                },
                {
                    "market_id": "fed_rates_march",
                    "total_position_size_usd": 150000,  # 30% allocation
                    "current_value_usd": 160000,
                    "first_entry_timestamp": 1641081600
                },
                {
                    "market_id": "btc_100k_2024",
                    "total_position_size_usd": 150000,  # 30% allocation
                    "current_value_usd": 145000,
                    "first_entry_timestamp": 1641168000
                }
            ]
        }
        
        trader_analyzer.blockchain_client.get_trader_portfolio.return_value = high_conviction_data
        
        result = await trader_analyzer.analyze_trader_behavior("0xhighconviction123")
        
        assert "error" not in result
        
        # Should detect high conviction signals
        conviction_signals = result["conviction_signals"]
        high_allocation_signals = [s for s in conviction_signals if s["type"] == "high_allocation"]
        assert len(high_allocation_signals) >= 2  # Two positions > 10% threshold
        
        # Risk assessment should show high concentration
        risk_assessment = result["risk_assessment"]
        assert risk_assessment.portfolio_concentration_risk >= Decimal('0.6')
        
        # Intelligence score should be reasonable despite high concentration
        assert result["intelligence_score"] >= 0.4
    
    @pytest.mark.asyncio
    async def test_diversified_trader_scenario(self, trader_analyzer):
        """Test analysis of a well-diversified trader."""
        diversified_data = {
            "address": "0xdiversified123", 
            "total_portfolio_value_usd": 200000,
            "active_positions": 10,
            "positions": [
                {
                    "market_id": f"market_{i}",
                    "total_position_size_usd": 20000,  # 10% each
                    "current_value_usd": 21000,
                    "first_entry_timestamp": 1640995200 + (i * 86400)  # Staggered entries
                }
                for i in range(10)
            ]
        }
        
        trader_analyzer.blockchain_client.get_trader_portfolio.return_value = diversified_data
        
        result = await trader_analyzer.analyze_trader_behavior("0xdiversified123")
        
        assert "error" not in result
        
        # Should have high diversification score
        portfolio_metrics = result["portfolio_metrics"]
        assert portfolio_metrics.diversification_score >= Decimal('0.8')
        
        # Should have low concentration risk
        risk_assessment = result["risk_assessment"] 
        assert risk_assessment.portfolio_concentration_risk <= Decimal('0.4')
        assert risk_assessment.risk_level in ["low", "moderate"]
        
        # Should have high intelligence score due to good diversification
        assert result["intelligence_score"] >= 0.6
    
    @pytest.mark.asyncio
    async def test_small_portfolio_trader_scenario(self, trader_analyzer):
        """Test analysis of a trader with small portfolio."""
        small_portfolio_data = {
            "address": "0xsmalltrader123",
            "total_portfolio_value_usd": 5000,
            "active_positions": 2,
            "positions": [
                {
                    "market_id": "market_1",
                    "total_position_size_usd": 3000,
                    "current_value_usd": 3200,
                    "first_entry_timestamp": 1640995200
                },
                {
                    "market_id": "market_2", 
                    "total_position_size_usd": 2000,
                    "current_value_usd": 1800,
                    "first_entry_timestamp": 1641081600
                }
            ]
        }
        
        trader_analyzer.blockchain_client.get_trader_portfolio.return_value = small_portfolio_data
        
        result = await trader_analyzer.analyze_trader_behavior("0xsmalltrader123")
        
        assert "error" not in result
        
        # Confidence level should be lower due to small portfolio
        assert result["confidence_level"] <= 0.5
        
        # Intelligence score should be lower due to portfolio size
        assert result["intelligence_score"] <= 0.4
        
        # Should still provide meaningful analysis
        assert len(result["key_insights"]) >= 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])