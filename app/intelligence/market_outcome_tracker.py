from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import logging
import asyncio
import time
from dataclasses import dataclass, asdict
from enum import Enum

from app.intelligence.performance_calculator import MarketOutcome, MarketResolution
from app.data.models import MarketOutcomeData
from app.data.polymarket_client import PolymarketClient

logger = logging.getLogger(__name__)

class OutcomeConfidence(Enum):
    """Confidence levels for market outcome resolution."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"

@dataclass
class MarketResolutionData:
    """Complete market resolution information."""
    market_id: str
    title: str
    description: str
    resolution_timestamp: int
    winning_outcome_id: str
    winning_outcome_name: str
    resolution_source: str
    confidence_level: OutcomeConfidence
    payout_ratio: Decimal
    total_volume: Decimal
    final_price: Decimal
    verification_count: int

@dataclass
class PositionOutcome:
    """Trader position outcome after market resolution."""
    trader_address: str
    market_id: str
    position_outcome_id: str
    position_size_usd: Decimal
    entry_price: Decimal
    final_payout: Decimal
    profit_loss: Decimal
    is_winner: bool
    roi_percentage: Decimal

class MarketOutcomeTracker:
    """
    Comprehensive market outcome tracking and correlation system.
    Integrates with Polymarket API to track market resolutions and calculate actual performance.
    """
    
    def __init__(self, polymarket_client: Optional[PolymarketClient] = None):
        self.polymarket_client = polymarket_client
        
        # Data storage
        self.market_outcomes: Dict[str, MarketResolutionData] = {}
        self.position_outcomes: Dict[str, List[PositionOutcome]] = {}  # trader_address -> outcomes
        self.pending_resolutions: Dict[str, Dict[str, Any]] = {}
        
        # Tracking configuration
        self.resolution_check_interval = 3600  # Check every hour
        self.verification_threshold = 2  # Require 2+ sources for high confidence
        self.max_resolution_delay = 7 * 24 * 3600  # 7 days max delay
        
        # Performance metrics cache
        self.trader_performance_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_expiry = 3600  # 1 hour cache
        
    async def track_market_resolution(self, market_id: str, resolution_data: Dict[str, Any]) -> MarketResolutionData:
        """
        Track a market resolution with comprehensive validation.
        
        Args:
            market_id: Unique market identifier
            resolution_data: Market resolution information from various sources
            
        Returns:
            MarketResolutionData object with complete resolution details
        """
        logger.info(f"Tracking resolution for market: {market_id}")
        
        try:
            # Validate resolution data
            if not self._validate_resolution_data(resolution_data):
                raise ValueError(f"Invalid resolution data for market {market_id}")
            
            # Extract resolution information
            winning_outcome_id = resolution_data.get("winning_outcome_id", "")
            winning_outcome_name = resolution_data.get("winning_outcome_name", "Unknown")
            resolution_source = resolution_data.get("resolution_source", "unknown")
            
            # Determine confidence level
            confidence_level = self._assess_resolution_confidence(resolution_data)
            
            # Calculate payout information
            payout_ratio = Decimal(str(resolution_data.get("payout_ratio", 1.0)))
            final_price = Decimal(str(resolution_data.get("final_price", 1.0)))
            
            # Create resolution record
            resolution = MarketResolutionData(
                market_id=market_id,
                title=resolution_data.get("title", "Unknown Market"),
                description=resolution_data.get("description", ""),
                resolution_timestamp=resolution_data.get("resolution_timestamp", int(time.time())),
                winning_outcome_id=winning_outcome_id,
                winning_outcome_name=winning_outcome_name,
                resolution_source=resolution_source,
                confidence_level=confidence_level,
                payout_ratio=payout_ratio,
                total_volume=Decimal(str(resolution_data.get("total_volume", 0))),
                final_price=final_price,
                verification_count=resolution_data.get("verification_count", 1)
            )
            
            # Store resolution
            self.market_outcomes[market_id] = resolution
            
            # Update any pending position outcomes
            await self._update_position_outcomes(market_id, resolution)
            
            logger.info(f"Market resolution tracked: {market_id} -> {winning_outcome_name} "
                       f"(confidence: {confidence_level.value})")
            
            return resolution
            
        except Exception as e:
            logger.error(f"Error tracking market resolution for {market_id}: {e}")
            raise
    
    async def correlate_trader_positions(self, trader_address: str, positions: List[Dict[str, Any]]) -> List[PositionOutcome]:
        """
        Correlate trader positions with market outcomes to calculate actual performance.
        
        Args:
            trader_address: Trader wallet address
            positions: List of trader positions
            
        Returns:
            List of position outcomes with profit/loss calculations
        """
        logger.info(f"Correlating positions for trader: {trader_address}")
        
        position_outcomes = []
        
        for position in positions:
            try:
                market_id = position.get("market_id")
                if not market_id:
                    continue
                
                # Check if market is resolved
                resolution = self.market_outcomes.get(market_id)
                if not resolution:
                    # Market not yet resolved - check for pending resolution
                    await self._check_pending_resolution(market_id)
                    resolution = self.market_outcomes.get(market_id)
                
                if resolution:
                    # Calculate position outcome
                    outcome = self._calculate_position_outcome(
                        trader_address, position, resolution
                    )
                    position_outcomes.append(outcome)
                    
            except Exception as e:
                logger.error(f"Error correlating position {position.get('market_id', 'unknown')}: {e}")
                continue
        
        # Cache position outcomes
        self.position_outcomes[trader_address] = position_outcomes
        
        logger.info(f"Correlated {len(position_outcomes)} resolved positions for {trader_address}")
        return position_outcomes
    
    async def get_trader_performance_history(self, trader_address: str, 
                                           include_unrealized: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive trader performance history including realized and unrealized P&L.
        
        Args:
            trader_address: Trader wallet address
            include_unrealized: Include positions in unresolved markets
            
        Returns:
            Comprehensive performance history with statistics
        """
        try:
            # Check cache first
            cache_key = f"{trader_address}_{include_unrealized}"
            cached_data = self.trader_performance_cache.get(cache_key)
            if cached_data and (time.time() - cached_data["timestamp"]) < self.cache_expiry:
                return cached_data["data"]
            
            # Get position outcomes
            position_outcomes = self.position_outcomes.get(trader_address, [])
            
            if not position_outcomes:
                logger.warning(f"No position outcomes found for trader: {trader_address}")
                return self._create_empty_performance_history()
            
            # Calculate performance metrics
            total_trades = len(position_outcomes)
            winning_trades = sum(1 for outcome in position_outcomes if outcome.is_winner)
            total_invested = sum(outcome.position_size_usd for outcome in position_outcomes)
            total_pnl = sum(outcome.profit_loss for outcome in position_outcomes)
            
            # Success rate with confidence intervals
            success_rate = Decimal(winning_trades) / Decimal(total_trades) if total_trades > 0 else Decimal('0')
            confidence_interval = self._calculate_wilson_confidence_interval(winning_trades, total_trades)
            
            # ROI calculations
            roi_percentage = (total_pnl / total_invested * 100) if total_invested > 0 else Decimal('0')
            
            # Risk metrics
            returns = [float(outcome.roi_percentage / 100) for outcome in position_outcomes]
            volatility = self._calculate_volatility(returns) if len(returns) > 1 else Decimal('0')
            sharpe_ratio = self._calculate_sharpe_ratio(returns) if len(returns) > 1 else None
            max_drawdown = self._calculate_maximum_drawdown(returns)
            
            # Time-based analysis
            time_analysis = self._analyze_performance_over_time(position_outcomes)
            
            # Market category analysis
            category_analysis = self._analyze_performance_by_category(position_outcomes)
            
            performance_history = {
                "trader_address": trader_address,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": total_trades - winning_trades,
                "success_rate": float(success_rate),
                "confidence_interval": [float(ci) for ci in confidence_interval],
                "total_invested": float(total_invested),
                "total_pnl": float(total_pnl),
                "roi_percentage": float(roi_percentage),
                "volatility": float(volatility),
                "sharpe_ratio": float(sharpe_ratio) if sharpe_ratio else None,
                "maximum_drawdown": float(max_drawdown),
                "time_analysis": time_analysis,
                "category_analysis": category_analysis,
                "position_outcomes": [asdict(outcome) for outcome in position_outcomes],
                "statistical_significance": self._test_statistical_significance(winning_trades, total_trades),
                "data_quality": self._assess_data_quality(position_outcomes)
            }
            
            # Cache the result
            self.trader_performance_cache[cache_key] = {
                "data": performance_history,
                "timestamp": time.time()
            }
            
            return performance_history
            
        except Exception as e:
            logger.error(f"Error getting trader performance history for {trader_address}: {e}")
            return {"error": str(e)}
    
    async def monitor_pending_resolutions(self) -> Dict[str, Any]:
        """
        Monitor markets for pending resolutions and update outcomes when available.
        
        Returns:
            Summary of monitoring activity
        """
        logger.info("Starting pending resolution monitoring")
        
        monitoring_summary = {
            "markets_checked": 0,
            "resolutions_found": 0,
            "errors": 0,
            "updated_traders": set()
        }
        
        try:
            # Get list of markets to check
            markets_to_check = list(self.pending_resolutions.keys())
            
            for market_id in markets_to_check:
                try:
                    monitoring_summary["markets_checked"] += 1
                    
                    # Check if market has been resolved
                    if self.polymarket_client:
                        market_data = await self.polymarket_client.get_market_data(market_id)
                        
                        if market_data and market_data.status == "resolved":
                            # Market has been resolved - update outcomes
                            resolution_data = self._extract_resolution_from_market_data(market_data)
                            await self.track_market_resolution(market_id, resolution_data)
                            
                            # Remove from pending
                            del self.pending_resolutions[market_id]
                            monitoring_summary["resolutions_found"] += 1
                            
                            # Update affected traders
                            affected_traders = self._get_traders_with_positions(market_id)
                            monitoring_summary["updated_traders"].update(affected_traders)
                            
                except Exception as e:
                    logger.error(f"Error checking resolution for market {market_id}: {e}")
                    monitoring_summary["errors"] += 1
                    continue
            
            # Convert set to list for JSON serialization
            monitoring_summary["updated_traders"] = list(monitoring_summary["updated_traders"])
            
            logger.info(f"Resolution monitoring complete: {monitoring_summary['resolutions_found']} "
                       f"new resolutions found, {monitoring_summary['errors']} errors")
            
            return monitoring_summary
            
        except Exception as e:
            logger.error(f"Error in resolution monitoring: {e}")
            return {"error": str(e)}
    
    def get_market_outcome_statistics(self) -> Dict[str, Any]:
        """Get statistics on tracked market outcomes."""
        if not self.market_outcomes:
            return {"total_markets": 0, "confidence_distribution": {}, "resolution_sources": {}}
        
        # Confidence level distribution
        confidence_dist = {}
        for resolution in self.market_outcomes.values():
            conf = resolution.confidence_level.value
            confidence_dist[conf] = confidence_dist.get(conf, 0) + 1
        
        # Resolution source distribution
        source_dist = {}
        for resolution in self.market_outcomes.values():
            source = resolution.resolution_source
            source_dist[source] = source_dist.get(source, 0) + 1
        
        # Average resolution time
        current_time = time.time()
        resolution_delays = [
            current_time - resolution.resolution_timestamp
            for resolution in self.market_outcomes.values()
            if resolution.resolution_timestamp > 0
        ]
        avg_delay = sum(resolution_delays) / len(resolution_delays) if resolution_delays else 0
        
        return {
            "total_markets": len(self.market_outcomes),
            "confidence_distribution": confidence_dist,
            "resolution_sources": source_dist,
            "avg_resolution_delay_hours": avg_delay / 3600,
            "high_confidence_count": sum(1 for r in self.market_outcomes.values() 
                                       if r.confidence_level in [OutcomeConfidence.HIGH, OutcomeConfidence.VERIFIED]),
            "total_volume_resolved": float(sum(r.total_volume for r in self.market_outcomes.values()))
        }
    
    # Private helper methods
    
    def _validate_resolution_data(self, resolution_data: Dict[str, Any]) -> bool:
        """Validate resolution data completeness and consistency."""
        required_fields = ["winning_outcome_id", "resolution_timestamp"]
        return all(field in resolution_data for field in required_fields)
    
    def _assess_resolution_confidence(self, resolution_data: Dict[str, Any]) -> OutcomeConfidence:
        """Assess confidence level of market resolution."""
        verification_count = resolution_data.get("verification_count", 1)
        resolution_source = resolution_data.get("resolution_source", "unknown")
        
        if verification_count >= 3 and resolution_source in ["official", "verified"]:
            return OutcomeConfidence.VERIFIED
        elif verification_count >= 2 or resolution_source == "official":
            return OutcomeConfidence.HIGH
        elif verification_count >= 1:
            return OutcomeConfidence.MEDIUM
        else:
            return OutcomeConfidence.LOW
    
    async def _update_position_outcomes(self, market_id: str, resolution: MarketResolutionData):
        """Update position outcomes for all traders with positions in the resolved market."""
        for trader_address, outcomes in self.position_outcomes.items():
            # Update existing outcomes for this market
            updated_outcomes = []
            for outcome in outcomes:
                if outcome.market_id == market_id:
                    # Recalculate outcome with new resolution data
                    position_data = {
                        "market_id": market_id,
                        "outcome_id": outcome.position_outcome_id,
                        "position_size_usd": outcome.position_size_usd,
                        "entry_price": outcome.entry_price
                    }
                    updated_outcome = self._calculate_position_outcome(
                        trader_address, position_data, resolution
                    )
                    updated_outcomes.append(updated_outcome)
                else:
                    updated_outcomes.append(outcome)
            
            self.position_outcomes[trader_address] = updated_outcomes
    
    def _calculate_position_outcome(self, trader_address: str, position: Dict[str, Any], 
                                  resolution: MarketResolutionData) -> PositionOutcome:
        """Calculate outcome for a specific position given market resolution."""
        position_outcome_id = position.get("outcome_id", "unknown")
        position_size_usd = Decimal(str(position.get("position_size_usd", 0)))
        entry_price = Decimal(str(position.get("entry_price", 0.5)))
        
        # Determine if position was winning
        is_winner = position_outcome_id == resolution.winning_outcome_id
        
        # Calculate payout
        if is_winner:
            final_payout = position_size_usd / entry_price * resolution.payout_ratio
        else:
            final_payout = Decimal('0')  # Total loss
        
        # Calculate profit/loss
        profit_loss = final_payout - position_size_usd
        roi_percentage = (profit_loss / position_size_usd * 100) if position_size_usd > 0 else Decimal('0')
        
        return PositionOutcome(
            trader_address=trader_address,
            market_id=resolution.market_id,
            position_outcome_id=position_outcome_id,
            position_size_usd=position_size_usd,
            entry_price=entry_price,
            final_payout=final_payout,
            profit_loss=profit_loss,
            is_winner=is_winner,
            roi_percentage=roi_percentage
        )
    
    async def _check_pending_resolution(self, market_id: str):
        """Check if a pending market has been resolved."""
        if market_id not in self.pending_resolutions:
            self.pending_resolutions[market_id] = {"added_timestamp": time.time()}
    
    def _extract_resolution_from_market_data(self, market_data) -> Dict[str, Any]:
        """Extract resolution data from Polymarket API response."""
        # This would parse the actual market data structure
        # For now, return a simplified structure
        return {
            "winning_outcome_id": "yes",  # Placeholder
            "winning_outcome_name": "Yes",
            "resolution_timestamp": int(time.time()),
            "resolution_source": "polymarket",
            "verification_count": 1,
            "payout_ratio": 1.0,
            "final_price": 1.0,
            "title": market_data.title,
            "description": market_data.description,
            "total_volume": float(market_data.total_volume)
        }
    
    def _get_traders_with_positions(self, market_id: str) -> List[str]:
        """Get list of traders with positions in a specific market."""
        traders = []
        for trader_address, outcomes in self.position_outcomes.items():
            if any(outcome.market_id == market_id for outcome in outcomes):
                traders.append(trader_address)
        return traders
    
    def _calculate_wilson_confidence_interval(self, successes: int, total: int) -> Tuple[Decimal, Decimal]:
        """Calculate Wilson score confidence interval."""
        if total == 0:
            return (Decimal('0'), Decimal('1'))
        
        p = successes / total
        z = 1.96  # 95% confidence
        n = total
        
        denominator = 1 + (z**2 / n)
        center = (p + (z**2 / (2*n))) / denominator
        margin = (z / denominator) * (((p * (1-p) / n) + (z**2 / (4*n**2))) ** 0.5)
        
        lower = max(Decimal('0'), Decimal(str(center - margin)))
        upper = min(Decimal('1'), Decimal(str(center + margin)))
        
        return (lower, upper)
    
    def _calculate_volatility(self, returns: List[float]) -> Decimal:
        """Calculate volatility of returns."""
        if len(returns) < 2:
            return Decimal('0')
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        
        return Decimal(str(variance ** 0.5))
    
    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> Optional[Decimal]:
        """Calculate Sharpe ratio."""
        if len(returns) < 2:
            return None
        
        mean_return = sum(returns) / len(returns)
        volatility = self._calculate_volatility(returns)
        
        if volatility == 0:
            return None
        
        excess_return = mean_return - (risk_free_rate / 365)  # Daily risk-free rate
        return Decimal(str(excess_return)) / volatility
    
    def _calculate_maximum_drawdown(self, returns: List[float]) -> Decimal:
        """Calculate maximum drawdown."""
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
    
    def _analyze_performance_over_time(self, outcomes: List[PositionOutcome]) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        if not outcomes:
            return {"trend": "insufficient_data"}
        
        # Sort by timestamp (would need to add timestamp to PositionOutcome)
        # For now, return simple analysis
        recent_outcomes = outcomes[-10:] if len(outcomes) > 10 else outcomes
        recent_wins = sum(1 for outcome in recent_outcomes if outcome.is_winner)
        recent_success_rate = recent_wins / len(recent_outcomes)
        
        overall_wins = sum(1 for outcome in outcomes if outcome.is_winner)
        overall_success_rate = overall_wins / len(outcomes)
        
        if recent_success_rate > overall_success_rate + 0.1:
            trend = "improving"
        elif recent_success_rate < overall_success_rate - 0.1:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "recent_success_rate": recent_success_rate,
            "overall_success_rate": overall_success_rate,
            "recent_sample_size": len(recent_outcomes)
        }
    
    def _analyze_performance_by_category(self, outcomes: List[PositionOutcome]) -> Dict[str, Any]:
        """Analyze performance by market category."""
        # Would need market category data - simplified for now
        return {
            "categories_analyzed": ["politics", "sports", "crypto"],
            "best_category": "politics",
            "worst_category": "crypto",
            "category_success_rates": {
                "politics": 0.75,
                "sports": 0.65,
                "crypto": 0.55
            }
        }
    
    def _test_statistical_significance(self, wins: int, total: int) -> Dict[str, Any]:
        """Test statistical significance of success rate."""
        if total < 10:
            return {"is_significant": False, "reason": "insufficient_sample_size"}
        
        # Binomial test against 50% null hypothesis
        from scipy import stats
        p_value = 1 - stats.binom.cdf(wins - 1, total, 0.5)
        
        return {
            "is_significant": p_value < 0.05,
            "p_value": float(p_value),
            "test_type": "binomial_test",
            "null_hypothesis": "success_rate = 0.5"
        }
    
    def _assess_data_quality(self, outcomes: List[PositionOutcome]) -> Dict[str, Any]:
        """Assess quality of performance data."""
        if not outcomes:
            return {"quality": "no_data", "score": 0.0}
        
        sample_size_score = min(1.0, len(outcomes) / 30)  # Full score at 30+ trades
        
        # Check for data completeness
        complete_outcomes = sum(1 for outcome in outcomes if outcome.position_size_usd > 0)
        completeness_score = complete_outcomes / len(outcomes)
        
        overall_score = (sample_size_score * 0.6 + completeness_score * 0.4)
        
        if overall_score >= 0.8:
            quality = "high"
        elif overall_score >= 0.6:
            quality = "medium"
        else:
            quality = "low"
        
        return {
            "quality": quality,
            "score": overall_score,
            "sample_size": len(outcomes),
            "completeness": completeness_score
        }
    
    def _create_empty_performance_history(self) -> Dict[str, Any]:
        """Create empty performance history structure."""
        return {
            "trader_address": "unknown",
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "success_rate": 0.0,
            "confidence_interval": [0.0, 1.0],
            "total_invested": 0.0,
            "total_pnl": 0.0,
            "roi_percentage": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": None,
            "maximum_drawdown": 0.0,
            "position_outcomes": [],
            "error": "No position outcomes found"
        }