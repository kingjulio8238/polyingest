from functools import lru_cache
from typing import Annotated
from fastapi import Depends
from app.data.polymarket_client import PolymarketClient
from app.agents.coordinator import AgentCoordinator
import logging

logger = logging.getLogger(__name__)

# Singleton instances for dependency injection
_coordinator_instance = None
_polymarket_client_instance = None

@lru_cache()
def get_agent_coordinator() -> AgentCoordinator:
    """
    Get singleton AgentCoordinator instance for dependency injection.
    
    Returns:
        AgentCoordinator: Singleton coordinator instance
    """
    global _coordinator_instance
    if _coordinator_instance is None:
        try:
            _coordinator_instance = AgentCoordinator()
            logger.info("AgentCoordinator singleton created")
        except Exception as e:
            logger.error(f"Failed to create AgentCoordinator: {e}")
            raise
    return _coordinator_instance

async def get_polymarket_client() -> PolymarketClient:
    """
    Create PolymarketClient instance for dependency injection.
    
    Note: Returns a new instance each time since PolymarketClient
    is designed to be used as an async context manager.
    
    Returns:
        PolymarketClient: New client instance
    """
    return PolymarketClient()

# Type annotations for dependency injection
CoordinatorDep = Annotated[AgentCoordinator, Depends(get_agent_coordinator)]
ClientDep = Annotated[PolymarketClient, Depends(get_polymarket_client)]