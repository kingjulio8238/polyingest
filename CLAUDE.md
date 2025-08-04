# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HashIngest is a web scraping application that mirrors the functionality of "GitIngest" but for Hashdive market analysis. The application provides a GitIngest-like experience where users simply replace `hashdive.com` with `hashingest.com` in any Hashdive market URL.

**Production Usage**:
- User finds market on Hashdive: `https://hashdive.com/Analyze_Market?market=Xi+Jinping+out+in+2025%3F`
- User changes URL to: `https://hashingest.com/Analyze_Market?market=Xi+Jinping+out+in+2025%3F`
- HashIngest returns formatted plain text optimized for LLM consumption

**Features**:
- Direct URL replacement workflow (no complex routing needed)
- Scrapes dynamic Streamlit content from Hashdive
- Extracts market data (probabilities, trading volume, liquidity, positions, trends)
- Rate limiting and caching for respectful usage
- Fallback support for simple market names

## Technical Stack

- **Framework**: FastAPI for the web server
- **Scraping**: Selenium with headless Chrome for dynamic content + BeautifulSoup for parsing
- **Deployment**: Designed for platforms like Vercel, Render, or Heroku with ChromeDriver support
- **Libraries**: requests, beautifulsoup4, selenium, fastapi, uvicorn

## Development Commands

Since this is a new repository with only a README, there are no established build/test commands yet. When implementing:

- **Local Development**: `python app.py` (should include uvicorn.run() in main block)
- **Install Dependencies**: `pip install requests beautifulsoup4 selenium fastapi uvicorn`
- **Local Testing**: Visit `http://localhost:8000/{market}` after starting the server

## Architecture Notes

The application should be structured as a single FastAPI application (`app.py`) with:

1. **URL Handling**: FastAPI path parameter to capture full market names
2. **Scraping Engine**: Selenium-based scraper with fallback to requests+BeautifulSoup
3. **Data Extraction**: BeautifulSoup parsers for market data (needs real HTML inspection)
4. **Response Formatting**: Plain text output optimized for LLM consumption
5. **Error Handling**: Graceful failures with plain text error messages
6. **Performance**: Caching mechanism and rate limiting considerations

## Important Implementation Notes

- HTML selectors need real-world validation by inspecting actual Hashdive pages
- Include 3-5 second delays after page loads for JS content rendering
- Respect Hashdive's terms of service and implement rate limiting
- Use headless Chrome with no-sandbox and disable-dev-shm-usage for deployment
- Handle URL encoding properly for market names with spaces/special characters
- Design for extensibility (future user analysis features)

## Output Format

The application should return structured plain text like:
```
## Market Analysis
- Title: [title]
- Human Probability: [value]
- AI Probability: [value]
- Trading Volume: [value]
- Liquidity: [value]
- Smart Score: [value]

## Positions
- Position 1: [details]
- Position 2: [details]

## Trends
- [Textual description of charts/insights]
```

## Deployment Considerations

- ChromeDriver setup required in deployment environment
- Consider buildpacks for Render/Heroku deployment
- Environment variables for configuration
- Caching strategy (simple dict or Redis for production)