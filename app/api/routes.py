from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any, List
from app.data.polymarket_client import PolymarketClient
from app.data.blockchain_client import BlockchainClient
from app.data.models import (MarketData, AlphaAnalysis, TraderPerformance, 
                             TraderIntelligenceAnalysis, ConvictionSignal,
                             PortfolioMetricsModel, TradingPatternAnalysisModel, 
                             RiskAssessmentModel, TraderProfileModel)
from app.agents.coordinator import AgentCoordinator
from app.api.dependencies import CoordinatorDep, ClientDep
from app.intelligence.trader_analyzer import TraderAnalyzer
import logging
import asyncio
from decimal import Decimal

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency functions

async def get_blockchain_client() -> BlockchainClient:
    """Dependency to get blockchain client instance."""
    return BlockchainClient()

async def get_trader_analyzer() -> TraderAnalyzer:
    """Dependency to get trader analyzer instance."""
    blockchain_client = BlockchainClient()
    return TraderAnalyzer(blockchain_client)

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

async def _get_comprehensive_trader_data(
    client: PolymarketClient, 
    blockchain_client: BlockchainClient, 
    trader_address: str
) -> Optional[Dict[str, Any]]:
    """Get comprehensive trader data from blockchain and Polymarket sources."""
    try:
        logger.info(f"Fetching comprehensive trader data for {trader_address}")
        
        # Get portfolio data from blockchain
        portfolio_data = await blockchain_client.get_trader_portfolio(trader_address)
        
        if "error" in portfolio_data:
            logger.error(f"Blockchain error for {trader_address}: {portfolio_data['error']}")
            return None
        
        # Get transaction history for performance analysis
        transaction_history = await blockchain_client.get_transaction_history(trader_address, limit=500)
        
        # Calculate performance metrics from real data
        performance_metrics = _calculate_performance_metrics(portfolio_data, transaction_history)
        
        # Calculate position analysis
        position_analysis = _calculate_position_analysis(portfolio_data)
        
        # Analyze trading patterns
        trading_patterns = _analyze_trading_patterns(transaction_history, portfolio_data)
        
        return {
            "address": trader_address,
            "total_portfolio_value_usd": portfolio_data.get("total_portfolio_value_usd", 0),
            "active_positions": portfolio_data.get("active_positions", 0),
            "total_markets_traded": len(set(pos.get("market_id") for pos in portfolio_data.get("positions", []))),
            "performance_metrics": performance_metrics,
            "position_analysis": position_analysis,
            "trading_patterns": trading_patterns,
            "blockchain_data": {
                "eth_balance_usd": portfolio_data.get("eth_balance_usd", 0),
                "usdc_balance": portfolio_data.get("usdc_balance", 0),
                "positions_value_usd": portfolio_data.get("positions_value_usd", 0),
                "last_updated": portfolio_data.get("last_updated")
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching trader data for {trader_address}: {e}")
        return None

def _calculate_performance_metrics(portfolio_data: Dict[str, Any], transaction_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate performance metrics from blockchain data."""
    try:
        positions = portfolio_data.get("positions", [])
        total_invested = sum(Decimal(str(pos.get("total_position_size_usd", 0))) for pos in positions)
        total_current_value = sum(Decimal(str(pos.get("current_value_usd", 0))) for pos in positions)
        
        # Calculate ROI
        roi_percentage = 0.0
        if total_invested > 0:
            profit = total_current_value - total_invested
            roi_percentage = float((profit / total_invested) * 100)
        
        # Estimate success rate from position performance (simplified)
        successful_positions = sum(1 for pos in positions if 
                                 Decimal(str(pos.get("current_value_usd", 0))) > 
                                 Decimal(str(pos.get("total_position_size_usd", 0))))
        
        success_rate = 0.0
        if len(positions) > 0:
            success_rate = successful_positions / len(positions)
        
        # Calculate average position size
        avg_position_size = float(total_invested / max(len(positions), 1))
        
        return {
            "overall_success_rate": success_rate,
            "total_profit_usd": float(total_current_value - total_invested),
            "roi_percentage": roi_percentage,
            "avg_position_size_usd": avg_position_size,
            "markets_resolved": len(positions),  # Simplified - would need market resolution data
            "confidence_interval": [max(0.0, success_rate - 0.1), min(1.0, success_rate + 0.1)]
        }
        
    except Exception as e:
        logger.error(f"Error calculating performance metrics: {e}")
        return {
            "overall_success_rate": 0.0,
            "total_profit_usd": 0.0,
            "roi_percentage": 0.0,
            "avg_position_size_usd": 0.0,
            "markets_resolved": 0,
            "confidence_interval": [0.0, 1.0]
        }

def _calculate_position_analysis(portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate position analysis from portfolio data."""
    try:
        positions = portfolio_data.get("positions", [])
        total_portfolio_value = Decimal(str(portfolio_data.get("total_portfolio_value_usd", 0)))
        
        if total_portfolio_value == 0 or not positions:
            return {
                "avg_portfolio_allocation": 0.0,
                "max_single_position": 0.0,
                "diversification_score": 0.0,
                "concentration_risk": "unknown"
            }
        
        # Calculate allocation ratios
        allocations = []
        for pos in positions:
            position_value = Decimal(str(pos.get("total_position_size_usd", 0)))
            allocation_ratio = position_value / total_portfolio_value
            allocations.append(allocation_ratio)
        
        avg_allocation = sum(allocations) / len(allocations) if allocations else Decimal('0')
        max_allocation = max(allocations) if allocations else Decimal('0')
        
        # Calculate diversification score (1 - Herfindahl Index)
        hhi = sum(allocation ** 2 for allocation in allocations)
        max_possible_hhi = Decimal('1.0')
        min_possible_hhi = Decimal('1.0') / len(allocations) if allocations else Decimal('1.0')
        
        diversification_score = 0.0
        if max_possible_hhi != min_possible_hhi:
            normalized_hhi = (hhi - min_possible_hhi) / (max_possible_hhi - min_possible_hhi)
            diversification_score = 1.0 - float(normalized_hhi)
        
        # Determine concentration risk
        concentration_risk = "low"
        if max_allocation >= Decimal('0.5'):
            concentration_risk = "high"
        elif max_allocation >= Decimal('0.25'):
            concentration_risk = "medium"
        
        return {
            "avg_portfolio_allocation": float(avg_allocation),
            "max_single_position": float(max_allocation),
            "diversification_score": max(0.0, min(1.0, diversification_score)),
            "concentration_risk": concentration_risk
        }
        
    except Exception as e:
        logger.error(f"Error calculating position analysis: {e}")
        return {
            "avg_portfolio_allocation": 0.0,
            "max_single_position": 0.0,
            "diversification_score": 0.0,
            "concentration_risk": "unknown"
        }

def _analyze_trading_patterns(transaction_history: List[Dict[str, Any]], portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze trading patterns from transaction history."""
    try:
        if not transaction_history:
            return {
                "preferred_categories": [],
                "entry_timing": "unknown",
                "hold_duration_avg_days": 0,
                "risk_tolerance": "unknown"
            }
        
        # Analyze transaction frequency and timing
        polymarket_txs = [tx for tx in transaction_history if _is_polymarket_tx(tx)]
        
        # Calculate average time between transactions
        if len(polymarket_txs) > 1:
            timestamps = [int(tx.get("timeStamp", 0)) for tx in polymarket_txs]
            timestamps.sort()
            intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            avg_interval_days = sum(intervals) / len(intervals) / (24 * 60 * 60) if intervals else 0
        else:
            avg_interval_days = 0
        
        # Determine entry timing behavior
        entry_timing = "unknown"
        if avg_interval_days < 1:
            entry_timing = "frequent_trader"
        elif avg_interval_days < 7:
            entry_timing = "active_trader"
        elif avg_interval_days < 30:
            entry_timing = "regular_trader"
        else:
            entry_timing = "occasional_trader"
        
        # Analyze position sizes for risk tolerance
        positions = portfolio_data.get("positions", [])
        position_sizes = [Decimal(str(pos.get("total_position_size_usd", 0))) for pos in positions]
        
        risk_tolerance = "unknown"
        if position_sizes:
            avg_size = sum(position_sizes) / len(position_sizes)
            max_size = max(position_sizes)
            
            if max_size > avg_size * Decimal('3'):  # Large variation in position sizes
                risk_tolerance = "high"
            elif max_size > avg_size * Decimal('1.5'):
                risk_tolerance = "moderate"
            else:
                risk_tolerance = "low"
        
        return {
            "preferred_categories": ["Prediction Markets"],  # Would need market categorization data
            "entry_timing": entry_timing,
            "hold_duration_avg_days": int(avg_interval_days),
            "risk_tolerance": risk_tolerance
        }
        
    except Exception as e:
        logger.error(f"Error analyzing trading patterns: {e}")
        return {
            "preferred_categories": [],
            "entry_timing": "unknown",
            "hold_duration_avg_days": 0,
            "risk_tolerance": "unknown"
        }

def _is_polymarket_tx(tx: Dict[str, Any]) -> bool:
    """Check if transaction is related to Polymarket."""
    to_address = tx.get("to", "").lower()
    polymarket_addresses = {
        "0x4d97dcd97ec945f40cf65f87097ace5ea0476045",  # Conditional Tokens
        "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e"   # Exchange
    }
    return to_address in polymarket_addresses

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
    client: ClientDep,
    blockchain_client: BlockchainClient = Depends(get_blockchain_client)
) -> Dict[str, Any]:
    """Get comprehensive trader analysis using blockchain data."""
    try:
        # Validate trader address format
        if not _is_valid_address(trader_address):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid trader address format: {trader_address}"
            )
        
        # Check blockchain connection
        if not blockchain_client.is_connected():
            logger.warning("Blockchain connection not available, using limited analysis")
        
        async with client:
            # Get comprehensive trader data from blockchain and other sources
            trader_data = await _get_comprehensive_trader_data(client, blockchain_client, trader_address)
            
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
                "trading_patterns": trader_data["trading_patterns"],
                "blockchain_data": trader_data.get("blockchain_data", {})
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

@router.get("/trader/{trader_address}/portfolio")
async def get_trader_portfolio(
    trader_address: str,
    blockchain_client: BlockchainClient = Depends(get_blockchain_client)
) -> Dict[str, Any]:
    """Get trader portfolio data directly from blockchain."""
    try:
        # Validate trader address format
        if not _is_valid_address(trader_address):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid trader address format: {trader_address}"
            )
        
        # Get portfolio data from blockchain
        portfolio_data = await blockchain_client.get_trader_portfolio(trader_address)
        
        if "error" in portfolio_data:
            raise HTTPException(
                status_code=400,
                detail=f"Error fetching portfolio data: {portfolio_data['error']}"
            )
        
        return portfolio_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching portfolio for {trader_address}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during portfolio fetch"
        )

@router.get("/trader/{trader_address}/positions")
async def get_trader_positions(
    trader_address: str,
    market_id: Optional[str] = Query(None, description="Filter positions by market ID"),
    blockchain_client: BlockchainClient = Depends(get_blockchain_client)
) -> Dict[str, Any]:
    """Get trader positions from blockchain, optionally filtered by market."""
    try:
        # Validate trader address format
        if not _is_valid_address(trader_address):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid trader address format: {trader_address}"
            )
        
        if market_id:
            # Get positions for specific market
            market_participation = await blockchain_client.verify_market_participation(trader_address, market_id)
            return {
                "trader_address": trader_address,
                "market_id": market_id,
                "participation_data": market_participation
            }
        else:
            # Get all positions
            positions = await blockchain_client.get_polymarket_positions(trader_address)
            return {
                "trader_address": trader_address,
                "positions": positions,
                "total_positions": len(positions)
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching positions for {trader_address}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during position fetch"
        )

@router.get("/trader/{trader_address}/intelligence")
async def get_trader_intelligence(
    trader_address: str,
    trader_analyzer: TraderAnalyzer = Depends(get_trader_analyzer)
) -> TraderIntelligenceAnalysis:
    """Get comprehensive trader intelligence analysis using the advanced analyzer."""
    try:
        # Validate trader address format
        if not _is_valid_address(trader_address):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid trader address format: {trader_address}"
            )
        
        logger.info(f"Starting comprehensive intelligence analysis for {trader_address}")
        
        # Run comprehensive behavioral analysis
        analysis_result = await trader_analyzer.analyze_trader_behavior(trader_address)
        
        if "error" in analysis_result:
            if "Insufficient" in analysis_result["error"]:
                raise HTTPException(
                    status_code=404,
                    detail=f"Trader has insufficient data for analysis: {analysis_result['error']}"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error analyzing trader: {analysis_result['error']}"
                )
        
        # Convert analysis result to Pydantic models
        try:
            # Convert trader profile
            trader_profile = None
            if analysis_result.get("trader_profile"):
                tp = analysis_result["trader_profile"]
                trader_profile = TraderProfileModel(
                    address=tp.address,
                    total_portfolio_value_usd=tp.total_portfolio_value_usd,
                    active_positions=tp.active_positions,
                    portfolio_diversity=tp.portfolio_diversity,
                    risk_tolerance=tp.risk_tolerance,
                    conviction_level=tp.conviction_level,
                    success_rate=tp.success_rate,
                    avg_position_size=tp.avg_position_size,
                    position_sizing_consistency=tp.position_sizing_consistency,
                    market_timing_score=tp.market_timing_score,
                    sector_preferences=tp.sector_preferences,
                    confidence_score=tp.confidence_score
                )
            
            # Convert portfolio metrics
            portfolio_metrics = None
            if analysis_result.get("portfolio_metrics"):
                pm = analysis_result["portfolio_metrics"]
                portfolio_metrics = PortfolioMetricsModel(
                    total_value_usd=pm.total_value_usd,
                    position_count=pm.position_count,
                    max_single_allocation=pm.max_single_allocation,
                    avg_allocation_per_position=pm.avg_allocation_per_position,
                    diversification_score=pm.diversification_score,
                    concentration_risk=pm.concentration_risk,
                    sector_allocation=pm.sector_allocation,
                    market_allocation=pm.market_allocation
                )
            
            # Convert trading patterns
            trading_patterns = None
            if analysis_result.get("trading_patterns"):
                tp = analysis_result["trading_patterns"]
                trading_patterns = TradingPatternAnalysisModel(
                    entry_timing_preference=tp.entry_timing_preference,
                    hold_duration_avg_days=tp.hold_duration_avg_days,
                    position_sizing_style=tp.position_sizing_style,
                    market_selection_pattern=tp.market_selection_pattern,
                    risk_adjustment_behavior=tp.risk_adjustment_behavior,
                    conviction_signals=tp.conviction_signals
                )
            
            # Convert risk assessment
            risk_assessment = None
            if analysis_result.get("risk_assessment"):
                ra = analysis_result["risk_assessment"]
                risk_assessment = RiskAssessmentModel(
                    overall_risk_score=ra.overall_risk_score,
                    portfolio_concentration_risk=ra.portfolio_concentration_risk,
                    position_sizing_risk=ra.position_sizing_risk,
                    market_timing_risk=ra.market_timing_risk,
                    liquidity_risk=ra.liquidity_risk,
                    correlation_risk=ra.correlation_risk,
                    risk_level=ra.risk_level
                )
            
            # Convert conviction signals
            conviction_signals = []
            for signal in analysis_result.get("conviction_signals", []):
                conviction_signal = ConvictionSignal(
                    type=signal["type"],
                    market_id=signal["market_id"],
                    allocation_percentage=signal.get("allocation_percentage"),
                    position_size_usd=signal.get("position_size_usd"),
                    entry_timestamp=signal.get("entry_timestamp"),
                    hold_duration_days=signal.get("hold_duration_days"),
                    confidence=signal["confidence"],
                    reasoning=signal["reasoning"]
                )
                conviction_signals.append(conviction_signal)
            
            # Create comprehensive response
            response = TraderIntelligenceAnalysis(
                address=trader_address,
                analysis_timestamp=analysis_result["analysis_timestamp"],
                trader_profile=trader_profile,
                portfolio_metrics=portfolio_metrics,
                trading_patterns=trading_patterns,
                risk_assessment=risk_assessment,
                conviction_signals=conviction_signals,
                intelligence_score=Decimal(str(analysis_result["intelligence_score"])),
                key_insights=analysis_result["key_insights"],
                confidence_level=Decimal(str(analysis_result["confidence_level"]))
            )
            
            logger.info(f"Intelligence analysis complete for {trader_address}: "
                       f"Score {analysis_result['intelligence_score']:.2f}")
            
            return response
            
        except Exception as conversion_error:
            logger.error(f"Error converting analysis result to Pydantic models: {conversion_error}")
            raise HTTPException(
                status_code=500,
                detail="Error formatting analysis results"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in trader intelligence analysis for {trader_address}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during intelligence analysis"
        )

@router.get("/trader/{trader_address}/conviction-signals")
async def get_trader_conviction_signals(
    trader_address: str,
    market_id: Optional[str] = Query(None, description="Filter signals by market ID"),
    min_confidence: str = Query("medium", description="Minimum confidence level: low, medium, high"),
    trader_analyzer: TraderAnalyzer = Depends(get_trader_analyzer)
) -> Dict[str, Any]:
    """Get trader conviction signals with optional filtering."""
    try:
        # Validate trader address format
        if not _is_valid_address(trader_address):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid trader address format: {trader_address}"
            )
        
        # Get blockchain data
        blockchain_data = await trader_analyzer.blockchain_client.get_trader_portfolio(trader_address)
        
        if "error" in blockchain_data:
            raise HTTPException(
                status_code=400,
                detail=f"Error fetching trader data: {blockchain_data['error']}"
            )
        
        # Get conviction signals
        positions = blockchain_data.get("positions", [])
        total_value = Decimal(str(blockchain_data.get("total_portfolio_value_usd", 0)))
        
        conviction_signals = trader_analyzer.identify_conviction_signals(positions, total_value)
        
        # Apply filters
        filtered_signals = conviction_signals
        
        if market_id:
            filtered_signals = [s for s in filtered_signals if s.get("market_id") == market_id]
        
        if min_confidence != "low":
            confidence_levels = {"medium": ["medium", "high"], "high": ["high"]}
            allowed_levels = confidence_levels.get(min_confidence, ["low", "medium", "high"])
            filtered_signals = [s for s in filtered_signals if s.get("confidence") in allowed_levels]
        
        return {
            "trader_address": trader_address,
            "total_signals": len(conviction_signals),
            "filtered_signals": len(filtered_signals),
            "conviction_signals": filtered_signals,
            "filters_applied": {
                "market_id": market_id,
                "min_confidence": min_confidence
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conviction signals for {trader_address}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during conviction signal analysis"
        )

@router.get("/trader/{trader_address}/risk-profile")
async def get_trader_risk_profile(
    trader_address: str,
    trader_analyzer: TraderAnalyzer = Depends(get_trader_analyzer)
) -> Dict[str, Any]:
    """Get detailed risk assessment for a trader."""
    try:
        # Validate trader address format
        if not _is_valid_address(trader_address):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid trader address format: {trader_address}"
            )
        
        # Get blockchain data
        blockchain_data = await trader_analyzer.blockchain_client.get_trader_portfolio(trader_address)
        
        if "error" in blockchain_data:
            raise HTTPException(
                status_code=400,
                detail=f"Error fetching trader data: {blockchain_data['error']}"
            )
        
        # Calculate comprehensive risk profile
        risk_assessment = trader_analyzer.calculate_risk_profile(blockchain_data)
        
        # Get portfolio metrics for additional context
        positions = blockchain_data.get("positions", [])
        total_value = Decimal(str(blockchain_data.get("total_portfolio_value_usd", 0)))
        portfolio_metrics = trader_analyzer.calculate_portfolio_metrics(positions, total_value)
        
        return {
            "trader_address": trader_address,
            "risk_assessment": {
                "overall_risk_score": float(risk_assessment.overall_risk_score),
                "risk_level": risk_assessment.risk_level,
                "risk_components": {
                    "portfolio_concentration": float(risk_assessment.portfolio_concentration_risk),
                    "position_sizing": float(risk_assessment.position_sizing_risk),
                    "market_timing": float(risk_assessment.market_timing_risk),
                    "liquidity": float(risk_assessment.liquidity_risk),
                    "correlation": float(risk_assessment.correlation_risk)
                }
            },
            "portfolio_context": {
                "total_value_usd": float(portfolio_metrics.total_value_usd),
                "position_count": portfolio_metrics.position_count,
                "diversification_score": float(portfolio_metrics.diversification_score),
                "concentration_risk": portfolio_metrics.concentration_risk,
                "max_single_allocation": float(portfolio_metrics.max_single_allocation)
            },
            "risk_recommendations": _generate_risk_recommendations(risk_assessment, portfolio_metrics)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating risk profile for {trader_address}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during risk assessment"
        )

def _generate_risk_recommendations(risk_assessment: RiskAssessmentModel, 
                                 portfolio_metrics: PortfolioMetricsModel) -> List[str]:
    """Generate risk management recommendations based on assessment."""
    recommendations = []
    
    # Concentration risk recommendations
    if risk_assessment.portfolio_concentration_risk > Decimal('0.7'):
        recommendations.append("Consider diversifying portfolio - high concentration in single positions")
    
    # Position sizing recommendations
    if risk_assessment.position_sizing_risk > Decimal('0.6'):
        recommendations.append("Implement more consistent position sizing strategy")
    
    # Diversification recommendations
    if portfolio_metrics.diversification_score < Decimal('0.4'):
        recommendations.append("Increase portfolio diversification across different markets/sectors")
    
    # Liquidity recommendations
    if risk_assessment.liquidity_risk > Decimal('0.5'):
        recommendations.append("Monitor position sizes relative to market liquidity")
    
    # Overall risk recommendations
    if risk_assessment.overall_risk_score > Decimal('0.8'):
        recommendations.append("Overall risk profile is very high - consider reducing exposure")
    elif risk_assessment.overall_risk_score < Decimal('0.2'):
        recommendations.append("Very conservative approach - may consider selective increased exposure")
    
    return recommendations or ["Risk profile appears well-balanced"]