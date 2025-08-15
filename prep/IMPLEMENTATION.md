# PolyIngest Implementation Guide

This document provides step-by-step implementation instructions for the PolyIngest Alpha Detection Service based on the approved plan in `PLAN.md`.

## Prerequisites

Before starting implementation, ensure you have:
- Python 3.11 or higher installed
- Git for version control
- Access to required API keys:
  - Polymarket API key (if available)
  - Polygon RPC endpoint (Alchemy/Infura recommended)
  - Redis instance (local or cloud)
  - PostgreSQL database (local or cloud)

## Implementation Overview

We'll implement the PolyIngest service in 5 phases, following the plan structure:

1. **Phase 1**: Project Foundation & Data Retrieval
2. **Phase 2**: Multi-Agent System Foundation  
3. **Phase 3**: Blockchain Integration & Portfolio Analysis
4. **Phase 4**: Data Storage & Caching
5. **Phase 5**: Production Deployment & Monitoring

Each phase must be completed and verified before proceeding to the next.

---

## Phase 1: Project Foundation & Data Retrieval

### Step 1.1: Initialize Project Structure

```bash
# Create the main project directories
mkdir -p app/{api,data,agents,intelligence,alpha,storage,monitoring}
mkdir -p app/api/models
mkdir -p scripts
mkdir -p tests/{unit,integration,load}
mkdir -p migrations

# Initialize Python package structure
touch app/__init__.py
touch app/api/__init__.py
touch app/data/__init__.py
touch app/agents/__init__.py
touch app/intelligence/__init__.py
touch app/alpha/__init__.py
touch app/storage/__init__.py
touch app/monitoring/__init__.py
touch app/api/models/__init__.py
```

### Step 1.2: Create Core Dependencies File

Create `requirements.txt`:
```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# HTTP & Async
aiohttp==3.9.1
httpx==0.25.2

# Data Processing
pandas==2.1.4
numpy==1.25.2

# Blockchain
web3==6.13.0

# Storage
redis==5.0.1
asyncpg==0.29.0
sqlalchemy[asyncio]==2.0.23
alembic==1.13.1

# Data Validation
pydantic==2.5.2
pydantic-settings==2.1.0

# Environment
python-dotenv==1.0.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-mock==3.12.0

# Development
mypy==1.7.1
black==23.11.0
isort==5.12.0
```

### Step 1.3: Environment Configuration

Create `.env.example`:
```bash
# Application
APP_NAME=PolyIngest
APP_VERSION=1.0.0
DEBUG=true
LOG_LEVEL=INFO

# Polymarket API
POLYMARKET_API_KEY=your_api_key_here
POLYMARKET_GRAPHQL_URL=https://clob.polymarket.com/graphql
POLYMARKET_REST_URL=https://clob.polymarket.com

# Blockchain Data
POLYGON_RPC_URL=https://polygon-mainnet.infura.io/v3/YOUR_PROJECT_ID
POLYGON_ARCHIVE_URL=https://polygon-mainnet.infura.io/v3/YOUR_PROJECT_ID
ETHERSCAN_API_KEY=your_etherscan_api_key

# Data Storage
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/polyingest

# Agent Configuration
AGENT_VOTE_THRESHOLD=0.6
MIN_PORTFOLIO_RATIO=0.1
MIN_SUCCESS_RATE=0.7
MIN_TRADE_HISTORY=10

# Performance
RATE_LIMIT_PER_MINUTE=100
CACHE_TTL_SECONDS=300
MAX_CONCURRENT_REQUESTS=50
```

### Step 1.4: Application Configuration

Create `app/config.py`:
```python
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # Application
    app_name: str = "PolyIngest"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Polymarket API
    polymarket_api_key: Optional[str] = None
    polymarket_graphql_url: str = "https://clob.polymarket.com/graphql"
    polymarket_rest_url: str = "https://clob.polymarket.com"
    
    # Blockchain
    polygon_rpc_url: str
    polygon_archive_url: Optional[str] = None
    etherscan_api_key: Optional[str] = None
    
    # Storage
    redis_url: str = "redis://localhost:6379/0"
    database_url: str
    
    # Agent Configuration
    agent_vote_threshold: float = 0.6
    min_portfolio_ratio: float = 0.1
    min_success_rate: float = 0.7
    min_trade_history: int = 10
    
    # Performance
    rate_limit_per_minute: int = 100
    cache_ttl_seconds: int = 300
    max_concurrent_requests: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### Step 1.5: Data Models

Create `app/data/models.py`:
```python
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
```

### Step 1.6: Polymarket API Client

Create `app/data/polymarket_client.py`:
```python
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
```

### Step 1.7: FastAPI Application Setup

Create `app/main.py`:
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.config import settings
from app.api.routes import router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Advanced alpha detection service for Polymarket prediction markets",
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.app_name}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
```

### Step 1.8: API Routes Structure

Create `app/api/routes.py`:
```python
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging
from app.data.polymarket_client import PolymarketClient
from app.data.models import MarketData, AlphaAnalysis, TraderPerformance

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_polymarket_client():
    """Dependency to get Polymarket client."""
    async with PolymarketClient() as client:
        yield client

@router.get("/market/{market_id}/data", response_model=MarketData)
async def get_market_data(
    market_id: str,
    client: PolymarketClient = Depends(get_polymarket_client)
):
    """Get comprehensive market data."""
    try:
        market_data = await client.get_market_data(market_id)
        if not market_data:
            raise HTTPException(status_code=404, detail="Market not found")
        return market_data
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/market/{market_id}/alpha", response_model=AlphaAnalysis)
async def analyze_market_alpha(
    market_id: str,
    min_portfolio_ratio: Optional[float] = None,
    min_success_rate: Optional[float] = None,
    client: PolymarketClient = Depends(get_polymarket_client)
):
    """Analyze market for alpha opportunities."""
    # Placeholder implementation - will be completed in Phase 2
    raise HTTPException(status_code=501, detail="Alpha analysis not yet implemented")

@router.get("/trader/{trader_address}/analysis", response_model=TraderPerformance)
async def analyze_trader(trader_address: str):
    """Get comprehensive trader analysis."""
    # Placeholder implementation - will be completed in Phase 3
    raise HTTPException(status_code=501, detail="Trader analysis not yet implemented")
```

### Step 1.9: Basic Tests

Create `tests/test_phase1.py`:
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data

def test_market_data_endpoint_exists():
    """Test that market data endpoint exists (will return 404 for fake ID)."""
    response = client.get("/api/market/fake_market_id/data")
    # Should return 404 or 500, not 404 for route not found
    assert response.status_code in [404, 500]

def test_alpha_analysis_not_implemented():
    """Test that alpha analysis returns not implemented."""
    response = client.get("/api/market/fake_market_id/alpha")
    assert response.status_code == 501

def test_trader_analysis_not_implemented():
    """Test that trader analysis returns not implemented."""
    response = client.get("/api/trader/0x123/analysis")
    assert response.status_code == 501
```

### Step 1.10: Development Setup Script

Create `scripts/setup_dev.py`:
```python
#!/usr/bin/env python3
"""
Development environment setup script.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"📋 {description}")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False
    return True

def main():
    """Set up development environment."""
    print("🚀 Setting up PolyIngest development environment")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required")
        sys.exit(1)
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        sys.exit(1)
    
    # Create .env file if it doesn't exist
    if not Path(".env").exists():
        if Path(".env.example").exists():
            run_command("cp .env.example .env", "Creating .env file from template")
            print("📝 Please edit .env file with your API keys and configuration")
        else:
            print("⚠️  No .env.example found, please create .env manually")
    
    # Run tests
    if not run_command("python -m pytest tests/test_phase1.py -v", "Running Phase 1 tests"):
        print("⚠️  Some tests failed, but this is expected for initial setup")
    
    print("\n🎉 Phase 1 setup complete!")
    print("📝 Next steps:")
    print("   1. Edit .env file with your API keys")
    print("   2. Run: python -m uvicorn app.main:app --reload")
    print("   3. Visit: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
```

### Phase 1 Verification

Run these commands to verify Phase 1 implementation:

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
python scripts/setup_dev.py

# Start the application
python -m uvicorn app.main:app --reload

# Test health check
curl http://localhost:8000/health

# Test API documentation
# Visit: http://localhost:8000/docs

# Run tests
python -m pytest tests/test_phase1.py -v

# Type checking (optional but recommended)
python -m mypy app/ --ignore-missing-imports
```

**Phase 1 Success Criteria Checklist:**
- [ ] Application starts successfully
- [ ] Health check returns 200
- [ ] Dependencies install cleanly
- [ ] FastAPI documentation loads at `/docs`
- [ ] Environment variables load correctly
- [ ] Basic API structure is in place
- [ ] Tests pass

---

## Phase 2: Multi-Agent System Foundation

### Step 2.1: Base Agent Framework

Create `app/agents/base_agent.py`:
```python
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
```

### Step 2.2: Portfolio Analyzer Agent

Create `app/agents/portfolio_agent.py`:
```python
from typing import Dict, Any, List
from decimal import Decimal
from app.agents.base_agent import BaseAgent
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class PortfolioAnalyzerAgent(BaseAgent):
    """Analyzes trader portfolio allocation patterns."""
    
    def __init__(self):
        super().__init__("Portfolio Analyzer", weight=1.2)
        self.min_allocation_threshold = Decimal(str(settings.min_portfolio_ratio))
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio allocation patterns."""
        market_data = data.get("market")
        traders_data = data.get("traders", [])
        
        if not market_data or not traders_data:
            logger.warning("Insufficient data for portfolio analysis")
            self.confidence = Decimal('0.0')
            return {"error": "Insufficient data"}
        
        high_conviction_traders = []
        total_allocation = Decimal('0.0')
        allocation_count = 0
        
        for trader in traders_data:
            positions = trader.get("positions", [])
            portfolio_value = Decimal(str(trader.get("total_portfolio_value_usd", 0)))
            
            if portfolio_value == 0:
                continue
            
            # Find positions in this specific market
            market_positions = [
                pos for pos in positions 
                if pos.get("market_id") == market_data.get("id")
            ]
            
            if not market_positions:
                continue
            
            # Calculate total allocation to this market
            market_allocation = sum(
                Decimal(str(pos.get("position_size_usd", 0))) 
                for pos in market_positions
            )
            
            allocation_ratio = market_allocation / portfolio_value
            total_allocation += allocation_ratio
            allocation_count += 1
            
            # Check if this trader meets high conviction criteria
            if allocation_ratio >= self.min_allocation_threshold:
                high_conviction_traders.append({
                    "address": trader.get("address"),
                    "allocation_ratio": allocation_ratio,
                    "position_size_usd": market_allocation,
                    "portfolio_value_usd": portfolio_value
                })
        
        # Calculate analysis metrics
        avg_allocation = total_allocation / max(allocation_count, 1)
        conviction_ratio = len(high_conviction_traders) / max(len(traders_data), 1)
        
        # Determine confidence based on findings
        if len(high_conviction_traders) >= 3 and avg_allocation > self.min_allocation_threshold:
            self.confidence = Decimal('0.9')
        elif len(high_conviction_traders) >= 2:
            self.confidence = Decimal('0.7')
        elif len(high_conviction_traders) >= 1:
            self.confidence = Decimal('0.5')
        else:
            self.confidence = Decimal('0.2')
        
        analysis_result = {
            "high_conviction_traders": high_conviction_traders,
            "total_traders_analyzed": len(traders_data),
            "high_conviction_count": len(high_conviction_traders),
            "average_allocation": float(avg_allocation),
            "conviction_ratio": conviction_ratio,
            "confidence": float(self.confidence)
        }
        
        self.last_analysis = analysis_result
        return analysis_result
    
    def vote(self, analysis: Dict[str, Any]) -> str:
        """Vote based on portfolio allocation analysis."""
        if "error" in analysis:
            return "abstain"
        
        high_conviction_count = analysis.get("high_conviction_count", 0)
        conviction_ratio = analysis.get("conviction_ratio", 0)
        avg_allocation = analysis.get("average_allocation", 0)
        
        # Strong alpha signal: Multiple high-conviction traders
        if high_conviction_count >= 3 and conviction_ratio > 0.15:
            return "alpha"
        
        # Moderate alpha signal: Some high-conviction activity
        elif high_conviction_count >= 2 and avg_allocation > settings.min_portfolio_ratio:
            return "alpha"
        
        # Weak signal
        elif high_conviction_count >= 1:
            return "alpha" if self.confidence > Decimal('0.6') else "abstain"
        
        return "no_alpha"
    
    def get_reasoning(self) -> str:
        """Get human-readable reasoning for the vote."""
        if not self.last_analysis:
            return "No analysis performed"
        
        count = self.last_analysis.get("high_conviction_count", 0)
        avg_alloc = self.last_analysis.get("average_allocation", 0)
        
        if count >= 3:
            return f"{count} traders with >10% portfolio allocation, avg {avg_alloc:.1%}"
        elif count >= 2:
            return f"{count} traders showing high conviction with avg {avg_alloc:.1%} allocation"
        elif count >= 1:
            return f"{count} trader with significant portfolio allocation"
        else:
            return "No significant portfolio allocation patterns detected"
```

### Step 2.3: Success Rate Agent

Create `app/agents/success_rate_agent.py`:
```python
from typing import Dict, Any, List
from decimal import Decimal
from app.agents.base_agent import BaseAgent
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class SuccessRateAgent(BaseAgent):
    """Analyzes trader historical success rates."""
    
    def __init__(self):
        super().__init__("Success Rate Analyzer", weight=1.3)
        self.min_success_rate = Decimal(str(settings.min_success_rate))
        self.min_trade_history = settings.min_trade_history
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trader historical success rates."""
        traders_data = data.get("traders", [])
        
        if not traders_data:
            logger.warning("No trader data for success rate analysis")
            self.confidence = Decimal('0.0')
            return {"error": "No trader data"}
        
        successful_traders = []
        total_success_rate = Decimal('0.0')
        qualified_traders = 0
        
        for trader in traders_data:
            success_rate = Decimal(str(trader.get("overall_success_rate", 0)))
            markets_traded = trader.get("total_markets_traded", 0)
            markets_resolved = trader.get("markets_resolved", 0)
            
            # Skip traders without sufficient trading history
            if markets_resolved < self.min_trade_history:
                continue
            
            qualified_traders += 1
            total_success_rate += success_rate
            
            # Check if trader meets success criteria
            if success_rate >= self.min_success_rate:
                # Calculate statistical significance (simplified)
                confidence_interval = self._calculate_confidence_interval(
                    success_rate, markets_resolved
                )
                
                successful_traders.append({
                    "address": trader.get("address"),
                    "success_rate": float(success_rate),
                    "markets_resolved": markets_resolved,
                    "total_markets_traded": markets_traded,
                    "confidence_interval": confidence_interval,
                    "is_statistically_significant": self._is_statistically_significant(
                        success_rate, markets_resolved
                    )
                })
        
        # Calculate metrics
        avg_success_rate = total_success_rate / max(qualified_traders, 1)
        success_ratio = len(successful_traders) / max(qualified_traders, 1)
        
        # Determine confidence
        statistically_significant = sum(
            1 for trader in successful_traders 
            if trader["is_statistically_significant"]
        )
        
        if statistically_significant >= 2 and avg_success_rate > self.min_success_rate:
            self.confidence = Decimal('0.85')
        elif statistically_significant >= 1:
            self.confidence = Decimal('0.7')
        elif len(successful_traders) >= 2:
            self.confidence = Decimal('0.6')
        elif len(successful_traders) >= 1:
            self.confidence = Decimal('0.4')
        else:
            self.confidence = Decimal('0.2')
        
        analysis_result = {
            "successful_traders": successful_traders,
            "qualified_traders_count": qualified_traders,
            "successful_traders_count": len(successful_traders),
            "statistically_significant_count": statistically_significant,
            "average_success_rate": float(avg_success_rate),
            "success_ratio": success_ratio,
            "confidence": float(self.confidence)
        }
        
        self.last_analysis = analysis_result
        return analysis_result
    
    def vote(self, analysis: Dict[str, Any]) -> str:
        """Vote based on success rate analysis."""
        if "error" in analysis:
            return "abstain"
        
        successful_count = analysis.get("successful_traders_count", 0)
        significant_count = analysis.get("statistically_significant_count", 0)
        avg_success = analysis.get("average_success_rate", 0)
        
        # Strong signal: Multiple statistically significant successful traders
        if significant_count >= 2:
            return "alpha"
        
        # Moderate signal: One significant trader or multiple successful
        elif significant_count >= 1 or (successful_count >= 2 and avg_success > 0.75):
            return "alpha"
        
        # Weak signal
        elif successful_count >= 1:
            return "alpha" if self.confidence > Decimal('0.6') else "abstain"
        
        return "no_alpha"
    
    def _calculate_confidence_interval(self, success_rate: Decimal, sample_size: int) -> List[float]:
        """Calculate approximate confidence interval for success rate."""
        import math
        
        if sample_size < 5:
            return [0.0, 1.0]  # Wide interval for small samples
        
        # Simplified 95% confidence interval using normal approximation
        p = float(success_rate)
        n = sample_size
        z = 1.96  # 95% confidence
        
        margin = z * math.sqrt((p * (1 - p)) / n)
        lower = max(0.0, p - margin)
        upper = min(1.0, p + margin)
        
        return [lower, upper]
    
    def _is_statistically_significant(self, success_rate: Decimal, sample_size: int) -> bool:
        """Check if success rate is statistically significant."""
        if sample_size < 10:
            return False
        
        # Simple significance test: success rate significantly above 50%
        confidence_interval = self._calculate_confidence_interval(success_rate, sample_size)
        return confidence_interval[0] > 0.5  # Lower bound above 50%
    
    def get_reasoning(self) -> str:
        """Get human-readable reasoning for the vote."""
        if not self.last_analysis:
            return "No analysis performed"
        
        successful = self.last_analysis.get("successful_traders_count", 0)
        significant = self.last_analysis.get("statistically_significant_count", 0)
        avg_rate = self.last_analysis.get("average_success_rate", 0)
        
        if significant >= 2:
            return f"{successful} successful traders, {significant} statistically significant (avg {avg_rate:.1%})"
        elif significant >= 1:
            return f"{successful} successful traders with {significant} statistically significant"
        elif successful >= 1:
            return f"{successful} traders with >{self.min_success_rate:.0%} success rate"
        else:
            return "No traders meeting success rate criteria"
```

### Step 2.4: Voting System

Create `app/agents/voting_system.py`:
```python
from typing import List, Dict, Any
from decimal import Decimal
from app.agents.base_agent import BaseAgent
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class VotingSystem:
    """Coordinates agent voting and builds consensus."""
    
    def __init__(self):
        self.vote_threshold = Decimal(str(settings.agent_vote_threshold))
    
    def collect_votes(self, agents: List[BaseAgent], analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Collect votes from all agents and build consensus."""
        if len(agents) != len(analyses):
            raise ValueError("Number of agents must match number of analyses")
        
        votes = []
        total_weight = Decimal('0.0')
        alpha_weight = Decimal('0.0')
        no_alpha_weight = Decimal('0.0')
        abstain_weight = Decimal('0.0')
        
        agent_results = []
        
        for agent, analysis in zip(agents, analyses):
            vote = agent.vote(analysis)
            confidence = agent.get_confidence()
            weight = Decimal(str(agent.weight))
            
            votes.append(vote)
            total_weight += weight
            
            # Weight votes by agent confidence and historical accuracy
            effective_weight = weight * confidence
            
            if vote == "alpha":
                alpha_weight += effective_weight
            elif vote == "no_alpha":
                no_alpha_weight += effective_weight
            else:  # abstain
                abstain_weight += effective_weight
            
            # Get reasoning from agent if available
            reasoning = getattr(agent, 'get_reasoning', lambda: "No reasoning provided")()
            
            agent_results.append({
                "agent_name": agent.name,
                "vote": vote,
                "confidence": float(confidence),
                "weight": float(weight),
                "effective_weight": float(effective_weight),
                "reasoning": reasoning,
                "key_findings": self._extract_key_findings(analysis)
            })
        
        # Calculate consensus
        if total_weight == 0:
            consensus = "abstain"
            consensus_confidence = Decimal('0.0')
        else:
            alpha_ratio = alpha_weight / total_weight
            no_alpha_ratio = no_alpha_weight / total_weight
            
            if alpha_ratio >= self.vote_threshold:
                consensus = "alpha"
                consensus_confidence = alpha_ratio
            elif no_alpha_ratio >= self.vote_threshold:
                consensus = "no_alpha"
                consensus_confidence = no_alpha_ratio
            else:
                consensus = "abstain"
                consensus_confidence = Decimal('1.0') - max(alpha_ratio, no_alpha_ratio)
        
        # Count raw votes for transparency
        vote_counts = {
            "alpha": votes.count("alpha"),
            "no_alpha": votes.count("no_alpha"),
            "abstain": votes.count("abstain")
        }
        
        return {
            "consensus": consensus,
            "consensus_confidence": float(consensus_confidence),
            "vote_counts": vote_counts,
            "weighted_scores": {
                "alpha": float(alpha_weight / total_weight) if total_weight > 0 else 0,
                "no_alpha": float(no_alpha_weight / total_weight) if total_weight > 0 else 0,
                "abstain": float(abstain_weight / total_weight) if total_weight > 0 else 0
            },
            "agent_results": agent_results,
            "total_agents": len(agents),
            "vote_threshold": float(self.vote_threshold)
        }
    
    def _extract_key_findings(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract key findings from agent analysis."""
        findings = []
        
        # Portfolio findings
        if "high_conviction_count" in analysis:
            count = analysis["high_conviction_count"]
            if count > 0:
                findings.append(f"{count} high-conviction traders identified")
        
        # Success rate findings
        if "statistically_significant_count" in analysis:
            count = analysis["statistically_significant_count"]
            if count > 0:
                findings.append(f"{count} statistically significant successful traders")
        
        # General confidence
        if "confidence" in analysis:
            conf = analysis["confidence"]
            if conf > 0.8:
                findings.append("High confidence analysis")
            elif conf > 0.6:
                findings.append("Moderate confidence analysis")
        
        return findings or ["Analysis completed"]
```

### Step 2.5: Agent Coordinator

Create `app/agents/agent_coordinator.py`:
```python
from typing import List, Dict, Any, Optional
from app.agents.base_agent import BaseAgent
from app.agents.portfolio_agent import PortfolioAnalyzerAgent
from app.agents.success_rate_agent import SuccessRateAgent
from app.agents.voting_system import VotingSystem
from app.data.models import AlphaAnalysis, AgentAnalysis
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class AgentCoordinator:
    """Coordinates multiple analysis agents for alpha detection."""
    
    def __init__(self):
        self.agents: List[BaseAgent] = [
            PortfolioAnalyzerAgent(),
            SuccessRateAgent()
        ]
        self.voting_system = VotingSystem()
    
    async def analyze_market_alpha(self, market_data: Dict[str, Any], trader_data: List[Dict[str, Any]]) -> AlphaAnalysis:
        """Coordinate agents to analyze market for alpha opportunities."""
        logger.info(f"Starting alpha analysis for market {market_data.get('id')}")
        
        # Prepare data for agents
        analysis_data = {
            "market": market_data,
            "traders": trader_data
        }
        
        # Run all agent analyses
        agent_analyses = []
        for agent in self.agents:
            try:
                logger.info(f"Running analysis with {agent.name}")
                analysis = await agent.analyze(analysis_data)
                agent_analyses.append(analysis)
            except Exception as e:
                logger.error(f"Error in {agent.name}: {e}")
                agent_analyses.append({"error": str(e)})
        
        # Collect votes and build consensus
        voting_results = self.voting_system.collect_votes(self.agents, agent_analyses)
        
        # Build final alpha analysis
        has_alpha = voting_results["consensus"] == "alpha"
        confidence_score = Decimal(str(voting_results["consensus_confidence"]))
        
        # Determine strength based on confidence and vote distribution
        if confidence_score >= Decimal('0.8'):
            strength = "strong"
        elif confidence_score >= Decimal('0.6'):
            strength = "moderate"
        else:
            strength = "weak"
        
        # Convert agent results to response models
        agent_analysis_models = []
        for result in voting_results["agent_results"]:
            agent_analysis = AgentAnalysis(
                agent_name=result["agent_name"],
                vote=result["vote"],
                confidence=Decimal(str(result["confidence"])),
                reasoning=result["reasoning"],
                key_findings=result["key_findings"]
            )
            agent_analysis_models.append(agent_analysis)
        
        # Extract key traders from portfolio analysis
        key_traders = self._extract_key_traders(agent_analyses, trader_data)
        
        # Generate risk factors
        risk_factors = self._generate_risk_factors(market_data, voting_results)
        
        return AlphaAnalysis(
            market_id=market_data.get("id", "unknown"),
            has_alpha=has_alpha,
            confidence_score=confidence_score,
            recommended_side=self._determine_recommended_side(agent_analyses) if has_alpha else None,
            strength=strength,
            agent_analyses=agent_analysis_models,
            key_traders=[],  # Will be populated in Phase 3 with full trader models
            risk_factors=risk_factors,
            analysis_timestamp=datetime.utcnow()
        )
    
    def _extract_key_traders(self, agent_analyses: List[Dict[str, Any]], trader_data: List[Dict[str, Any]]) -> List[str]:
        """Extract addresses of key traders from agent analyses."""
        key_trader_addresses = set()
        
        for analysis in agent_analyses:
            # From portfolio analysis
            if "high_conviction_traders" in analysis:
                for trader in analysis["high_conviction_traders"]:
                    key_trader_addresses.add(trader.get("address"))
            
            # From success rate analysis
            if "successful_traders" in analysis:
                for trader in analysis["successful_traders"]:
                    if trader.get("is_statistically_significant", False):
                        key_trader_addresses.add(trader.get("address"))
        
        return list(key_trader_addresses)
    
    def _determine_recommended_side(self, agent_analyses: List[Dict[str, Any]]) -> Optional[str]:
        """Determine which outcome side to recommend based on trader positions."""
        # This is a simplified implementation
        # In a real system, you'd analyze actual trader positions
        return "Yes"  # Placeholder - will be enhanced in Phase 3
    
    def _generate_risk_factors(self, market_data: Dict[str, Any], voting_results: Dict[str, Any]) -> List[str]:
        """Generate relevant risk factors for the market."""
        risk_factors = []
        
        # Market-specific risks
        category = market_data.get("category", "").lower()
        if "politics" in category:
            risk_factors.append("Market highly politicized - emotion may override analysis")
        
        # Time-based risks
        end_date = market_data.get("end_date")
        if end_date:
            # Add time-to-resolution risk assessment
            risk_factors.append("Time to resolution creates event risk")
        
        # Consensus-based risks
        consensus_confidence = voting_results.get("consensus_confidence", 0)
        if consensus_confidence < 0.7:
            risk_factors.append("Agent consensus is not strong - higher uncertainty")
        
        # Liquidity risks
        liquidity = market_data.get("total_liquidity", 0)
        if liquidity < 100000:  # Less than $100k
            risk_factors.append("Low liquidity may impact position entry/exit")
        
        return risk_factors or ["Standard market risks apply"]
```

### Step 2.6: Update API Routes for Alpha Analysis

Update `app/api/routes.py`:
```python
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging
from app.data.polymarket_client import PolymarketClient
from app.data.models import MarketData, AlphaAnalysis, TraderPerformance
from app.agents.agent_coordinator import AgentCoordinator

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_polymarket_client():
    """Dependency to get Polymarket client."""
    async with PolymarketClient() as client:
        yield client

async def get_agent_coordinator():
    """Dependency to get agent coordinator."""
    return AgentCoordinator()

@router.get("/market/{market_id}/data", response_model=MarketData)
async def get_market_data(
    market_id: str,
    client: PolymarketClient = Depends(get_polymarket_client)
):
    """Get comprehensive market data."""
    try:
        market_data = await client.get_market_data(market_id)
        if not market_data:
            raise HTTPException(status_code=404, detail="Market not found")
        return market_data
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/market/{market_id}/alpha", response_model=AlphaAnalysis)
async def analyze_market_alpha(
    market_id: str,
    min_portfolio_ratio: Optional[float] = None,
    min_success_rate: Optional[float] = None,
    client: PolymarketClient = Depends(get_polymarket_client),
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    """Analyze market for alpha opportunities."""
    try:
        # Get market data
        market_data = await client.get_market_data(market_id)
        if not market_data:
            raise HTTPException(status_code=404, detail="Market not found")
        
        # For Phase 2, use mock trader data
        # This will be replaced with real blockchain data in Phase 3
        mock_trader_data = [
            {
                "address": "0x123...abc",
                "total_portfolio_value_usd": 500000,
                "overall_success_rate": 0.75,
                "total_markets_traded": 25,
                "markets_resolved": 20,
                "positions": [
                    {
                        "market_id": market_id,
                        "position_size_usd": 50000,
                        "entry_price": 0.45
                    }
                ]
            },
            {
                "address": "0x456...def",
                "total_portfolio_value_usd": 200000,
                "overall_success_rate": 0.80,
                "total_markets_traded": 15,
                "markets_resolved": 12,
                "positions": [
                    {
                        "market_id": market_id,
                        "position_size_usd": 30000,
                        "entry_price": 0.42
                    }
                ]
            }
        ]
        
        # Run alpha analysis
        alpha_analysis = await coordinator.analyze_market_alpha(
            market_data.dict(), 
            mock_trader_data
        )
        
        return alpha_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing market alpha: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trader/{trader_address}/analysis", response_model=TraderPerformance)
async def analyze_trader(trader_address: str):
    """Get comprehensive trader analysis."""
    # Still not implemented - will be completed in Phase 3
    raise HTTPException(status_code=501, detail="Trader analysis not yet implemented")
```

### Step 2.7: Phase 2 Tests

Create `tests/test_phase2.py`:
```python
import pytest
from app.agents.portfolio_agent import PortfolioAnalyzerAgent
from app.agents.success_rate_agent import SuccessRateAgent
from app.agents.voting_system import VotingSystem
from app.agents.agent_coordinator import AgentCoordinator

@pytest.mark.asyncio
async def test_portfolio_agent():
    """Test portfolio analyzer agent."""
    agent = PortfolioAnalyzerAgent()
    
    test_data = {
        "market": {"id": "test_market"},
        "traders": [
            {
                "address": "0x123",
                "total_portfolio_value_usd": 100000,
                "positions": [
                    {
                        "market_id": "test_market",
                        "position_size_usd": 15000
                    }
                ]
            }
        ]
    }
    
    analysis = await agent.analyze(test_data)
    assert "high_conviction_traders" in analysis
    assert analysis["total_traders_analyzed"] == 1
    
    vote = agent.vote(analysis)
    assert vote in ["alpha", "no_alpha", "abstain"]

@pytest.mark.asyncio
async def test_success_rate_agent():
    """Test success rate analyzer agent."""
    agent = SuccessRateAgent()
    
    test_data = {
        "traders": [
            {
                "address": "0x123",
                "overall_success_rate": 0.75,
                "total_markets_traded": 20,
                "markets_resolved": 15
            }
        ]
    }
    
    analysis = await agent.analyze(test_data)
    assert "successful_traders" in analysis
    
    vote = agent.vote(analysis)
    assert vote in ["alpha", "no_alpha", "abstain"]

def test_voting_system():
    """Test voting system consensus."""
    voting_system = VotingSystem()
    
    # Create mock agents
    agents = [PortfolioAnalyzerAgent(), SuccessRateAgent()]
    analyses = [
        {"confidence": 0.8, "high_conviction_count": 2},
        {"confidence": 0.7, "successful_traders_count": 1}
    ]
    
    # Mock the vote method
    agents[0].vote = lambda x: "alpha"
    agents[1].vote = lambda x: "alpha"
    agents[0].confidence = 0.8
    agents[1].confidence = 0.7
    
    results = voting_system.collect_votes(agents, analyses)
    
    assert "consensus" in results
    assert "vote_counts" in results
    assert "agent_results" in results
    assert len(results["agent_results"]) == 2

@pytest.mark.asyncio
async def test_agent_coordinator():
    """Test agent coordinator integration."""
    coordinator = AgentCoordinator()
    
    market_data = {
        "id": "test_market",
        "title": "Test Market",
        "category": "test"
    }
    
    trader_data = [
        {
            "address": "0x123",
            "total_portfolio_value_usd": 100000,
            "overall_success_rate": 0.75,
            "markets_resolved": 15,
            "positions": [{"market_id": "test_market", "position_size_usd": 15000}]
        }
    ]
    
    result = await coordinator.analyze_market_alpha(market_data, trader_data)
    
    assert result.market_id == "test_market"
    assert isinstance(result.has_alpha, bool)
    assert 0 <= result.confidence_score <= 1
    assert result.strength in ["weak", "moderate", "strong"]
    assert len(result.agent_analyses) > 0
```

### Phase 2 Verification

Run these commands to verify Phase 2 implementation:

```bash
# Run Phase 2 tests
python -m pytest tests/test_phase2.py -v

# Test alpha analysis endpoint with mock data
curl "http://localhost:8000/api/market/test_market_id/alpha"

# Check API documentation for new endpoints
# Visit: http://localhost:8000/docs

# Type checking
python -m mypy app/agents/ --ignore-missing-imports
```

**Phase 2 Success Criteria Checklist:**
- [ ] Agent framework instantiates correctly
- [ ] Portfolio agent analyzes test data
- [ ] Success rate agent processes trader data  
- [ ] Voting system reaches consensus
- [ ] Alpha analysis endpoint returns structured response
- [ ] Agent confidence scores are reasonable (0.0-1.0)
- [ ] Error handling works for invalid inputs

---

## Phase 3: Blockchain Integration & Portfolio Analysis

### Step 3.1: Blockchain Client Implementation

Create `app/data/blockchain_client.py`:
```python
from web3 import Web3
from typing import Dict, List, Any, Optional
from decimal import Decimal
import aiohttp
import asyncio
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class BlockchainClient:
    """Client for interacting with Polygon blockchain."""
    
    def __init__(self):
        self.rpc_url = settings.polygon_rpc_url
        self.archive_url = settings.polygon_archive_url or self.rpc_url
        self.etherscan_api_key = settings.etherscan_api_key
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Polymarket contract addresses (mainnet)
        self.conditional_tokens_address = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
        self.exchange_address = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"
    
    async def get_trader_portfolio(self, address: str) -> Dict[str, Any]:
        """Get comprehensive trader portfolio from blockchain."""
        if not self.w3.is_address(address):
            raise ValueError(f"Invalid Ethereum address: {address}")
        
        try:
            # Get ETH balance
            eth_balance = await self._get_eth_balance(address)
            
            # Get USDC balance (primary trading token on Polymarket)
            usdc_balance = await self._get_usdc_balance(address)
            
            # Get Polymarket positions
            positions = await self._get_polymarket_positions(address)
            
            # Calculate total portfolio value
            total_value = eth_balance + usdc_balance + sum(
                pos.get("current_value_usd", 0) for pos in positions
            )
            
            return {
                "address": address,
                "eth_balance": float(eth_balance),
                "usdc_balance": float(usdc_balance),
                "total_portfolio_value_usd": float(total_value),
                "active_positions": len(positions),
                "positions": positions
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio for {address}: {e}")
            return {
                "address": address,
                "error": str(e),
                "total_portfolio_value_usd": 0,
                "active_positions": 0,
                "positions": []
            }
    
    async def _get_eth_balance(self, address: str) -> Decimal:
        """Get ETH balance in USD."""
        try:
            balance_wei = self.w3.eth.get_balance(address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            
            # Get ETH price (simplified - in production use a price oracle)
            eth_price_usd = await self._get_eth_price()
            return Decimal(str(balance_eth)) * Decimal(str(eth_price_usd))
            
        except Exception as e:
            logger.error(f"Error getting ETH balance: {e}")
            return Decimal('0')
    
    async def _get_usdc_balance(self, address: str) -> Decimal:
        """Get USDC balance."""
        try:
            # USDC contract address on Polygon
            usdc_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
            
            # ERC20 ABI for balanceOf
            erc20_abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function"
                }
            ]
            
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(usdc_address),
                abi=erc20_abi
            )
            
            balance = contract.functions.balanceOf(address).call()
            decimals = contract.functions.decimals().call()
            
            # Convert to decimal format
            return Decimal(balance) / Decimal(10 ** decimals)
            
        except Exception as e:
            logger.error(f"Error getting USDC balance: {e}")
            return Decimal('0')
    
    async def _get_polymarket_positions(self, address: str) -> List[Dict[str, Any]]:
        """Get Polymarket positions using transaction history."""
        positions = []
        
        try:
            # Get transaction history from Polygonscan API
            transactions = await self._get_transaction_history(address)
            
            # Parse transactions to identify Polymarket trades
            for tx in transactions:
                if self._is_polymarket_transaction(tx):
                    position = await self._parse_polymarket_transaction(tx)
                    if position:
                        positions.append(position)
            
            # Aggregate positions by market
            aggregated_positions = self._aggregate_positions(positions)
            
            return aggregated_positions
            
        except Exception as e:
            logger.error(f"Error getting Polymarket positions: {e}")
            return []
    
    async def _get_transaction_history(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transaction history from Polygonscan API."""
        if not self.etherscan_api_key:
            logger.warning("No Etherscan API key configured")
            return []
        
        url = "https://api.polygonscan.com/api"
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": limit,
            "sort": "desc",
            "apikey": self.etherscan_api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("result", [])
                    else:
                        logger.error(f"Polygonscan API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching transaction history: {e}")
            return []
    
    def _is_polymarket_transaction(self, tx: Dict[str, Any]) -> bool:
        """Check if transaction is related to Polymarket."""
        to_address = tx.get("to", "").lower()
        return (
            to_address == self.exchange_address.lower() or
            to_address == self.conditional_tokens_address.lower()
        )
    
    async def _parse_polymarket_transaction(self, tx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a Polymarket transaction to extract position information."""
        # This is a simplified implementation
        # In production, you'd decode the transaction input data
        try:
            value_eth = Decimal(tx.get("value", "0")) / Decimal(10**18)
            gas_used = int(tx.get("gasUsed", "0"))
            
            # Estimate position based on transaction value
            # This is a placeholder - real implementation would decode contract calls
            if value_eth > 0:
                return {
                    "transaction_hash": tx.get("hash"),
                    "market_id": f"market_{tx.get('blockNumber')}",  # Placeholder
                    "position_size_usd": float(value_eth * 2000),  # Assuming ETH price
                    "timestamp": int(tx.get("timeStamp", "0")),
                    "transaction_type": "buy" if tx.get("isError") == "0" else "unknown"
                }
        except Exception as e:
            logger.error(f"Error parsing transaction: {e}")
        
        return None
    
    def _aggregate_positions(self, positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate positions by market."""
        market_positions = {}
        
        for position in positions:
            market_id = position.get("market_id")
            if market_id not in market_positions:
                market_positions[market_id] = {
                    "market_id": market_id,
                    "total_position_size_usd": 0,
                    "transaction_count": 0,
                    "first_entry_timestamp": position.get("timestamp"),
                    "last_entry_timestamp": position.get("timestamp")
                }
            
            market_positions[market_id]["total_position_size_usd"] += position.get("position_size_usd", 0)
            market_positions[market_id]["transaction_count"] += 1
            market_positions[market_id]["last_entry_timestamp"] = max(
                market_positions[market_id]["last_entry_timestamp"],
                position.get("timestamp", 0)
            )
        
        return list(market_positions.values())
    
    async def _get_eth_price(self) -> float:
        """Get current ETH price in USD (simplified implementation)."""
        try:
            # In production, use a reliable price oracle
            # This is a placeholder using a free API
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("ethereum", {}).get("usd", 2000)
        except Exception as e:
            logger.error(f"Error getting ETH price: {e}")
        
        return 2000.0  # Fallback price
```

### Step 3.2: Trader Intelligence Module

Create `app/intelligence/portfolio_composition.py`:
```python
from typing import Dict, List, Any
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class PortfolioComposer:
    """Analyzes trader portfolio composition and allocation patterns."""
    
    def __init__(self):
        self.min_position_threshold = Decimal('100')  # Minimum $100 position
    
    def analyze_portfolio_allocation(self, portfolio_data: Dict[str, Any], target_market_id: str) -> Dict[str, Any]:
        """Analyze how much of a trader's portfolio is allocated to a specific market."""
        total_portfolio_value = Decimal(str(portfolio_data.get("total_portfolio_value_usd", 0)))
        positions = portfolio_data.get("positions", [])
        
        if total_portfolio_value == 0:
            return {
                "allocation_ratio": 0.0,
                "position_size_usd": 0.0,
                "is_significant": False,
                "risk_level": "unknown"
            }
        
        # Find positions in target market
        target_positions = [
            pos for pos in positions 
            if pos.get("market_id") == target_market_id
        ]
        
        total_market_allocation = sum(
            Decimal(str(pos.get("total_position_size_usd", 0)))
            for pos in target_positions
        )
        
        allocation_ratio = total_market_allocation / total_portfolio_value
        
        # Determine significance and risk level
        is_significant = (
            total_market_allocation >= self.min_position_threshold and
            allocation_ratio >= Decimal('0.05')  # At least 5% allocation
        )
        
        risk_level = self._assess_risk_level(allocation_ratio)
        
        return {
            "allocation_ratio": float(allocation_ratio),
            "position_size_usd": float(total_market_allocation),
            "is_significant": is_significant,
            "risk_level": risk_level,
            "total_portfolio_value": float(total_portfolio_value),
            "position_count": len(target_positions)
        }
    
    def _assess_risk_level(self, allocation_ratio: Decimal) -> str:
        """Assess risk level based on allocation ratio."""
        if allocation_ratio >= Decimal('0.25'):  # 25%+
            return "high"
        elif allocation_ratio >= Decimal('0.10'):  # 10-25%
            return "moderate"
        elif allocation_ratio >= Decimal('0.05'):  # 5-10%
            return "low"
        else:
            return "minimal"
    
    def calculate_diversification_score(self, positions: List[Dict[str, Any]]) -> float:
        """Calculate portfolio diversification score (0-1, higher = more diversified)."""
        if not positions:
            return 0.0
        
        # Calculate Herfindahl-Hirschman Index for diversification
        total_value = sum(Decimal(str(pos.get("total_position_size_usd", 0))) for pos in positions)
        
        if total_value == 0:
            return 0.0
        
        # Calculate market share for each position
        shares = [
            (Decimal(str(pos.get("total_position_size_usd", 0))) / total_value) ** 2
            for pos in positions
        ]
        
        hhi = sum(shares)
        
        # Convert to diversification score (1 - normalized HHI)
        max_hhi = Decimal('1.0')  # Maximum concentration (all in one position)
        min_hhi = Decimal('1.0') / len(positions)  # Perfect diversification
        
        if max_hhi == min_hhi:
            return 1.0
        
        normalized_hhi = (hhi - min_hhi) / (max_hhi - min_hhi)
        diversification_score = 1.0 - float(normalized_hhi)
        
        return max(0.0, min(1.0, diversification_score))
```

### Step 3.3: Performance Calculator

Create `app/intelligence/performance_calculator.py`:
```python
from typing import Dict, List, Any, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PerformanceCalculator:
    """Calculates trader performance metrics and success rates."""
    
    def __init__(self):
        self.confidence_level = 0.95  # For confidence intervals
    
    def calculate_success_rate(self, trading_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trader success rate with statistical confidence."""
        if not trading_history:
            return {
                "success_rate": 0.0,
                "total_trades": 0,
                "winning_trades": 0,
                "confidence_interval": [0.0, 1.0],
                "is_statistically_significant": False
            }
        
        total_trades = len(trading_history)
        winning_trades = sum(
            1 for trade in trading_history 
            if trade.get("outcome") == "win"
        )
        
        success_rate = Decimal(winning_trades) / Decimal(total_trades)
        confidence_interval = self._calculate_confidence_interval(success_rate, total_trades)
        is_significant = self._is_statistically_significant(success_rate, total_trades)
        
        return {
            "success_rate": float(success_rate),
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "confidence_interval": confidence_interval,
            "is_statistically_significant": is_significant,
            "sample_size_adequate": total_trades >= 10
        }
    
    def calculate_roi(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate return on investment metrics."""
        total_invested = Decimal('0')
        total_current_value = Decimal('0')
        realized_pnl = Decimal('0')
        
        for position in positions:
            invested = Decimal(str(position.get("position_size_usd", 0)))
            current_value = Decimal(str(position.get("current_value_usd", invested)))
            
            total_invested += invested
            total_current_value += current_value
            
            # If position is closed, add to realized P&L
            if position.get("status") == "closed":
                realized_pnl += current_value - invested
        
        if total_invested == 0:
            return {
                "roi_percentage": 0.0,
                "total_invested": 0.0,
                "current_value": 0.0,
                "unrealized_pnl": 0.0,
                "realized_pnl": 0.0,
                "total_pnl": 0.0
            }
        
        unrealized_pnl = total_current_value - total_invested
        total_pnl = realized_pnl + unrealized_pnl
        roi_percentage = (total_pnl / total_invested) * 100
        
        return {
            "roi_percentage": float(roi_percentage),
            "total_invested": float(total_invested),
            "current_value": float(total_current_value),
            "unrealized_pnl": float(unrealized_pnl),
            "realized_pnl": float(realized_pnl),
            "total_pnl": float(total_pnl)
        }
    
    def analyze_trading_patterns(self, trading_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trader behavioral patterns."""
        if not trading_history:
            return {
                "avg_position_size": 0.0,
                "position_size_consistency": 0.0,
                "avg_hold_duration_days": 0.0,
                "preferred_market_types": [],
                "risk_tolerance": "unknown"
            }
        
        # Calculate average position size
        position_sizes = [
            Decimal(str(trade.get("position_size_usd", 0)))
            for trade in trading_history
        ]
        avg_position_size = sum(position_sizes) / len(position_sizes)
        
        # Calculate position size consistency (coefficient of variation)
        if avg_position_size > 0:
            variance = sum((size - avg_position_size) ** 2 for size in position_sizes) / len(position_sizes)
            std_dev = variance ** Decimal('0.5')
            consistency = 1 - (std_dev / avg_position_size)  # Higher = more consistent
        else:
            consistency = Decimal('0')
        
        # Calculate average hold duration
        hold_durations = []
        for trade in trading_history:
            start_time = trade.get("entry_timestamp", 0)
            end_time = trade.get("exit_timestamp", start_time)
            if end_time > start_time:
                duration_days = (end_time - start_time) / (24 * 60 * 60)  # Convert to days
                hold_durations.append(duration_days)
        
        avg_hold_duration = sum(hold_durations) / len(hold_durations) if hold_durations else 0
        
        # Analyze preferred market types
        market_types = [trade.get("market_category", "unknown") for trade in trading_history]
        market_type_counts = {}
        for market_type in market_types:
            market_type_counts[market_type] = market_type_counts.get(market_type, 0) + 1
        
        preferred_types = sorted(
            market_type_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]  # Top 3 preferred types
        
        # Assess risk tolerance
        risk_tolerance = self._assess_risk_tolerance(position_sizes, avg_position_size)
        
        return {
            "avg_position_size": float(avg_position_size),
            "position_size_consistency": float(consistency),
            "avg_hold_duration_days": avg_hold_duration,
            "preferred_market_types": [pref[0] for pref in preferred_types],
            "risk_tolerance": risk_tolerance
        }
    
    def _calculate_confidence_interval(self, success_rate: Decimal, sample_size: int) -> List[float]:
        """Calculate confidence interval for success rate."""
        if sample_size < 5:
            return [0.0, 1.0]
        
        import math
        
        p = float(success_rate)
        n = sample_size
        z = 1.96  # 95% confidence level
        
        margin = z * math.sqrt((p * (1 - p)) / n)
        lower = max(0.0, p - margin)
        upper = min(1.0, p + margin)
        
        return [lower, upper]
    
    def _is_statistically_significant(self, success_rate: Decimal, sample_size: int) -> bool:
        """Check if success rate is statistically significant above 50%."""
        if sample_size < 10:
            return False
        
        confidence_interval = self._calculate_confidence_interval(success_rate, sample_size)
        return confidence_interval[0] > 0.5
    
    def _assess_risk_tolerance(self, position_sizes: List[Decimal], avg_size: Decimal) -> str:
        """Assess trader risk tolerance based on position sizing."""
        if not position_sizes or avg_size == 0:
            return "unknown"
        
        # Calculate coefficient of variation
        variance = sum((size - avg_size) ** 2 for size in position_sizes) / len(position_sizes)
        std_dev = variance ** Decimal('0.5')
        cv = std_dev / avg_size if avg_size > 0 else Decimal('0')
        
        max_position = max(position_sizes)
        max_ratio = max_position / avg_size if avg_size > 0 else Decimal('1')
        
        # Risk tolerance classification
        if cv > Decimal('1.0') or max_ratio > Decimal('5.0'):
            return "high"
        elif cv > Decimal('0.5') or max_ratio > Decimal('2.0'):
            return "moderate"
        else:
            return "low"
```

### Step 3.4: Update Trader Analysis Endpoint

Update `app/api/routes.py` to implement trader analysis:
```python
from app.data.blockchain_client import BlockchainClient
from app.intelligence.portfolio_composition import PortfolioComposer
from app.intelligence.performance_calculator import PerformanceCalculator

async def get_blockchain_client():
    """Dependency to get blockchain client."""
    return BlockchainClient()

@router.get("/trader/{trader_address}/analysis", response_model=TraderPerformance)
async def analyze_trader(
    trader_address: str,
    blockchain_client: BlockchainClient = Depends(get_blockchain_client)
):
    """Get comprehensive trader analysis."""
    try:
        # Get portfolio data from blockchain
        portfolio_data = await blockchain_client.get_trader_portfolio(trader_address)
        
        if "error" in portfolio_data:
            raise HTTPException(status_code=400, detail=f"Error fetching trader data: {portfolio_data['error']}")
        
        # Analyze portfolio composition
        portfolio_composer = PortfolioComposer()
        performance_calculator = PerformanceCalculator()
        
        # Calculate performance metrics
        positions = portfolio_data.get("positions", [])
        roi_metrics = performance_calculator.calculate_roi(positions)
        
        # For now, use mock trading history since we don't have complete trade data
        mock_trading_history = [
            {"outcome": "win", "position_size_usd": 1000, "market_category": "politics"},
            {"outcome": "win", "position_size_usd": 1500, "market_category": "sports"},
            {"outcome": "loss", "position_size_usd": 800, "market_category": "politics"},
            {"outcome": "win", "position_size_usd": 2000, "market_category": "crypto"},
        ]
        
        success_metrics = performance_calculator.calculate_success_rate(mock_trading_history)
        trading_patterns = performance_calculator.analyze_trading_patterns(mock_trading_history)
        
        # Calculate diversification
        diversification_score = portfolio_composer.calculate_diversification_score(positions)
        
        # Build TraderPerformance response
        return TraderPerformance(
            address=trader_address,
            total_portfolio_value_usd=Decimal(str(portfolio_data.get("total_portfolio_value_usd", 0))),
            active_positions=portfolio_data.get("active_positions", 0),
            total_markets_traded=len(set(pos.get("market_id") for pos in positions)),
            overall_success_rate=Decimal(str(success_metrics.get("success_rate", 0))),
            total_profit_usd=Decimal(str(roi_metrics.get("total_pnl", 0))),
            roi_percentage=Decimal(str(roi_metrics.get("roi_percentage", 0))),
            positions=[
                TraderPosition(
                    market_id=pos.get("market_id", "unknown"),
                    outcome_id="unknown",  # We don't have this data yet
                    position_size_usd=Decimal(str(pos.get("total_position_size_usd", 0))),
                    entry_price=Decimal('0.5'),  # Placeholder
                    current_value_usd=Decimal(str(pos.get("total_position_size_usd", 0))),
                    portfolio_allocation_pct=Decimal('0')  # Will be calculated
                )
                for pos in positions
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing trader: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Step 3.5: Update Alpha Analysis with Real Trader Data

Update `app/agents/agent_coordinator.py` to use real blockchain data:
```python
# Add to AgentCoordinator class
async def analyze_market_alpha_with_blockchain(
    self, 
    market_data: Dict[str, Any], 
    trader_addresses: List[str],
    blockchain_client
) -> AlphaAnalysis:
    """Analyze market alpha using real blockchain data."""
    logger.info(f"Fetching blockchain data for {len(trader_addresses)} traders")
    
    # Fetch real trader data
    trader_data = []
    for address in trader_addresses:
        try:
            portfolio = await blockchain_client.get_trader_portfolio(address)
            if "error" not in portfolio:
                trader_data.append(portfolio)
        except Exception as e:
            logger.error(f"Error fetching data for trader {address}: {e}")
    
    # Run alpha analysis with real data
    return await self.analyze_market_alpha(market_data, trader_data)
```

### Step 3.6: Phase 3 Tests

Create `tests/test_phase3.py`:
```python
import pytest
from unittest.mock import Mock, AsyncMock
from app.data.blockchain_client import BlockchainClient
from app.intelligence.portfolio_composition import PortfolioComposer
from app.intelligence.performance_calculator import PerformanceCalculator

@pytest.mark.asyncio
async def test_blockchain_client():
    """Test blockchain client functionality."""
    client = BlockchainClient()
    
    # Mock the Web3 instance
    client.w3 = Mock()
    client.w3.is_address = Mock(return_value=True)
    client.w3.eth.get_balance = Mock(return_value=1000000000000000000)  # 1 ETH in wei
    client.w3.from_wei = Mock(return_value=1.0)
    
    # Mock external API calls
    client._get_eth_price = AsyncMock(return_value=2000.0)
    client._get_usdc_balance = AsyncMock(return_value=1000.0)
    client._get_polymarket_positions = AsyncMock(return_value=[])
    
    portfolio = await client.get_trader_portfolio("0x123456789abcdef")
    
    assert "address" in portfolio
    assert "total_portfolio_value_usd" in portfolio
    assert isinstance(portfolio["total_portfolio_value_usd"], float)

def test_portfolio_composer():
    """Test portfolio composition analysis."""
    composer = PortfolioComposer()
    
    portfolio_data = {
        "total_portfolio_value_usd": 100000,
        "positions": [
            {
                "market_id": "target_market",
                "total_position_size_usd": 15000
            },
            {
                "market_id": "other_market",
                "total_position_size_usd": 5000
            }
        ]
    }
    
    analysis = composer.analyze_portfolio_allocation(portfolio_data, "target_market")
    
    assert analysis["allocation_ratio"] == 0.15  # 15%
    assert analysis["is_significant"] is True
    assert analysis["risk_level"] == "moderate"

def test_performance_calculator():
    """Test performance calculation."""
    calculator = PerformanceCalculator()
    
    trading_history = [
        {"outcome": "win", "position_size_usd": 1000},
        {"outcome": "win", "position_size_usd": 1500},
        {"outcome": "loss", "position_size_usd": 800},
        {"outcome": "win", "position_size_usd": 1200},
    ]
    
    success_metrics = calculator.calculate_success_rate(trading_history)
    
    assert success_metrics["success_rate"] == 0.75  # 3/4 wins
    assert success_metrics["total_trades"] == 4
    assert success_metrics["winning_trades"] == 3
    assert len(success_metrics["confidence_interval"]) == 2

def test_roi_calculation():
    """Test ROI calculation."""
    calculator = PerformanceCalculator()
    
    positions = [
        {
            "position_size_usd": 1000,
            "current_value_usd": 1200,
            "status": "open"
        },
        {
            "position_size_usd": 500,
            "current_value_usd": 600,
            "status": "closed"
        }
    ]
    
    roi_metrics = calculator.calculate_roi(positions)
    
    assert roi_metrics["total_invested"] == 1500
    assert roi_metrics["current_value"] == 1800
    assert roi_metrics["total_pnl"] == 300
    assert roi_metrics["roi_percentage"] == 20.0  # 20% return
```

### Phase 3 Verification

Run these commands to verify Phase 3 implementation:

```bash
# Run Phase 3 tests
python -m pytest tests/test_phase3.py -v

# Test trader analysis endpoint (requires valid Ethereum address)
curl "http://localhost:8000/api/trader/0x742ba4cb0d5a3c41f9c1c2e4dcb9c1f9d2c8c1f1/analysis"

# Test alpha analysis with blockchain integration
curl "http://localhost:8000/api/market/test_market_id/alpha"

# Check logs for blockchain integration
tail -f logs/app.log  # If you've set up logging to file
```

**Phase 3 Success Criteria Checklist:**
- [ ] Blockchain client connects to Polygon
- [ ] Portfolio analysis processes test addresses
- [ ] Trader endpoint returns valid data
- [ ] Alpha scoring model functions with real data
- [ ] Performance calculations work correctly
- [ ] Integration tests pass
- [ ] Error handling works for invalid addresses

---

## Implementation Notes

### API Keys Required

To complete the implementation, you'll need:

1. **Polygon RPC URL**: Get from Alchemy, Infura, or QuickNode
2. **Polygonscan API Key**: For transaction history (free at polygonscan.com)
3. **Polymarket API Key**: Contact Polymarket for access (if available)

### Development vs Production

This implementation includes:
- Mock data for testing when APIs aren't available
- Graceful error handling for missing API keys
- Simplified calculations that can be enhanced in production
- Placeholder values for complex blockchain data parsing

### Next Steps

After completing Phase 3:
1. Add comprehensive caching (Phase 4)
2. Implement proper monitoring and logging (Phase 5)
3. Deploy to staging environment
4. Add more sophisticated agent algorithms
5. Implement real-time data updates

The implementation provides a solid foundation that can be enhanced incrementally while maintaining functionality at each phase.