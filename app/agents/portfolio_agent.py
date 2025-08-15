from typing import Dict, Any, List
from decimal import Decimal
from app.agents.base_agent import BaseAgent
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class PortfolioAnalyzerAgent(BaseAgent):
    """Analyzes trader portfolio allocation patterns."""
    
    def __init__(self):
        super().__init__("Portfolio Analyzer", weight=1.2)
        self.min_allocation_threshold = Decimal(str(settings.min_portfolio_ratio))
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio allocation patterns."""
        market_data = data.get("market")
        traders_data = data.get("traders", [])
        
        if not market_data or not traders_data:
            logger.warning("Insufficient data for portfolio analysis")
            self.confidence = Decimal('0.0')
            return {"error": "Insufficient data"}
        
        high_conviction_traders = []
        total_allocation = Decimal('0.0')
        allocation_count = 0
        
        for trader in traders_data:
            positions = trader.get("positions", [])
            portfolio_value = Decimal(str(trader.get("total_portfolio_value_usd", 0)))
            
            if portfolio_value == 0:
                continue
            
            # Find positions in this specific market
            market_positions = [
                pos for pos in positions 
                if pos.get("market_id") == market_data.get("id")
            ]
            
            if not market_positions:
                continue
            
            # Calculate total allocation to this market
            market_allocation = sum(
                Decimal(str(pos.get("position_size_usd", 0))) 
                for pos in market_positions
            )
            
            allocation_ratio = market_allocation / portfolio_value
            total_allocation += allocation_ratio
            allocation_count += 1
            
            # Check if this trader meets high conviction criteria
            if allocation_ratio >= self.min_allocation_threshold:
                high_conviction_traders.append({
                    "address": trader.get("address"),
                    "allocation_ratio": allocation_ratio,
                    "position_size_usd": market_allocation,
                    "portfolio_value_usd": portfolio_value
                })
        
        # Calculate analysis metrics
        avg_allocation = total_allocation / max(allocation_count, 1)
        conviction_ratio = len(high_conviction_traders) / max(len(traders_data), 1)
        
        # Determine confidence based on findings
        if len(high_conviction_traders) >= 3 and avg_allocation > self.min_allocation_threshold:
            self.confidence = Decimal('0.9')
        elif len(high_conviction_traders) >= 2:
            self.confidence = Decimal('0.7')
        elif len(high_conviction_traders) >= 1:
            self.confidence = Decimal('0.5')
        else:
            self.confidence = Decimal('0.2')
        
        analysis_result = {
            "high_conviction_traders": high_conviction_traders,
            "total_traders_analyzed": len(traders_data),
            "high_conviction_count": len(high_conviction_traders),
            "average_allocation": float(avg_allocation),
            "conviction_ratio": conviction_ratio,
            "confidence": float(self.confidence)
        }
        
        self.last_analysis = analysis_result
        return analysis_result
    
    def vote(self, analysis: Dict[str, Any]) -> str:
        """Vote based on portfolio allocation analysis."""
        if "error" in analysis:
            return "abstain"
        
        high_conviction_count = analysis.get("high_conviction_count", 0)
        conviction_ratio = analysis.get("conviction_ratio", 0)
        avg_allocation = analysis.get("average_allocation", 0)
        
        # Strong alpha signal: Multiple high-conviction traders
        if high_conviction_count >= 3 and conviction_ratio > 0.15:
            return "alpha"
        
        # Moderate alpha signal: Some high-conviction activity
        elif high_conviction_count >= 2 and avg_allocation > settings.min_portfolio_ratio:
            return "alpha"
        
        # Weak signal
        elif high_conviction_count >= 1:
            return "alpha" if self.confidence > Decimal('0.6') else "abstain"
        
        return "no_alpha"
    
    def get_reasoning(self) -> str:
        """Get human-readable reasoning for the vote."""
        if not self.last_analysis:
            return "No analysis performed"
        
        count = self.last_analysis.get("high_conviction_count", 0)
        avg_alloc = self.last_analysis.get("average_allocation", 0)
        
        if count >= 3:
            return f"{count} traders with >10% portfolio allocation, avg {avg_alloc:.1%}"
        elif count >= 2:
            return f"{count} traders showing high conviction with avg {avg_alloc:.1%} allocation"
        elif count >= 1:
            return f"{count} trader with significant portfolio allocation"
        else:
            return "No significant portfolio allocation patterns detected"