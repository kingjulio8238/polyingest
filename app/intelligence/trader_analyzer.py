from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import statistics
import math
import logging
from dataclasses import dataclass
from app.data.blockchain_client import BlockchainClient

logger = logging.getLogger(__name__)

@dataclass
class TraderProfile:
    """Comprehensive trader profile with behavioral metrics."""
    address: str
    total_portfolio_value_usd: Decimal
    active_positions: int
    portfolio_diversity: Decimal
    risk_tolerance: str
    conviction_level: str
    success_rate: Decimal
    avg_position_size: Decimal
    position_sizing_consistency: Decimal
    market_timing_score: Decimal
    sector_preferences: List[str]
    confidence_score: Decimal

@dataclass 
class PortfolioMetrics:
    """Portfolio composition and allocation metrics."""
    total_value_usd: Decimal
    position_count: int
    max_single_allocation: Decimal
    avg_allocation_per_position: Decimal
    diversification_score: Decimal
    concentration_risk: str
    sector_allocation: Dict[str, Decimal]
    market_allocation: Dict[str, Decimal]

@dataclass
class TradingPatternAnalysis:
    """Trading behavior pattern analysis results."""
    entry_timing_preference: str  # early, mid, late
    hold_duration_avg_days: float
    position_sizing_style: str  # conservative, moderate, aggressive
    market_selection_pattern: str  # specialist, generalist
    risk_adjustment_behavior: str  # static, dynamic
    conviction_signals: List[str]

@dataclass
class RiskAssessment:
    """Comprehensive risk assessment of trader behavior."""
    overall_risk_score: Decimal  # 0-1, higher = riskier
    portfolio_concentration_risk: Decimal
    position_sizing_risk: Decimal
    market_timing_risk: Decimal
    liquidity_risk: Decimal
    correlation_risk: Decimal
    risk_level: str  # low, moderate, high, extreme

class TraderAnalyzer:
    """Comprehensive trader intelligence and behavioral analysis module."""
    
    def __init__(self, blockchain_client: Optional[BlockchainClient] = None):
        self.blockchain_client = blockchain_client or BlockchainClient()
        
        # Analysis thresholds
        self.min_position_threshold = Decimal('100')  # $100 minimum
        self.high_conviction_threshold = Decimal('0.10')  # 10% of portfolio
        self.significant_position_threshold = Decimal('0.05')  # 5% of portfolio
        self.min_trade_history = 5  # Minimum trades for analysis
        
        # Risk assessment parameters
        self.concentration_threshold = Decimal('0.25')  # 25% concentration = high risk
        self.diversification_threshold = Decimal('0.6')  # Below 60% = poor diversification
        
    async def analyze_trader_behavior(self, address: str, blockchain_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Comprehensive behavioral analysis of a trader.
        
        Args:
            address: Trader wallet address
            blockchain_data: Optional pre-fetched blockchain data
            
        Returns:
            Comprehensive analysis including portfolio metrics, patterns, and risk assessment
        """
        logger.info(f"Starting comprehensive analysis for trader: {address}")
        
        try:
            # Get blockchain data if not provided
            if blockchain_data is None:
                blockchain_data = await self.blockchain_client.get_trader_portfolio(address)
            
            if "error" in blockchain_data:
                logger.error(f"Error in blockchain data for {address}: {blockchain_data['error']}")
                return {"error": blockchain_data["error"], "address": address}
            
            # Extract basic portfolio information
            total_value = Decimal(str(blockchain_data.get("total_portfolio_value_usd", 0)))
            positions = blockchain_data.get("positions", [])
            
            if total_value == 0 or not positions:
                logger.warning(f"Insufficient data for analysis: {address}")
                return self._create_empty_analysis(address, "Insufficient portfolio data")
            
            # Perform comprehensive analysis
            portfolio_metrics = self.calculate_portfolio_metrics(positions, total_value)
            pattern_analysis = await self.assess_trading_patterns(blockchain_data)
            risk_assessment = self.calculate_risk_profile(blockchain_data)
            conviction_signals = self.identify_conviction_signals(positions, total_value)
            
            # Create comprehensive trader profile
            trader_profile = self._build_trader_profile(
                address, blockchain_data, portfolio_metrics, 
                pattern_analysis, risk_assessment
            )
            
            # Calculate overall intelligence score
            intelligence_score = self._calculate_intelligence_score(
                portfolio_metrics, pattern_analysis, risk_assessment, conviction_signals
            )
            
            analysis_result = {
                "address": address,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "trader_profile": trader_profile,
                "portfolio_metrics": portfolio_metrics,
                "trading_patterns": pattern_analysis,
                "risk_assessment": risk_assessment,
                "conviction_signals": conviction_signals,
                "intelligence_score": float(intelligence_score),
                "key_insights": self._generate_key_insights(
                    trader_profile, portfolio_metrics, risk_assessment
                ),
                "confidence_level": self._assess_analysis_confidence(blockchain_data)
            }
            
            logger.info(f"Analysis complete for {address}: Intelligence score {intelligence_score:.2f}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing trader {address}: {e}")
            return {"error": str(e), "address": address}
    
    def calculate_portfolio_metrics(self, positions: List[Dict[str, Any]], total_value: Decimal) -> PortfolioMetrics:
        """Calculate comprehensive portfolio composition metrics."""
        if not positions or total_value == 0:
            return PortfolioMetrics(
                total_value_usd=Decimal('0'),
                position_count=0,
                max_single_allocation=Decimal('0'),
                avg_allocation_per_position=Decimal('0'),
                diversification_score=Decimal('0'),
                concentration_risk="unknown",
                sector_allocation={},
                market_allocation={}
            )
        
        # Calculate position allocations
        position_allocations = []
        market_allocation = {}
        sector_allocation = {}
        
        for position in positions:
            position_value = Decimal(str(position.get("total_position_size_usd", 0)))
            if position_value == 0:
                continue
                
            allocation_ratio = position_value / total_value
            position_allocations.append(allocation_ratio)
            
            # Track market allocation
            market_id = position.get("market_id", "unknown")
            market_allocation[market_id] = market_allocation.get(market_id, Decimal('0')) + allocation_ratio
            
            # Track sector allocation (simplified - would need market categorization)
            sector = self._categorize_market_sector(position)
            sector_allocation[sector] = sector_allocation.get(sector, Decimal('0')) + allocation_ratio
        
        # Calculate metrics
        max_allocation = max(position_allocations) if position_allocations else Decimal('0')
        avg_allocation = sum(position_allocations) / len(position_allocations) if position_allocations else Decimal('0')
        
        # Calculate diversification score using Herfindahl-Hirschman Index
        diversification_score = self._calculate_diversification_score(position_allocations)
        
        # Assess concentration risk
        concentration_risk = self._assess_concentration_risk(max_allocation, diversification_score)
        
        return PortfolioMetrics(
            total_value_usd=total_value,
            position_count=len(positions),
            max_single_allocation=max_allocation,
            avg_allocation_per_position=avg_allocation,
            diversification_score=diversification_score,
            concentration_risk=concentration_risk,
            sector_allocation=sector_allocation,
            market_allocation=market_allocation
        )
    
    async def assess_trading_patterns(self, trader_data: Dict[str, Any]) -> TradingPatternAnalysis:
        """Analyze trader behavioral patterns and preferences."""
        positions = trader_data.get("positions", [])
        
        if not positions:
            return TradingPatternAnalysis(
                entry_timing_preference="unknown",
                hold_duration_avg_days=0.0,
                position_sizing_style="unknown",
                market_selection_pattern="unknown",
                risk_adjustment_behavior="unknown",
                conviction_signals=[]
            )
        
        # Analyze entry timing patterns
        entry_timing = self._analyze_entry_timing(positions)
        
        # Analyze hold duration patterns
        hold_duration = self._analyze_hold_duration(positions)
        
        # Analyze position sizing patterns
        position_sizing_style = self._analyze_position_sizing_style(positions)
        
        # Analyze market selection patterns
        market_selection = self._analyze_market_selection_pattern(positions)
        
        # Analyze risk adjustment behavior
        risk_adjustment = self._analyze_risk_adjustment_behavior(positions)
        
        # Identify conviction signals
        conviction_signals = self._identify_behavioral_conviction_signals(positions, trader_data)
        
        return TradingPatternAnalysis(
            entry_timing_preference=entry_timing,
            hold_duration_avg_days=hold_duration,
            position_sizing_style=position_sizing_style,
            market_selection_pattern=market_selection,
            risk_adjustment_behavior=risk_adjustment,
            conviction_signals=conviction_signals
        )
    
    def calculate_risk_profile(self, trader_data: Dict[str, Any]) -> RiskAssessment:
        """Calculate comprehensive risk assessment for trader."""
        positions = trader_data.get("positions", [])
        total_value = Decimal(str(trader_data.get("total_portfolio_value_usd", 0)))
        
        if not positions or total_value == 0:
            return RiskAssessment(
                overall_risk_score=Decimal('0.5'),
                portfolio_concentration_risk=Decimal('0'),
                position_sizing_risk=Decimal('0'),
                market_timing_risk=Decimal('0'),
                liquidity_risk=Decimal('0'),
                correlation_risk=Decimal('0'),
                risk_level="unknown"
            )
        
        # Calculate individual risk components
        concentration_risk = self._assess_portfolio_concentration_risk(positions, total_value)
        position_sizing_risk = self._assess_position_sizing_risk(positions, total_value)
        market_timing_risk = self._assess_market_timing_risk(positions)
        liquidity_risk = self._assess_liquidity_risk(positions)
        correlation_risk = self._assess_correlation_risk(positions)
        
        # Calculate overall risk score (weighted average)
        risk_weights = {
            'concentration': Decimal('0.3'),
            'position_sizing': Decimal('0.25'),
            'market_timing': Decimal('0.2'),
            'liquidity': Decimal('0.15'),
            'correlation': Decimal('0.1')
        }
        
        overall_risk = (
            concentration_risk * risk_weights['concentration'] +
            position_sizing_risk * risk_weights['position_sizing'] +
            market_timing_risk * risk_weights['market_timing'] +
            liquidity_risk * risk_weights['liquidity'] +
            correlation_risk * risk_weights['correlation']
        )
        
        # Determine risk level
        if overall_risk >= Decimal('0.8'):
            risk_level = "extreme"
        elif overall_risk >= Decimal('0.6'):
            risk_level = "high"
        elif overall_risk >= Decimal('0.4'):
            risk_level = "moderate"
        else:
            risk_level = "low"
        
        return RiskAssessment(
            overall_risk_score=overall_risk,
            portfolio_concentration_risk=concentration_risk,
            position_sizing_risk=position_sizing_risk,
            market_timing_risk=market_timing_risk,
            liquidity_risk=liquidity_risk,
            correlation_risk=correlation_risk,
            risk_level=risk_level
        )
    
    def identify_conviction_signals(self, positions: List[Dict[str, Any]], total_value: Decimal) -> List[Dict[str, Any]]:
        """Identify high-conviction trading signals from position analysis."""
        conviction_signals = []
        
        if not positions or total_value == 0:
            return conviction_signals
        
        for position in positions:
            position_value = Decimal(str(position.get("total_position_size_usd", 0)))
            if position_value == 0:
                continue
            
            allocation_ratio = position_value / total_value
            
            # High allocation signal
            if allocation_ratio >= self.high_conviction_threshold:
                conviction_signals.append({
                    "type": "high_allocation",
                    "market_id": position.get("market_id"),
                    "allocation_percentage": float(allocation_ratio * 100),
                    "position_size_usd": float(position_value),
                    "confidence": "high",
                    "reasoning": f"Allocated {allocation_ratio:.1%} of portfolio to single market"
                })
            
            # Significant position signal
            elif allocation_ratio >= self.significant_position_threshold:
                conviction_signals.append({
                    "type": "significant_position",
                    "market_id": position.get("market_id"),
                    "allocation_percentage": float(allocation_ratio * 100),
                    "position_size_usd": float(position_value),
                    "confidence": "medium",
                    "reasoning": f"Significant {allocation_ratio:.1%} allocation indicates conviction"
                })
            
            # Early entry signal (based on timestamp analysis)
            entry_timestamp = position.get("first_entry_timestamp", 0)
            if entry_timestamp and self._is_early_entry(entry_timestamp):
                conviction_signals.append({
                    "type": "early_entry",
                    "market_id": position.get("market_id"),
                    "entry_timestamp": entry_timestamp,
                    "confidence": "medium",
                    "reasoning": "Early position entry suggests conviction in market outcome"
                })
            
            # Sustained position signal (long holding period)
            if self._is_sustained_position(position):
                conviction_signals.append({
                    "type": "sustained_position",
                    "market_id": position.get("market_id"),
                    "hold_duration_days": self._calculate_hold_duration_days(position),
                    "confidence": "medium",
                    "reasoning": "Long-term position holding indicates sustained conviction"
                })
        
        # Sort by confidence and significance
        conviction_signals.sort(key=lambda x: (
            x.get("confidence") == "high",
            x.get("allocation_percentage", 0)
        ), reverse=True)
        
        return conviction_signals
    
    def _build_trader_profile(self, address: str, blockchain_data: Dict[str, Any], 
                             portfolio_metrics: PortfolioMetrics, 
                             pattern_analysis: TradingPatternAnalysis,
                             risk_assessment: RiskAssessment) -> TraderProfile:
        """Build comprehensive trader profile from analysis components."""
        
        # Calculate overall confidence score
        confidence_score = self._calculate_confidence_score(
            portfolio_metrics, pattern_analysis, risk_assessment
        )
        
        # Determine conviction level
        conviction_level = self._determine_conviction_level(
            portfolio_metrics.max_single_allocation,
            len(pattern_analysis.conviction_signals)
        )
        
        # Calculate success rate (simplified - would need historical trade data)
        success_rate = self._estimate_success_rate(blockchain_data)
        
        return TraderProfile(
            address=address,
            total_portfolio_value_usd=portfolio_metrics.total_value_usd,
            active_positions=portfolio_metrics.position_count,
            portfolio_diversity=portfolio_metrics.diversification_score,
            risk_tolerance=risk_assessment.risk_level,
            conviction_level=conviction_level,
            success_rate=success_rate,
            avg_position_size=portfolio_metrics.avg_allocation_per_position * portfolio_metrics.total_value_usd,
            position_sizing_consistency=self._calculate_position_consistency(blockchain_data.get("positions", [])),
            market_timing_score=Decimal('1.0') - risk_assessment.market_timing_risk,
            sector_preferences=list(portfolio_metrics.sector_allocation.keys())[:3],
            confidence_score=confidence_score
        )
    
    def _calculate_diversification_score(self, allocations: List[Decimal]) -> Decimal:
        """Calculate diversification score using Herfindahl-Hirschman Index."""
        if not allocations:
            return Decimal('0')
        
        # Calculate HHI
        hhi = sum(allocation ** 2 for allocation in allocations)
        
        # Convert to diversification score (1 - normalized HHI)
        n = len(allocations)
        max_hhi = Decimal('1.0')  # All in one position
        min_hhi = Decimal('1.0') / n if n > 0 else Decimal('1.0')  # Perfectly diversified
        
        if max_hhi == min_hhi:
            return Decimal('1.0')
        
        normalized_hhi = (hhi - min_hhi) / (max_hhi - min_hhi)
        diversification_score = Decimal('1.0') - normalized_hhi
        
        return max(Decimal('0'), min(Decimal('1'), diversification_score))
    
    def _assess_concentration_risk(self, max_allocation: Decimal, diversification_score: Decimal) -> str:
        """Assess portfolio concentration risk level."""
        if max_allocation >= Decimal('0.5') or diversification_score < Decimal('0.3'):
            return "high"
        elif max_allocation >= Decimal('0.25') or diversification_score < Decimal('0.6'):
            return "moderate"
        elif max_allocation >= Decimal('0.15') or diversification_score < Decimal('0.8'):
            return "low"
        else:
            return "minimal"
    
    def _categorize_market_sector(self, position: Dict[str, Any]) -> str:
        """Categorize market into sector (simplified implementation)."""
        market_id = position.get("market_id", "").lower()
        
        # Simple heuristic categorization - in production would use market metadata
        if "trump" in market_id or "biden" in market_id or "election" in market_id:
            return "politics"
        elif "btc" in market_id or "eth" in market_id or "crypto" in market_id:
            return "crypto"
        elif "nfl" in market_id or "nba" in market_id or "sports" in market_id:
            return "sports"
        elif "fed" in market_id or "rate" in market_id or "inflation" in market_id:
            return "economics"
        else:
            return "other"
    
    def _analyze_entry_timing(self, positions: List[Dict[str, Any]]) -> str:
        """Analyze trader's entry timing preference."""
        early_entries = 0
        total_entries = 0
        
        for position in positions:
            entry_timestamp = position.get("first_entry_timestamp", 0)
            if entry_timestamp:
                total_entries += 1
                if self._is_early_entry(entry_timestamp):
                    early_entries += 1
        
        if total_entries == 0:
            return "unknown"
        
        early_ratio = early_entries / total_entries
        if early_ratio >= 0.7:
            return "early"
        elif early_ratio >= 0.3:
            return "mixed"
        else:
            return "late"
    
    def _analyze_hold_duration(self, positions: List[Dict[str, Any]]) -> float:
        """Calculate average hold duration in days."""
        durations = []
        
        for position in positions:
            duration = self._calculate_hold_duration_days(position)
            if duration > 0:
                durations.append(duration)
        
        return statistics.mean(durations) if durations else 0.0
    
    def _analyze_position_sizing_style(self, positions: List[Dict[str, Any]]) -> str:
        """Analyze position sizing consistency and style."""
        if not positions:
            return "unknown"
        
        sizes = [
            Decimal(str(pos.get("total_position_size_usd", 0)))
            for pos in positions
            if pos.get("total_position_size_usd", 0) > 0
        ]
        
        if not sizes:
            return "unknown"
        
        # Calculate coefficient of variation
        mean_size = sum(sizes) / len(sizes)
        if mean_size == 0:
            return "unknown"
        
        variance = sum((size - mean_size) ** 2 for size in sizes) / len(sizes)
        std_dev = variance ** Decimal('0.5')
        cv = std_dev / mean_size
        
        if cv <= Decimal('0.3'):
            return "consistent"
        elif cv <= Decimal('0.7'):
            return "moderate"
        else:
            return "variable"
    
    def _analyze_market_selection_pattern(self, positions: List[Dict[str, Any]]) -> str:
        """Analyze market selection patterns."""
        sectors = [self._categorize_market_sector(pos) for pos in positions]
        unique_sectors = set(sectors)
        
        if len(unique_sectors) == 1:
            return "specialist"
        elif len(unique_sectors) <= 2:
            return "focused"
        else:
            return "generalist"
    
    def _analyze_risk_adjustment_behavior(self, positions: List[Dict[str, Any]]) -> str:
        """Analyze how trader adjusts risk over time."""
        # Simplified analysis - would need more sophisticated time series analysis
        if len(positions) < 3:
            return "unknown"
        
        # Analyze position size variance over time
        sizes_over_time = []
        for position in sorted(positions, key=lambda x: x.get("first_entry_timestamp", 0)):
            size = Decimal(str(position.get("total_position_size_usd", 0)))
            if size > 0:
                sizes_over_time.append(size)
        
        if len(sizes_over_time) < 3:
            return "unknown"
        
        # Calculate trend in position sizing
        early_avg = statistics.mean(sizes_over_time[:len(sizes_over_time)//3])
        late_avg = statistics.mean(sizes_over_time[-len(sizes_over_time)//3:])
        
        if abs(late_avg - early_avg) / early_avg > 0.2:
            return "dynamic"
        else:
            return "static"
    
    def _identify_behavioral_conviction_signals(self, positions: List[Dict[str, Any]], 
                                              trader_data: Dict[str, Any]) -> List[str]:
        """Identify behavioral signals of conviction."""
        signals = []
        total_value = Decimal(str(trader_data.get("total_portfolio_value_usd", 0)))
        
        # High concentration signal
        if positions:
            max_position = max(
                Decimal(str(pos.get("total_position_size_usd", 0)))
                for pos in positions
            )
            if total_value > 0 and max_position / total_value > Decimal('0.2'):
                signals.append("high_concentration")
        
        # Large absolute position signal
        large_positions = [
            pos for pos in positions
            if Decimal(str(pos.get("total_position_size_usd", 0))) > Decimal('10000')
        ]
        if large_positions:
            signals.append("large_absolute_positions")
        
        # Sustained holding signal
        sustained_positions = [
            pos for pos in positions
            if self._is_sustained_position(pos)
        ]
        if sustained_positions:
            signals.append("sustained_positions")
        
        return signals
    
    def _assess_portfolio_concentration_risk(self, positions: List[Dict[str, Any]], 
                                           total_value: Decimal) -> Decimal:
        """Assess portfolio concentration risk (0-1)."""
        if not positions or total_value == 0:
            return Decimal('0.5')
        
        allocations = [
            Decimal(str(pos.get("total_position_size_usd", 0))) / total_value
            for pos in positions
            if pos.get("total_position_size_usd", 0) > 0
        ]
        
        max_allocation = max(allocations) if allocations else Decimal('0')
        
        # Risk increases exponentially with concentration
        if max_allocation >= Decimal('0.5'):
            return Decimal('0.9')
        elif max_allocation >= Decimal('0.3'):
            return Decimal('0.7')
        elif max_allocation >= Decimal('0.2'):
            return Decimal('0.5')
        else:
            return Decimal('0.3')
    
    def _assess_position_sizing_risk(self, positions: List[Dict[str, Any]], 
                                   total_value: Decimal) -> Decimal:
        """Assess position sizing risk based on variability."""
        if not positions:
            return Decimal('0.5')
        
        sizes = [
            Decimal(str(pos.get("total_position_size_usd", 0)))
            for pos in positions
            if pos.get("total_position_size_usd", 0) > 0
        ]
        
        if len(sizes) < 2:
            return Decimal('0.3')
        
        # Calculate coefficient of variation
        mean_size = sum(sizes) / len(sizes)
        if mean_size == 0:
            return Decimal('0.5')
        
        variance = sum((size - mean_size) ** 2 for size in sizes) / len(sizes)
        std_dev = variance ** Decimal('0.5')
        cv = std_dev / mean_size
        
        # Higher variability = higher risk
        return min(Decimal('1.0'), cv / 2)
    
    def _assess_market_timing_risk(self, positions: List[Dict[str, Any]]) -> Decimal:
        """Assess market timing risk based on entry patterns."""
        # Simplified - would need more sophisticated market timing analysis
        early_entries = sum(
            1 for pos in positions
            if self._is_early_entry(pos.get("first_entry_timestamp", 0))
        )
        
        total_positions = len(positions)
        if total_positions == 0:
            return Decimal('0.5')
        
        early_ratio = early_entries / total_positions
        
        # Early entry generally considered lower risk in prediction markets
        return Decimal('1.0') - Decimal(str(early_ratio))
    
    def _assess_liquidity_risk(self, positions: List[Dict[str, Any]]) -> Decimal:
        """Assess liquidity risk of positions."""
        # Simplified implementation - would need market liquidity data
        large_positions = sum(
            1 for pos in positions
            if Decimal(str(pos.get("total_position_size_usd", 0))) > Decimal('50000')
        )
        
        total_positions = len(positions)
        if total_positions == 0:
            return Decimal('0.3')
        
        large_position_ratio = large_positions / total_positions
        return Decimal(str(large_position_ratio))
    
    def _assess_correlation_risk(self, positions: List[Dict[str, Any]]) -> Decimal:
        """Assess correlation risk between positions."""
        sectors = [self._categorize_market_sector(pos) for pos in positions]
        unique_sectors = set(sectors)
        
        if len(positions) == 0:
            return Decimal('0.5')
        
        # Higher diversification = lower correlation risk
        sector_diversity = len(unique_sectors) / len(positions)
        return Decimal('1.0') - Decimal(str(sector_diversity))
    
    def _calculate_intelligence_score(self, portfolio_metrics: PortfolioMetrics,
                                    pattern_analysis: TradingPatternAnalysis,
                                    risk_assessment: RiskAssessment,
                                    conviction_signals: List[Dict[str, Any]]) -> Decimal:
        """Calculate overall trader intelligence score."""
        
        # Portfolio sophistication score
        portfolio_score = (
            portfolio_metrics.diversification_score * Decimal('0.3') +
            min(Decimal('1.0'), portfolio_metrics.total_value_usd / Decimal('100000')) * Decimal('0.2')
        )
        
        # Risk management score (inverse of risk)
        risk_score = (Decimal('1.0') - risk_assessment.overall_risk_score) * Decimal('0.3')
        
        # Conviction signal score
        conviction_score = min(Decimal('1.0'), Decimal(str(len(conviction_signals))) / 5) * Decimal('0.2')
        
        return portfolio_score + risk_score + conviction_score
    
    def _generate_key_insights(self, trader_profile: TraderProfile,
                             portfolio_metrics: PortfolioMetrics,
                             risk_assessment: RiskAssessment) -> List[str]:
        """Generate key insights about the trader."""
        insights = []
        
        # Portfolio insights
        if portfolio_metrics.diversification_score >= Decimal('0.8'):
            insights.append("Highly diversified portfolio indicates sophisticated risk management")
        elif portfolio_metrics.diversification_score <= Decimal('0.3'):
            insights.append("Concentrated portfolio suggests conviction-based investing")
        
        # Risk insights
        if risk_assessment.risk_level == "low":
            insights.append("Conservative risk profile with steady position sizing")
        elif risk_assessment.risk_level == "high":
            insights.append("Aggressive risk profile with variable position sizing")
        
        # Conviction insights
        if trader_profile.conviction_level == "high":
            insights.append("Strong conviction signals with significant position allocations")
        
        # Performance insights
        if trader_profile.success_rate >= Decimal('0.7'):
            insights.append("Strong historical performance indicates skilled trader")
        
        return insights[:5]  # Limit to top 5 insights
    
    def _assess_analysis_confidence(self, blockchain_data: Dict[str, Any]) -> Decimal:
        """Assess confidence in the analysis based on data quality."""
        confidence_factors = []
        
        # Portfolio value factor
        total_value = Decimal(str(blockchain_data.get("total_portfolio_value_usd", 0)))
        if total_value >= Decimal('10000'):
            confidence_factors.append(Decimal('0.3'))
        elif total_value >= Decimal('1000'):
            confidence_factors.append(Decimal('0.2'))
        else:
            confidence_factors.append(Decimal('0.1'))
        
        # Position count factor
        position_count = len(blockchain_data.get("positions", []))
        if position_count >= 5:
            confidence_factors.append(Decimal('0.3'))
        elif position_count >= 2:
            confidence_factors.append(Decimal('0.2'))
        else:
            confidence_factors.append(Decimal('0.1'))
        
        # Data completeness factor
        has_timestamps = any(
            pos.get("first_entry_timestamp") for pos in blockchain_data.get("positions", [])
        )
        confidence_factors.append(Decimal('0.2') if has_timestamps else Decimal('0.1'))
        
        return sum(confidence_factors)
    
    def _create_empty_analysis(self, address: str, reason: str) -> Dict[str, Any]:
        """Create empty analysis structure for insufficient data."""
        return {
            "address": address,
            "error": reason,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "trader_profile": None,
            "portfolio_metrics": None,
            "trading_patterns": None,
            "risk_assessment": None,
            "conviction_signals": [],
            "intelligence_score": 0.0,
            "key_insights": [],
            "confidence_level": 0.0
        }
    
    # Helper methods for timing and duration analysis
    def _is_early_entry(self, timestamp: int) -> bool:
        """Determine if entry was early relative to market lifecycle."""
        if timestamp == 0:
            return False
        
        # Simplified - assume entry within first 25% of market lifecycle is "early"
        # In production, would need market creation and end timestamps
        current_time = datetime.utcnow().timestamp()
        time_since_entry = current_time - timestamp
        
        # Consider early if entered more than 30 days ago (simplified heuristic)
        return time_since_entry > (30 * 24 * 60 * 60)
    
    def _is_sustained_position(self, position: Dict[str, Any]) -> bool:
        """Check if position has been held for sustained period."""
        duration_days = self._calculate_hold_duration_days(position)
        return duration_days >= 14  # 2+ weeks considered sustained
    
    def _calculate_hold_duration_days(self, position: Dict[str, Any]) -> float:
        """Calculate position hold duration in days."""
        start_timestamp = position.get("first_entry_timestamp", 0)
        end_timestamp = position.get("last_entry_timestamp", 0)
        
        if start_timestamp == 0:
            return 0.0
        
        if end_timestamp == 0 or end_timestamp <= start_timestamp:
            # Position still active
            current_timestamp = datetime.utcnow().timestamp()
            duration_seconds = current_timestamp - start_timestamp
        else:
            duration_seconds = end_timestamp - start_timestamp
        
        return duration_seconds / (24 * 60 * 60)  # Convert to days
    
    def _determine_conviction_level(self, max_allocation: Decimal, signal_count: int) -> str:
        """Determine overall conviction level."""
        if max_allocation >= Decimal('0.25') or signal_count >= 3:
            return "high"
        elif max_allocation >= Decimal('0.15') or signal_count >= 2:
            return "medium"
        elif max_allocation >= Decimal('0.05') or signal_count >= 1:
            return "low"
        else:
            return "minimal"
    
    def _estimate_success_rate(self, blockchain_data: Dict[str, Any]) -> Decimal:
        """Estimate success rate from available data (simplified)."""
        # In production, would calculate from resolved market outcomes
        # For now, return moderate estimate based on portfolio growth
        total_value = Decimal(str(blockchain_data.get("total_portfolio_value_usd", 0)))
        
        if total_value >= Decimal('100000'):
            return Decimal('0.7')  # Assume successful traders have larger portfolios
        elif total_value >= Decimal('10000'):
            return Decimal('0.6')
        else:
            return Decimal('0.5')  # Neutral estimate
    
    def _calculate_position_consistency(self, positions: List[Dict[str, Any]]) -> Decimal:
        """Calculate position sizing consistency score."""
        if len(positions) < 2:
            return Decimal('1.0')
        
        sizes = [
            Decimal(str(pos.get("total_position_size_usd", 0)))
            for pos in positions
            if pos.get("total_position_size_usd", 0) > 0
        ]
        
        if not sizes:
            return Decimal('0.0')
        
        mean_size = sum(sizes) / len(sizes)
        if mean_size == 0:
            return Decimal('0.0')
        
        # Calculate coefficient of variation and invert for consistency score
        variance = sum((size - mean_size) ** 2 for size in sizes) / len(sizes)
        std_dev = variance ** Decimal('0.5')
        cv = std_dev / mean_size
        
        # Higher consistency = lower coefficient of variation
        return max(Decimal('0'), Decimal('1.0') - cv)
    
    def _calculate_confidence_score(self, portfolio_metrics: PortfolioMetrics,
                                  pattern_analysis: TradingPatternAnalysis,
                                  risk_assessment: RiskAssessment) -> Decimal:
        """Calculate confidence score for trader profile."""
        
        # Base confidence on portfolio size and diversity
        portfolio_confidence = min(Decimal('0.4'), 
                                 portfolio_metrics.total_value_usd / Decimal('250000'))
        
        # Risk management confidence
        risk_confidence = (Decimal('1.0') - risk_assessment.overall_risk_score) * Decimal('0.3')
        
        # Pattern clarity confidence
        pattern_confidence = Decimal('0.3') if len(pattern_analysis.conviction_signals) > 0 else Decimal('0.1')
        
        return portfolio_confidence + risk_confidence + pattern_confidence