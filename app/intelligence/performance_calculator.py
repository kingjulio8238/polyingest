from typing import Dict, List, Any, Tuple, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import logging
import statistics
import math
from dataclasses import dataclass, asdict
from enum import Enum
import time

# Statistical libraries for advanced calculations
try:
    import scipy.stats as stats
    from scipy import special
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("SciPy not available - using simplified statistical calculations")

logger = logging.getLogger(__name__)

class MarketResolution(Enum):
    """Market resolution outcomes."""
    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"
    VOID = "void"
    PENDING = "pending"

@dataclass
class MarketOutcome:
    """Represents a resolved market outcome."""
    market_id: str
    resolution: MarketResolution
    winning_outcome_id: str
    resolution_timestamp: int
    resolution_source: str
    confidence_score: Decimal  # 0-1, confidence in resolution accuracy

@dataclass
class TraderPosition:
    """Represents a trader's position in a market."""
    market_id: str
    outcome_id: str
    position_size_usd: Decimal
    entry_price: Decimal
    entry_timestamp: int
    exit_price: Optional[Decimal] = None
    exit_timestamp: Optional[int] = None
    current_price: Optional[Decimal] = None
    status: str = "active"  # active, closed, expired

@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for a trader."""
    success_rate: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    confidence_interval: Tuple[Decimal, Decimal]
    wilson_score_interval: Tuple[Decimal, Decimal]
    statistical_significance: bool
    p_value: Optional[Decimal]
    
    # Financial metrics
    total_invested: Decimal
    total_returns: Decimal
    net_profit: Decimal
    roi_percentage: Decimal
    sharpe_ratio: Optional[Decimal]
    sortino_ratio: Optional[Decimal]
    maximum_drawdown: Decimal
    
    # Risk metrics
    volatility: Decimal
    value_at_risk_95: Decimal
    expected_shortfall_95: Decimal
    
    # Timing metrics
    avg_hold_duration_days: float
    win_rate_by_duration: Dict[str, Decimal]
    timing_alpha: Decimal

@dataclass
class PerformanceTrend:
    """Performance trend analysis over time."""
    time_period: str
    period_start: datetime
    period_end: datetime
    success_rate: Decimal
    trade_count: int
    net_profit: Decimal
    roi_percentage: Decimal
    trend_direction: str  # improving, declining, stable

class PerformanceCalculator:
    """
    Comprehensive performance calculator for trader analysis.
    Tracks actual market outcomes and calculates statistically sound performance metrics.
    """
    
    def __init__(self):
        self.confidence_level = 0.95
        self.min_trades_for_significance = 10
        self.risk_free_rate = Decimal('0.02')  # 2% annual risk-free rate
        
        # Market outcome cache
        self.market_outcomes: Dict[str, MarketOutcome] = {}
        self.position_cache: Dict[str, List[TraderPosition]] = {}
        
    async def calculate_trader_performance(
        self, 
        trader_data: Dict[str, Any], 
        market_outcomes: Dict[str, MarketOutcome]
    ) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics for a trader.
        
        Args:
            trader_data: Trader portfolio and position data
            market_outcomes: Dictionary of resolved market outcomes
            
        Returns:
            Comprehensive performance metrics with statistical confidence
        """
        logger.info(f"Calculating performance for trader: {trader_data.get('address', 'unknown')}")
        
        try:
            # Extract positions and create TraderPosition objects
            positions = self._extract_trader_positions(trader_data)
            
            if not positions:
                logger.warning("No positions found for performance calculation")
                return self._create_empty_performance_metrics()
            
            # Match positions with market outcomes
            resolved_positions = self._match_positions_with_outcomes(positions, market_outcomes)
            
            if not resolved_positions:
                logger.warning("No resolved positions found for performance calculation")
                return self._create_performance_from_active_positions(positions)
            
            # Calculate success rate metrics
            success_metrics = self._calculate_success_rate_metrics(resolved_positions)
            
            # Calculate financial performance metrics
            financial_metrics = self._calculate_financial_metrics(resolved_positions, positions)
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(resolved_positions)
            
            # Calculate timing metrics
            timing_metrics = self._calculate_timing_metrics(resolved_positions)
            
            # Combine all metrics
            performance = PerformanceMetrics(
                **success_metrics,
                **financial_metrics,
                **risk_metrics,
                **timing_metrics
            )
            
            logger.info(f"Performance calculation complete: {success_metrics['success_rate']:.1%} success rate, "
                       f"{financial_metrics['roi_percentage']:.1f}% ROI")
            
            return performance
            
        except Exception as e:
            logger.error(f"Error calculating trader performance: {e}")
            return self._create_empty_performance_metrics()
    
    async def track_market_outcomes(self, market_id: str, resolution_data: Dict[str, Any]) -> MarketOutcome:
        """
        Track and store market outcome data for performance correlation.
        
        Args:
            market_id: Unique market identifier
            resolution_data: Market resolution information
            
        Returns:
            MarketOutcome object with resolution details
        """
        try:
            # Parse resolution data
            resolution_str = resolution_data.get("resolution", "pending").lower()
            resolution = MarketResolution(resolution_str) if resolution_str in [r.value for r in MarketResolution] else MarketResolution.PENDING
            
            outcome = MarketOutcome(
                market_id=market_id,
                resolution=resolution,
                winning_outcome_id=resolution_data.get("winning_outcome_id", ""),
                resolution_timestamp=resolution_data.get("resolution_timestamp", int(time.time())),
                resolution_source=resolution_data.get("resolution_source", "unknown"),
                confidence_score=Decimal(str(resolution_data.get("confidence_score", 0.95)))
            )
            
            # Cache the outcome
            self.market_outcomes[market_id] = outcome
            
            logger.info(f"Tracked market outcome for {market_id}: {resolution.value}")
            return outcome
            
        except Exception as e:
            logger.error(f"Error tracking market outcome for {market_id}: {e}")
            raise
    
    def calculate_success_rate(self, positions: List[TraderPosition], outcomes: Dict[str, MarketOutcome]) -> Dict[str, Any]:
        """
        Calculate success rate with statistical confidence intervals.
        
        Args:
            positions: List of trader positions
            outcomes: Market outcomes for correlation
            
        Returns:
            Dictionary with success rate and confidence metrics
        """
        try:
            resolved_positions = self._match_positions_with_outcomes(positions, outcomes)
            
            if not resolved_positions:
                return {
                    "success_rate": Decimal('0'),
                    "total_trades": 0,
                    "winning_trades": 0,
                    "confidence_interval": (Decimal('0'), Decimal('1')),
                    "wilson_score_interval": (Decimal('0'), Decimal('1')),
                    "statistical_significance": False,
                    "p_value": None
                }
            
            return self._calculate_success_rate_metrics(resolved_positions)
            
        except Exception as e:
            logger.error(f"Error calculating success rate: {e}")
            return {"error": str(e)}
    
    def calculate_risk_adjusted_returns(self, positions: List[TraderPosition], timeframe_days: int = 365) -> Dict[str, Any]:
        """
        Calculate risk-adjusted returns including Sharpe and Sortino ratios.
        
        Args:
            positions: List of trader positions
            timeframe_days: Analysis timeframe in days
            
        Returns:
            Dictionary with risk-adjusted performance metrics
        """
        try:
            if not positions:
                return self._create_empty_risk_metrics()
            
            # Calculate returns for each position
            returns = []
            for position in positions:
                if position.status == "closed" and position.exit_price is not None:
                    position_return = (position.exit_price - position.entry_price) / position.entry_price
                    returns.append(float(position_return))
            
            if not returns:
                return self._create_empty_risk_metrics()
            
            # Calculate risk metrics
            mean_return = statistics.mean(returns)
            return_volatility = statistics.stdev(returns) if len(returns) > 1 else 0.0
            
            # Annualize metrics
            annualized_return = mean_return * (365 / timeframe_days)
            annualized_volatility = return_volatility * math.sqrt(365 / timeframe_days)
            
            # Calculate Sharpe ratio
            risk_free_annual = float(self.risk_free_rate)
            sharpe_ratio = (annualized_return - risk_free_annual) / annualized_volatility if annualized_volatility > 0 else None
            
            # Calculate Sortino ratio (downside deviation)
            downside_returns = [r for r in returns if r < 0]
            downside_volatility = statistics.stdev(downside_returns) if len(downside_returns) > 1 else 0.0
            annualized_downside_vol = downside_volatility * math.sqrt(365 / timeframe_days)
            sortino_ratio = (annualized_return - risk_free_annual) / annualized_downside_vol if annualized_downside_vol > 0 else None
            
            return {
                "mean_return": Decimal(str(mean_return)),
                "volatility": Decimal(str(return_volatility)),
                "annualized_return": Decimal(str(annualized_return)),
                "annualized_volatility": Decimal(str(annualized_volatility)),
                "sharpe_ratio": Decimal(str(sharpe_ratio)) if sharpe_ratio is not None else None,
                "sortino_ratio": Decimal(str(sortino_ratio)) if sortino_ratio is not None else None,
                "max_drawdown": self._calculate_maximum_drawdown(returns)
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk-adjusted returns: {e}")
            return {"error": str(e)}
    
    def analyze_performance_trends(self, trader_history: List[Dict[str, Any]], time_periods: List[str]) -> List[PerformanceTrend]:
        """
        Analyze performance trends over different time periods.
        
        Args:
            trader_history: Historical trading data
            time_periods: List of time periods to analyze (e.g., ['30d', '90d', '1y'])
            
        Returns:
            List of performance trends for each time period
        """
        trends = []
        current_time = datetime.utcnow()
        
        for period in time_periods:
            try:
                # Parse time period
                days = self._parse_time_period(period)
                period_start = current_time - timedelta(days=days)
                
                # Filter data for this period
                period_data = [
                    trade for trade in trader_history
                    if datetime.fromtimestamp(trade.get('timestamp', 0)) >= period_start
                ]
                
                if not period_data:
                    continue
                
                # Calculate period metrics
                success_rate = self._calculate_period_success_rate(period_data)
                net_profit = sum(Decimal(str(trade.get('profit_loss', 0))) for trade in period_data)
                total_invested = sum(Decimal(str(trade.get('position_size', 0))) for trade in period_data)
                roi = (net_profit / total_invested * 100) if total_invested > 0 else Decimal('0')
                
                # Determine trend direction
                trend_direction = self._determine_trend_direction(period_data)
                
                trend = PerformanceTrend(
                    time_period=period,
                    period_start=period_start,
                    period_end=current_time,
                    success_rate=success_rate,
                    trade_count=len(period_data),
                    net_profit=net_profit,
                    roi_percentage=roi,
                    trend_direction=trend_direction
                )
                
                trends.append(trend)
                
            except Exception as e:
                logger.error(f"Error analyzing trend for period {period}: {e}")
                continue
        
        return trends
    
    def validate_statistical_significance(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate statistical significance of performance metrics.
        
        Args:
            performance_data: Performance data to validate
            
        Returns:
            Dictionary with significance test results
        """
        try:
            success_rate = performance_data.get('success_rate', 0)
            total_trades = performance_data.get('total_trades', 0)
            winning_trades = performance_data.get('winning_trades', 0)
            
            if total_trades < self.min_trades_for_significance:
                return {
                    "is_significant": False,
                    "reason": f"Insufficient sample size (need >= {self.min_trades_for_significance})",
                    "p_value": None,
                    "test_statistic": None
                }
            
            # Binomial test against null hypothesis of 50% success rate
            if SCIPY_AVAILABLE:
                from scipy.stats import binomtest
                result = binomtest(winning_trades, total_trades, 0.5, alternative='two-sided')
                p_value = result.pvalue
                z_score = stats.norm.ppf(1 - (1 - self.confidence_level) / 2)
                
                return {
                    "is_significant": p_value < (1 - self.confidence_level),
                    "p_value": Decimal(str(p_value)),
                    "z_score": Decimal(str(z_score)),
                    "confidence_level": self.confidence_level,
                    "null_hypothesis": "Success rate = 50%",
                    "alternative_hypothesis": "Success rate ≠ 50%"
                }
            else:
                # Simplified significance test without scipy
                return self._simplified_significance_test(success_rate, total_trades)
                
        except Exception as e:
            logger.error(f"Error validating statistical significance: {e}")
            return {"error": str(e)}
    
    def _extract_trader_positions(self, trader_data: Dict[str, Any]) -> List[TraderPosition]:
        """Extract and convert position data to TraderPosition objects."""
        positions = []
        
        for pos_data in trader_data.get("positions", []):
            try:
                position = TraderPosition(
                    market_id=pos_data.get("market_id", ""),
                    outcome_id=pos_data.get("outcome_id", "unknown"),
                    position_size_usd=Decimal(str(pos_data.get("total_position_size_usd", 0))),
                    entry_price=Decimal(str(pos_data.get("entry_price", 0.5))),
                    entry_timestamp=pos_data.get("first_entry_timestamp", 0),
                    exit_timestamp=pos_data.get("exit_timestamp"),
                    current_price=Decimal(str(pos_data.get("current_price", 0.5))) if pos_data.get("current_price") else None,
                    status=pos_data.get("status", "active")
                )
                positions.append(position)
                
            except Exception as e:
                logger.error(f"Error parsing position data: {e}")
                continue
        
        return positions
    
    def _match_positions_with_outcomes(self, positions: List[TraderPosition], outcomes: Dict[str, MarketOutcome]) -> List[Tuple[TraderPosition, MarketOutcome]]:
        """Match trader positions with market outcomes for performance calculation."""
        matched = []
        
        for position in positions:
            outcome = outcomes.get(position.market_id)
            if outcome and outcome.resolution != MarketResolution.PENDING:
                matched.append((position, outcome))
        
        return matched
    
    def _calculate_success_rate_metrics(self, resolved_positions: List[Tuple[TraderPosition, MarketOutcome]]) -> Dict[str, Any]:
        """Calculate success rate with statistical confidence intervals."""
        total_trades = len(resolved_positions)
        winning_trades = 0
        
        for position, outcome in resolved_positions:
            if outcome.resolution == MarketResolution.WIN and position.outcome_id == outcome.winning_outcome_id:
                winning_trades += 1
            elif outcome.resolution == MarketResolution.LOSS and position.outcome_id != outcome.winning_outcome_id:
                winning_trades += 1
        
        if total_trades == 0:
            return {
                "success_rate": Decimal('0'),
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "confidence_interval": (Decimal('0'), Decimal('1')),
                "wilson_score_interval": (Decimal('0'), Decimal('1')),
                "statistical_significance": False,
                "p_value": None
            }
        
        success_rate = Decimal(winning_trades) / Decimal(total_trades)
        losing_trades = total_trades - winning_trades
        
        # Calculate confidence intervals
        confidence_interval = self._calculate_confidence_interval(success_rate, total_trades)
        wilson_interval = self._calculate_wilson_score_interval(winning_trades, total_trades)
        
        # Statistical significance test
        significance_result = self.validate_statistical_significance({
            'success_rate': success_rate,
            'total_trades': total_trades,
            'winning_trades': winning_trades
        })
        
        return {
            "success_rate": success_rate,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "confidence_interval": confidence_interval,
            "wilson_score_interval": wilson_interval,
            "statistical_significance": significance_result.get("is_significant", False),
            "p_value": significance_result.get("p_value")
        }
    
    def _calculate_financial_metrics(self, resolved_positions: List[Tuple[TraderPosition, MarketOutcome]], all_positions: List[TraderPosition]) -> Dict[str, Any]:
        """Calculate financial performance metrics."""
        total_invested = Decimal('0')
        total_returns = Decimal('0')
        
        # Calculate from resolved positions
        for position, outcome in resolved_positions:
            total_invested += position.position_size_usd
            
            # Calculate return based on outcome
            if outcome.resolution == MarketResolution.WIN and position.outcome_id == outcome.winning_outcome_id:
                # Winning position - assume full payout
                total_returns += position.position_size_usd / position.entry_price
            elif outcome.resolution == MarketResolution.LOSS:
                # Losing position - total loss
                total_returns += Decimal('0')
            elif outcome.resolution == MarketResolution.DRAW:
                # Draw - return original investment
                total_returns += position.position_size_usd
        
        # Add active positions at current value
        for position in all_positions:
            if position.status == "active" and position.current_price:
                current_value = position.position_size_usd * (position.current_price / position.entry_price)
                total_returns += current_value
                if position.market_id not in [p.market_id for p, _ in resolved_positions]:
                    total_invested += position.position_size_usd
        
        net_profit = total_returns - total_invested
        roi_percentage = (net_profit / total_invested * 100) if total_invested > 0 else Decimal('0')
        
        return {
            "total_invested": total_invested,
            "total_returns": total_returns,
            "net_profit": net_profit,
            "roi_percentage": roi_percentage
        }
    
    def _calculate_risk_metrics(self, resolved_positions: List[Tuple[TraderPosition, MarketOutcome]]) -> Dict[str, Any]:
        """Calculate risk metrics including VaR and expected shortfall."""
        if not resolved_positions:
            return self._create_empty_risk_metrics()
        
        # Calculate returns for each position
        returns = []
        for position, outcome in resolved_positions:
            if outcome.resolution == MarketResolution.WIN and position.outcome_id == outcome.winning_outcome_id:
                position_return = (Decimal('1') - position.entry_price) / position.entry_price
            else:
                position_return = -position.entry_price / position.entry_price
            returns.append(float(position_return))
        
        if not returns:
            return self._create_empty_risk_metrics()
        
        # Calculate volatility
        volatility = Decimal(str(statistics.stdev(returns))) if len(returns) > 1 else Decimal('0')
        
        # Calculate VaR and Expected Shortfall at 95% confidence
        sorted_returns = sorted(returns)
        var_index = int(len(sorted_returns) * 0.05)  # 5th percentile
        var_95 = Decimal(str(sorted_returns[var_index])) if var_index < len(sorted_returns) else Decimal('0')
        
        # Expected Shortfall (average of returns below VaR)
        tail_returns = sorted_returns[:var_index] if var_index > 0 else [sorted_returns[0]]
        expected_shortfall = Decimal(str(statistics.mean(tail_returns))) if tail_returns else Decimal('0')
        
        # Maximum drawdown
        max_drawdown = self._calculate_maximum_drawdown(returns)
        
        return {
            "volatility": volatility,
            "value_at_risk_95": abs(var_95),
            "expected_shortfall_95": abs(expected_shortfall),
            "maximum_drawdown": max_drawdown
        }
    
    def _calculate_timing_metrics(self, resolved_positions: List[Tuple[TraderPosition, MarketOutcome]]) -> Dict[str, Any]:
        """Calculate timing-related performance metrics."""
        if not resolved_positions:
            return {
                "avg_hold_duration_days": 0.0,
                "win_rate_by_duration": {},
                "timing_alpha": Decimal('0')
            }
        
        durations = []
        short_term_wins = 0
        short_term_total = 0
        long_term_wins = 0
        long_term_total = 0
        
        for position, outcome in resolved_positions:
            # Calculate hold duration
            if outcome.resolution_timestamp and position.entry_timestamp:
                duration_seconds = outcome.resolution_timestamp - position.entry_timestamp
                duration_days = duration_seconds / (24 * 60 * 60)
                durations.append(duration_days)
                
                # Categorize by duration
                is_winner = (outcome.resolution == MarketResolution.WIN and 
                           position.outcome_id == outcome.winning_outcome_id)
                
                if duration_days <= 7:  # Short-term (1 week)
                    short_term_total += 1
                    if is_winner:
                        short_term_wins += 1
                else:  # Long-term
                    long_term_total += 1
                    if is_winner:
                        long_term_wins += 1
        
        avg_duration = statistics.mean(durations) if durations else 0.0
        
        # Calculate win rates by duration
        win_rate_by_duration = {}
        if short_term_total > 0:
            win_rate_by_duration["short_term"] = Decimal(short_term_wins) / Decimal(short_term_total)
        if long_term_total > 0:
            win_rate_by_duration["long_term"] = Decimal(long_term_wins) / Decimal(long_term_total)
        
        # Simple timing alpha calculation
        timing_alpha = Decimal('0')
        if short_term_total > 0 and long_term_total > 0:
            short_rate = win_rate_by_duration.get("short_term", Decimal('0'))
            long_rate = win_rate_by_duration.get("long_term", Decimal('0'))
            timing_alpha = abs(short_rate - long_rate)  # Higher = better timing differentiation
        
        return {
            "avg_hold_duration_days": avg_duration,
            "win_rate_by_duration": win_rate_by_duration,
            "timing_alpha": timing_alpha
        }
    
    def _calculate_confidence_interval(self, success_rate: Decimal, sample_size: int) -> Tuple[Decimal, Decimal]:
        """Calculate normal approximation confidence interval."""
        if sample_size < 5:
            return (Decimal('0'), Decimal('1'))
        
        p = float(success_rate)
        n = sample_size
        z = 1.96  # 95% confidence
        
        margin = z * math.sqrt((p * (1 - p)) / n)
        lower = max(Decimal('0'), Decimal(str(p - margin)))
        upper = min(Decimal('1'), Decimal(str(p + margin)))
        
        return (lower, upper)
    
    def _calculate_wilson_score_interval(self, successes: int, total: int) -> Tuple[Decimal, Decimal]:
        """Calculate Wilson score confidence interval (more robust for small samples)."""
        if total == 0:
            return (Decimal('0'), Decimal('1'))
        
        z = 1.96  # 95% confidence
        n = total
        p = successes / n
        
        denominator = 1 + (z**2 / n)
        centre = (p + (z**2 / (2*n))) / denominator
        margin = (z / denominator) * math.sqrt((p * (1-p) / n) + (z**2 / (4*n**2)))
        
        lower = max(Decimal('0'), Decimal(str(centre - margin)))
        upper = min(Decimal('1'), Decimal(str(centre + margin)))
        
        return (lower, upper)
    
    def _calculate_maximum_drawdown(self, returns: List[float]) -> Decimal:
        """Calculate maximum drawdown from returns series."""
        if not returns:
            return Decimal('0')
        
        cumulative = 1.0
        peak = 1.0
        max_drawdown = 0.0
        
        for ret in returns:
            cumulative *= (1 + ret)
            if cumulative > peak:
                peak = cumulative
            
            drawdown = (peak - cumulative) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        return Decimal(str(max_drawdown))
    
    def _create_empty_performance_metrics(self) -> PerformanceMetrics:
        """Create empty performance metrics structure."""
        return PerformanceMetrics(
            success_rate=Decimal('0'),
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            confidence_interval=(Decimal('0'), Decimal('1')),
            wilson_score_interval=(Decimal('0'), Decimal('1')),
            statistical_significance=False,
            p_value=None,
            total_invested=Decimal('0'),
            total_returns=Decimal('0'),
            net_profit=Decimal('0'),
            roi_percentage=Decimal('0'),
            maximum_drawdown=Decimal('0'),
            volatility=Decimal('0'),
            value_at_risk_95=Decimal('0'),
            expected_shortfall_95=Decimal('0'),
            avg_hold_duration_days=0.0,
            win_rate_by_duration={},
            timing_alpha=Decimal('0'),
            sharpe_ratio=None,
            sortino_ratio=None
        )
    
    def _create_performance_from_active_positions(self, positions: List[TraderPosition]) -> PerformanceMetrics:
        """Create performance metrics from active positions only."""
        total_invested = sum(pos.position_size_usd for pos in positions)
        current_value = sum(
            pos.position_size_usd * (pos.current_price / pos.entry_price) 
            if pos.current_price else pos.position_size_usd
            for pos in positions
        )
        
        unrealized_pnl = current_value - total_invested
        roi = (unrealized_pnl / total_invested * 100) if total_invested > 0 else Decimal('0')
        
        # Create metrics with limited data
        metrics = self._create_empty_performance_metrics()
        # Update the specific fields since dataclass is immutable
        from dataclasses import replace
        metrics = replace(
            metrics,
            total_invested=total_invested,
            total_returns=current_value,
            net_profit=unrealized_pnl,
            roi_percentage=roi
        )
        
        return metrics
    
    def _create_empty_risk_metrics(self) -> Dict[str, Any]:
        """Create empty risk metrics."""
        return {
            "volatility": Decimal('0'),
            "value_at_risk_95": Decimal('0'),
            "expected_shortfall_95": Decimal('0'),
            "maximum_drawdown": Decimal('0'),
            "sharpe_ratio": None,
            "sortino_ratio": None
        }
    
    def _parse_time_period(self, period: str) -> int:
        """Parse time period string to days."""
        period = period.lower()
        if period.endswith('d'):
            return int(period[:-1])
        elif period.endswith('w'):
            return int(period[:-1]) * 7
        elif period.endswith('m'):
            return int(period[:-1]) * 30
        elif period.endswith('y'):
            return int(period[:-1]) * 365
        else:
            return int(period)  # Assume days
    
    def _calculate_period_success_rate(self, period_data: List[Dict[str, Any]]) -> Decimal:
        """Calculate success rate for a specific time period."""
        if not period_data:
            return Decimal('0')
        
        winning_trades = sum(1 for trade in period_data if trade.get('outcome') == 'win')
        return Decimal(winning_trades) / Decimal(len(period_data))
    
    def _determine_trend_direction(self, period_data: List[Dict[str, Any]]) -> str:
        """Determine performance trend direction."""
        if len(period_data) < 4:
            return "insufficient_data"
        
        # Split into early and late periods
        mid_point = len(period_data) // 2
        early_data = period_data[:mid_point]
        late_data = period_data[mid_point:]
        
        early_success = self._calculate_period_success_rate(early_data)
        late_success = self._calculate_period_success_rate(late_data)
        
        difference = late_success - early_success
        
        if difference > Decimal('0.1'):
            return "improving"
        elif difference < Decimal('-0.1'):
            return "declining"
        else:
            return "stable"
    
    def _simplified_significance_test(self, success_rate: float, total_trades: int) -> Dict[str, Any]:
        """Simplified significance test without scipy."""
        # Simple z-test approximation
        p0 = 0.5  # Null hypothesis
        p = success_rate
        n = total_trades
        
        if n == 0:
            return {"is_significant": False, "reason": "No trades"}
        
        # Standard error
        se = math.sqrt(p0 * (1 - p0) / n)
        
        # Z-score
        z = (p - p0) / se if se > 0 else 0
        
        # Two-tailed test at 95% confidence
        z_critical = 1.96
        is_significant = abs(z) > z_critical
        
        # Approximate p-value (simplified)
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
        
        return {
            "is_significant": is_significant,
            "p_value": Decimal(str(p_value)),
            "z_score": Decimal(str(z)),
            "confidence_level": 0.95,
            "method": "simplified_z_test"
        }

# Additional helper functions for integration

def calculate_portfolio_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> Optional[float]:
    """Calculate Sharpe ratio for a portfolio."""
    if not returns or len(returns) < 2:
        return None
    
    mean_return = statistics.mean(returns)
    return_std = statistics.stdev(returns)
    
    if return_std == 0:
        return None
    
    return (mean_return - risk_free_rate) / return_std

def calculate_information_ratio(portfolio_returns: List[float], benchmark_returns: List[float]) -> Optional[float]:
    """Calculate information ratio vs benchmark."""
    if len(portfolio_returns) != len(benchmark_returns) or len(portfolio_returns) < 2:
        return None
    
    active_returns = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
    
    if not active_returns:
        return None
    
    mean_active = statistics.mean(active_returns)
    std_active = statistics.stdev(active_returns) if len(active_returns) > 1 else 0
    
    return mean_active / std_active if std_active > 0 else None

def validate_performance_data_quality(performance_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the quality and completeness of performance data."""
    quality_score = 0.0
    issues = []
    
    # Check sample size
    total_trades = performance_data.get('total_trades', 0)
    if total_trades >= 30:
        quality_score += 0.4
    elif total_trades >= 10:
        quality_score += 0.2
    else:
        issues.append(f"Small sample size: {total_trades} trades")
    
    # Check time span
    if 'avg_hold_duration_days' in performance_data:
        avg_duration = performance_data['avg_hold_duration_days']
        if avg_duration > 0:
            quality_score += 0.2
        else:
            issues.append("No duration data available")
    
    # Check statistical significance
    if performance_data.get('statistical_significance', False):
        quality_score += 0.3
    else:
        issues.append("Results not statistically significant")
    
    # Check data completeness
    required_fields = ['success_rate', 'total_trades', 'roi_percentage']
    missing_fields = [field for field in required_fields if field not in performance_data]
    if not missing_fields:
        quality_score += 0.1
    else:
        issues.append(f"Missing required fields: {missing_fields}")
    
    return {
        "quality_score": min(1.0, quality_score),
        "issues": issues,
        "is_reliable": quality_score >= 0.7,
        "recommendation": "High quality data" if quality_score >= 0.8 else 
                         "Moderate quality data" if quality_score >= 0.5 else 
                         "Low quality data - use with caution"
    }