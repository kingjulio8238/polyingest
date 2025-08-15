from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from app.data.polymarket_client import PolymarketClient
from app.data.models import MarketData, AlphaAnalysis, TraderPerformance
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/market/{market_id}/data", response_model=MarketData)
async def get_market_data(market_id: str):
    """Get comprehensive market data from Polymarket."""
    async with PolymarketClient() as client:
        market_data = await client.get_market_data(market_id)
        if not market_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Market not found: {market_id}"
            )
        return market_data

@router.get("/market/{market_id}/alpha", response_model=AlphaAnalysis)
async def get_market_alpha(
    market_id: str,
    min_portfolio_ratio: Optional[float] = 0.1,
    min_success_rate: Optional[float] = 0.7
):
    """Get alpha analysis for a specific market."""
    # This will be implemented in later phases with agent system
    raise HTTPException(
        status_code=501, 
        detail="Alpha analysis not yet implemented"
    )

@router.get("/trader/{trader_address}/analysis", response_model=TraderPerformance)
async def get_trader_analysis(trader_address: str):
    """Get comprehensive trader analysis."""
    # This will be implemented in later phases with blockchain integration
    raise HTTPException(
        status_code=501, 
        detail="Trader analysis not yet implemented"
    )