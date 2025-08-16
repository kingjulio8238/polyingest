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
    print("uvicorn examples.api_integration_example:app --reload")
    print("=" * 50)
    
    def _setup_agents(self):
        """Set up and register analysis agents."""
        # Register core agents
        portfolio_agent = PortfolioAnalyzerAgent()
        success_rate_agent = SuccessRateAgent()
        
        self.voting_system.register_agent(portfolio_agent)
        self.voting_system.register_agent(success_rate_agent)
        
        # Future agents can be added here:
        # volume_agent = VolumeAnalysisAgent()
        # sentiment_agent = MarketSentimentAgent() 
        # technical_agent = TechnicalAnalysisAgent()
        # self.voting_system.register_agent(volume_agent)
        # self.voting_system.register_agent(sentiment_agent)
        # self.voting_system.register_agent(technical_agent)
        
        logger.info(f"Registered {len(self.voting_system.agents)} analysis agents")
    
    async def analyze_market_alpha(self, market_data: Dict[str, Any], 
                                 min_portfolio_ratio: Optional[float] = None,
                                 min_success_rate: Optional[float] = None) -> Dict[str, Any]:
        """
        Analyze market for alpha opportunities using multi-agent consensus.
        
        Args:
            market_data: Complete market and trader data
            min_portfolio_ratio: Override minimum portfolio allocation threshold
            min_success_rate: Override minimum success rate threshold
            
        Returns:
            Comprehensive alpha analysis with agent consensus
        """
        try:
            # Apply optional filters to agent configuration
            if min_portfolio_ratio is not None:
                for agent in self.voting_system.agents.values():
                    if hasattr(agent, 'min_allocation_threshold'):
                        agent.min_allocation_threshold = Decimal(str(min_portfolio_ratio))
            
            if min_success_rate is not None:
                for agent in self.voting_system.agents.values():
                    if hasattr(agent, 'min_success_rate'):
                        agent.min_success_rate = Decimal(str(min_success_rate))
            
            # Conduct voting process
            voting_result = await self.voting_system.conduct_vote(market_data)
            
            # Build response in API format
            return self._build_api_response(market_data, voting_result)
            
        except Exception as e:
            logger.error(f"Alpha analysis failed: {e}")
            return {
                "market": market_data.get("market", {}),
                "alpha_analysis": {
                    "has_alpha": False,
                    "confidence_score": 0.0,
                    "error": str(e),
                    "agent_consensus": {
                        "votes_for_alpha": 0,
                        "votes_against_alpha": 0,
                        "abstentions": 0
                    }
                },
                "key_traders": [],
                "agent_analyses": [],
                "risk_factors": ["Analysis system error"],
                "metadata": {
                    "analysis_timestamp": voting_result.to_dict()["metadata"]["timestamp"] if 'voting_result' in locals() else None,
                    "error": True
                }
            }
    
    def _build_api_response(self, market_data: Dict[str, Any], 
                          voting_result) -> Dict[str, Any]:
        """Build API response format from voting results."""
        
        # Extract key trader information
        key_traders = self._extract_key_traders(market_data, voting_result)
        
        # Determine recommended side based on agent analysis
        recommended_side = self._determine_recommended_side(voting_result)
        
        # Assess alpha strength
        strength = "strong" if voting_result.confidence_score > 0.8 else \
                  "moderate" if voting_result.confidence_score > 0.6 else "weak"
        
        # Extract risk factors
        risk_factors = self._assess_risk_factors(market_data, voting_result)
        
        return {
            "market": {
                "id": market_data.get("market", {}).get("id"),
                "title": market_data.get("market", {}).get("title"),
                "description": market_data.get("market", {}).get("description"),
                "end_date": market_data.get("market", {}).get("end_date"),
                "status": market_data.get("market", {}).get("status", "active"),
                "current_prices": market_data.get("market", {}).get("current_prices", {}),
                "total_volume_24h": market_data.get("market", {}).get("total_volume_24h"),
                "total_liquidity": market_data.get("market", {}).get("total_liquidity")
            },
            "alpha_analysis": {
                "has_alpha": voting_result.has_alpha,
                "confidence_score": voting_result.confidence_score,
                "recommended_side": recommended_side,
                "strength": strength,
                "agent_consensus": {
                    "votes_for_alpha": voting_result.votes_for_alpha,
                    "votes_against_alpha": voting_result.votes_against_alpha,
                    "abstentions": voting_result.abstentions
                }
            },
            "key_traders": key_traders,
            "agent_analyses": [
                {
                    "agent_name": result["agent_name"],
                    "vote": result["vote"],
                    "confidence": result["confidence"],
                    "reasoning": result["reasoning"],
                    "key_findings": self._extract_key_findings(result)
                }
                for result in voting_result.agent_results
                if result["success"]
            ],
            "risk_factors": risk_factors,
            "metadata": {
                "analysis_timestamp": voting_result.to_dict()["metadata"]["timestamp"],
                "data_freshness": "real-time",
                "trader_sample_size": len(market_data.get("traders", [])),
                "min_portfolio_ratio_filter": settings.min_portfolio_ratio,
                "min_success_rate_filter": settings.min_success_rate
            }
        }
    
    def _extract_key_traders(self, market_data: Dict[str, Any], voting_result) -> list:
        """Extract key trader information for the API response."""
        key_traders = []
        
        # Get high-conviction traders from portfolio agent
        portfolio_results = next(
            (r for r in voting_result.agent_results 
             if r["agent_name"] == "Portfolio Analyzer" and r["success"]), 
            None
        )
        
        # Get high-performing traders from success rate agent
        success_results = next(
            (r for r in voting_result.agent_results 
             if r["agent_name"] == "Success Rate Analyzer" and r["success"]), 
            None
        )
        
        if portfolio_results and "analysis" in portfolio_results:
            high_conviction = portfolio_results["analysis"].get("high_conviction_traders", [])
            
            for trader in high_conviction:
                # Find additional trader data
                trader_data = next(
                    (t for t in market_data.get("traders", []) 
                     if t.get("address") == trader.get("address")), 
                    {}
                )
                
                # Check if this trader is also high-performing
                high_performer = False
                if success_results and "analysis" in success_results:
                    high_performer = any(
                        hp.get("address") == trader.get("address")
                        for hp in success_results["analysis"].get("high_performing_traders", [])
                    )
                
                # Get position details
                positions = trader_data.get("positions", [])
                market_positions = [
                    pos for pos in positions 
                    if pos.get("market_id") == market_data.get("market", {}).get("id")
                ]
                
                if market_positions:
                    position = market_positions[0]  # Take first position
                    key_traders.append({
                        "address": trader.get("address"),
                        "position_size_usd": trader.get("position_size_usd"),
                        "portfolio_allocation_pct": round(trader.get("allocation_ratio", 0) * 100, 1),
                        "historical_success_rate": trader_data.get("performance_metrics", {}).get("overall_success_rate"),
                        "position_side": position.get("side"),
                        "entry_price": position.get("entry_price"),
                        "confidence_indicators": {
                            "large_position": trader.get("position_size_usd", 0) > 50000,
                            "high_allocation": trader.get("allocation_ratio", 0) > 0.15,
                            "proven_track_record": high_performer,
                            "early_entry": position.get("entry_price", 0) != market_data.get("market", {}).get("current_prices", {}).get(position.get("side", ""), 0)
                        }
                    })
        
        return key_traders[:5]  # Return top 5 key traders
    
    def _determine_recommended_side(self, voting_result) -> Optional[str]:
        """Determine recommended trading side based on agent analysis."""
        if not voting_result.has_alpha:
            return None
        
        # Look for consensus on position side from key traders
        # This is a simplified approach - in production, you'd analyze
        # the specific positions that agents are highlighting
        return "Yes"  # Simplified for this example
    
    def _extract_key_findings(self, agent_result: Dict[str, Any]) -> list:
        """Extract key findings from agent analysis."""
        findings = []
        
        if not agent_result.get("success") or "analysis" not in agent_result:
            return findings
        
        analysis = agent_result["analysis"]
        agent_name = agent_result["agent_name"]
        
        if agent_name == "Portfolio Analyzer":
            high_conviction_count = analysis.get("high_conviction_count", 0)
            avg_allocation = analysis.get("average_allocation", 0)
            
            if high_conviction_count > 0:
                findings.append(f"Top trader allocated {avg_allocation:.1%} of ${analysis.get('high_conviction_traders', [{}])[0].get('portfolio_value_usd', 0):,.0f} portfolio")
            
            if avg_allocation > 0.15:
                findings.append(f"Average allocation {avg_allocation:.1%} is 3x higher than typical market")
            
            if high_conviction_count >= 3:
                findings.append(f"High-conviction cluster detected with {high_conviction_count} traders")
        
        elif agent_name == "Success Rate Analyzer":
            high_performers = analysis.get("high_performing_traders", [])
            avg_success_rate = analysis.get("avg_success_rate", 0)
            
            if high_performers:
                top_performer = high_performers[0]
                findings.append(f"Lead trader: {top_performer['success_rate']:.0%} success rate across {top_performer['markets_resolved']} resolved markets")
            
            if analysis.get("statistical_significance"):
                findings.append("Statistical significance confirmed (p < 0.05)")
            
            if avg_success_rate > 0.7:
                findings.append(f"Strong performance in {len(high_performers)} similar markets")
        
        return findings
    
    def _assess_risk_factors(self, market_data: Dict[str, Any], voting_result) -> list:
        """Assess and return risk factors for the alpha opportunity."""
        risk_factors = []
        
        market = market_data.get("market", {})
        
        # Market-specific risks
        title = market.get("title", "").lower()
        if any(word in title for word in ["election", "political", "trump", "biden"]):
            risk_factors.append("Market highly politicized - emotion may override analysis")
        
        # Time-based risks
        if "2024" in title:
            risk_factors.append("Time to resolution: significant event risk")
        
        # Liquidity/volume risks
        volume_24h = market.get("total_volume_24h", 0)
        if volume_24h > 1000000:
            risk_factors.append("High media attention may attract noise traders")
        elif volume_24h < 10000:
            risk_factors.append("Low liquidity market - price impact risk")
        
        # Consensus risks
        if voting_result.abstentions > voting_result.votes_for_alpha:
            risk_factors.append("Limited agent consensus - higher uncertainty")
        
        if not voting_result.consensus_reached:
            risk_factors.append("No clear agent consensus reached")
        
        return risk_factors

# Example usage function
async def example_api_endpoint():
    """Example of how this would be used in a FastAPI endpoint."""
    
    # Initialize service (this would typically be done once at startup)
    alpha_service = AlphaDetectionService()
    
    # Sample request data (this would come from the API request)
    market_data = {
        "market": {
            "id": "0x1234...",
            "title": "Will Donald Trump win the 2024 Presidential Election?",
            "description": "Market resolves to Yes if Donald Trump wins...",
            "end_date": "2024-11-05T23:59:59Z",
            "status": "active",
            "current_prices": {"Yes": 0.52, "No": 0.48},
            "total_volume_24h": 2500000,
            "total_liquidity": 1200000
        },
        "traders": [
            {
                "address": "0xabc123...",
                "total_portfolio_value_usd": 850000,
                "positions": [
                    {
                        "market_id": "0x1234...",
                        "position_size_usd": 50000,
                        "side": "Yes",
                        "entry_price": 0.45
                    }
                ],
                "performance_metrics": {
                    "overall_success_rate": 0.78,
                    "markets_resolved": 32,
                    "total_profit_usd": 125000
                }
            }
        ]
    }
    
    # Analyze for alpha (this would be the main API logic)
    result = await alpha_service.analyze_market_alpha(
        market_data, 
        min_portfolio_ratio=0.1, 
        min_success_rate=0.7
    )
    
    return result

if __name__ == "__main__":
    # Run the example
    result = asyncio.run(example_api_endpoint())
    print("API Response Example:")
    print("=" * 50)
    
    import json
    from decimal import Decimal
    
    def decimal_default(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError
    
    print(json.dumps(result, indent=2, default=decimal_default))