from typing import Dict, Any, List, Optional
from decimal import Decimal
import math
from scipy import stats
from app.agents.base_agent import BaseAgent
from app.config import settings
from app.intelligence.performance_calculator import PerformanceCalculator, MarketOutcome, TraderPosition
from app.data.models import MarketOutcomeData, ComprehensivePerformanceMetrics
import logging

logger = logging.getLogger(__name__)

class SuccessRateAgent(BaseAgent):
    """Analyzes trader historical performance and success rates with performance calculator integration."""
    
    def __init__(self, performance_calculator: Optional[PerformanceCalculator] = None):
        super().__init__("Success Rate Analyzer", weight=1.5)
        self.min_success_rate = Decimal(str(settings.min_success_rate))
        self.min_trade_history = settings.min_trade_history
        self.performance_calculator = performance_calculator or PerformanceCalculator()
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trader historical performance data with enhanced performance calculator."""
        market_data = data.get("market")
        traders_data = data.get("traders", [])
        market_outcomes = data.get("market_outcomes", {})
        
        if not market_data or not traders_data:
            logger.warning("Insufficient data for success rate analysis")
            self.confidence = Decimal('0.0')
            return {"error": "Insufficient data"}
        
        high_performing_traders = []
        comprehensive_performance_data = []
        total_success_rate = Decimal('0.0')
        valid_trader_count = 0
        statistical_significance_count = 0
        
        for trader in traders_data:
            trader_address = trader.get("address")
            
            try:
                # Use performance calculator for comprehensive analysis
                performance_metrics = await self.performance_calculator.calculate_trader_performance(
                    trader, market_outcomes
                )
                
                # Extract enhanced metrics
                success_rate = performance_metrics.success_rate
                total_trades = performance_metrics.total_trades
                winning_trades = performance_metrics.winning_trades
                statistical_significance = performance_metrics.statistical_significance
                p_value = performance_metrics.p_value
                confidence_interval = performance_metrics.confidence_interval
                wilson_interval = performance_metrics.wilson_score_interval
                roi_percentage = performance_metrics.roi_percentage
                sharpe_ratio = performance_metrics.sharpe_ratio
                
                # Skip traders with insufficient trade history
                if total_trades < self.min_trade_history:
                    continue
                
                total_success_rate += success_rate
                valid_trader_count += 1
                
                if statistical_significance:
                    statistical_significance_count += 1
                
                # Enhanced trader performance data
                trader_performance = {
                    "address": trader_address,
                    "success_rate": float(success_rate),
                    "total_trades": total_trades,
                    "winning_trades": winning_trades,
                    "losing_trades": performance_metrics.losing_trades,
                    "statistical_significance": statistical_significance,
                    "p_value": float(p_value) if p_value else None,
                    "confidence_interval": [float(ci) for ci in confidence_interval],
                    "wilson_score_interval": [float(wi) for wi in wilson_interval],
                    "roi_percentage": float(roi_percentage),
                    "total_invested": float(performance_metrics.total_invested),
                    "net_profit": float(performance_metrics.net_profit),
                    "sharpe_ratio": float(sharpe_ratio) if sharpe_ratio else None,
                    "maximum_drawdown": float(performance_metrics.maximum_drawdown),
                    "volatility": float(performance_metrics.volatility),
                    "avg_hold_duration_days": performance_metrics.avg_hold_duration_days,
                    "timing_alpha": float(performance_metrics.timing_alpha)
                }
                
                comprehensive_performance_data.append(trader_performance)
                
                # Check if trader meets high performance criteria with enhanced validation
                if (success_rate >= self.min_success_rate and 
                    statistical_significance and 
                    total_trades >= self.min_trade_history):
                    high_performing_traders.append(trader_performance)
                    
            except Exception as e:
                logger.error(f"Error analyzing trader {trader_address}: {e}")
                # Fallback to basic analysis
                performance_data = trader.get("performance_metrics", {})
                success_rate = Decimal(str(performance_data.get("overall_success_rate", 0)))
                markets_resolved = performance_data.get("markets_resolved", 0)
                
                if markets_resolved >= self.min_trade_history:
                    total_success_rate += success_rate
                    valid_trader_count += 1
                    
                    wins = int(markets_resolved * float(success_rate))
                    p_value = self._calculate_binomial_p_value(wins, markets_resolved, 0.5)
                    is_significant = p_value < 0.05
                    
                    if is_significant:
                        statistical_significance_count += 1
                    
                    if success_rate >= self.min_success_rate and is_significant:
                        high_performing_traders.append({
                            "address": trader_address,
                            "success_rate": float(success_rate),
                            "total_trades": markets_resolved,
                            "statistical_significance": is_significant,
                            "p_value": p_value,
                            "fallback_analysis": True
                        })
        
        # Calculate analysis metrics
        avg_success_rate = float(total_success_rate / max(valid_trader_count, 1))
        high_performer_ratio = len(high_performing_traders) / max(len(traders_data), 1)
        significance_ratio = statistical_significance_count / max(valid_trader_count, 1)
        
        # Enhanced confidence calculation with performance calculator data
        enhanced_traders = [t for t in comprehensive_performance_data if not t.get("fallback_analysis")]
        avg_sharpe = sum(t.get("sharpe_ratio", 0) or 0 for t in enhanced_traders) / max(len(enhanced_traders), 1)
        avg_timing_alpha = sum(t.get("timing_alpha", 0) for t in enhanced_traders) / max(len(enhanced_traders), 1)
        
        # Determine confidence based on enhanced findings
        if (len(high_performing_traders) >= 3 and significance_ratio > 0.3 and 
            avg_sharpe > 0.5 and avg_timing_alpha > 0.1):
            self.confidence = Decimal('0.95')
        elif (len(high_performing_traders) >= 2 and avg_success_rate > float(self.min_success_rate) and
              avg_sharpe > 0.2):
            self.confidence = Decimal('0.85')
        elif (len(high_performing_traders) >= 1 and significance_ratio > 0.1 and
              avg_timing_alpha > 0.05):
            self.confidence = Decimal('0.7')
        elif valid_trader_count >= self.min_trade_history:
            self.confidence = Decimal('0.4')
        else:
            self.confidence = Decimal('0.1')
        
        analysis_result = {
            "high_performing_traders": high_performing_traders,
            "comprehensive_performance_data": comprehensive_performance_data,
            "total_traders_analyzed": len(traders_data),
            "valid_traders_count": valid_trader_count,
            "high_performers_count": len(high_performing_traders),
            "avg_success_rate": avg_success_rate,
            "avg_sharpe_ratio": avg_sharpe,
            "avg_timing_alpha": avg_timing_alpha,
            "high_performer_ratio": high_performer_ratio,
            "statistical_significance": statistical_significance_count > 0,
            "statistically_significant_traders": statistical_significance_count,
            "significance_ratio": significance_ratio,
            "enhanced_analysis_count": len(enhanced_traders),
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