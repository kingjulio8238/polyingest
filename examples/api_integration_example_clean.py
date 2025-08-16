#!/usr/bin/env python3
"""
API Integration Example

This example shows how to integrate the AgentCoordinator into FastAPI endpoints
for the alpha analysis API according to CLAUDE.md specifications.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from app.agents.coordinator import AgentCoordinator

# Initialize the global coordinator instance
coordinator = AgentCoordinator()

# Pydantic models for API requests/responses
class AlphaAnalysisRequest(BaseModel):
    market_id: str
    min_portfolio_ratio: Optional[float] = 0.1
    min_success_rate: Optional[float] = 0.7
    min_trade_history: Optional[int] = 10

class AlphaAnalysisResponse(BaseModel):
    market: Dict[str, Any]
    alpha_analysis: Dict[str, Any]
    key_traders: List[Dict[str, Any]]
    agent_analyses: List[Dict[str, Any]]
    risk_factors: List[str]
    metadata: Dict[str, Any]

# Create FastAPI app
app = FastAPI(
    title="PolyIngest Alpha Detection API",
    description="Multi-agent alpha detection for Polymarket prediction markets",
    version="1.0.0"
)

# Mock data functions (in real implementation, these would fetch from Polymarket API)
def get_market_data(market_id: str) -> Dict[str, Any]:
    """Mock function to get market data - would call Polymarket API in production."""
    return {
        "id": market_id,
        "title": "Sample Market for Demo",
        "description": "This is a sample market for API demonstration",
        "category": "Politics",
        "subcategory": "US Elections",
        "end_date": "2024-12-31T23:59:59Z",
        "resolution_criteria": "Market resolves based on official results",
        "status": "active",
        "creator": "0xmarket_creator",
        "total_volume": 1500000,
        "total_liquidity": 750000,
        "current_prices": {"Yes": 0.58, "No": 0.42},
        "outcomes": [
            {"id": "yes", "name": "Yes", "current_price": 0.58},
            {"id": "no", "name": "No", "current_price": 0.42}
        ]
    }

def get_traders_data(market_id: str) -> List[Dict[str, Any]]:
    """Mock function to get trader data - would query blockchain and historical data in production."""
    return [
        {
            "address": "0xalpha_trader_1",
            "total_portfolio_value_usd": 500000,
            "performance_metrics": {
                "overall_success_rate": 0.78,
                "markets_resolved": 25,
                "total_profit_usd": 85000,
                "roi_percentage": 20.5
            },
            "positions": [
                {
                    "market_id": market_id,
                    "outcome_id": "yes",
                    "position_size_usd": 75000,
                    "entry_price": 0.52,
                    "current_value_usd": 83600,
                    "portfolio_allocation_pct": 0.15
                }
            ]
        },
        {
            "address": "0xalpha_trader_2",
            "total_portfolio_value_usd": 300000,
            "performance_metrics": {
                "overall_success_rate": 0.74,
                "markets_resolved": 18,
                "total_profit_usd": 45000,
                "roi_percentage": 17.3
            },
            "positions": [
                {
                    "market_id": market_id,
                    "outcome_id": "yes",
                    "position_size_usd": 42000,
                    "entry_price": 0.49,
                    "current_value_usd": 49800,
                    "portfolio_allocation_pct": 0.14
                }
            ]
        }
    ]

@app.get("/api/market/{market_id}/alpha", response_model=AlphaAnalysisResponse)
async def analyze_market_alpha(
    market_id: str,
    min_portfolio_ratio: Optional[float] = Query(0.1, ge=0.0, le=1.0, description="Minimum portfolio allocation ratio"),
    min_success_rate: Optional[float] = Query(0.7, ge=0.0, le=1.0, description="Minimum historical success rate"),
    min_trade_history: Optional[int] = Query(10, ge=1, description="Minimum number of resolved markets")
):
    """
    Analyze alpha opportunities for a specific market.
    
    This endpoint orchestrates the multi-agent analysis system to detect alpha
    opportunities based on trader behavior and performance patterns.
    """
    try:
        # Fetch market and trader data
        market_data = get_market_data(market_id)
        traders_data = get_traders_data(market_id)
        
        if not market_data:
            raise HTTPException(status_code=404, detail=f"Market {market_id} not found")
        
        # Prepare filters
        filters = {
            "min_portfolio_ratio": min_portfolio_ratio,
            "min_success_rate": min_success_rate,
            "min_trade_history": min_trade_history
        }
        
        # Run alpha analysis through AgentCoordinator
        analysis_result = await coordinator.analyze_market(
            market_data=market_data,
            traders_data=traders_data,
            filters=filters
        )
        
        return AlphaAnalysisResponse(**analysis_result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alpha analysis failed: {str(e)}")

@app.get("/api/market/{market_id}/data")
async def get_market_data_endpoint(market_id: str):
    """Get comprehensive market data including trading activity."""
    try:
        market_data = get_market_data(market_id)
        
        if not market_data:
            raise HTTPException(status_code=404, detail=f"Market {market_id} not found")
        
        # Add trading activity data
        market_data["trading_activity"] = {
            "total_trades_24h": 1247,
            "unique_traders_24h": 203,
            "avg_trade_size": 2850,
            "large_trades_24h": 15
        }
        
        return {"market": market_data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve market data: {str(e)}")

@app.get("/api/trader/{trader_address}/analysis")
async def analyze_trader(trader_address: str):
    """Get comprehensive trader performance analysis."""
    try:
        # Mock trader analysis - would query blockchain and historical data in production
        trader_data = {
            "trader": {
                "address": trader_address,
                "total_portfolio_value_usd": 500000,
                "active_positions": 8,
                "total_markets_traded": 45
            },
            "performance_metrics": {
                "overall_success_rate": 0.73,
                "total_profit_usd": 75000,
                "roi_percentage": 17.8,
                "avg_position_size_usd": 12500,
                "markets_resolved": 25,
                "confidence_interval": [0.67, 0.79]
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
        
        return trader_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trader analysis failed: {str(e)}")

@app.get("/api/system/status")
async def get_system_status():
    """Get system health and performance metrics."""
    try:
        # Get coordinator performance metrics
        performance_metrics = coordinator.get_performance_metrics()
        
        # Get agent status
        agent_status = coordinator.get_agent_status()
        
        return {
            "system_status": "operational",
            "agent_coordinator": performance_metrics,
            "agents": agent_status,
            "api_status": {
                "endpoints_active": 4,
                "last_health_check": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System status check failed: {str(e)}")

@app.get("/api/system/agents/performance")
async def update_agent_performance():
    """Update agent performance weights (admin endpoint)."""
    try:
        # Mock performance data - would come from backtesting and validation in production
        performance_data = {
            "Portfolio Analyzer": 0.85,
            "Success Rate Analyzer": 0.92
        }
        
        coordinator.update_agent_performance(performance_data)
        
        return {
            "message": "Agent performance updated successfully",
            "updated_weights": performance_data,
            "current_status": coordinator.get_agent_status()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent performance update failed: {str(e)}")

# Run the demo
async def run_api_demo():
    """Demonstrate the API endpoints with the AgentCoordinator integration."""
    print("=" * 80)
    print("API INTEGRATION DEMO")
    print("AgentCoordinator integrated with FastAPI endpoints")
    print("=" * 80)
    
    # Simulate API calls
    market_id = "0xdemo_market_123"
    
    print(f"\n1. Alpha Analysis API Call: GET /api/market/{market_id}/alpha")
    print("   Parameters: min_portfolio_ratio=0.1, min_success_rate=0.7")
    
    # Call alpha analysis endpoint
    result = await analyze_market_alpha(
        market_id=market_id,
        min_portfolio_ratio=0.1,
        min_success_rate=0.7,
        min_trade_history=10
    )
    
    print(f"   ✓ Response: Alpha={result.alpha_analysis['has_alpha']}, "
          f"Confidence={result.alpha_analysis['confidence_score']:.3f}")
    print(f"   ✓ Key Traders: {len(result.key_traders)}")
    print(f"   ✓ Agent Votes: {result.alpha_analysis['agent_consensus']['votes_for_alpha']} for alpha")
    
    print(f"\n2. System Status API Call: GET /api/system/status")
    status = await get_system_status()
    
    coord_perf = status["agent_coordinator"]["coordinator_performance"]
    print(f"   ✓ System Status: {status['system_status']}")
    print(f"   ✓ Analysis Success Rate: {coord_perf['success_rate']:.1%}")
    print(f"   ✓ Average Duration: {coord_perf['avg_analysis_duration']:.3f}s")
    
    print(f"\n3. Agent Performance Update: POST /api/system/agents/performance")
    perf_update = await update_agent_performance()
    print(f"   ✓ {perf_update['message']}")
    
    print("\n" + "=" * 80)
    print("API INTEGRATION DEMO COMPLETED")
    print("AgentCoordinator successfully integrated with FastAPI endpoints")
    print("Ready for production deployment!")
    print("=" * 80)

if __name__ == "__main__":
    # Run the demo
    asyncio.run(run_api_demo())
    
    print("\n" + "=" * 50)
    print("To run the actual FastAPI server:")
    print("uvicorn examples.api_integration_example_clean:app --reload")
    print("=" * 50)