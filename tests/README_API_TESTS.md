# API Tests for Phase 2 PolyIngest Endpoints

This directory contains comprehensive test suites for all Phase 2 API endpoints with AgentCoordinator integration.

## Test Files

### `test_api_routes_phase2.py`
Basic API tests that work with the real application dependencies. These tests validate:
- Health check and metrics endpoints
- Basic endpoint structure and response formats
- Input validation and error handling
- Query parameter validation
- Address format validation

### `test_api_routes_phase2_integration.py` ⭐ **RECOMMENDED**
Comprehensive integration tests with proper dependency mocking. These tests provide:
- Full API endpoint testing with mocked dependencies
- AgentCoordinator integration testing
- Proper async handling for coordinator operations
- Response structure validation against CLAUDE.md specification
- Performance testing (response times < 5 seconds)
- Error handling and edge case coverage
- Concurrent request testing

## Test Coverage

The integration tests cover all required API endpoints:

### Health & Metrics
- `GET /api/health` - Service health check
- `GET /api/metrics` - System performance metrics with agent status

### Market Data
- `GET /api/market/{market_id}/data` - Enhanced market data with order books and trading activity
- Error handling for non-existent markets

### Alpha Analysis (Core Feature)
- `GET /api/market/{market_id}/alpha` - Multi-agent alpha detection
- Query parameters: `min_portfolio_ratio`, `min_success_rate`, `min_trade_history`
- AgentCoordinator integration with voting system
- Response structure matches CLAUDE.md specification
- Both Portfolio Analyzer and Success Rate Analyzer agent responses

### Trader Analysis
- `GET /api/trader/{trader_address}/analysis` - Comprehensive trader performance analysis
- Ethereum address validation (42 chars, 0x prefix, valid hex)
- Error handling for invalid addresses and non-existent traders

## Key Test Features

### 1. **AgentCoordinator Integration**
Tests verify the coordination between API endpoints and the multi-agent system:
- Agent voting and consensus building
- Confidence scoring and uncertainty quantification
- Performance metrics aggregation

### 2. **Response Structure Validation**
Tests ensure API responses exactly match the CLAUDE.md specification:
- Required fields validation
- Nested object structure verification
- Data type consistency

### 3. **Performance Testing**
- Alpha analysis response time < 5 seconds
- Concurrent request handling (5 simultaneous requests)
- Agent consensus timing validation

### 4. **Error Handling**
- HTTP status code validation (400, 404, 422, 500)
- Error message format consistency
- Graceful degradation scenarios

### 5. **Input Validation**
- Query parameter bounds checking
- Ethereum address format validation
- URL structure validation

## Running Tests

```bash
# Run all integration tests (recommended)
python -m pytest tests/test_api_routes_phase2_integration.py -v

# Run specific test classes
python -m pytest tests/test_api_routes_phase2_integration.py::TestAPIEndpointsIntegration -v

# Run basic tests with real dependencies
python -m pytest tests/test_api_routes_phase2.py -v

# Run with coverage
python -m pytest tests/test_api_routes_phase2_integration.py --cov=app.api
```

## Mock Configuration

The integration tests use FastAPI dependency overrides to inject mocked dependencies:
- **AgentCoordinator**: Mocked with predefined alpha analysis responses
- **PolymarketClient**: Mocked with sample market data
- **External API calls**: Patched to prevent actual network requests

## Test Data

Tests use realistic mock data that matches production scenarios:
- Political prediction markets (Trump 2024 election)
- Trader portfolios with $500k+ values
- Success rates around 78% with statistical significance
- Portfolio allocations from 10-22%
- Multi-agent consensus with confidence scores

## Production Readiness

These tests ensure the API endpoints are production-ready by validating:
- ✅ AgentCoordinator integration
- ✅ Response time requirements  
- ✅ Error handling robustness
- ✅ Input validation security
- ✅ Response format consistency
- ✅ Concurrent request handling
- ✅ Agent voting system functionality