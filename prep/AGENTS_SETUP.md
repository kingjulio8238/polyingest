## Agents Setup Guide

### Objective
Review `IMPLEMENTATION.md` and design a multi-agent team to deliver the codebase end-to-end. Define ownership, workflows, guardrails, and measurable outcomes. Include a Code Reviewer and a Testing Lead.

### Inputs
- `IMPLEMENTATION.md` (primary source of truth)
- `RESEARCH.md`, `CREATE_PLAN.md` (context and constraints)
- Current repository structure and conventions

### Final Deliverables
- Agent roster with roles, responsibilities, and success criteria
- Work breakdown (epics/issues) mapped to owners and milestones
- PR/Code Review policy and CI testing policy
- Test strategy with coverage goals and critical scenarios
- Architecture notes and integration points aligned to `IMPLEMENTATION.md`

### Required Roles
1) Orchestrator (Lead)
- Owns overall plan, sequencing, risks, and cross-agent coordination
- Produces weekly plan, dependency map, and unblock plan

2) Backend/Integration Agent
- Implements core APIs/services and integrations described in `IMPLEMENTATION.md`
- Documents public interfaces and error contracts; ensures idempotency and retries

3) Data/Storage Agent
- Designs schemas, migrations, indexing; owns data access utilities
- Ensures performance, consistency, backup/restore procedures

4) Infra/DevOps Agent
- Reproducible environments, CI/CD, secrets, and deployment scripts
- Observability: logs, metrics, traces, alerts, dashboards

5) Documentation Agent
- Developer guides, runbooks, user docs, change logs, ADRs

6) Code Reviewer Agent (Required)
- Enforces style, correctness, security, and architecture alignment in all PRs
- Blocks risky changes; ensures tests and docs are updated

7) Testing Lead Agent (Required)
- Defines test pyramid, coverage thresholds, and critical-path scenarios
- Builds fixtures/mocks; ensures fast and reliable CI

### Optional/Specialized Roles
- Performance & Optimization Agent (profiling, latency/throughput improvements)
- Security & Compliance Agent (threat modeling, dependency scanning, secrets policy)
- Frontend/UX Agent (if user-facing surfaces exist)
- Release Manager (versioning, release notes, rollout strategy)

### Workflow
1) Discovery
- Read `IMPLEMENTATION.md`; extract components, APIs, data flows, integrations
- Produce an architecture/component map and interface contracts

2) Planning & Ownership
- Convert architecture into epics/issues with acceptance criteria
- Assign each epic to an agent; define dependencies and milestones

3) Execution Loop
- Small, focused PRs with tests and docs; feature flags where appropriate
- Code Reviewer applies PR checklist; Testing Lead enforces quality and coverage
- CI gates: lint, type-check, unit/integration tests; no red merges

4) Integration & Hardening
- End-to-end tests, performance checks, security scans; fix regressions
- Observability dashboards updated; SLOs validated

5) Sign-off
- Acceptance criteria verified per epic; docs and ADRs updated
- Release candidate built; handoff/runbooks prepared

### Quality Bar
- Code: readable, typed (where applicable), clear error handling, minimal side effects
- Tests: ≥ 80% coverage on critical modules; cover happy-path, edge, and failure cases
- Security: no secrets in repo; input validation at boundaries; deps scanned
- Performance: baseline metrics captured; regressions require ADR and approval
- Docs: setup, operations, and troubleshooting up to date

### Policies
#### Branching & PRs
- Short-lived feature branches; one logical change per PR
- PR must include: summary, linked issue, screenshots/logs (if relevant), tests, docs updates

#### Reviews & Merging
- At least one approval from Code Reviewer for all code changes
- CI must pass: lint, type-check, unit tests, integration tests (as configured)

### Templates
#### Agent Definition
```
AGENT NAME: <Concise role name>
OBJECTIVE: <Outcome this agent owns>
MISSION: <Key tasks and owned files/services>
INTERFACES: <APIs, modules, external systems>
SUCCESS CRITERIA: <Measurable, verifiable outcomes>
RISKS/MITIGATIONS: <Top risks and mitigations>
```

#### Issue
```
Title: <Component>: <Action>
Context: <Why this change is needed>
Acceptance Criteria:
- [ ] Behavior A validated via test X
- [ ] Behavior B documented in Y
Out of Scope:
Assignees/Reviewers:
```

#### PR Checklist (for Code Reviewer)
```
- [ ] Linked issue and clear summary
- [ ] Small, focused changes; no unrelated diffs
- [ ] Tests: unit + integration; negative cases included
- [ ] API contracts documented; breaking changes called out
- [ ] Security considerations addressed (inputs, secrets, deps)
- [ ] Performance impact considered/measured if relevant
- [ ] Docs updated (README/runbook/ADR)
```

#### Test Plan (owned by Testing Lead)
```
Scope:
- Components under test
Test Types:
- Unit, integration, e2e, property-based (if applicable)
Coverage Goals:
- Critical modules ≥ 80%; others ≥ 70%
Tooling:
- Test runner, coverage tool, fixtures, CI steps
Exit Criteria:
- All critical tests pass and flakiness < 1%
```

### Example Agents
1) Code Reviewer Agent
- OBJECTIVE: Keep main stable and high quality
- MISSION: Apply PR checklist; enforce standards; require tests/docs; guard architecture
- SUCCESS CRITERIA: 0 broken main builds; 100% PRs with tests and docs; <2% post-merge defects

2) Testing Lead Agent
- OBJECTIVE: Changes are safe and fast to validate
- MISSION: Define test pyramid; build fixtures/mocks; maintain CI stability and speed
- SUCCESS CRITERIA: ≥ 80% coverage on critical paths; CI time < 10 min; flake rate < 1%

3) Backend/Integration Agent
- OBJECTIVE: Implement and integrate backend per `IMPLEMENTATION.md`
- MISSION: Build APIs/services; error handling, retries, idempotency; document contracts
- SUCCESS CRITERIA: All endpoints pass integration tests; SLOs met; zero critical staging bugs

4) Infra/DevOps Agent
- OBJECTIVE: Reliable builds/deployments with observability
- MISSION: CI/CD; env parity; logs/metrics/traces; secret management
- SUCCESS CRITERIA: Green CI on main; one-command local setup; actionable dashboards

### Execution Checklist
- [ ] Read `IMPLEMENTATION.md` and extract components/APIs/data flows
- [ ] Draft agent roster using the template and assign owners
- [ ] Create issues with acceptance criteria and milestones
- [ ] Establish CI gates and testing policy
- [ ] Start iterative implementation with enforced reviews and tests
- [ ] Run integration/e2e tests and finalize docs before sign-off

### Non-Goals
- Large, unreviewed PRs
- Bypassing tests or merging on red CI

### Definition of Done
- All epics closed with passing CI, documented interfaces, and validated test plans
- Stakeholder review completed; release candidate produced