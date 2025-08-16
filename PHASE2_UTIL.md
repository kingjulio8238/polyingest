# Phase 2 Utilities & Available Commands

## Phase 2 Success Criteria Status ✅

**Phase 2 Success Criteria Checklist:**
- [x] **Agent framework instantiates correctly** - Verified in `test_portfolio_agent_initialization`, `test_success_rate_agent_initialization`, `test_agent_coordinator_initialization`
- [x] **Portfolio agent analyzes test data** - Verified in `test_portfolio_agent_with_specification_data` using exact IMPLEMENTATION.md test data (15% allocation trader)
- [x] **Success rate agent processes trader data** - Verified in `test_success_rate_agent_with_specification_data` using exact IMPLEMENTATION.md test data (75% success rate, 15 markets)
- [x] **Voting system reaches consensus** - Verified in `test_voting_system_consensus_with_specification_data` with weighted voting and agent coordination
- [x] **Alpha analysis endpoint returns structured response** - Verified in `test_agent_coordinator_with_specification_data` with complete CLAUDE.md API response format
- [x] **Agent confidence scores are reasonable (0.0-1.0)** - Verified in `test_confidence_score_calibration` across multiple scenarios
- [x] **Error handling works for invalid inputs** - Verified in `test_error_recovery_and_resilience`, `test_agent_coordinator_error_handling`

**Status: All 7 success criteria PASSED** ✅

## What You Can Do Now

### 1. API Testing & Development

#### Start the Development Server
```bash
# Start the FastAPI server
python app/main.py
# or
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Test Alpha Analysis Endpoint
```bash
# Basic alpha analysis
curl "http://localhost:8000/api/market/0x1234567890abcdef/alpha"

# Alpha analysis with custom filters
curl "http://localhost:8000/api/market/0x1234567890abcdef/alpha?min_portfolio_ratio=0.15&min_success_rate=0.8&min_trade_history=20"

# Market data endpoint
curl "http://localhost:8000/api/market/0x1234567890abcdef/data"

# Trader analysis endpoint
curl "http://localhost:8000/api/trader/0xabc123456789def012345678901234567890abcdef/analysis"

# Health check
curl "http://localhost:8000/api/health"

# System metrics
curl "http://localhost:8000/api/metrics"
```

### 2. Agent Testing & Analysis

#### Run Comprehensive Test Suite
```bash
# Run all Phase 2 tests (28 tests)
pytest tests/test_phase2.py -v

# Run API integration tests (14 tests)  
pytest tests/test_api_routes_phase2_integration.py -v

# Run specific agent tests
pytest tests/test_phase2.py::TestPortfolioAgent -v
pytest tests/test_phase2.py::TestSuccessRateAgent -v
pytest tests/test_phase2.py::TestVotingSystem -v
pytest tests/test_phase2.py::TestAgentCoordinator -v

# Run end-to-end integration tests
pytest tests/test_phase2.py::TestIntegration -v
```

#### Test Individual Agents Programmatically
```python
# Portfolio Agent Analysis
from app.agents.portfolio_agent import PortfolioAnalyzerAgent

agent = PortfolioAnalyzerAgent()
test_data = {
    "market": {"id": "test_market", "title": "Test Market"},
    "traders": [{
        "address": "0x123",
        "total_portfolio_value_usd": 100000,
        "positions": [{"market_id": "test_market", "position_size_usd": 15000}]
    }]
}
analysis = await agent.analyze(test_data)
vote = agent.vote(analysis)
print(f"Vote: {vote}, Confidence: {agent.confidence}")
```

```python
# Success Rate Agent Analysis
from app.agents.success_rate_agent import SuccessRateAgent

agent = SuccessRateAgent()
test_data = {
    "market": {"id": "test_market", "title": "Test Market"},
    "traders": [{
        "address": "0x123",
        "performance_metrics": {
            "overall_success_rate": 0.75,
            "markets_resolved": 15,
            "total_profit_usd": 25000
        }
    }]
}
analysis = await agent.analyze(test_data)
vote = agent.vote(analysis)
print(f"Vote: {vote}, Reasoning: {agent.get_reasoning()}")
```

### 3. Agent Coordination Workflow

#### Full Agent Coordinator Usage
```python
from app.agents.coordinator import AgentCoordinator

coordinator = AgentCoordinator()

# Analyze market with trader data
market_data = {
    "id": "test_market",
    "title": "Test Market",
    "status": "active",
    "total_volume": 100000,
    "total_liquidity": 50000
}

traders_data = [{
    "address": "0x123",
    "total_portfolio_value_usd": 100000,
    "performance_metrics": {
        "overall_success_rate": 0.75,
        "markets_resolved": 15,
        "total_profit_usd": 25000
    },
    "positions": [{
        "market_id": "test_market",
        "position_size_usd": 15000,
        "outcome_id": "Yes",
        "entry_price": 0.45
    }]
}]

result = await coordinator.analyze_market(market_data, traders_data)
print(f"Alpha detected: {result['alpha_analysis']['has_alpha']}")
print(f"Confidence: {result['alpha_analysis']['confidence_score']}")
```

#### Monitor Agent Performance
```python
# Get performance metrics
metrics = coordinator.get_performance_metrics()
print(f"Analyses completed: {metrics['coordinator_performance']['total_analyses']}")
print(f"Success rate: {metrics['coordinator_performance']['success_rate']}")

# Get agent status
status = coordinator.get_agent_status()
print(f"Registered agents: {status['registered_agents']}")
print(f"Agent details: {status['agent_details']}")
```

### 4. Voting System Operations

#### Direct Voting System Usage
```python
from app.agents.voting_system import VotingSystem
from app.agents.portfolio_agent import PortfolioAnalyzerAgent
from app.agents.success_rate_agent import SuccessRateAgent

voting_system = VotingSystem()
voting_system.register_agent(PortfolioAnalyzerAgent())
voting_system.register_agent(SuccessRateAgent())

# Conduct vote
test_data = {
    "market": {"id": "test_market"},
    "traders": [...]  # Your trader data
}

voting_result = await voting_system.conduct_vote(test_data)
print(f"Consensus: {voting_result.consensus_reached}")
print(f"Alpha votes: {voting_result.votes_for_alpha}")
print(f"Against votes: {voting_result.votes_against_alpha}")
print(f"Confidence: {voting_result.confidence_score}")
```

### 5. Development & Debugging

#### Configuration Management
```python
from app.config import settings

# View current configuration
print(f"Vote threshold: {settings.agent_vote_threshold}")
print(f"Min portfolio ratio: {settings.min_portfolio_ratio}")
print(f"Min success rate: {settings.min_success_rate}")
print(f"Min trade history: {settings.min_trade_history}")
```

#### Logging & Monitoring
```bash
# Start server with debug logging
LOG_LEVEL=DEBUG python app/main.py

# Monitor API requests in real-time
tail -f logs/api.log  # if logging to file
```

#### Testing Different Scenarios
```python
# Test high-conviction scenario
high_conviction_data = {
    "traders": [{
        "address": "0x123",
        "total_portfolio_value_usd": 250000,
        "performance_metrics": {"overall_success_rate": 0.85, "markets_resolved": 20},
        "positions": [{"position_size_usd": 50000}]  # 20% allocation
    }]
}

# Test low-conviction scenario
low_conviction_data = {
    "traders": [{
        "address": "0x456", 
        "total_portfolio_value_usd": 100000,
        "performance_metrics": {"overall_success_rate": 0.55, "markets_resolved": 8},
        "positions": [{"position_size_usd": 3000}]  # 3% allocation
    }]
}
```

### 6. Data Validation & Error Handling

#### Test Error Scenarios
```python
# Test with invalid data
invalid_data = {
    "market": {},  # Missing required fields
    "traders": [{
        "address": "invalid",
        "total_portfolio_value_usd": -1000,  # Invalid negative
        "performance_metrics": {"overall_success_rate": 1.5}  # Invalid > 1.0
    }]
}

result = await coordinator.analyze_market(invalid_data["market"], invalid_data["traders"])
# Should handle gracefully and return valid response
```

### 7. Performance Testing

#### Concurrent Request Testing
```python
import asyncio
import time

async def performance_test():
    coordinator = AgentCoordinator()
    
    # Test multiple concurrent analyses
    tasks = []
    for i in range(10):
        task = coordinator.analyze_market(market_data, traders_data)
        tasks.append(task)
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    print(f"Completed 10 analyses in {end_time - start_time:.2f} seconds")
    print(f"Average time per analysis: {(end_time - start_time) / 10:.2f} seconds")
```

## API Response Examples

### Alpha Analysis Response Structure
The API now returns complete CLAUDE.md-compliant responses:

```json
{
  "market": {
    "id": "0x1234567890abcdef",
    "title": "Will Donald Trump win the 2024 Presidential Election?",
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
  "key_traders": [...],
  "agent_analyses": [
    {
      "agent_name": "Portfolio Analyzer",
      "vote": "alpha",
      "confidence": 0.9,
      "reasoning": "3 traders with >10% portfolio allocation, avg 14.2%",
      "key_findings": [...]
    },
    {
      "agent_name": "Success Rate Analyzer",
      "vote": "alpha", 
      "confidence": 0.82,
      "reasoning": "Key traders show 76% avg success rate over 25+ markets",
      "key_findings": [...]
    }
  ],
  "risk_factors": [...],
  "metadata": {
    "analysis_timestamp": "2024-01-01T12:00:00Z",
    "trader_sample_size": 1247,
    "consensus_reached": true,
    "voting_duration_seconds": 2.5
  }
}
```

## Next Phase Readiness

**Phase 2 Complete** ✅ - Ready for **Phase 3: Blockchain Integration & Portfolio Analysis**

Phase 3 will add:
- Polygon blockchain integration for on-chain portfolio analysis
- Real-time trader wallet monitoring 
- Historical transaction analysis
- Enhanced portfolio allocation calculations
- On-chain position verification

All Phase 2 components are production-ready and fully tested with 42/42 tests passing.