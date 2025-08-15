#!/usr/bin/env python3
"""
VotingSystem Demo Script

This script demonstrates how to use the VotingSystem class with real analysis agents
to detect alpha opportunities in Polymarket prediction markets.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, Any
from decimal import Decimal

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agents import VotingSystem, PortfolioAnalyzerAgent, SuccessRateAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_market_data() -> Dict[str, Any]:
    """Create realistic sample data for testing the voting system."""
    return {
        "market": {
            "id": "0x1234567890abcdef1234567890abcdef12345678",
            "title": "Will Donald Trump win the 2024 Presidential Election?",
            "description": "Market resolves to Yes if Donald Trump wins the 2024 U.S. Presidential Election",
            "end_date": "2024-11-05T23:59:59Z",
            "status": "active",
            "current_prices": {"Yes": 0.52, "No": 0.48},
            "total_volume_24h": 2500000,
            "total_liquidity": 1200000
        },
        "traders": [
            {
                "address": "0xabc123def456789abc123def456789abc123def4",
                "total_portfolio_value_usd": 850000,
                "positions": [
                    {
                        "market_id": "0x1234567890abcdef1234567890abcdef12345678",
                        "position_size_usd": 187000,  # 22% of portfolio
                        "side": "Yes",
                        "entry_price": 0.45
                    }
                ],
                "performance_metrics": {
                    "overall_success_rate": 0.78,
                    "markets_resolved": 32,
                    "total_profit_usd": 125000,
                    "roi_percentage": 18.5
                }
            },
            {
                "address": "0xdef789abc123def789abc123def789abc123def7",
                "total_portfolio_value_usd": 650000,
                "positions": [
                    {
                        "market_id": "0x1234567890abcdef1234567890abcdef12345678",
                        "position_size_usd": 91000,  # 14% of portfolio
                        "side": "Yes",
                        "entry_price": 0.48
                    }
                ],
                "performance_metrics": {
                    "overall_success_rate": 0.82,
                    "markets_resolved": 28,
                    "total_profit_usd": 95000,
                    "roi_percentage": 16.2
                }
            },
            {
                "address": "0x789abc123def789abc123def789abc123def789a",
                "total_portfolio_value_usd": 420000,
                "positions": [
                    {
                        "market_id": "0x1234567890abcdef1234567890abcdef12345678",
                        "position_size_usd": 58000,  # 13.8% of portfolio
                        "side": "Yes",
                        "entry_price": 0.46
                    }
                ],
                "performance_metrics": {
                    "overall_success_rate": 0.71,
                    "markets_resolved": 24,
                    "total_profit_usd": 65000,
                    "roi_percentage": 18.9
                }
            },
            {
                "address": "0x456def789abc456def789abc456def789abc456d",
                "total_portfolio_value_usd": 1200000,
                "positions": [
                    {
                        "market_id": "0x1234567890abcdef1234567890abcdef12345678",
                        "position_size_usd": 24000,  # 2% of portfolio - low allocation
                        "side": "No",
                        "entry_price": 0.51
                    }
                ],
                "performance_metrics": {
                    "overall_success_rate": 0.65,
                    "markets_resolved": 45,
                    "total_profit_usd": 180000,
                    "roi_percentage": 12.8
                }
            }
        ]
    }

def create_weak_signal_data() -> Dict[str, Any]:
    """Create sample data with weak alpha signals."""
    return {
        "market": {
            "id": "0xweaksignal123456789",
            "title": "Will it rain tomorrow?",
            "description": "Simple weather prediction market",
            "end_date": "2024-01-02T12:00:00Z",
            "status": "active"
        },
        "traders": [
            {
                "address": "0xweak1...",
                "total_portfolio_value_usd": 50000,
                "positions": [
                    {
                        "market_id": "0xweaksignal123456789",
                        "position_size_usd": 2000,  # 4% allocation - below threshold
                        "side": "Yes"
                    }
                ],
                "performance_metrics": {
                    "overall_success_rate": 0.55,  # Poor success rate
                    "markets_resolved": 8,  # Limited history
                    "total_profit_usd": 500
                }
            },
            {
                "address": "0xweak2...",
                "total_portfolio_value_usd": 30000,
                "positions": [
                    {
                        "market_id": "0xweaksignal123456789",
                        "position_size_usd": 1500,  # 5% allocation
                        "side": "No"
                    }
                ],
                "performance_metrics": {
                    "overall_success_rate": 0.48,  # Below 50%
                    "markets_resolved": 12,
                    "total_profit_usd": -800  # Losing money
                }
            }
        ]
    }

async def demonstrate_voting_system():
    """Demonstrate the VotingSystem with various scenarios."""
    logger.info("=== VotingSystem Demonstration ===")
    
    # Initialize voting system
    voting_system = VotingSystem(vote_threshold=0.6)
    logger.info(f"Initialized VotingSystem with threshold: {voting_system.vote_threshold}")
    
    # Register agents
    portfolio_agent = PortfolioAnalyzerAgent()
    success_rate_agent = SuccessRateAgent()
    
    voting_system.register_agent(portfolio_agent)
    voting_system.register_agent(success_rate_agent)
    
    logger.info("Registered agents:")
    summary = voting_system.get_voting_summary()
    for agent in summary["registered_agents"]:
        logger.info(f"  - {agent['name']} (weight: {agent['weight']}, type: {agent['type']})")
    
    print("\n" + "="*60)
    print("SCENARIO 1: Strong Alpha Signal")
    print("="*60)
    
    # Test with strong alpha signal
    strong_data = create_sample_market_data()
    result = await voting_system.conduct_vote(strong_data)
    
    print(f"Market: {strong_data['market']['title']}")
    print(f"Traders analyzed: {len(strong_data['traders'])}")
    print(f"\nVoting Results:")
    print(f"  Alpha detected: {result.has_alpha}")
    print(f"  Confidence: {result.confidence_score:.2f}")
    print(f"  Votes for alpha: {result.votes_for_alpha}")
    print(f"  Votes against: {result.votes_against_alpha}")
    print(f"  Abstentions: {result.abstentions}")
    print(f"  Consensus reached: {result.consensus_reached}")
    print(f"  Voting duration: {result.voting_duration:.2f}s")
    
    print(f"\nAgent Analysis Details:")
    for agent_result in result.agent_results:
        print(f"  {agent_result['agent_name']}:")
        print(f"    Vote: {agent_result['vote']}")
        print(f"    Confidence: {agent_result['confidence']:.2f}")
        print(f"    Weight: {agent_result['agent_weight']:.1f}")
        print(f"    Effective Weight: {agent_result['effective_weight']:.2f}")
        print(f"    Reasoning: {agent_result['reasoning']}")
        print()
    
    print(f"Summary: {result.reasoning_summary}")
    
    print("\n" + "="*60)
    print("SCENARIO 2: Weak Alpha Signal")
    print("="*60)
    
    # Test with weak signal
    weak_data = create_weak_signal_data()
    result2 = await voting_system.conduct_vote(weak_data)
    
    print(f"Market: {weak_data['market']['title']}")
    print(f"Traders analyzed: {len(weak_data['traders'])}")
    print(f"\nVoting Results:")
    print(f"  Alpha detected: {result2.has_alpha}")
    print(f"  Confidence: {result2.confidence_score:.2f}")
    print(f"  Votes for alpha: {result2.votes_for_alpha}")
    print(f"  Votes against: {result2.votes_against_alpha}")
    print(f"  Abstentions: {result2.abstentions}")
    print(f"  Consensus reached: {result2.consensus_reached}")
    
    print(f"\nAgent Analysis Details:")
    for agent_result in result2.agent_results:
        print(f"  {agent_result['agent_name']}:")
        print(f"    Vote: {agent_result['vote']}")
        print(f"    Confidence: {agent_result['confidence']:.2f}")
        print(f"    Reasoning: {agent_result['reasoning']}")
        print()
    
    print(f"Summary: {result2.reasoning_summary}")
    
    print("\n" + "="*60)
    print("JSON Output Example (Strong Alpha)")
    print("="*60)
    
    # Show JSON format (with custom encoder for Decimal)
    def decimal_default(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError
    
    result_dict = result.to_dict()
    print(json.dumps(result_dict, indent=2, default=decimal_default))
    
    print("\n" + "="*60)
    print("Agent Weight Management Demo")
    print("="*60)
    
    # Demonstrate weight updates
    print("Current agent weights:")
    for agent_name, agent in voting_system.agents.items():
        print(f"  {agent_name}: {agent.weight}")
    
    # Update weights based on simulated performance
    performance_data = {
        "Portfolio Analyzer": 0.85,  # 85% historical accuracy
        "Success Rate Analyzer": 0.92  # 92% historical accuracy
    }
    
    print(f"\nUpdating weights based on performance: {performance_data}")
    voting_system.update_agent_weights(performance_data)
    
    print("Updated agent weights:")
    for agent_name, agent in voting_system.agents.items():
        print(f"  {agent_name}: {agent.weight}")
    
    # Reset weights
    print("\nResetting all weights to 1.0...")
    voting_system.reset_agent_weights()
    
    print("Final agent weights:")
    for agent_name, agent in voting_system.agents.items():
        print(f"  {agent_name}: {agent.weight}")

def main():
    """Main function to run the demonstration."""
    try:
        asyncio.run(demonstrate_voting_system())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        raise

if __name__ == "__main__":
    main()