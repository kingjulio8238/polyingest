"""
API Integration Example for VotingSystem

This example shows how to integrate the VotingSystem into FastAPI endpoints
for real-time alpha detection in production.
"""

from typing import Dict, Any, Optional
from decimal import Decimal
import asyncio
import logging
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agents import VotingSystem, PortfolioAnalyzerAgent, SuccessRateAgent
from app.config import settings

logger = logging.getLogger(__name__)

class AlphaDetectionService:
    """Service class for alpha detection using the VotingSystem."""
    
    def __init__(self):
        """Initialize the alpha detection service."""
        self.voting_system = VotingSystem(vote_threshold=settings.agent_vote_threshold)
        self._setup_agents()
        logger.info("AlphaDetectionService initialized")
    
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