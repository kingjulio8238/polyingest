# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PolyIngest is an advanced alpha detection service for Polymarket prediction markets. The system uses comprehensive market data analysis and multi-agent intelligence to identify trading opportunities ("alpha") by analyzing trader behavior, success rates, and portfolio allocation patterns.

**Production Usage**:
- Primary endpoint: `GET /api/market/{market_id}/alpha`
- Market data endpoint: `GET /api/market/{market_id}/data`
- Trader analysis endpoint: `GET /api/trader/{trader_address}/analysis`
- Example: `GET /api/market/0x1234.../alpha?min_portfolio_ratio=0.1&min_success_rate=0.7`
- Returns comprehensive alpha analysis with agent consensus and confidence scores

**Core Features**:
- Comprehensive Polymarket data retrieval using GraphQL API, REST endpoints, and on-chain analysis
- Multi-agent alpha detection system with specialized analysis agents
- Trader behavior analysis including portfolio allocation and historical success rates
- Agent voting system with confidence scoring and consensus building
- Real-time market monitoring and alert capabilities
- Advanced filtering for high-conviction traders and significant position sizes

## Technical Stack

- **Framework**: FastAPI for the API server with async request handling
- **Data Sources**: 
  - Polymarket GraphQL API (`https://clob.polymarket.com/graphql`)
  - Polymarket REST API (`https://clob.polymarket.com/`)
  - Polygon blockchain data for on-chain portfolio analysis
  - Historical trading data and market outcomes
- **Agent System**: Multi-agent architecture with specialized analysis modules
- **Data Processing**: Pandas, NumPy for statistical analysis and trader behavior modeling
- **Blockchain Integration**: Web3.py for on-chain portfolio and transaction analysis
- **Caching**: Redis for market data and trader analysis caching
- **Database**: PostgreSQL for historical data storage and trader performance tracking
- **Deployment**: Containerized deployment for Vercel, Render, or Heroku
- **Libraries**: fastapi, uvicorn, aiohttp, pandas, numpy, web3, redis, asyncpg

## Development Commands

**Environment Setup**:
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Configure: POLYMARKET_API_KEY, POLYGON_RPC_URL, REDIS_URL, DATABASE_URL

# Initialize database
python scripts/init_db.py

# Start Redis (for caching)
redis-server
```

**Local Development**:
```bash
# Start the API server
python app.py
# or
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Testing**:
```bash
# Test market data retrieval
curl http://localhost:8000/api/market/0x1234.../data

# Test alpha analysis
curl "http://localhost:8000/api/market/0x1234.../alpha?min_portfolio_ratio=0.1&min_success_rate=0.7"

# Test trader analysis
curl http://localhost:8000/api/trader/0xabcd.../analysis

# Run unit tests
pytest tests/

# Run integration tests with live Polymarket data
pytest tests/integration/ --live-data
```

## Architecture Notes

The application follows a microservices-inspired architecture within a single FastAPI application:

### Core Components

1. **API Layer** (`app/api/`):
   - Market data endpoints
   - Alpha analysis endpoints
   - Trader analysis endpoints
   - Real-time market monitoring

2. **Data Retrieval Engine** (`app/data/`):
   - Polymarket API clients (GraphQL + REST)
   - On-chain data retrieval (Polygon blockchain)
   - Historical data aggregation
   - Market outcome tracking

3. **Multi-Agent Analysis System** (`app/agents/`):
   - **Portfolio Analyzer Agent**: Analyzes trader portfolio allocation patterns
   - **Success Rate Agent**: Calculates trader historical performance and win rates
   - **Volume Analysis Agent**: Evaluates bet sizes relative to trader portfolios
   - **Market Sentiment Agent**: Analyzes market dynamics and crowd behavior
   - **Technical Analysis Agent**: Performs price action and momentum analysis
   - **Consensus Agent**: Coordinates agent voting and builds final alpha recommendations

4. **Trader Intelligence Module** (`app/intelligence/`):
   - Trader behavior modeling and pattern recognition
   - Portfolio composition analysis across multiple markets
   - Success rate calculation with confidence intervals
   - Risk assessment and position sizing analysis

5. **Alpha Detection Pipeline** (`app/alpha/`):
   - Multi-factor alpha scoring models
   - Agent coordination and voting mechanisms
   - Confidence scoring and uncertainty quantification
   - Alert generation for high-confidence opportunities

6. **Data Storage & Caching** (`app/storage/`):
   - Redis caching for real-time market data
   - PostgreSQL for historical trader performance
   - Market outcome database
   - Agent analysis result storage

## Important Implementation Notes

### Polymarket API Integration
- **GraphQL Endpoint**: `https://clob.polymarket.com/graphql`
- **REST API**: `https://clob.polymarket.com/` for additional market data
- **Required Data Points**:
  - Market details (title, description, end_date, resolution_criteria)
  - Current market prices and probabilities
  - Order book depth and bid-ask spreads
  - Trading volume and liquidity metrics
  - Individual trade history with trader addresses
  - Market maker activity and large position changes

### On-Chain Analysis Requirements
- **Polygon Network Integration**: Access trader wallet data and transaction history
- **Portfolio Analysis**: Calculate total portfolio value and market-specific allocation ratios
- **Transaction Tracking**: Monitor large position changes and bet timing
- **Success Rate Calculation**: Track resolved market outcomes vs. trader positions

### Multi-Agent System Design
- **Agent Independence**: Each agent analyzes data independently without bias
- **Specialized Analysis**: Agents focus on specific aspects (portfolio, success rate, volume, etc.)
- **Voting Mechanism**: Weighted voting system based on agent confidence and historical accuracy
- **Consensus Building**: Require multiple agents to agree before flagging alpha opportunities

### Alpha Detection Criteria
- **High Portfolio Allocation**: Traders betting significant portion (>10%) of portfolio on specific market
- **Proven Success Rate**: Historical win rate above 70% with statistical significance
- **Position Size Significance**: Absolute bet size above meaningful threshold
- **Timing Analysis**: Early position entry vs. late market movements
- **Market Context**: Consider market liquidity, volatility, and time to resolution

## Output Formats

### Alpha Analysis Response (`/api/market/{market_id}/alpha`)
```json
{
  "market": {
    "id": "0x1234...",
    "title": "Will Donald Trump win the 2024 Presidential Election?",
    "description": "Market resolves to Yes if Donald Trump wins...",
    "end_date": "2024-11-05T23:59:59Z",
    "status": "active",
    "current_prices": {"Yes": 0.52, "No": 0.48},
    "total_volume_24h": 2500000,
    "total_liquidity": 1200000
  },
  "alpha_analysis": {
    "has_alpha": true,
    "confidence_score": 0.85,
    "recommended_side": "Yes",
    "strength": "strong",
    "agent_consensus": {
      "votes_for_alpha": 4,
      "votes_against_alpha": 1,
      "abstentions": 0
    }
  },
  "key_traders": [
    {
      "address": "0xabc123...",
      "position_size_usd": 50000,
      "portfolio_allocation_pct": 15.2,
      "historical_success_rate": 0.78,
      "position_side": "Yes",
      "entry_price": 0.45,
      "confidence_indicators": {
        "large_position": true,
        "high_allocation": true,
        "proven_track_record": true,
        "early_entry": true
      }
    }
  ],
  "agent_analyses": [
    {
      "agent_name": "Portfolio Analyzer",
      "vote": "alpha",
      "confidence": 0.9,
      "reasoning": "3 traders with >10% portfolio allocation, avg 14.2%",
      "key_findings": [
        "Top trader allocated 22% of $850k portfolio",
        "Average allocation 3x higher than typical market",
        "High-conviction cluster around 'Yes' outcome"
      ]
    },
    {
      "agent_name": "Success Rate Analyzer", 
      "vote": "alpha",
      "confidence": 0.82,
      "reasoning": "Key traders show 76% avg success rate over 25+ markets",
      "key_findings": [
        "Lead trader: 78% success rate across 32 resolved markets",
        "Statistical significance confirmed (p < 0.01)",
        "Strong performance in similar political markets"
      ]
    }
  ],
  "risk_factors": [
    "Market highly politicized - emotion may override analysis",
    "Time to resolution: 45 days - significant event risk",
    "High media attention may attract noise traders"
  ],
  "metadata": {
    "analysis_timestamp": "2024-01-01T12:00:00Z",
    "data_freshness": "real-time",
    "trader_sample_size": 1247,
    "min_portfolio_ratio_filter": 0.1,
    "min_success_rate_filter": 0.7
  }
}
```

### Market Data Response (`/api/market/{market_id}/data`)
```json
{
  "market": {
    "id": "0x1234...",
    "title": "Market Title",
    "description": "Detailed market description...",
    "category": "Politics", 
    "subcategory": "US Elections",
    "end_date": "2024-11-05T23:59:59Z",
    "resolution_criteria": "Market resolves based on...",
    "status": "active",
    "creator": "0xdef456...",
    "total_volume": 15000000,
    "total_liquidity": 2500000
  },
  "outcomes": [
    {
      "id": "yes",
      "name": "Yes", 
      "current_price": 0.52,
      "volume_24h": 1800000,
      "liquidity": 1200000,
      "order_book": {
        "bids": [{"price": 0.515, "size": 10000}],
        "asks": [{"price": 0.525, "size": 15000}]
      }
    }
  ],
  "trading_activity": {
    "total_trades_24h": 2847,
    "unique_traders_24h": 432,
    "avg_trade_size": 1250,
    "large_trades_24h": 23,
    "recent_large_trades": [
      {
        "timestamp": "2024-01-01T11:45:00Z",
        "trader": "0x789...",
        "side": "Yes",
        "amount_usd": 25000,
        "price": 0.518
      }
    ]
  }
}
```

### Trader Analysis Response (`/api/trader/{address}/analysis`)
```json
{
  "trader": {
    "address": "0xabc123...",
    "total_portfolio_value_usd": 850000,
    "active_positions": 12,
    "total_markets_traded": 67
  },
  "performance_metrics": {
    "overall_success_rate": 0.78,
    "total_profit_usd": 125000,
    "roi_percentage": 18.5,
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
```
```

## Deployment Considerations

### Infrastructure Requirements
- **API-only service**: No browser dependencies or frontend components
- **Database**: PostgreSQL for historical data and trader performance tracking
- **Caching**: Redis cluster for real-time market data and analysis results
- **Background Jobs**: Celery for periodic data updates and batch analysis
- **Monitoring**: Application metrics, API response times, and agent performance tracking

### Environment Configuration
```bash
# Polymarket API
POLYMARKET_API_KEY=your_api_key
POLYMARKET_GRAPHQL_URL=https://clob.polymarket.com/graphql
POLYMARKET_REST_URL=https://clob.polymarket.com

# Blockchain Data
POLYGON_RPC_URL=https://polygon-rpc.com
POLYGON_ARCHIVE_URL=https://polygon-archive.com
ETHERSCAN_API_KEY=your_etherscan_key

# Data Storage
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/polyingest

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

### Scaling Considerations
- **Horizontal scaling**: Stateless API design enables multiple instances
- **Database optimization**: Indexed queries for trader lookups and market data
- **Caching strategy**: Multi-tier caching (Redis + in-memory) for performance
- **Background processing**: Separate worker processes for data collection and analysis
- **Rate limiting**: Respect external API limits while maintaining responsiveness

### Monitoring and Alerts
- **API Performance**: Response times, error rates, and throughput metrics
- **Agent Performance**: Voting accuracy, confidence calibration, and consensus timing
- **Data Quality**: Market data freshness, trader analysis completeness
- **Alpha Detection**: Alert generation for high-confidence opportunities
- **System Health**: Database performance, cache hit rates, external API status