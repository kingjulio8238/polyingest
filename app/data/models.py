from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from decimal import Decimal

class OrderBookEntry(BaseModel):
    price: Decimal = Field(..., ge=0, le=1)
    size: Decimal = Field(..., ge=0)

class OrderBook(BaseModel):
    bids: List[OrderBookEntry] = Field(default_factory=list)
    asks: List[OrderBookEntry] = Field(default_factory=list)

class MarketOutcome(BaseModel):
    id: str
    name: str
    current_price: Decimal = Field(..., ge=0, le=1)
    volume_24h: Decimal = Field(..., ge=0)
    liquidity: Decimal = Field(..., ge=0)
    order_book: Optional[OrderBook] = None

class LargeTrade(BaseModel):
    timestamp: datetime
    trader: str
    side: str
    amount_usd: Decimal = Field(..., ge=0)
    price: Decimal = Field(..., ge=0, le=1)

class TradingActivity(BaseModel):
    total_trades_24h: int = Field(..., ge=0)
    unique_traders_24h: int = Field(..., ge=0)
    avg_trade_size: Decimal = Field(..., ge=0)
    large_trades_24h: int = Field(..., ge=0)
    recent_large_trades: List[LargeTrade] = Field(default_factory=list)

class MarketData(BaseModel):
    id: str
    title: str
    description: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    end_date: datetime
    resolution_criteria: str
    status: str
    creator: str
    total_volume: Decimal = Field(..., ge=0)
    total_liquidity: Decimal = Field(..., ge=0)
    outcomes: List[MarketOutcome]
    trading_activity: Optional[TradingActivity] = None

class TraderPosition(BaseModel):
    market_id: str
    outcome_id: str
    position_size_usd: Decimal = Field(..., ge=0)
    entry_price: Decimal = Field(..., ge=0, le=1)
    current_value_usd: Decimal = Field(..., ge=0)
    portfolio_allocation_pct: Decimal = Field(..., ge=0)

class PerformanceMetrics(BaseModel):
    overall_success_rate: Decimal = Field(..., ge=0, le=1)
    total_profit_usd: Decimal
    roi_percentage: Decimal
    avg_position_size_usd: Decimal = Field(..., ge=0)
    markets_resolved: int = Field(..., ge=0)
    confidence_interval: List[Decimal] = Field(default_factory=list)

class PositionAnalysis(BaseModel):
    avg_portfolio_allocation: Decimal = Field(..., ge=0, le=1)
    max_single_position: Decimal = Field(..., ge=0, le=1)
    diversification_score: Decimal = Field(..., ge=0, le=1)
    concentration_risk: str

class TradingPatterns(BaseModel):
    preferred_categories: List[str] = Field(default_factory=list)
    entry_timing: str
    hold_duration_avg_days: int = Field(..., ge=0)
    risk_tolerance: str

class TraderPerformance(BaseModel):
    address: str
    total_portfolio_value_usd: Decimal
    active_positions: int
    total_markets_traded: int
    performance_metrics: PerformanceMetrics
    position_analysis: PositionAnalysis
    trading_patterns: TradingPatterns
    positions: List[TraderPosition] = Field(default_factory=list)

class AgentAnalysis(BaseModel):
    agent_name: str
    vote: str  # "alpha", "no_alpha", "abstain"
    confidence: Decimal = Field(..., ge=0, le=1)
    reasoning: str
    key_findings: List[str]

class ConfidenceIndicators(BaseModel):
    large_position: bool
    high_allocation: bool
    proven_track_record: bool
    early_entry: bool

# Enhanced models for trader intelligence module

class ConvictionSignal(BaseModel):
    type: str  # "high_allocation", "significant_position", "early_entry", "sustained_position"
    market_id: str
    allocation_percentage: Optional[float] = None
    position_size_usd: Optional[float] = None
    entry_timestamp: Optional[int] = None
    hold_duration_days: Optional[float] = None
    confidence: str  # "low", "medium", "high"
    reasoning: str

class PortfolioMetricsModel(BaseModel):
    total_value_usd: Decimal = Field(..., ge=0)
    position_count: int = Field(..., ge=0)
    max_single_allocation: Decimal = Field(..., ge=0, le=1)
    avg_allocation_per_position: Decimal = Field(..., ge=0, le=1)
    diversification_score: Decimal = Field(..., ge=0, le=1)
    concentration_risk: str  # "minimal", "low", "moderate", "high"
    sector_allocation: Dict[str, Decimal] = Field(default_factory=dict)
    market_allocation: Dict[str, Decimal] = Field(default_factory=dict)

class TradingPatternAnalysisModel(BaseModel):
    entry_timing_preference: str  # "early", "mixed", "late", "unknown"
    hold_duration_avg_days: float = Field(..., ge=0)
    position_sizing_style: str  # "consistent", "moderate", "variable", "unknown"
    market_selection_pattern: str  # "specialist", "focused", "generalist"
    risk_adjustment_behavior: str  # "static", "dynamic", "unknown"
    conviction_signals: List[str] = Field(default_factory=list)

class RiskAssessmentModel(BaseModel):
    overall_risk_score: Decimal = Field(..., ge=0, le=1)
    portfolio_concentration_risk: Decimal = Field(..., ge=0, le=1)
    position_sizing_risk: Decimal = Field(..., ge=0, le=1)
    market_timing_risk: Decimal = Field(..., ge=0, le=1)
    liquidity_risk: Decimal = Field(..., ge=0, le=1)
    correlation_risk: Decimal = Field(..., ge=0, le=1)
    risk_level: str  # "low", "moderate", "high", "extreme", "unknown"

class TraderProfileModel(BaseModel):
    address: str
    total_portfolio_value_usd: Decimal = Field(..., ge=0)
    active_positions: int = Field(..., ge=0)
    portfolio_diversity: Decimal = Field(..., ge=0, le=1)
    risk_tolerance: str  # "low", "moderate", "high", "extreme"
    conviction_level: str  # "minimal", "low", "medium", "high"
    success_rate: Decimal = Field(..., ge=0, le=1)
    avg_position_size: Decimal = Field(..., ge=0)
    position_sizing_consistency: Decimal = Field(..., ge=0, le=1)
    market_timing_score: Decimal = Field(..., ge=0, le=1)
    sector_preferences: List[str] = Field(default_factory=list)
    confidence_score: Decimal = Field(..., ge=0, le=1)

class TraderIntelligenceAnalysis(BaseModel):
    address: str
    analysis_timestamp: str
    trader_profile: Optional[TraderProfileModel] = None
    portfolio_metrics: Optional[PortfolioMetricsModel] = None
    trading_patterns: Optional[TradingPatternAnalysisModel] = None
    risk_assessment: Optional[RiskAssessmentModel] = None
    conviction_signals: List[ConvictionSignal] = Field(default_factory=list)
    intelligence_score: Decimal = Field(..., ge=0, le=1)
    key_insights: List[str] = Field(default_factory=list)
    confidence_level: Decimal = Field(..., ge=0, le=1)
    error: Optional[str] = None

# Enhanced performance metrics with statistical analysis
class StatisticalMetrics(BaseModel):
    success_rate: Decimal = Field(..., ge=0, le=1)
    total_trades: int = Field(..., ge=0)
    winning_trades: int = Field(..., ge=0)
    confidence_interval: List[float] = Field(default_factory=list)
    is_statistically_significant: bool = False
    sample_size_adequate: bool = False

class ROIMetrics(BaseModel):
    roi_percentage: Decimal
    total_invested: Decimal = Field(..., ge=0)
    current_value: Decimal = Field(..., ge=0)
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    total_pnl: Decimal

class BehavioralPatterns(BaseModel):
    avg_position_size: Decimal = Field(..., ge=0)
    position_size_consistency: Decimal = Field(..., ge=0, le=1)
    avg_hold_duration_days: float = Field(..., ge=0)
    preferred_market_types: List[str] = Field(default_factory=list)
    risk_tolerance: str

# Enhanced trader performance model
class EnhancedTraderPerformance(BaseModel):
    address: str
    total_portfolio_value_usd: Decimal = Field(..., ge=0)
    active_positions: int = Field(..., ge=0)
    total_markets_traded: int = Field(..., ge=0)
    statistical_metrics: StatisticalMetrics
    roi_metrics: ROIMetrics
    behavioral_patterns: BehavioralPatterns
    intelligence_analysis: Optional[TraderIntelligenceAnalysis] = None
    positions: List[TraderPosition] = Field(default_factory=list)

class KeyTrader(BaseModel):
    address: str
    position_size_usd: Decimal = Field(..., ge=0)
    portfolio_allocation_pct: Decimal = Field(..., ge=0)
    historical_success_rate: Decimal = Field(..., ge=0, le=1)
    position_side: str
    entry_price: Decimal = Field(..., ge=0, le=1)
    confidence_indicators: ConfidenceIndicators

class AgentConsensus(BaseModel):
    votes_for_alpha: int = Field(..., ge=0)
    votes_against_alpha: int = Field(..., ge=0)
    abstentions: int = Field(..., ge=0)

class AlphaAnalysisResult(BaseModel):
    has_alpha: bool
    confidence_score: Decimal = Field(..., ge=0, le=1)
    recommended_side: Optional[str] = None
    strength: str  # "weak", "moderate", "strong", "none"
    agent_consensus: AgentConsensus

class AnalysisMetadata(BaseModel):
    analysis_timestamp: str
    data_freshness: str
    trader_sample_size: int = Field(..., ge=0)
    min_portfolio_ratio_filter: Decimal = Field(..., ge=0, le=1)
    min_success_rate_filter: Decimal = Field(..., ge=0, le=1)
    consensus_reached: Optional[bool] = None
    voting_duration_seconds: Optional[Decimal] = None
    error: Optional[str] = None

class AlphaAnalysis(BaseModel):
    market: Dict[str, Any]
    alpha_analysis: AlphaAnalysisResult
    key_traders: List[KeyTrader] = Field(default_factory=list)
    agent_analyses: List[AgentAnalysis] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    metadata: AnalysisMetadata