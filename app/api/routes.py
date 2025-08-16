from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any, List
from app.data.polymarket_client import PolymarketClient
from app.data.models import MarketData, AlphaAnalysis, TraderPerformance
from app.agents.coordinator import AgentCoordinator
from app.api.dependencies import CoordinatorDep, ClientDep
import logging
import asyncio
from decimal import Decimal

logger = logging.getLogger(__name__)

router = APIRouter()

# Helper functions for data retrieval and processing

async def _get_trading_activity(client: PolymarketClient, market_id: str) -> Dict[str, Any]:
    """Get trading activity data for a market."""
    try:
        # This would integrate with additional Polymarket API endpoints
        # For now, return mock data structure
        return {
            "total_trades_24h": 0,
            "unique_traders_24h": 0,
            "avg_trade_size": 0,
            "large_trades_24h": 0,
            "recent_large_trades": []
        }
    except Exception as e:
        logger.warning(f"Could not fetch trading activity for {market_id}: {e}")
        return {
            "total_trades_24h": 0,
            "unique_traders_24h": 0,
            "avg_trade_size": 0,
            "large_trades_24h": 0,
            "recent_large_trades": []
        }

async def _get_market_traders(client: PolymarketClient, market_id: str) -> List[Dict[str, Any]]:
    """Get trader data for a specific market."""
    try:
        # This would integrate with blockchain data and Polymarket APIs
        # For now, return mock data structure for development
        return [
            {
                "address": "0xexample123...",
                "total_portfolio_value_usd": 100000,
                "performance_metrics": {
                    "overall_success_rate": 0.75,
                    "markets_resolved": 15,
                    "total_profit_usd": 25000,
                    "roi_percentage": 25.0
                },
                "positions": [
                    {
                        "market_id": market_id,
                        "outcome_id": "yes",
                        "position_size_usd": 10000,
                        "portfolio_allocation_pct": 0.1,
                        "entry_price": 0.45
                    }
                ]
            }
        ]
    except Exception as e:
        logger.warning(f"Could not fetch traders for market {market_id}: {e}")
        return []

async def _get_comprehensive_trader_data(client: PolymarketClient, trader_address: str) -> Optional[Dict[str, Any]]:
    """Get comprehensive trader data from multiple sources."""
    try:
        # This would integrate with blockchain APIs and Polymarket data
        # For now, return mock data structure
        return {
            "address": trader_address,
            "total_portfolio_value_usd": 500000,
            "active_positions": 8,
            "total_markets_traded": 45,
            "performance_metrics": {
                "overall_success_rate": 0.78,
                "total_profit_usd": 125000,
                "roi_percentage": 25.0,
                "avg_position_size_usd": 15000,
                "markets_resolved": 32,
                "confidence_interval": [0.72, 0.84]
            },
            "position_analysis": {
                "avg_portfolio_allocation": 0.087,
                "max_single_position": 0.22,
                "diversification_score": 0.65,
                "concentration_risk": "medium"
            },
            "trading_patterns": {
                "preferred_categories": ["Politics", "Sports", "Crypto"],
                "entry_timing": "early_adopter",
                "hold_duration_avg_days": 18,
                "risk_tolerance": "high"
            }
        }
    except Exception as e:
        logger.error(f"Error fetching trader data for {trader_address}: {e}")
        return None

def _is_valid_address(address: str) -> bool:
    """Validate Ethereum address format."""
    if not address:
        return False
    
    # Basic Ethereum address validation
    if not address.startswith('0x'):
        return False
    
    if len(address) != 42:
        return False
    
    try:
        int(address[2:], 16)
        return True
    except ValueError:
        return False

# API Endpoints

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "polyingest-api"}

@router.get("/metrics")
async def get_metrics(coordinator: CoordinatorDep):
    """Get system performance metrics."""
    try:
        metrics = coordinator.get_performance_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error fetching system metrics"
        )

@router.get("/market/{market_id}/data")
async def get_market_data(
    market_id: str,
    client: ClientDep
) -> Dict[str, Any]:
    """Get comprehensive market data from Polymarket."""
    try:
        async with client:
            # Get basic market data
            market_data = await client.get_market_data(market_id)
            if not market_data:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Market not found: {market_id}"
                )
            
            # Get additional trading activity data
            trading_activity = await _get_trading_activity(client, market_id)
            
            # Format response according to CLAUDE.md specification
            response = {
                "market": {
                    "id": market_data.id,
                    "title": market_data.title,
                    "description": market_data.description,
                    "category": market_data.category,
                    "subcategory": market_data.subcategory,
                    "end_date": market_data.end_date.isoformat() if market_data.end_date else None,
                    "resolution_criteria": market_data.resolution_criteria,
                    "status": market_data.status,
                    "creator": market_data.creator,
                    "total_volume": float(market_data.total_volume),
                    "total_liquidity": float(market_data.total_liquidity)
                },
                "outcomes": [
                    {
                        "id": outcome.id,
                        "name": outcome.name,
                        "current_price": float(outcome.current_price),
                        "volume_24h": float(outcome.volume_24h),
                        "liquidity": float(outcome.liquidity),
                        "order_book": {
                            "bids": [{
                                "price": float(bid.price), 
                                "size": float(bid.size)
                            } for bid in outcome.order_book.bids] if outcome.order_book else [],
                            "asks": [{
                                "price": float(ask.price), 
                                "size": float(ask.size)
                            } for ask in outcome.order_book.asks] if outcome.order_book else []
                        }
                    }
                    for outcome in market_data.outcomes
                ],
                "trading_activity": trading_activity
            }
            
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market data for {market_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while fetching market data"
        )

@router.get("/market/{market_id}/alpha")
async def get_market_alpha(
    market_id: str,
    coordinator: CoordinatorDep,
    client: ClientDep,
    min_portfolio_ratio: float = Query(0.1, ge=0.0, le=1.0, description="Minimum portfolio allocation ratio"),
    min_success_rate: float = Query(0.7, ge=0.0, le=1.0, description="Minimum historical success rate"),
    min_trade_history: int = Query(10, ge=1, description="Minimum number of resolved markets")
) -> Dict[str, Any]:
    """Get comprehensive alpha analysis for a specific market."""
    try:
        async with client:
            # Get market data
            market_data = await client.get_market_data(market_id)
            if not market_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Market not found: {market_id}"
                )
            
            # Convert market data to dict format for coordinator
            market_dict = {
                "id": market_data.id,
                "title": market_data.title,
                "description": market_data.description,
                "category": market_data.category,
                "subcategory": market_data.subcategory,
                "end_date": market_data.end_date,
                "resolution_criteria": market_data.resolution_criteria,
                "status": market_data.status,
                "creator": market_data.creator,
                "total_volume": float(market_data.total_volume),
                "total_liquidity": float(market_data.total_liquidity),
                "outcomes": [
                    {
                        "id": outcome.id,
                        "name": outcome.name,
                        "current_price": float(outcome.current_price),
                        "volume_24h": float(outcome.volume_24h),
                        "liquidity": float(outcome.liquidity)
                    }
                    for outcome in market_data.outcomes
                ],
                "current_prices": {
                    outcome.name: float(outcome.current_price)
                    for outcome in market_data.outcomes
                }
            }
            
            # Get trader data for this market
            traders_data = await _get_market_traders(client, market_id)
            
            # Set up filters
            filters = {
                "min_portfolio_ratio": min_portfolio_ratio,
                "min_success_rate": min_success_rate,
                "min_trade_history": min_trade_history
            }
            
            # Run alpha analysis through coordinator
            analysis_result = await coordinator.analyze_market(
                market_dict, 
                traders_data, 
                filters
            )
            
            return analysis_result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in alpha analysis for market {market_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during alpha analysis: {str(e)}"
        )

@router.get("/trader/{trader_address}/analysis")
async def get_trader_analysis(
    trader_address: str,
    client: ClientDep
) -> Dict[str, Any]:
    """Get comprehensive trader analysis."""
    try:
        # Validate trader address format
        if not _is_valid_address(trader_address):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid trader address format: {trader_address}"
            )
        
        async with client:
            # Get trader data from various sources
            trader_data = await _get_comprehensive_trader_data(client, trader_address)
            
            if not trader_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Trader not found or has no trading history: {trader_address}"
                )
            
            # Format response according to CLAUDE.md specification
            response = {
                "trader": {
                    "address": trader_data["address"],
                    "total_portfolio_value_usd": trader_data["total_portfolio_value_usd"],
                    "active_positions": trader_data["active_positions"],
                    "total_markets_traded": trader_data["total_markets_traded"]
                },
                "performance_metrics": trader_data["performance_metrics"],
                "position_analysis": trader_data["position_analysis"],
                "trading_patterns": trader_data["trading_patterns"]
            }
            
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing trader {trader_address}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during trader analysis"
        )