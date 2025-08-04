"""
PolyIngest - Web scraping application for Polymarket analysis
Mirrors the functionality of GitIngest but for prediction markets.

IMPORTANT: This application respects Polymarket's terms of service.
Implement rate limiting (max 1 request per minute) and avoid overloading their servers.
"""

import time
import urllib.parse
from typing import Dict, Optional
from datetime import datetime, timedelta

import requests
import uvicorn
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager


app = FastAPI(
    title="PolyIngest",
    description="Extract and format market analysis data from Polymarket",
    version="1.0.0"
)

# Simple in-memory cache for rate limiting and caching responses
cache: Dict[str, Dict] = {}
CACHE_DURATION = 300  # 5 minutes
RATE_LIMIT_DURATION = 60  # 1 minute between requests


def get_chrome_driver() -> webdriver.Chrome:
    """Initialize Chrome driver with appropriate options for deployment."""
    chrome_options = Options()
    # Specify Chrome binary path for macOS
    chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    # Enable JavaScript - required for Streamlit apps
    # chrome_options.add_argument("--disable-javascript")  # REMOVED - JS needed for Streamlit
    
    try:
        # Try to use system chromedriver first (installed via brew)
        from selenium.webdriver.chrome.service import Service
        service = Service()  # Will look for chromedriver in PATH
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        # Fallback to webdriver-manager
        try:
            driver = webdriver.Chrome(
                service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            return driver
        except Exception as e2:
            raise RuntimeError(f"Failed to initialize Chrome driver. System chromedriver error: {str(e)}. WebDriver-manager error: {str(e2)}")


def is_rate_limited(market_key: str) -> bool:
    """Check if we're rate limited for this market."""
    if market_key in cache:
        last_request = cache[market_key].get("last_request")
        if last_request and datetime.now() - last_request < timedelta(seconds=RATE_LIMIT_DURATION):
            return True
    return False


def get_cached_response(market_key: str) -> Optional[str]:
    """Get cached response if it's still valid."""
    if market_key in cache:
        cached_data = cache[market_key]
        if "response" in cached_data and "timestamp" in cached_data:
            if datetime.now() - cached_data["timestamp"] < timedelta(seconds=CACHE_DURATION):
                return cached_data["response"]
    return None


def cache_response(market_key: str, response: str):
    """Cache the response with timestamp."""
    cache[market_key] = {
        "response": response,
        "timestamp": datetime.now(),
        "last_request": datetime.now()
    }


def scrape_with_selenium(url: str) -> str:
    """Scrape dynamic content using Selenium."""
    driver = None
    try:
        driver = get_chrome_driver()
        driver.get(url)
        
        # Wait for page to load - adjust timeout as needed
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Wait for React app to load - look for main content to be populated
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        
        # Additional wait for dynamic content to fully render
        time.sleep(10)
        
        # Check if we're getting actual content or just the loading screen
        page_source = driver.page_source
        if "noscript" in page_source.lower() and len(page_source) < 10000:
            # Still loading, wait a bit more
            time.sleep(10)
            page_source = driver.page_source
        
        return page_source
    
    except TimeoutException:
        raise HTTPException(status_code=408, detail="Page load timeout - Polymarket page may be taking too long to load")
    except WebDriverException as e:
        raise HTTPException(status_code=500, detail=f"WebDriver error: {str(e)}")
    finally:
        if driver:
            driver.quit()


def scrape_with_requests(url: str) -> str:
    """Fallback scraping using requests."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")


def extract_market_data(html_content: str, market_name: str) -> Dict[str, str]:
    """
    Extract market data from Polymarket HTML content.
    
    Polymarket is a React-based application that loads market data dynamically.
    This function looks for React components and market-specific elements.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Initialize data structure
    market_data = {
        'title': market_name,
        'yes_probability': 'N/A',
        'no_probability': 'N/A', 
        'trading_volume': 'N/A',
        'liquidity': 'N/A',
        'total_volume': 'N/A',
        'outcomes': [],
        'description': 'N/A'
    }
    
    try:
        import re
        
        # Extract title from page title or main heading
        title_element = soup.find('title')
        if title_element:
            title_text = title_element.get_text(strip=True)
            if title_text and "Polymarket" in title_text:
                # Clean up the title
                market_data['title'] = title_text.replace(" | Polymarket", "").strip()
        
        # Look for main heading elements
        for header_tag in ['h1', 'h2']:
            headers = soup.find_all(header_tag)
            for header in headers:
                header_text = header.get_text(strip=True)
                if header_text and len(header_text) > 5 and "Polymarket" not in header_text:
                    market_data['title'] = header_text
                    break
            if market_data['title'] != market_name:
                break
        
        # Get all page text for pattern matching
        all_text = soup.get_text()
        
        # Look for percentage values (probabilities)
        percentage_pattern = r'(\d+(?:\.\d+)?%)'
        percentages = re.findall(percentage_pattern, all_text)
        
        if percentages:
            # Polymarket typically shows Yes/No probabilities
            if len(percentages) >= 1:
                market_data['yes_probability'] = percentages[0]
            if len(percentages) >= 2:
                market_data['no_probability'] = percentages[1]
        
        # Look for volume/liquidity values
        # Polymarket shows values like $1.2M, $45.3K, etc.
        volume_pattern = r'\$[\d,]+(?:\.\d+)?[KMB]?'
        volume_values = re.findall(volume_pattern, all_text)
        
        if volume_values:
            # Try to identify volume vs liquidity based on context
            unique_volumes = list(dict.fromkeys(volume_values))  # Remove duplicates while preserving order
            if len(unique_volumes) >= 1:
                market_data['trading_volume'] = unique_volumes[0]
            if len(unique_volumes) >= 2:
                market_data['liquidity'] = unique_volumes[1]
            if len(unique_volumes) >= 3:
                market_data['total_volume'] = unique_volumes[2]
        
        # Look for outcome buttons/options (Yes/No, candidate names, etc.)
        # Polymarket uses buttons for trading outcomes
        outcome_elements = soup.find_all(['button', 'div'], 
                                       string=lambda text: text and any(keyword in text.lower() 
                                       for keyword in ['yes', 'no', 'buy', 'sell']) and len(text.strip()) < 50)
        
        outcomes = []
        for elem in outcome_elements[:10]:
            outcome_text = elem.get_text(strip=True)
            if outcome_text and outcome_text not in outcomes and len(outcome_text) > 1:
                outcomes.append(outcome_text)
        
        # Also look for candidate names or specific outcomes in spans/divs
        candidate_elements = soup.find_all(['span', 'div'], 
                                         class_=lambda x: x and any(term in ' '.join(x).lower() if isinstance(x, list) else term in x.lower() 
                                         for term in ['outcome', 'option', 'candidate']) if x else False)
        
        for elem in candidate_elements[:5]:
            candidate_text = elem.get_text(strip=True)
            if candidate_text and len(candidate_text) < 100 and candidate_text not in outcomes:
                outcomes.append(candidate_text)
        
        if outcomes:
            market_data['outcomes'] = outcomes
        else:
            market_data['outcomes'] = ["Yes", "No"]  # Default for binary markets
        
        # Look for market description
        # Check for meta description or paragraph elements
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            market_data['description'] = meta_desc.get('content')[:200]
        else:
            # Look for paragraph elements that might contain description
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                p_text = p.get_text(strip=True)
                if p_text and len(p_text) > 20 and len(p_text) < 500:
                    market_data['description'] = p_text[:200]
                    break
        
        # If we still have the original market_name as title, try to clean it up
        if market_data['title'] == market_name:
            # Convert URL-style path to readable title
            readable_title = market_name.replace('-', ' ').replace('_', ' ').title()
            market_data['title'] = f"Market: {readable_title}"
        
    except Exception as e:
        # If extraction fails, return what we have with error info
        market_data['error'] = f"Extraction error: {str(e)}"
    
    return market_data


def format_market_analysis(market_data: Dict[str, str]) -> str:
    """Format extracted data into LLM-ready plain text."""
    
    output = []
    output.append("## Polymarket Analysis")
    output.append(f"- Title: {market_data['title']}")
    output.append(f"- Yes Probability: {market_data['yes_probability']}")
    output.append(f"- No Probability: {market_data['no_probability']}")
    output.append(f"- Trading Volume: {market_data['trading_volume']}")
    output.append(f"- Liquidity: {market_data['liquidity']}")
    output.append(f"- Total Volume: {market_data['total_volume']}")
    output.append("")
    
    output.append("## Market Description")
    output.append(f"- {market_data['description']}")
    output.append("")
    
    output.append("## Trading Outcomes")
    if market_data['outcomes']:
        for i, outcome in enumerate(market_data['outcomes'], 1):
            output.append(f"- Outcome {i}: {outcome}")
    else:
        output.append("- No outcome data available")
    output.append("")
    
    # Add data source information
    output.append("## Data Source")
    output.append("- Source: Polymarket.com")
    output.append("- Format: Plain text optimized for LLM consumption")
    output.append("- Generated by: PolyIngest (polyingest.com)")
    
    # Add note about data extraction
    if market_data.get('yes_probability') == 'N/A' and market_data.get('no_probability') == 'N/A':
        output.append("- Note: Probability data not found (market may not exist or be loading)")
    else:
        output.append("- Note: Market-specific data successfully extracted")
    
    output.append("")
    
    if 'error' in market_data:
        output.append("## Extraction Notes")
        output.append(f"- {market_data['error']}")
    
    return "\n".join(output)


@app.get("/", response_class=PlainTextResponse)
async def root():
    """Root endpoint with usage instructions."""
    return """PolyIngest - Polymarket Analysis Extractor

Usage: Replace 'polymarket.com' with 'polyingest.com' in any Polymarket URL

Example: 
  Polymarket: https://polymarket.com/event/presidential-election-winner-2028?tid=1754301474937
  PolyIngest: https://polyingest.com/event/presidential-election-winner-2028?tid=1754301474937

This will fetch and format the market data as plain text for LLM consumption.
"""


@app.get("/health", response_class=PlainTextResponse)
async def health_check():
    """Health check endpoint."""
    return "OK"


@app.get("/event/{event_path:path}", response_class=PlainTextResponse)
async def analyze_polymarket_event(event_path: str, tid: Optional[str] = None):
    """
    Analyze Polymarket event (mirrors Polymarket URL structure).
    
    Args:
        event_path: The event path from URL
        tid: Optional transaction ID parameter
    
    Returns:
        Plain text formatted market analysis
    """
    
    if not event_path or event_path.strip() == "":
        raise HTTPException(status_code=400, detail="Event path cannot be empty")
    
    # Create cache key from event path and tid
    cache_key = f"{event_path}_{tid}" if tid else event_path
    market_key = cache_key.lower().strip()
    
    # Check rate limiting
    if is_rate_limited(market_key):
        raise HTTPException(
            status_code=429, 
            detail="Rate limited. Please wait before making another request for this market."
        )
    
    # Check cache
    cached_response = get_cached_response(market_key)
    if cached_response:
        return cached_response
    
    # Construct the original Polymarket URL
    polymarket_url = f"https://polymarket.com/event/{event_path}"
    if tid:
        polymarket_url += f"?tid={tid}"
    
    try:
        # Try Selenium first for dynamic content
        try:
            html_content = scrape_with_selenium(polymarket_url)
        except Exception as selenium_error:
            # Fallback to requests
            try:
                html_content = scrape_with_requests(polymarket_url)
            except Exception as requests_error:
                error_msg = f"Failed to fetch market data. Selenium error: {selenium_error}. Requests error: {requests_error}"
                raise HTTPException(status_code=500, detail=error_msg)
        
        # Extract market data
        market_data = extract_market_data(html_content, event_path)
        
        # Format response
        formatted_response = format_market_analysis(market_data)
        
        # Cache the response
        cache_response(market_key, formatted_response)
        
        return formatted_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/{market_path:path}", response_class=PlainTextResponse)
async def analyze_fallback_path(market_path: str):
    """
    Fallback endpoint - attempts to find market on Polymarket.
    Handles cases where users provide simple market descriptions.
    """
    
    if not market_path or market_path.strip() == "":
        raise HTTPException(status_code=400, detail="Market path cannot be empty")
    
    # Return helpful message for unsupported paths
    return f"""PolyIngest - Path not supported

The path '/{market_path}' is not supported.

To use PolyIngest:
1. Go to polymarket.com and find a market
2. Copy the full URL (e.g., https://polymarket.com/event/presidential-election-winner-2028?tid=1754301474937)  
3. Replace 'polymarket.com' with 'polyingest.com' in the URL

Example:
  Original: https://polymarket.com/event/presidential-election-winner-2028?tid=1754301474937
  PolyIngest: https://polyingest.com/event/presidential-election-winner-2028?tid=1754301474937
"""


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)