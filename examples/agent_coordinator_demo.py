#!/usr/bin/env python3
"""
Agent Coordinator Integration Demo

This script demonstrates the complete AgentCoordinator workflow with sample data
that simulates a real Polymarket alpha detection scenario.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

from app.agents.coordinator import AgentCoordinator
from app.config import settings

def create_sample_market_data() -> Dict[str, Any]:
    """Create sample market data for a political prediction market."""
    return {
        "id": "0xpolitical_market_2024",
        "title": "Will Donald Trump win the 2024 Presidential Election?",
        "description": "Market resolves to Yes if Donald Trump wins the 2024 US Presidential Election. Resolution based on official election results.",
        "category": "Politics",
        "subcategory": "US Elections", 
        "end_date": "2024-11-05T23:59:59Z",
        "resolution_criteria": "Market resolves based on official election results and electoral college outcome",
        "status": "active",
        "creator": "0xmarket_creator_address",
        "total_volume": 2500000,  # $2.5M total volume
        "total_liquidity": 1200000,  # $1.2M liquidity
        "current_prices": {"Yes": 0.52, "No": 0.48},
        "trading_activity": {
            "total_trades_24h": 2847,
            "unique_traders_24h": 432,
            "avg_trade_size": 1250,
            "large_trades_24h": 23
        },
        "outcomes": [
            {
                "id": "yes",
                "name": "Yes",
                "current_price": 0.52,
                "volume_24h": 1800000,
                "liquidity": 620000
            },
            {
                "id": "no", 
                "name": "No",
                "current_price": 0.48,
                "volume_24h": 700000,
                "liquidity": 580000
            }
        ]
    }

def create_sample_traders_data() -> List[Dict[str, Any]]:
    """Create sample trader data representing various trader profiles."""
    return [
        # High-conviction profitable trader - Strong alpha signal
        {
            "address": "0xalpha_trader_1",
            "total_portfolio_value_usd": 850000,
            "performance_metrics": {
                "overall_success_rate": 0.78,  # 78% success rate
                "markets_resolved": 32,
                "total_profit_usd": 125000,
                "roi_percentage": 18.5
            },
            "positions": [
                {
                    "market_id": "0xpolitical_market_2024",
                    "outcome_id": "yes",
                    "position_size_usd": 50000,  # 22% of portfolio
                    "entry_price": 0.45,  # Early entry at good price
                    "current_value_usd": 57700,
                    "portfolio_allocation_pct": 0.22
                }
            ]
        },
        
        # Another high-performing trader with significant position
        {
            "address": "0xalpha_trader_2", 
            "total_portfolio_value_usd": 650000,
            "performance_metrics": {
                "overall_success_rate": 0.76,
                "markets_resolved": 28,
                "total_profit_usd": 98000,
                "roi_percentage": 15.8
            },
            "positions": [
                {
                    "market_id": "0xpolitical_market_2024",
                    "outcome_id": "yes",
                    "position_size_usd": 78000,  # 12% of portfolio
                    "entry_price": 0.47,
                    "current_value_usd": 86400,
                    "portfolio_allocation_pct": 0.12
                }
            ]
        },
        
        # Smaller but very successful trader
        {
            "address": "0xalpha_trader_3",
            "total_portfolio_value_usd": 125000,
            "performance_metrics": {
                "overall_success_rate": 0.85,  # Very high success rate
                "markets_resolved": 20,
                "total_profit_usd": 45000,
                "roi_percentage": 36.0
            },
            "positions": [
                {
                    "market_id": "0xpolitical_market_2024",
                    "outcome_id": "yes",
                    "position_size_usd": 18000,  # 14% of portfolio
                    "entry_price": 0.44,
                    "current_value_usd": 21200,
                    "portfolio_allocation_pct": 0.14
                }
            ]
        },
        
        # Contrarian trader with good track record betting No
        {
            "address": "0xcontrarian_trader",
            "total_portfolio_value_usd": 400000,
            "performance_metrics": {
                "overall_success_rate": 0.72,
                "markets_resolved": 25,
                "total_profit_usd": 55000,
                "roi_percentage": 13.8
            },
            "positions": [
                {
                    "market_id": "0xpolitical_market_2024",
                    "outcome_id": "no",
                    "position_size_usd": 32000,  # 8% of portfolio  
                    "entry_price": 0.58,
                    "current_value_usd": 26400,
                    "portfolio_allocation_pct": 0.08
                }
            ]
        },
        
        # Noise trader - Poor performance, should be filtered out
        {
            "address": "0xnoise_trader",
            "total_portfolio_value_usd": 75000,
            "performance_metrics": {
                "overall_success_rate": 0.42,  # Below threshold
                "markets_resolved": 12,
                "total_profit_usd": -8000,
                "roi_percentage": -10.7
            },
            "positions": [
                {
                    "market_id": "0xpolitical_market_2024",
                    "outcome_id": "yes",
                    "position_size_usd": 3000,
                    "entry_price": 0.51,
                    "current_value_usd": 3060,
                    "portfolio_allocation_pct": 0.04
                }
            ]
        },
        
        # High-volume trader with moderate performance
        {
            "address": "0xvolume_trader",
            "total_portfolio_value_usd": 1200000,
            "performance_metrics": {
                "overall_success_rate": 0.68,
                "markets_resolved": 45,
                "total_profit_usd": 180000,
                "roi_percentage": 15.0
            },
            "positions": [
                {
                    "market_id": "0xpolitical_market_2024",
                    "outcome_id": "yes",
                    "position_size_usd": 60000,  # 5% of portfolio - lower conviction
                    "entry_price": 0.49,
                    "current_value_usd": 63600,
                    "portfolio_allocation_pct": 0.05
                }
            ]
        }
    ]

async def run_alpha_detection_demo():
    """Run a complete alpha detection demonstration."""
    print("=" * 80)
    print("POLYINGEST AGENT COORDINATOR DEMO")
    print("Multi-Agent Alpha Detection System")
    print("=" * 80)
    
    # Initialize the coordinator
    print("\n1. Initializing AgentCoordinator...")
    coordinator = AgentCoordinator()
    
    # Display initial system status
    print(f"   ✓ Initialized with {len(coordinator.voting_system.agents)} analysis agents")
    print(f"   ✓ Vote threshold: {coordinator.voting_system.vote_threshold}")
    
    agent_status = coordinator.get_agent_status()
    print("   ✓ Registered agents:")
    for agent_name in agent_status["registered_agents"]:
        agent_details = agent_status["agent_details"][agent_name]
        print(f"     - {agent_name} (type: {agent_details['type']}, weight: {agent_details['weight']})")
    
    # Prepare sample data
    print("\n2. Preparing sample market and trader data...")
    market_data = create_sample_market_data()
    traders_data = create_sample_traders_data()
    
    print(f"   ✓ Market: {market_data['title']}")
    print(f"   ✓ Category: {market_data['category']} - {market_data['subcategory']}")
    print(f"   ✓ Total Volume: ${market_data['total_volume']:,}")
    print(f"   ✓ Current Prices: Yes {market_data['current_prices']['Yes']}, No {market_data['current_prices']['No']}")
    print(f"   ✓ Trader Sample: {len(traders_data)} traders")
    
    # Run alpha analysis with default filters
    print("\n3. Running alpha analysis with default filters...")
    print(f"   - Min Portfolio Ratio: {settings.min_portfolio_ratio}")
    print(f"   - Min Success Rate: {settings.min_success_rate}")
    print(f"   - Min Trade History: {settings.min_trade_history}")
    
    start_time = datetime.now()
    result = await coordinator.analyze_market(market_data, traders_data)
    analysis_duration = (datetime.now() - start_time).total_seconds()
    
    print(f"   ✓ Analysis completed in {analysis_duration:.2f} seconds")
    
    # Display results
    print("\n4. ALPHA ANALYSIS RESULTS")
    print("-" * 40)
    
    alpha_analysis = result["alpha_analysis"]
    print(f"Alpha Detected: {alpha_analysis['has_alpha']}")
    print(f"Confidence Score: {alpha_analysis['confidence_score']:.3f}")
    print(f"Recommended Side: {alpha_analysis.get('recommended_side', 'None')}")
    print(f"Signal Strength: {alpha_analysis['strength']}")
    
    # Agent consensus
    consensus = alpha_analysis["agent_consensus"]
    print(f"\nAgent Voting:")
    print(f"  For Alpha: {consensus['votes_for_alpha']}")
    print(f"  Against Alpha: {consensus['votes_against_alpha']}")
    print(f"  Abstentions: {consensus['abstentions']}")
    
    # Key traders
    print(f"\nKey Traders ({len(result['key_traders'])}):")
    for i, trader in enumerate(result['key_traders'][:3], 1):  # Show top 3
        print(f"  {i}. {trader['address'][:10]}...")
        print(f"     Position: ${trader['position_size_usd']:,} ({trader['portfolio_allocation_pct']:.1f}% allocation)")
        print(f"     Success Rate: {trader['historical_success_rate']:.1%}")
        print(f"     Side: {trader['position_side']}")
        
        indicators = trader['confidence_indicators']
        active_indicators = [k for k, v in indicators.items() if v]
        print(f"     Indicators: {', '.join(active_indicators)}")
        print()
    
    # Agent analyses
    print("Individual Agent Analyses:")
    for analysis in result['agent_analyses']:
        print(f"  • {analysis['agent_name']}")
        print(f"    Vote: {analysis['vote']} (confidence: {analysis['confidence']:.3f})")
        print(f"    Reasoning: {analysis['reasoning']}")
        print(f"    Key Findings: {len(analysis['key_findings'])} findings")
        print()
    
    # Risk factors
    if result['risk_factors']:
        print("Risk Factors:")
        for i, risk in enumerate(result['risk_factors'], 1):
            print(f"  {i}. {risk}")
        print()
    
    # Metadata
    metadata = result['metadata']
    print("Analysis Metadata:")
    print(f"  Trader Sample Size: {metadata['trader_sample_size']}")
    print(f"  Consensus Reached: {metadata['consensus_reached']}")
    print(f"  Voting Duration: {metadata['voting_duration_seconds']}s")
    print(f"  Timestamp: {metadata['analysis_timestamp']}")
    
    # Run analysis with stricter filters
    print("\n5. Running analysis with stricter filters...")
    strict_filters = {
        "min_portfolio_ratio": 0.15,  # 15% minimum allocation
        "min_success_rate": 0.75,     # 75% minimum success rate
        "min_trade_history": 20       # 20+ resolved markets
    }
    
    print(f"   - Min Portfolio Ratio: {strict_filters['min_portfolio_ratio']}")
    print(f"   - Min Success Rate: {strict_filters['min_success_rate']}")
    print(f"   - Min Trade History: {strict_filters['min_trade_history']}")
    
    strict_result = await coordinator.analyze_market(market_data, traders_data, strict_filters)
    
    print(f"\nStrict Filter Results:")
    print(f"  Alpha Detected: {strict_result['alpha_analysis']['has_alpha']}")
    print(f"  Confidence: {strict_result['alpha_analysis']['confidence_score']:.3f}")
    print(f"  Qualifying Traders: {strict_result['metadata']['trader_sample_size']}")
    
    # Performance metrics
    print("\n6. System Performance Metrics")
    print("-" * 40)
    
    perf_metrics = coordinator.get_performance_metrics()
    perf = perf_metrics["coordinator_performance"]
    
    print(f"Total Analyses: {perf['total_analyses']}")
    print(f"Successful Analyses: {perf['successful_analyses']}")
    print(f"Success Rate: {perf['success_rate']:.1%}")
    print(f"Average Duration: {perf['avg_analysis_duration']:.3f}s")
    print(f"System Status: {perf_metrics['system_status']}")
    
    print("\nAgent Health:")
    for agent_name, health in perf_metrics["agent_health"].items():
        print(f"  {agent_name}: {health['status']} (weight: {health['weight']:.2f})")
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("The AgentCoordinator successfully orchestrated multi-agent alpha detection")
    print(f"with {perf['total_analyses']} analyses and {perf['success_rate']:.1%} success rate")
    print("=" * 80)

async def run_performance_stress_test():
    """Run a quick performance stress test with multiple concurrent analyses."""
    print("\n" + "=" * 80)
    print("PERFORMANCE STRESS TEST")
    print("Running multiple concurrent alpha analyses...")
    print("=" * 80)
    
    coordinator = AgentCoordinator()
    market_data = create_sample_market_data()
    traders_data = create_sample_traders_data()
    
    # Run multiple analyses concurrently
    num_concurrent = 5
    print(f"\nRunning {num_concurrent} concurrent analyses...")
    
    start_time = datetime.now()
    
    tasks = [
        coordinator.analyze_market(
            {**market_data, "id": f"market_{i}"}, 
            traders_data
        ) 
        for i in range(num_concurrent)
    ]
    
    results = await asyncio.gather(*tasks)
    total_duration = (datetime.now() - start_time).total_seconds()
    
    print(f"\nConcurrent Analysis Results:")
    print(f"  Total Duration: {total_duration:.2f}s")
    print(f"  Average per Analysis: {total_duration/num_concurrent:.2f}s")
    print(f"  Analyses per Second: {num_concurrent/total_duration:.2f}")
    
    # Verify all analyses succeeded
    successful = sum(1 for r in results if r["alpha_analysis"]["has_alpha"] is not None)
    print(f"  Success Rate: {successful}/{num_concurrent} ({successful/num_concurrent:.1%})")
    
    # Performance metrics
    final_metrics = coordinator.get_performance_metrics()
    final_perf = final_metrics["coordinator_performance"]
    print(f"  Final Success Rate: {final_perf['success_rate']:.1%}")
    print(f"  Average Analysis Duration: {final_perf['avg_analysis_duration']:.3f}s")

if __name__ == "__main__":
    # Run the main demo
    asyncio.run(run_alpha_detection_demo())
    
    # Run performance stress test
    asyncio.run(run_performance_stress_test())