# Research Instructions for PolyIngest

## Overview

This document provides instructions for conducting comprehensive research across the PolyIngest codebase to answer questions by spawning parallel sub-agents and synthesizing their findings.

## Initial Setup

When research is requested, respond with:
```
I'm ready to research the PolyIngest codebase. Please provide your research question or area of interest, and I'll analyze it thoroughly by exploring relevant components and connections.
```

Then wait for the user's research query.

## Research Process

### Step 1: Read Directly Mentioned Files

- If the user mentions specific files (docs, configs, JSON), read them FULLY first
- **IMPORTANT**: Use the Read tool WITHOUT limit/offset parameters to read entire files
- **CRITICAL**: Read these files yourself in the main context before spawning any sub-tasks
- This ensures you have full context before decomposing the research

### Step 2: Analyze and Decompose the Research Question

- Break down the user's query into composable research areas
- Take time to think about the underlying patterns, connections, and architectural implications
- Identify specific components, patterns, or concepts to investigate
- Create a research plan using TodoWrite to track all subtasks
- Consider which directories, files, or architectural patterns are relevant

### Step 3: Spawn Parallel Sub-Agent Tasks

Create multiple Task agents to research different aspects concurrently:

**For codebase research:**
- Use the **codebase-locator** agent to find WHERE files and components live
- Use the **codebase-analyzer** agent to understand HOW specific code works
- Use the **codebase-pattern-finder** agent if you need examples of similar implementations

**For documentation:**
- Use the **docs-locator** agent to discover what documents exist about the topic
- Use the **docs-analyzer** agent to extract key insights from specific documents

**For web research (only if user explicitly asks):**
- Use the **web-search-researcher** agent for external documentation and resources
- If you use web-research agents, instruct them to return LINKS with their findings
- Include those links in your final report

**Agent Usage Guidelines:**
- Start with locator agents to find what exists
- Then use analyzer agents on the most promising findings
- Run multiple agents in parallel when they're searching for different things
- Each agent knows its job - just tell it what you're looking for
- Don't write detailed prompts about HOW to search - the agents already know

### Step 4: Wait and Synthesize Findings

- **IMPORTANT**: Wait for ALL sub-agent tasks to complete before proceeding
- Compile all sub-agent results (both codebase and documentation findings)
- Prioritize live codebase findings as primary source of truth
- Use documentation findings as supplementary historical context
- Connect findings across different components
- Include specific file paths and line numbers for reference
- Highlight patterns, connections, and architectural decisions
- Answer the user's specific questions with concrete evidence

### Step 5: Gather Metadata

Run appropriate commands to gather:
- Current date and time with timezone
- Git commit hash
- Current branch name
- Repository information

### Step 6: Generate Research Document

Create a structured document with YAML frontmatter:

```markdown
---
date: [Current date and time with timezone in ISO format]
researcher: [Researcher name]
git_commit: [Current commit hash]
branch: [Current branch name]
repository: [Repository name]
topic: "[User's Question/Topic]"
tags: [research, codebase, relevant-component-names]
status: complete
last_updated: [Current date in YYYY-MM-DD format]
last_updated_by: [Researcher name]
---

# Research: [User's Question/Topic]

**Date**: [Current date and time with timezone]
**Researcher**: [Researcher name]
**Git Commit**: [Current commit hash]
**Branch**: [Current branch name]
**Repository**: [Repository name]

## Research Question
[Original user query]

## Summary
[High-level findings answering the user's question]

## Detailed Findings

### [Component/Area 1]
- Finding with reference ([file.ext:line](link))
- Connection to other components
- Implementation details

### [Component/Area 2]
...

## Code References
- `path/to/file.py:123` - Description of what's there
- `another/file.ts:45-67` - Description of the code block

## Architecture Insights
[Patterns, conventions, and design decisions discovered]

## Historical Context
[Relevant insights from documentation with references]

## Related Research
[Links to other research documents]

## Open Questions
[Any areas that need further investigation]
```

### Step 7: Add GitHub Permalinks (if applicable)

- Check if on main branch or if commit is pushed
- If on main/master or pushed, generate GitHub permalinks
- Replace local file references with permalinks in the document

### Step 8: Present Findings

- Present a concise summary of findings to the user
- Include key file references for easy navigation
- Ask if they have follow-up questions or need clarification

### Step 9: Handle Follow-up Questions

- If the user has follow-up questions, append to the same research document
- Update the frontmatter fields `last_updated` and `last_updated_by`
- Add `last_updated_note: "Added follow-up research for [brief description]"`
- Add a new section: `## Follow-up Research [timestamp]`
- Spawn new sub-agents as needed for additional investigation

## Important Notes

### Research Guidelines
- Always use parallel Task agents to maximize efficiency and minimize context usage
- Always run fresh codebase research - never rely solely on existing research documents
- Focus on finding concrete file paths and line numbers for developer reference
- Research documents should be self-contained with all necessary context
- Each sub-agent prompt should be specific and focused on read-only operations
- Consider cross-component connections and architectural patterns
- Include temporal context (when the research was conducted)

### Critical Ordering
- **ALWAYS** read mentioned files first before spawning sub-tasks (step 1)
- **ALWAYS** wait for all sub-agents to complete before synthesizing (step 4)
- **ALWAYS** gather metadata before writing the document (step 5 before step 6)
- **NEVER** write the research document with placeholder values

### File and Path Handling
- Always read mentioned files FULLY (no limit/offset) before spawning sub-tasks
- Document all file paths accurately for navigation and editing
- Keep the main agent focused on synthesis, not deep file reading
- Encourage sub-agents to find examples and usage patterns, not just definitions

### Documentation Consistency
- Always include frontmatter at the beginning of research documents
- Keep frontmatter fields consistent across all research documents
- Update frontmatter when adding follow-up research
- Use snake_case for multi-word field names (e.g., `last_updated`, `git_commit`)
- Tags should be relevant to the research topic and components studied

## PolyIngest-Specific Research Areas

When researching the PolyIngest codebase, pay special attention to:

### Core Components
- **API Layer** (`app/api/`): FastAPI endpoints for market data, alpha analysis, trader analysis
- **Data Retrieval** (`app/data/`): Polymarket API clients, on-chain data, historical aggregation
- **Multi-Agent System** (`app/agents/`): Specialized analysis agents and consensus mechanisms
- **Trader Intelligence** (`app/intelligence/`): Behavior modeling and performance analysis
- **Alpha Detection** (`app/alpha/`): Scoring models and alert generation
- **Storage & Caching** (`app/storage/`): Redis and PostgreSQL integration

### Key Data Sources
- Polymarket GraphQL API (`https://clob.polymarket.com/graphql`)
- Polymarket REST API (`https://clob.polymarket.com/`)
- Polygon blockchain data for portfolio analysis
- Historical trading data and market outcomes

### Alpha Detection Criteria
- High Portfolio Allocation (>10% of portfolio)
- Proven Success Rate (>70% historical win rate)
- Position Size Significance
- Timing Analysis (early vs. late entry)
- Market Context (liquidity, volatility, time to resolution)

### Multi-Agent Architecture
- Portfolio Analyzer Agent
- Success Rate Agent
- Volume Analysis Agent
- Market Sentiment Agent
- Technical Analysis Agent
- Consensus Agent

Research should focus on understanding how these components work together to identify trading opportunities ("alpha") in Polymarket prediction markets.