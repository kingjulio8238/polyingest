from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from decimal import Decimal

class MarketOutcome(BaseModel):
    id: str
    name: str
    current_price: Decimal = Field(..., ge=0, le=1)
    volume_24h: Decimal = Field(..., ge=0)
    liquidity: Decimal = Field(..., ge=0)

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

class TraderPosition(BaseModel):
    market_id: str
    outcome_id: str
    position_size_usd: Decimal
    entry_price: Decimal
    current_value_usd: Decimal
    portfolio_allocation_pct: Decimal

class TraderPerformance(BaseModel):
    address: str
    total_portfolio_value_usd: Decimal
    active_positions: int
    total_markets_traded: int
    overall_success_rate: Decimal = Field(..., ge=0, le=1)
    total_profit_usd: Decimal
    roi_percentage: Decimal
    positions: List[TraderPosition]

class AgentAnalysis(BaseModel):
    agent_name: str
    vote: str  # "alpha", "no_alpha", "abstain"
    confidence: Decimal = Field(..., ge=0, le=1)
    reasoning: str
    key_findings: List[str]

class AlphaAnalysis(BaseModel):
    market_id: str
    has_alpha: bool
    confidence_score: Decimal = Field(..., ge=0, le=1)
    recommended_side: Optional[str] = None
    strength: str  # "weak", "moderate", "strong"
    agent_analyses: List[AgentAnalysis]
    key_traders: List[TraderPerformance]
    risk_factors: List[str]
    analysis_timestamp: datetime