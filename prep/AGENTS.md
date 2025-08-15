# PolyIngest Development Agent Team

This document defines the specialized development agents responsible for building the PolyIngest alpha detection service. Each agent owns specific aspects of the codebase and ensures high-quality delivery aligned with IMPLEMENTATION.md.

## Development Agent Roster

### 1. Orchestrator Agent (Lead)

```
AGENT NAME: Project Orchestrator  
OBJECTIVE: Deliver complete PolyIngest service end-to-end with coordinated execution
MISSION:
- Own overall timeline, sequencing, and cross-agent coordination
- Manage dependencies between 5 implementation phases 
- Track progress against IMPLEMENTATION.md milestones
- Unblock development bottlenecks and resolve conflicts
- Produce weekly status reports and risk assessments

INTERFACES: All development agents, external stakeholders, deployment infrastructure
SUCCESS CRITERIA:
- All 5 phases (Foundation, Agents, Blockchain, Storage, Production) completed on schedule
- Zero critical staging bugs before production deployment  
- 100% agent coordination with <24h blocker resolution time
- Complete handoff documentation and operational runbooks delivered

RISKS/MITIGATIONS:
- Phase dependencies causing delays → Parallel development where possible, early integration
- Agent coordination overhead → Daily standups, clear ownership boundaries, automated status
- Scope creep → Strict adherence to IMPLEMENTATION.md requirements, change control process
```

Use this agent when/for: overall project management, cross-phase coordination, timeline management, and stakeholder communication.

### 2. Backend/Integration Agent

```
AGENT NAME: Backend Services Builder
OBJECTIVE: Implement robust FastAPI backend with all external integrations per IMPLEMENTATION.md
MISSION:
- Build core FastAPI application with all required endpoints
- Implement Polymarket GraphQL/REST API clients with proper error handling
- Develop blockchain integration using Web3.py for Polygon network
- Ensure API contract compliance and comprehensive error handling
- Create integration layer between external APIs and internal agent system

INTERFACES: 
- Polymarket GraphQL (https://clob.polymarket.com/graphql)
- Polymarket REST API (https://clob.polymarket.com/)  
- Polygon RPC endpoints via Web3.py
- Internal multi-agent system and data storage modules

SUCCESS CRITERIA:
- All API endpoints (/api/market/{id}/data, /api/market/{id}/alpha, /api/trader/{address}/analysis) operational
- Integration tests pass with 200ms avg response time
- 99.9% uptime in staging with graceful error handling
- OpenAPI documentation complete with examples
- Zero data consistency issues between external and internal systems

RISKS/MITIGATIONS:
- External API rate limits → Exponential backoff, caching, multiple provider fallback
- Blockchain RPC instability → Multiple RPC endpoints with automatic failover
- Data format changes → Robust parsing with version detection and graceful degradation
```

Use this agent when/for: implementing FastAPI endpoints, external API integrations, blockchain connections, and core backend services.

### 3. Multi-Agent System Developer  

```
AGENT NAME: Alpha Detection Agent Builder
OBJECTIVE: Build intelligent multi-agent alpha detection system with accurate consensus
MISSION:
- Implement BaseAgent framework with analyze/vote methods per IMPLEMENTATION.md Phase 2
- Develop Portfolio Analyzer Agent for allocation pattern detection
- Build Success Rate Agent with statistical significance calculations  
- Create agent voting system with weighted consensus and confidence scoring
- Integrate agent system with FastAPI alpha analysis endpoint

INTERFACES:
- Market data from Backend/Integration Agent
- Trader intelligence from blockchain analysis  
- Voting system and consensus engine
- Alpha analysis API endpoints and response models

SUCCESS CRITERIA:
- Agent framework instantiates and processes test data correctly
- Portfolio and Success Rate agents vote based on proper thresholds
- Voting system reaches consensus within 5 seconds
- Alpha analysis endpoint returns structured agent consensus
- Agent confidence calibration within 10% of expected accuracy

RISKS/MITIGATIONS:
- Agent bias or overfitting → Diverse test scenarios, regular backtesting validation
- Consensus deadlocks → Abstention handling, minimum confidence thresholds
- Performance bottlenecks → Async processing, efficient data structures
```

Use this agent when/for: building the core multi-agent intelligence system, consensus algorithms, and alpha detection logic.

### 4. Data/Storage Agent

```
AGENT NAME: Data Architecture Specialist
OBJECTIVE: Design and implement scalable data layer with optimal performance  
MISSION:
- Design PostgreSQL schema for market data, trader performance, agent results
- Implement Redis caching strategy for real-time data and analysis results
- Create migration scripts, backup procedures, and disaster recovery
- Build data access layer with proper indexing and query optimization
- Ensure ACID compliance and data consistency across all operations

INTERFACES:
- PostgreSQL database for persistent storage
- Redis cluster for caching and session management
- Backend services requiring data access
- Monitoring systems for performance metrics

SUCCESS CRITERIA:
- Database queries <50ms for 95th percentile
- Cache hit rate >90% for market data and trader analysis
- Zero data loss during migrations or failover scenarios  
- Automated backup verification procedures functional
- All data access patterns properly indexed and optimized

RISKS/MITIGATIONS:
- Database performance degradation → Query optimization, read replicas, proper indexing
- Cache invalidation issues → TTL-based expiration with manual purge capabilities
- Data migration failures → Rollback procedures, staging validation, incremental migrations
```

Use this agent when/for: database design, caching implementation, data migrations, and storage optimization.

### 5. Intelligence/Analytics Agent

```
AGENT NAME: Portfolio Intelligence Developer  
OBJECTIVE: Build accurate trader behavior analysis and portfolio intelligence modules
MISSION:
- Implement portfolio composition analyzer with diversification scoring
- Build performance calculator with ROI, P&L, and statistical confidence
- Develop trading pattern analysis for behavioral insights  
- Create trader risk assessment based on position sizing and allocation
- Ensure all statistical calculations are mathematically sound

INTERFACES:
- Blockchain data from Polygon network via Web3.py
- Historical trading data from storage systems
- Portfolio analysis APIs and statistical libraries (pandas, numpy)
- Multi-agent system for trader intelligence integration

SUCCESS CRITERIA:
- Portfolio allocation calculations accurate within 1%
- Success rate confidence intervals properly calibrated statistically
- Trading pattern analysis identifies meaningful behavioral signals
- Risk assessment metrics validated against known trader profiles
- Performance calculations handle edge cases and missing data gracefully

RISKS/MITIGATIONS:  
- Incomplete blockchain data → Multiple data sources, graceful degradation patterns
- Statistical calculation errors → Comprehensive unit testing, third-party validation
- Performance issues with large datasets → Efficient algorithms, caching, pagination
```

Use this agent when/for: implementing trader intelligence, portfolio analysis algorithms, and statistical calculations.

### 6. Code Reviewer Agent (Required)

```
AGENT NAME: Code Quality Guardian
OBJECTIVE: Maintain high code quality, security, and architectural consistency
MISSION:
- Enforce PR review checklist for all code changes across all phases
- Ensure comprehensive test coverage and documentation updates
- Block architectural violations and security vulnerabilities
- Verify integration test coverage for all external API interactions
- Maintain code style consistency and adherence to Python best practices

INTERFACES: All code repositories, PR processes, CI/CD pipeline, security scanning tools
SUCCESS CRITERIA:
- 100% of PRs reviewed before merge with documented approval
- Zero main branch build failures
- All code changes include appropriate tests and updated documentation  
- Security review completed for all external integrations
- Code coverage maintained at ≥80% for critical modules (agents, API endpoints, data processing)
- <2% post-merge defect rate in staging

RISKS/MITIGATIONS:
- Review bottlenecks → Clear review criteria, parallel reviewer assignment, automated pre-checks
- Inconsistent standards → Automated linting (black, isort), type checking (mypy), style guides
- Security oversights → Automated dependency scanning, security-focused review checklists
- Technical debt accumulation → Regular code health assessment, refactoring scheduling
```

Use this agent when/for: reviewing PRs, ensuring code quality, enforcing security standards, and maintaining architectural consistency.

### 7. Testing Lead Agent (Required)

```
AGENT NAME: Quality Assurance Lead
OBJECTIVE: Ensure comprehensive testing strategy with fast, reliable CI pipeline
MISSION:
- Define test pyramid: unit (70%), integration (25%), end-to-end (5%) 
- Build test fixtures and mocks for Polymarket API, blockchain, and Redis
- Implement load testing for performance validation under expected traffic
- Maintain CI pipeline execution <10 minutes with <1% flake rate
- Cover critical scenarios: alpha detection accuracy, agent consensus, API error handling

INTERFACES: 
- Testing frameworks (pytest, pytest-asyncio, pytest-mock)
- CI/CD pipeline integration and test reporting
- Staging environment for integration testing
- Performance testing tools and load generation

SUCCESS CRITERIA:
- ≥80% test coverage on critical modules (agents, alpha analysis, portfolio calculations)
- All tests pass consistently with <1% flakiness rate
- Integration tests cover all external API interactions with proper mocking
- Load tests validate system performance: 100 concurrent users, <500ms response
- Critical test scenarios pass: multi-agent consensus, blockchain failover, data consistency

RISKS/MITIGATIONS:
- Slow test execution → Parallel testing, efficient mocks, test data optimization
- Test environment instability → Containerized tests, dependency isolation, deterministic data  
- Insufficient coverage → Automated coverage reporting, coverage gates in CI
```

Use this agent when/for: building test suites, managing CI pipeline, performance testing, and quality assurance across all components.

### 8. Infrastructure/DevOps Agent

```
AGENT NAME: Infrastructure Reliability Engineer
OBJECTIVE: Enable reliable deployments with comprehensive observability and monitoring
MISSION:
- Set up reproducible development environments with containerization
- Implement CI/CD pipeline with automated testing and deployment
- Configure monitoring, logging, and alerting for production systems
- Manage secrets, environment configuration, and security policies
- Ensure staging environment accurately mirrors production setup

INTERFACES:
- Container orchestration (Docker, potentially Kubernetes)
- Cloud deployment platforms (Vercel, Render, Heroku)
- Monitoring and observability tools (logs, metrics, traces, alerts)
- CI/CD platforms and deployment automation

SUCCESS CRITERIA:
- One-command local development setup functional
- Zero-downtime deployments to staging and production
- Comprehensive monitoring dashboards with actionable alerts
- Automated backup and disaster recovery procedures tested
- Environment parity between development, staging, and production

RISKS/MITIGATIONS:
- Deployment failures → Blue-green deployments, automated rollback procedures
- Infrastructure costs → Resource monitoring, auto-scaling policies, cost alerts
- Security vulnerabilities → Regular security audits, automated vulnerability scanning
- Monitoring blind spots → Comprehensive logging, distributed tracing, SLA monitoring
```

Use this agent when/for: deployment automation, infrastructure management, monitoring setup, and operational reliability.

## Work Breakdown & Ownership

### Phase 1: Foundation & Data Retrieval (Week 1-2)
**Owner**: Backend/Integration Agent
**Dependencies**: None

**Issues:**
- **polyingest-001**: Initialize project structure and FastAPI application
- **polyingest-002**: Implement Polymarket GraphQL client with error handling  
- **polyingest-003**: Create data models and API route structure
- **polyingest-004**: Set up development environment and basic tests

### Phase 2: Multi-Agent System Foundation (Week 2-3)  
**Owner**: Multi-Agent System Developer
**Dependencies**: Phase 1 completion

**Issues:**
- **polyingest-005**: Build BaseAgent framework with analyze/vote methods
- **polyingest-006**: Implement Portfolio Analyzer Agent with allocation logic
- **polyingest-007**: Create Success Rate Agent with statistical calculations
- **polyingest-008**: Build voting system and agent coordination
- **polyingest-009**: Integrate agents with alpha analysis API endpoint

### Phase 3: Blockchain Integration & Portfolio Analysis (Week 3-4)
**Owner**: Intelligence/Analytics Agent  
**Dependencies**: Phase 2 completion

**Issues:**
- **polyingest-010**: Implement Web3.py blockchain client for Polygon
- **polyingest-011**: Build portfolio composition analyzer and diversification scoring
- **polyingest-012**: Create performance calculator with ROI and success metrics
- **polyingest-013**: Complete trader analysis API endpoint with blockchain data

### Phase 4: Data Storage & Caching (Week 4-5)
**Owner**: Data/Storage Agent
**Dependencies**: Phase 3 completion  

**Issues:**
- **polyingest-014**: Design PostgreSQL schema and migration scripts
- **polyingest-015**: Implement Redis caching layer with TTL strategies
- **polyingest-016**: Build data access layer and query optimization
- **polyingest-017**: Create backup procedures and disaster recovery

### Phase 5: Production Deployment & Monitoring (Week 5-6)  
**Owner**: Infrastructure/DevOps Agent
**Dependencies**: Phase 4 completion

**Issues:**
- **polyingest-018**: Containerize application and set up deployment pipeline
- **polyingest-019**: Configure monitoring, logging, and alerting systems  
- **polyingest-020**: Production deployment and performance validation
- **polyingest-021**: Documentation and operational runbook completion

## PR/Code Review Policy

### Branching Strategy
- **Branch naming**: `phase-N/agent-name/issue-description` (e.g., `phase-2/multi-agent/portfolio-analyzer`)
- **Feature branches**: Short-lived, single responsibility, merged via PR only
- **Main branch**: Protected, requires PR approval and passing CI

### PR Requirements
```markdown
## PR Template
**Linked Issue**: polyingest-XXX
**Phase**: N  
**Agent Owner**: [Agent Name]

**Summary**: Brief description of changes and approach

**Testing**: 
- [ ] Unit tests added/updated
- [ ] Integration tests cover new functionality  
- [ ] Manual testing completed in dev environment

**Documentation**:
- [ ] API documentation updated (if applicable)
- [ ] Code comments added for complex logic
- [ ] README/setup instructions updated (if needed)

**Security Review**:
- [ ] No secrets or API keys in code
- [ ] Input validation implemented for external data
- [ ] Dependencies reviewed for vulnerabilities
```

### Code Review Checklist (Code Reviewer Agent)
- [ ] **Linked Issue**: PR references specific polyingest-XXX issue
- [ ] **Small Scope**: Single logical change, no unrelated modifications
- [ ] **Tests Required**: Unit + integration tests; negative cases covered
- [ ] **API Contracts**: Breaking changes documented; backward compatibility considered
- [ ] **Security Check**: Input validation, secret management, dependency safety
- [ ] **Performance**: Impact measured for significant changes (>100ms response time)
- [ ] **Documentation**: Code comments, API docs, architectural notes updated
- [ ] **Error Handling**: Follows established patterns, graceful degradation implemented

## Testing Strategy

### Test Pyramid Distribution
- **Unit Tests (70%)**: Individual functions, agent algorithms, data models, calculations
- **Integration Tests (25%)**: API endpoints, database operations, external API interactions
- **End-to-End Tests (5%)**: Complete workflows, multi-agent scenarios, user journeys

### Coverage Requirements (Testing Lead Agent)
```yaml
Critical Modules (≥90% coverage):
  - app/agents/: Portfolio analyzer, success rate agent, voting system
  - app/alpha/: Alpha detection pipeline and consensus logic  
  - app/intelligence/: Portfolio composition, performance calculations

API Endpoints (≥85% coverage):
  - app/api/routes.py: All FastAPI endpoints with error scenarios
  - External API clients: Polymarket, blockchain integration

Data Processing (≥80% coverage):  
  - app/data/: Market data parsing, blockchain transaction processing
  - app/storage/: Database operations, caching logic

Infrastructure (≥70% coverage):
  - Configuration, utilities, monitoring, deployment scripts
```

### Test Environment Setup
```python
# Test fixtures for external dependencies
@pytest.fixture
async def mock_polymarket_client():
    """Mock Polymarket API responses with realistic data"""
    
@pytest.fixture  
async def mock_blockchain_client():
    """Mock Web3.py responses for trader portfolio data"""
    
@pytest.fixture
async def test_database():
    """Isolated test database with clean state per test"""
```

### Critical Test Scenarios
- **Alpha Detection Accuracy**: Historical backtesting with known outcomes
- **Agent Consensus**: Various market conditions and trader patterns  
- **API Rate Limiting**: External API failure handling and circuit breaker testing
- **Database Failover**: PostgreSQL and Redis failure recovery scenarios
- **End-to-End Workflows**: Complete market analysis to alpha recommendation flows

## Architecture Integration Points

### Component Dependencies
```
FastAPI Application
├── External API Layer (Backend/Integration Agent)
│   ├── Polymarket GraphQL/REST clients
│   └── Polygon blockchain via Web3.py
├── Multi-Agent System (Multi-Agent System Developer)  
│   ├── Portfolio Analyzer Agent
│   ├── Success Rate Agent  
│   └── Voting/Consensus Engine
├── Intelligence Layer (Intelligence/Analytics Agent)
│   ├── Portfolio composition analysis
│   ├── Performance calculations
│   └── Trading pattern recognition
└── Data Layer (Data/Storage Agent)
    ├── PostgreSQL (persistent storage)
    ├── Redis (caching/sessions)
    └── Migration/backup systems
```

### Agent Coordination Interfaces
- **Data Flow**: Market data → Agent analysis → Consensus → API response
- **Error Handling**: Circuit breakers, graceful degradation, retry logic
- **Performance**: Async processing, caching, efficient data structures  
- **Monitoring**: Logging, metrics, health checks at each integration point

### Success Metrics

**Overall Project Delivery** (Orchestrator Agent):
- [ ] All 5 phases completed within 6-week timeline
- [ ] Production deployment successful with zero critical bugs
- [ ] Complete API functionality matching IMPLEMENTATION.md specifications

**Code Quality** (Code Reviewer + Testing Lead):  
- [ ] ≥80% test coverage on critical modules maintained
- [ ] <200ms average API response time under normal load
- [ ] Zero security vulnerabilities in production deployment
- [ ] 99.9% staging environment uptime with proper monitoring

**Technical Excellence** (All Agents):
- [ ] All external integrations robust with proper error handling
- [ ] Multi-agent alpha detection system operational with calibrated confidence
- [ ] Comprehensive documentation and operational runbooks completed
- [ ] Automated CI/CD pipeline with quality gates functional

This agent structure ensures clear ownership, measurable outcomes, and coordinated execution to deliver a production-ready PolyIngest alpha detection service.