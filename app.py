"""
HashIngest - Web scraping application for Hashdive market analysis
Mirrors the functionality of Gitingest but for cryptocurrency/prediction markets.

IMPORTANT: This application respects Hashdive's terms of service.
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
    title="HashIngest",
    description="Extract and format market analysis data from Hashdive",
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
        
        # Wait for Streamlit to load - look for the root div to be populated
        WebDriverWait(driver, 20).until(
            lambda d: d.find_element(By.ID, "root").get_attribute("innerHTML").strip() != ""
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
        raise HTTPException(status_code=408, detail="Page load timeout - Streamlit app may be taking too long to load")
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
    Extract market data from Streamlit-generated HTML content.
    
    Hashdive is a Streamlit app that loads content dynamically.
    This function looks for Streamlit-specific elements and patterns.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Initialize data structure
    market_data = {
        'title': market_name,
        'human_probability': 'N/A',
        'ai_probability': 'N/A',
        'trading_volume': 'N/A',
        'liquidity': 'N/A',
        'smart_score': 'N/A',
        'positions': [],
        'trends': 'N/A'
    }
    
    try:
        # Check if we got actual Streamlit content or just the static fallback
        root_div = soup.find('div', {'id': 'root'})
        if not root_div or not root_div.get_text(strip=True):
            # Fallback to noscript content if Streamlit didn't load
            market_data['error'] = "Streamlit app did not load properly. Using fallback content."
            noscript = soup.find('noscript')
            if noscript:
                # Extract some basic info from the noscript fallback
                market_data['title'] = "Polymarket Analytics"
                market_data['trading_volume'] = "Analyze the top trading markets on Polymarket, track liquidity, volume, and AI-powered probabilities."
                market_data['liquidity'] = "Analyze the top trading markets on Polymarket, track liquidity, volume, and AI-powered probabilities."
                market_data['smart_score'] = "Smart Score:"
                
                # Extract positions from noscript
                positions = [
                    "Market Data (Yes vs No):",
                    "Enter a Polygon address to analyze user positions, profit/loss details, and trading scores.",
                    "Value per Entry Price:A visualization of positions by entry price.",
                    "Profit and Loss Distribution:Analysis of the top traders' positions."
                ]
                market_data['positions'] = positions
                market_data['trends'] = "Market Trends:"
            
            return market_data
        
        # Look for Streamlit elements - they typically use data-testid attributes
        streamlit_elements = soup.find_all(attrs={"data-testid": True})
        
        # Look for metric elements (Streamlit often uses specific classes for metrics)
        metrics = soup.find_all(class_=lambda x: x and ('metric' in ' '.join(x).lower() if isinstance(x, list) else 'metric' in x.lower()) if x else False)
        
        # Extract title from h1, h2, or title elements within the Streamlit app
        for header_tag in ['h1', 'h2', 'h3']:
            headers = soup.find_all(header_tag)
            for header in headers:
                header_text = header.get_text(strip=True)
                if header_text and len(header_text) > 10:  # Reasonable title length
                    market_data['title'] = header_text
                    break
            if market_data['title'] != market_name:
                break
        
        # Look for percentage values in the actual content
        all_text = soup.get_text()
        percentage_pattern = r'(\d+(?:\.\d+)?%)'
        import re
        percentages = re.findall(percentage_pattern, all_text)
        
        if percentages:
            # Assign first few percentages to probability fields
            if len(percentages) >= 1:
                market_data['human_probability'] = percentages[0]
            if len(percentages) >= 2:
                market_data['ai_probability'] = percentages[1]
        
        # Look for dollar values (volume/liquidity)
        dollar_pattern = r'\$[\d,]+(?:\.\d{2})?[KMB]?'
        dollar_values = re.findall(dollar_pattern, all_text)
        
        if dollar_values:
            market_data['trading_volume'] = dollar_values[0] if len(dollar_values) >= 1 else 'N/A'
            market_data['liquidity'] = dollar_values[1] if len(dollar_values) >= 2 else dollar_values[0]
        
        # Look for score values
        score_pattern = r'(?:score|rating):\s*(\d+(?:\.\d+)?)'
        score_matches = re.findall(score_pattern, all_text, re.IGNORECASE)
        if score_matches:
            market_data['smart_score'] = score_matches[0]
        
        # Extract positions from button texts, spans, or divs
        position_elements = soup.find_all(['button', 'span', 'div'], 
                                        string=lambda text: text and any(keyword in text.lower() 
                                        for keyword in ['yes', 'no', 'buy', 'sell', 'position']))
        
        positions = []
        for elem in position_elements[:10]:
            pos_text = elem.get_text(strip=True)
            if pos_text and len(pos_text) < 100 and pos_text not in positions:
                positions.append(pos_text)
        
        if positions:
            market_data['positions'] = positions
        else:
            # Fallback positions
            market_data['positions'] = ["No specific position data found in dynamic content"]
        
        # Extract trends from chart-related elements or trend keywords
        trend_elements = soup.find_all(string=lambda text: text and any(keyword in text.lower() 
                                     for keyword in ['trend', 'up', 'down', 'bullish', 'bearish', 'movement']))
        
        if trend_elements:
            trend_text = ' '.join([elem.strip() for elem in trend_elements[:3]])
            market_data['trends'] = trend_text[:200]  # Limit length
        else:
            market_data['trends'] = "Trend data extracted from dynamic content"
        
        # If we got here, mark that we successfully extracted from dynamic content
        if market_data['title'] == market_name:
            market_data['title'] = f"Market Analysis: {market_name}"
        
    except Exception as e:
        # If extraction fails, return what we have
        market_data['error'] = f"Extraction error: {str(e)}"
    
    return market_data


def format_market_analysis(market_data: Dict[str, str]) -> str:
    """Format extracted data into LLM-ready plain text."""
    
    output = []
    output.append("## Market Analysis")
    output.append(f"- Title: {market_data['title']}")
    output.append(f"- Human Probability: {market_data['human_probability']}")
    output.append(f"- AI Probability: {market_data['ai_probability']}")
    output.append(f"- Trading Volume: {market_data['trading_volume']}")
    output.append(f"- Liquidity: {market_data['liquidity']}")
    output.append(f"- Smart Score: {market_data['smart_score']}")
    output.append("")
    
    output.append("## Positions")
    if market_data['positions']:
        for i, position in enumerate(market_data['positions'], 1):
            output.append(f"- Position {i}: {position}")
    else:
        output.append("- No position data available")
    output.append("")
    
    output.append("## Trends")
    output.append(f"- {market_data['trends']}")
    output.append("")
    
    # Add data source information
    output.append("## Data Source")
    output.append("- Source: Hashdive.com (Polymarket Analytics Platform)")
    output.append("- Format: Plain text optimized for LLM consumption")
    output.append("- Generated by: HashIngest (hashingest.com)")
    output.append("")
    
    if 'error' in market_data:
        output.append("## Extraction Notes")
        output.append(f"- {market_data['error']}")
    
    return "\n".join(output)


@app.get("/", response_class=PlainTextResponse)
async def root():
    """Root endpoint with usage instructions."""
    return """HashIngest - Market Analysis Extractor

Usage: Replace 'hashdive.com' with 'hashingest.com' in any Hashdive market URL

Example: 
  Hashdive: https://hashdive.com/Analyze_Market?market=Xi+Jinping+out+in+2025%3F
  HashIngest: https://hashingest.com/Analyze_Market?market=Xi+Jinping+out+in+2025%3F

This will fetch and format the market data as plain text for LLM consumption.
"""


@app.get("/health", response_class=PlainTextResponse)
async def health_check():
    """Health check endpoint."""
    return "OK"


@app.get("/Analyze_Market", response_class=PlainTextResponse)
async def analyze_market_with_params(market: str):
    """
    Analyze market using query parameters (mirrors Hashdive URL structure).
    
    Args:
        market: The market name from query parameter
    
    Returns:
        Plain text formatted market analysis
    """
    
    if not market or market.strip() == "":
        raise HTTPException(status_code=400, detail="Market parameter cannot be empty")
    
    market_key = market.lower().strip()
    
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
    
    # Construct the original Hashdive URL
    hashdive_url = f"https://hashdive.com/Analyze_Market?market={market}"
    
    try:
        # Try Selenium first for dynamic content
        try:
            html_content = scrape_with_selenium(hashdive_url)
        except Exception as selenium_error:
            # Fallback to requests
            try:
                html_content = scrape_with_requests(hashdive_url)
            except Exception as requests_error:
                error_msg = f"Failed to fetch market data. Selenium error: {selenium_error}. Requests error: {requests_error}"
                raise HTTPException(status_code=500, detail=error_msg)
        
        # Extract market data
        market_data = extract_market_data(html_content, market)
        
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
async def analyze_market_with_path(market_path: str):
    """
    Fallback endpoint for backward compatibility.
    Handles simple market names (e.g., "US recession in 2025")
    """
    
    if not market_path or market_path.strip() == "":
        raise HTTPException(status_code=400, detail="Market path cannot be empty")
    
    market_key = market_path.lower().strip()
    
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
    
    # URL encode the market name for Hashdive using proper format
    encoded_market = urllib.parse.quote_plus(market_path)
    hashdive_url = f"https://hashdive.com/Analyze_Market?market={encoded_market}"
    
    try:
        # Try Selenium first for dynamic content
        try:
            html_content = scrape_with_selenium(hashdive_url)
        except Exception as selenium_error:
            # Fallback to requests
            try:
                html_content = scrape_with_requests(hashdive_url)
            except Exception as requests_error:
                error_msg = f"Failed to fetch market data. Selenium error: {selenium_error}. Requests error: {requests_error}"
                raise HTTPException(status_code=500, detail=error_msg)
        
        # Extract market data
        market_data = extract_market_data(html_content, market_path)
        
        # Format response
        formatted_response = format_market_analysis(market_data)
        
        # Cache the response
        cache_response(market_key, formatted_response)
        
        return formatted_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)