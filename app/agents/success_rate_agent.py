from typing import Dict, Any, List
from decimal import Decimal
import math
from scipy import stats
from app.agents.base_agent import BaseAgent
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class SuccessRateAgent(BaseAgent):
    """Analyzes trader historical performance and success rates."""
    
    def __init__(self):
        super().__init__("Success Rate Analyzer", weight=1.5)
        self.min_success_rate = Decimal(str(settings.min_success_rate))
        self.min_trade_history = settings.min_trade_history
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trader historical performance data."""
        market_data = data.get("market")
        traders_data = data.get("traders", [])
        
        if not market_data or not traders_data:
            logger.warning("Insufficient data for success rate analysis")
            self.confidence = Decimal('0.0')
            return {"error": "Insufficient data"}
        
        high_performing_traders = []
        total_success_rate = Decimal('0.0')
        valid_trader_count = 0
        statistical_significance_count = 0
        
        for trader in traders_data:
            trader_address = trader.get("address")
            performance_data = trader.get("performance_metrics", {})
            
            # Extract performance metrics
            success_rate = performance_data.get("overall_success_rate", 0)
            markets_resolved = performance_data.get("markets_resolved", 0)
            total_profit_usd = performance_data.get("total_profit_usd", 0)
            
            # Skip traders with insufficient trade history
            if markets_resolved < self.min_trade_history:
                continue
            
            success_rate_decimal = Decimal(str(success_rate))
            total_success_rate += success_rate_decimal
            valid_trader_count += 1
            
            # Calculate statistical significance using binomial test
            # H0: success_rate = 0.5 (random), H1: success_rate > 0.5
            wins = int(markets_resolved * success_rate)
            p_value = self._calculate_binomial_p_value(wins, markets_resolved, 0.5)
            is_statistically_significant = p_value < 0.05
            
            if is_statistically_significant:
                statistical_significance_count += 1
            
            # Calculate confidence interval for success rate
            confidence_interval = self._calculate_confidence_interval(wins, markets_resolved)
            
            # Check if trader meets high performance criteria
            if success_rate_decimal >= self.min_success_rate and is_statistically_significant:
                high_performing_traders.append({
                    "address": trader_address,
                    "success_rate": success_rate,
                    "markets_resolved": markets_resolved,
                    "total_profit_usd": total_profit_usd,
                    "statistical_significance": is_statistically_significant,
                    "p_value": p_value,
                    "confidence_interval": confidence_interval,
                    "wins": wins,
                    "losses": markets_resolved - wins
                })
        
        # Calculate analysis metrics
        avg_success_rate = float(total_success_rate / max(valid_trader_count, 1))
        high_performer_ratio = len(high_performing_traders) / max(len(traders_data), 1)
        significance_ratio = statistical_significance_count / max(valid_trader_count, 1)
        
        # Determine confidence based on findings
        if len(high_performing_traders) >= 3 and significance_ratio > 0.3:
            self.confidence = Decimal('0.95')
        elif len(high_performing_traders) >= 2 and avg_success_rate > float(self.min_success_rate):
            self.confidence = Decimal('0.85')
        elif len(high_performing_traders) >= 1 and significance_ratio > 0.1:
            self.confidence = Decimal('0.7')
        elif valid_trader_count >= self.min_trade_history:
            self.confidence = Decimal('0.4')
        else:
            self.confidence = Decimal('0.1')
        
        analysis_result = {
            "high_performing_traders": high_performing_traders,
            "total_traders_analyzed": len(traders_data),
            "valid_traders_count": valid_trader_count,
            "high_performers_count": len(high_performing_traders),
            "avg_success_rate": avg_success_rate,
            "high_performer_ratio": high_performer_ratio,
            "statistical_significance": statistical_significance_count > 0,
            "statistically_significant_traders": statistical_significance_count,
            "significance_ratio": significance_ratio,
            "confidence": float(self.confidence)
        }
        
        self.last_analysis = analysis_result
        return analysis_result
    
    def vote(self, analysis: Dict[str, Any]) -> str:
        """Vote based on success rate analysis."""
        if "error" in analysis:
            return "abstain"
        
        high_performers_count = analysis.get("high_performers_count", 0)
        avg_success_rate = analysis.get("avg_success_rate", 0)
        significance_ratio = analysis.get("significance_ratio", 0)
        statistical_significance = analysis.get("statistical_significance", False)
        
        # Strong alpha signal: Multiple high-performing traders with statistical significance
        if high_performers_count >= 3 and statistical_significance:
            return "alpha"
        
        # Moderate alpha signal: Some high-performing traders
        elif high_performers_count >= 2 and avg_success_rate > float(self.min_success_rate):
            return "alpha"
        
        # Exceptional single trader performance
        elif high_performers_count >= 1 and significance_ratio > 0.2:
            return "alpha"
        
        # Borderline cases - need more evidence
        elif high_performers_count >= 1 or (avg_success_rate > 0.65 and statistical_significance):
            return "abstain"
        
        return "no_alpha"
    
    def get_reasoning(self) -> str:
        """Get human-readable reasoning for the vote."""
        if not self.last_analysis:
            return "No analysis performed"
        
        high_performers = self.last_analysis.get("high_performers_count", 0)
        avg_rate = self.last_analysis.get("avg_success_rate", 0)
        sig_traders = self.last_analysis.get("statistically_significant_traders", 0)
        valid_traders = self.last_analysis.get("valid_traders_count", 0)
        
        if high_performers >= 3:
            return f"{high_performers} traders with >{self.min_success_rate:.0%} success rate, {sig_traders} statistically significant"
        elif high_performers >= 2:
            return f"{high_performers} high-performing traders with {avg_rate:.1%} avg success rate"
        elif high_performers >= 1:
            return f"{high_performers} trader with proven track record above {self.min_success_rate:.0%}"
        elif sig_traders > 0:
            return f"{sig_traders} traders show statistical significance with {avg_rate:.1%} avg rate"
        elif valid_traders >= self.min_trade_history:
            return f"Analyzed {valid_traders} traders, avg success rate {avg_rate:.1%}"
        else:
            return "Insufficient trader history for reliable analysis"
    
    def _calculate_binomial_p_value(self, wins: int, total: int, null_prob: float = 0.5) -> float:
        """Calculate p-value for binomial test (one-tailed)."""
        try:
            # One-tailed test: P(X >= wins | p = null_prob)
            p_value = 1 - stats.binom.cdf(wins - 1, total, null_prob)
            return float(p_value)
        except Exception as e:
            logger.error(f"Error calculating p-value: {e}")
            return 1.0  # Conservative: assume not significant
    
    def _calculate_confidence_interval(self, wins: int, total: int, confidence_level: float = 0.95) -> List[float]:
        """Calculate confidence interval for binomial proportion."""
        try:
            if total == 0:
                return [0.0, 0.0]
            
            p = wins / total
            z = stats.norm.ppf((1 + confidence_level) / 2)  # Critical value for given confidence level
            
            # Wilson score interval (more accurate for small samples)
            denominator = 1 + z**2 / total
            center = (p + z**2 / (2 * total)) / denominator
            margin = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denominator
            
            lower = max(0.0, center - margin)
            upper = min(1.0, center + margin)
            
            return [round(lower, 3), round(upper, 3)]
        except Exception as e:
            logger.error(f"Error calculating confidence interval: {e}")
            return [0.0, 1.0]  # Conservative: maximum uncertainty