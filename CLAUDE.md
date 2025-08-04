# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PolyIngest is a web scraping application that mirrors the functionality of "GitIngest" but for Polymarket prediction markets. The application provides a GitIngest-like experience where users simply replace `polymarket.com` with `polyingest.com` in any Polymarket URL.

**Production Usage**:
- User finds market on Polymarket: `https://polymarket.com/event/presidential-election-winner-2028?tid=1754301474937`
- User changes URL to: `https://polyingest.com/event/presidential-election-winner-2028?tid=1754301474937`
- PolyIngest returns formatted plain text optimized for LLM consumption

**Features**:
- Direct URL replacement workflow (mirrors Polymarket URL structure)
- Scrapes dynamic React content from Polymarket
- Extracts market data (Yes/No probabilities, trading volume, liquidity, outcomes)
- Rate limiting and caching for respectful usage
- Support for full Polymarket event URLs with parameters

## Technical Stack

- **Framework**: FastAPI for the web server
- **Scraping**: Selenium with headless Chrome for React/dynamic content + BeautifulSoup for parsing
- **Deployment**: Designed for platforms like Vercel, Render, or Heroku with ChromeDriver support
- **Libraries**: requests, beautifulsoup4, selenium, fastapi, uvicorn

## Development Commands

Since this is a new repository with only a README, there are no established build/test commands yet. When implementing:

- **Local Development**: `python app.py` (should include uvicorn.run() in main block)
- **Install Dependencies**: `pip install requests beautifulsoup4 selenium fastapi uvicorn`
- **Local Testing**: Visit `http://localhost:8000/event/presidential-election-winner-2028?tid=1754301474937` after starting the server

## Architecture Notes

The application should be structured as a single FastAPI application (`app.py`) with:

1. **URL Handling**: FastAPI path parameter to capture full market names
2. **Scraping Engine**: Selenium-based scraper with fallback to requests+BeautifulSoup
3. **Data Extraction**: BeautifulSoup parsers for market data (needs real HTML inspection)
4. **Response Formatting**: Plain text output optimized for LLM consumption
5. **Error Handling**: Graceful failures with plain text error messages
6. **Performance**: Caching mechanism and rate limiting considerations

## Important Implementation Notes

- HTML selectors optimized for Polymarket's React-based structure
- Include delays after page loads for React content rendering
- Respect Polymarket's terms of service and implement rate limiting
- Use headless Chrome with no-sandbox and disable-dev-shm-usage for deployment
- Handle URL paths and query parameters properly (event paths + tid)
- Design for Polymarket's dynamic market structure

## Output Format

The application should return structured plain text like:
```
## Polymarket Analysis
- Title: [title]
- Yes Probability: [value]
- No Probability: [value]
- Trading Volume: [value]
- Liquidity: [value]
- Total Volume: [value]

## Market Description
- [Market description]

## Trading Outcomes
- Outcome 1: [details]
- Outcome 2: [details]
```

## Deployment Considerations

- ChromeDriver setup required in deployment environment
- Consider buildpacks for Render/Heroku deployment
- Environment variables for configuration
- Caching strategy (simple dict or Redis for production)