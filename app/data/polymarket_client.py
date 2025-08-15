import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from app.config import settings
from app.data.models import MarketData, MarketOutcome
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class PolymarketClient:
    def __init__(self):
        self.graphql_url = settings.polymarket_graphql_url
        self.rest_url = settings.polymarket_rest_url
        self.api_key = settings.polymarket_api_key
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_market_data(self, market_id: str) -> Optional[MarketData]:
        """Retrieve comprehensive market data from Polymarket."""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        # GraphQL query for market data
        query = """
        query GetMarket($id: String!) {
            market(id: $id) {
                id
                question
                description
                category
                endDate
                resolutionSource
                status
                creator
                volume
                liquidity
                outcomes {
                    id
                    title
                    price
                    volume
                    liquidity
                }
            }
        }
        """
        
        variables = {"id": market_id}
        
        try:
            async with self.session.post(
                self.graphql_url,
                json={"query": query, "variables": variables}
            ) as response:
                if response.status != 200:
                    logger.error(f"GraphQL request failed: {response.status}")
                    return None
                
                data = await response.json()
                market_data = data.get("data", {}).get("market")
                
                if not market_data:
                    logger.warning(f"No market data found for ID: {market_id}")
                    return None
                
                return self._parse_market_data(market_data)
        
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return None
    
    def _parse_market_data(self, raw_data: Dict[str, Any]) -> MarketData:
        """Parse raw market data into structured model."""
        outcomes = []
        for outcome_data in raw_data.get("outcomes", []):
            outcome = MarketOutcome(
                id=outcome_data["id"],
                name=outcome_data["title"],
                current_price=Decimal(str(outcome_data["price"])),
                volume_24h=Decimal(str(outcome_data.get("volume", 0))),
                liquidity=Decimal(str(outcome_data.get("liquidity", 0)))
            )
            outcomes.append(outcome)
        
        return MarketData(
            id=raw_data["id"],
            title=raw_data["question"],
            description=raw_data.get("description", ""),
            category=raw_data.get("category"),
            end_date=raw_data["endDate"],
            resolution_criteria=raw_data.get("resolutionSource", ""),
            status=raw_data["status"],
            creator=raw_data["creator"],
            total_volume=Decimal(str(raw_data.get("volume", 0))),
            total_liquidity=Decimal(str(raw_data.get("liquidity", 0))),
            outcomes=outcomes
        )
    
    async def get_market_trades(self, market_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trades for a market."""
        # Implementation for trade history
        # This would use REST API endpoints
        pass