from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Abstract base class for all analysis agents."""
    
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight  # Voting weight based on historical accuracy
        self.confidence = Decimal('0.0')
        self.last_analysis: Optional[Dict[str, Any]] = None
    
    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the provided data and return findings.
        
        Args:
            data: Market and trader data for analysis
            
        Returns:
            Dictionary containing analysis results
        """
        pass
    
    @abstractmethod
    def vote(self, analysis: Dict[str, Any]) -> str:
        """
        Make a voting decision based on analysis.
        
        Args:
            analysis: Results from the analyze method
            
        Returns:
            Vote: "alpha", "no_alpha", or "abstain"
        """
        pass
    
    def get_confidence(self) -> Decimal:
        """Get the confidence level of the last analysis."""
        return self.confidence
    
    def update_weight(self, accuracy: float):
        """Update agent weight based on historical accuracy."""
        self.weight = max(0.1, min(2.0, accuracy))  # Clamp between 0.1 and 2.0
        logger.info(f"Updated {self.name} weight to {self.weight}")