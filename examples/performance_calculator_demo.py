#!/usr/bin/env python3
"""
Performance Calculator Demo

This script demonstrates the comprehensive performance calculator functionality
implemented in Step 3.3, including:

1. Market outcome tracking and resolution verification
2. Statistical confidence intervals and significance testing
3. Risk-adjusted performance metrics (Sharpe ratio, Sortino ratio)
4. Time-series performance analysis and trend detection
5. Integration with SuccessRateAgent for enhanced alpha detection
"""

import asyncio
import time
from decimal import Decimal
from datetime import datetime, timedelta

from app.intelligence.performance_calculator import (
    PerformanceCalculator, MarketOutcome, MarketResolution, TraderPosition
)
from app.intelligence.market_outcome_tracker import (
    MarketOutcomeTracker, MarketResolutionData, PositionOutcome, OutcomeConfidence
)
from app.agents.success_rate_agent import SuccessRateAgent

async def demo_performance_calculator():
    """Demonstrate comprehensive performance calculator capabilities."""
    
    print("=== PolyIngest Performance Calculator Demo ===\n")
    
    # Initialize components
    performance_calc = PerformanceCalculator()
    outcome_tracker = MarketOutcomeTracker()
    success_rate_agent = SuccessRateAgent(performance_calc)
    
    print("1. MARKET OUTCOME TRACKING")
    print("-" * 40)
    
    # Track several market resolutions
    markets = [
        {
            "id": "election_2024",
            "resolution_data": {
                "winning_outcome_id": "yes",
                "winning_outcome_name": "Yes",
                "resolution_timestamp": int(time.time()) - 86400 * 30,  # 30 days ago
                "resolution_source": "official",
                "verification_count": 3,
                "payout_ratio": 1.0,
                "final_price": 1.0,
                "title": "2024 Election Market",
                "total_volume": 1000000
            }
        },
        {
            "id": "crypto_btc_100k",
            "resolution_data": {
                "winning_outcome_id": "no",
                "winning_outcome_name": "No",
                "resolution_timestamp": int(time.time()) - 86400 * 15,  # 15 days ago
                "resolution_source": "verified",
                "verification_count": 2,
                "payout_ratio": 1.0,
                "final_price": 1.0,
                "title": "BTC $100K by Year End",
                "total_volume": 500000
            }
        },
        {
            "id": "sports_superbowl",
            "resolution_data": {
                "winning_outcome_id": "chiefs",
                "winning_outcome_name": "Kansas City Chiefs",
                "resolution_timestamp": int(time.time()) - 86400 * 7,  # 7 days ago
                "resolution_source": "official",
                "verification_count": 4,
                "payout_ratio": 1.0,
                "final_price": 1.0,
                "title": "Super Bowl Winner",
                "total_volume": 750000
            }
        }
    ]
    
    # Track market resolutions
    for market in markets:
        resolution = await outcome_tracker.track_market_resolution(
            market["id"], market["resolution_data"]
        )
        print(f"✓ Tracked: {resolution.title} -> {resolution.winning_outcome_name}")
        print(f"  Confidence: {resolution.confidence_level.value}")
        print()
    
    print("2. TRADER PERFORMANCE ANALYSIS")
    print("-" * 40)
    
    # Create a sample trader with positions in resolved markets
    trader_data = {
        "address": "0xalpha_trader_demo",
        "total_portfolio_value_usd": 250000,
        "positions": [
            {
                "market_id": "election_2024",
                "outcome_id": "yes",
                "total_position_size_usd": 10000,
                "entry_price": 0.45,
                "first_entry_timestamp": int(time.time()) - 86400 * 35,
                "status": "closed"
            },
            {
                "market_id": "crypto_btc_100k", 
                "outcome_id": "yes",  # Wrong prediction
                "total_position_size_usd": 5000,
                "entry_price": 0.65,
                "first_entry_timestamp": int(time.time()) - 86400 * 20,
                "status": "closed"
            },
            {
                "market_id": "sports_superbowl",
                "outcome_id": "chiefs",  # Correct prediction
                "total_position_size_usd": 8000,
                "entry_price": 0.55,
                "first_entry_timestamp": int(time.time()) - 86400 * 10,
                "status": "closed"
            }
        ]
    }
    
    # Convert to market outcomes for performance calculation
    market_outcomes = {}
    for market in markets:
        market_outcomes[market["id"]] = MarketOutcome(
            market_id=market["id"],
            resolution=MarketResolution.WIN,
            winning_outcome_id=market["resolution_data"]["winning_outcome_id"],
            resolution_timestamp=market["resolution_data"]["resolution_timestamp"],
            resolution_source=market["resolution_data"]["resolution_source"],
            confidence_score=Decimal('0.95')
        )
    
    # Calculate comprehensive performance metrics
    performance = await performance_calc.calculate_trader_performance(
        trader_data, market_outcomes
    )
    
    print(f"Trader: {trader_data['address']}")
    print(f"Total Trades: {performance.total_trades}")
    print(f"Success Rate: {performance.success_rate:.1%}")
    print(f"Confidence Interval: [{performance.confidence_interval[0]:.1%}, {performance.confidence_interval[1]:.1%}]")
    print(f"Wilson Score Interval: [{performance.wilson_score_interval[0]:.1%}, {performance.wilson_score_interval[1]:.1%}]")
    print(f"Statistical Significance: {performance.statistical_significance}")
    if performance.p_value:
        print(f"P-Value: {performance.p_value:.4f}")
    print()
    
    print("Financial Metrics:")
    print(f"  Total Invested: ${performance.total_invested:,.2f}")
    print(f"  Total Returns: ${performance.total_returns:,.2f}")
    print(f"  Net Profit: ${performance.net_profit:,.2f}")
    print(f"  ROI: {performance.roi_percentage:.2f}%")
    print()
    
    print("Risk Metrics:")
    print(f"  Volatility: {performance.volatility:.1%}")
    print(f"  Maximum Drawdown: {performance.maximum_drawdown:.1%}")
    print(f"  Value at Risk (95%): {performance.value_at_risk_95:.1%}")
    if performance.sharpe_ratio:
        print(f"  Sharpe Ratio: {performance.sharpe_ratio:.2f}")
    if performance.sortino_ratio:
        print(f"  Sortino Ratio: {performance.sortino_ratio:.2f}")
    print()
    
    print("3. MARKET OUTCOME STATISTICS")
    print("-" * 40)
    
    # Get outcome tracking statistics
    stats = outcome_tracker.get_market_outcome_statistics()
    print(f"Total Markets Tracked: {stats['total_markets']}")
    print(f"High Confidence Resolutions: {stats['high_confidence_count']}")
    print(f"Average Resolution Delay: {stats['avg_resolution_delay_hours']:.1f} hours")
    print(f"Total Volume Resolved: ${stats['total_volume_resolved']:,.0f}")
    print()
    
    print("Confidence Distribution:")
    for confidence, count in stats['confidence_distribution'].items():
        print(f"  {confidence.title()}: {count}")
    print()
    
    print("4. ENHANCED SUCCESS RATE AGENT")
    print("-" * 40)
    
    # Test enhanced success rate agent with performance calculator
    agent_data = {
        "market": {"id": "test_market"},
        "traders": [trader_data],
        "market_outcomes": market_outcomes
    }
    
    analysis = await success_rate_agent.analyze(agent_data)
    vote = success_rate_agent.vote(analysis)
    reasoning = success_rate_agent.get_reasoning()
    
    print(f"Agent Vote: {vote}")
    print(f"Confidence: {analysis.get('confidence', 0):.2f}")
    print(f"Reasoning: {reasoning}")
    print()
    
    if analysis.get('comprehensive_performance_data'):
        perf_data = analysis['comprehensive_performance_data'][0]
        print("Enhanced Performance Data:")
        print(f"  Success Rate: {perf_data.get('success_rate', 0):.1%}")
        print(f"  Statistical Significance: {perf_data.get('statistical_significance', False)}")
        print(f"  Sharpe Ratio: {perf_data.get('sharpe_ratio', 'N/A')}")
        print(f"  Timing Alpha: {perf_data.get('timing_alpha', 0):.3f}")
    print()
    
    print("5. STATISTICAL VALIDATION")
    print("-" * 40)
    
    # Validate statistical significance
    significance_test = performance_calc.validate_statistical_significance({
        "success_rate": float(performance.success_rate),
        "total_trades": performance.total_trades,
        "winning_trades": performance.winning_trades
    })
    
    print(f"Statistical Test Results:")
    print(f"  Is Significant: {significance_test['is_significant']}")
    if significance_test.get('p_value'):
        print(f"  P-Value: {significance_test['p_value']:.4f}")
    print(f"  Confidence Level: {significance_test['confidence_level']:.0%}")
    print(f"  Test Method: {significance_test.get('test_method', 'binomial_test')}")
    print()
    
    print("6. PERFORMANCE TRENDS (SIMULATED)")
    print("-" * 40)
    
    # Simulate trading history for trend analysis
    simulated_history = []
    base_time = int(time.time()) - 86400 * 90  # 90 days ago
    
    for i in range(15):  # 15 trades over 90 days
        trade_time = base_time + (i * 86400 * 6)  # Every 6 days
        is_win = i % 3 != 0  # 2/3 win rate with some variation
        profit = 500 if is_win else -300
        
        simulated_history.append({
            "timestamp": trade_time,
            "profit_loss": profit,
            "position_size": 2000,
            "outcome": "win" if is_win else "loss"
        })
    
    # Analyze trends
    trends = performance_calc.analyze_performance_trends(simulated_history, ["30d", "60d", "90d"])
    
    print("Performance Trends:")
    for trend in trends:
        print(f"  {trend.time_period}:")
        print(f"    Success Rate: {trend.success_rate:.1%}")
        print(f"    Trade Count: {trend.trade_count}")
        print(f"    ROI: {trend.roi_percentage:.1f}%")
        print(f"    Trend: {trend.trend_direction}")
    print()
    
    print("=== Demo Complete ===")
    print("\nKey Features Demonstrated:")
    print("✓ Market outcome tracking with confidence scoring")
    print("✓ Statistical confidence intervals (Wilson score)")
    print("✓ Risk-adjusted performance metrics")
    print("✓ Statistical significance testing")
    print("✓ Performance trend analysis")
    print("✓ Enhanced agent integration")
    print("✓ Comprehensive data validation")

async def demo_risk_adjusted_returns():
    """Demonstrate risk-adjusted returns calculation."""
    
    print("\n=== RISK-ADJUSTED RETURNS DEMO ===\n")
    
    performance_calc = PerformanceCalculator()
    
    # Create positions with various outcomes for risk calculation
    positions = [
        TraderPosition(
            market_id="market_1", outcome_id="yes", position_size_usd=Decimal('1000'),
            entry_price=Decimal('0.6'), entry_timestamp=int(time.time()),
            exit_price=Decimal('1.0'), status="closed"  # 67% return
        ),
        TraderPosition(
            market_id="market_2", outcome_id="no", position_size_usd=Decimal('1500'),
            entry_price=Decimal('0.4'), entry_timestamp=int(time.time()),
            exit_price=Decimal('0.0'), status="closed"  # -100% return
        ),
        TraderPosition(
            market_id="market_3", outcome_id="yes", position_size_usd=Decimal('800'),
            entry_price=Decimal('0.7'), entry_timestamp=int(time.time()),
            exit_price=Decimal('1.0'), status="closed"  # 43% return
        ),
        TraderPosition(
            market_id="market_4", outcome_id="no", position_size_usd=Decimal('1200'),
            entry_price=Decimal('0.3'), entry_timestamp=int(time.time()),
            exit_price=Decimal('1.0'), status="closed"  # 233% return
        )
    ]
    
    risk_metrics = performance_calc.calculate_risk_adjusted_returns(positions)
    
    print("Risk-Adjusted Returns Analysis:")
    print(f"Mean Return: {risk_metrics['mean_return']:.1%}")
    print(f"Volatility: {risk_metrics['volatility']:.1%}")
    print(f"Annualized Return: {risk_metrics['annualized_return']:.1%}")
    print(f"Annualized Volatility: {risk_metrics['annualized_volatility']:.1%}")
    
    if risk_metrics['sharpe_ratio']:
        print(f"Sharpe Ratio: {risk_metrics['sharpe_ratio']:.2f}")
    if risk_metrics['sortino_ratio']:
        print(f"Sortino Ratio: {risk_metrics['sortino_ratio']:.2f}")
    
    print(f"Maximum Drawdown: {risk_metrics['max_drawdown']:.1%}")

if __name__ == "__main__":
    print("Starting PolyIngest Performance Calculator Demo...")
    print("This demonstrates the comprehensive performance tracking capabilities")
    print("implemented in Step 3.3 of the PolyIngest project.\n")
    
    asyncio.run(demo_performance_calculator())
    asyncio.run(demo_risk_adjusted_returns())
    
    print("\nDemo completed successfully!")
    print("The performance calculator provides statistically rigorous")
    print("analysis with verified market outcomes for accurate trader assessment.")