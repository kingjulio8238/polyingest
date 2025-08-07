"""
PolyIngest - Web scraping application for Polymarket analysis
Mirrors the functionality of GitIngest but for prediction markets.

IMPORTANT: This application respects Polymarket's terms of service.
Implement rate limiting (max 1 request per minute) and avoid overloading their servers.
"""

import time
import urllib.parse
import json
from typing import Dict, Optional
from datetime import datetime, timedelta

import requests
import uvicorn
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
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

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Polymarket API endpoints
POLYMARKET_GAMMA_API = "https://gamma-api.polymarket.com"
POLYMARKET_CLOB_API = "https://clob.polymarket.com"

# Simple in-memory cache for rate limiting and caching responses
cache: Dict[str, Dict] = {}
CACHE_DURATION = 300  # 5 minutes
RATE_LIMIT_DURATION = 5  # 5 seconds between requests (for testing)


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


def fetch_comprehensive_market_data(market_slug: str) -> Optional[Dict]:
    """Fetch comprehensive market data from Gamma API with improved search."""
    try:
        # Try multiple search approaches
        search_attempts = [
            {"slug": market_slug, "limit": 1},  # Direct slug match
            {"limit": 50}  # Get more markets to search through
        ]
        
        for params in search_attempts:
            gamma_url = f"{POLYMARKET_GAMMA_API}/markets"
            response = requests.get(gamma_url, params=params, timeout=10)
            
            if response.status_code == 200:
                gamma_data = response.json()
                if not gamma_data or len(gamma_data) == 0:
                    continue
                
                # If direct slug match worked, return first result
                if "slug" in params:
                    return gamma_data[0]
                
                # Otherwise, search through results for matching slug or similar question
                market_slug_clean = market_slug.lower().replace('-', ' ')
                for market in gamma_data:
                    market_slug_api = market.get('slug', '').lower()
                    market_question = market.get('question', '').lower()
                    
                    # Check for slug match or question keyword match
                    if (market_slug == market_slug_api or 
                        any(word in market_question for word in market_slug_clean.split() if len(word) > 3)):
                        return market
                
    except Exception as e:
        print(f"Gamma API request failed: {e}")
    
    return None


def fetch_clob_market_data(condition_id: str) -> Optional[Dict]:
    """Fetch detailed market data from CLOB API using condition_id."""
    try:
        clob_url = f"{POLYMARKET_CLOB_API}/markets/{condition_id}"
        
        response = requests.get(clob_url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"CLOB API request failed: {e}")
    
    return None


def extract_market_slug_from_path(event_path: str) -> str:
    """Extract market slug from URL path."""
    return event_path.strip('/').split('/')[-1] if event_path else ""


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


def extract_market_data(html_content: str, market_name: str, polymarket_url: str = None) -> Dict[str, str]:
    """
    Extract market data from Polymarket HTML content.
    
    Polymarket is a React-based application that loads market data dynamically.
    This function looks for React components and market-specific elements.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Initialize comprehensive data structure
    market_data = {
        # Basic info
        'title': market_name,
        'market_id': 'N/A',
        'condition_id': 'N/A',
        'question_id': 'N/A',
        'market_slug': 'N/A',
        'question': 'N/A',
        'description': 'N/A',
        'category': 'N/A',
        'creator': 'N/A',
        
        # Trading data
        'yes_probability': 'N/A',
        'no_probability': 'N/A',
        'trading_volume': 'N/A',
        'liquidity': 'N/A',
        'total_volume': 'N/A',
        
        # Tokens
        'tokens': [],
        'token_ids': [],
        'outcomes': [],
        'outcome_prices': [],
        
        # Market settings
        'minimum_order_size': 'N/A',
        'minimum_tick_size': 'N/A',
        'min_incentive_size': 'N/A',
        'max_incentive_spread': 'N/A',
        
        # Market status
        'active': 'N/A',
        'closed': 'N/A',
        'market_active': 'Unknown',
        'market_closed': 'Unknown',
        'market_archived': 'Unknown',
        
        # Timeline
        'created_at': 'N/A',
        'end_date': 'N/A',
        'end_date_iso': 'N/A',
        'game_start_time': 'N/A',
        
        # Technical details
        'seconds_delay': 'N/A',
        'icon': 'N/A',
        'fpmm': 'N/A',
        
        # Rewards system
        'rewards': {},
        'min_reward_size': 'N/A',
        'max_spread': 'N/A',
        'event_start_date': 'N/A',
        'event_end_date': 'N/A',
        'in_game_multiplier': 'N/A',
        'reward_epoch': 'N/A'
    }
    
    # Try to get comprehensive API data first
    api_data = None
    if polymarket_url:
        market_slug = extract_market_slug_from_path(market_name)
        api_data = fetch_comprehensive_market_data(market_slug)
        
        if api_data:
            # Basic market information
            market_data['condition_id'] = api_data.get('condition_id', api_data.get('conditionId', 'N/A'))
            market_data['question_id'] = api_data.get('question_id', api_data.get('questionId', 'N/A'))
            market_data['market_slug'] = api_data.get('market_slug', api_data.get('slug', 'N/A'))
            market_data['question'] = api_data.get('question', 'N/A')
            
            # Use question as title if available, otherwise use existing title
            if api_data.get('question'):
                market_data['title'] = api_data['question']
            
            # Market metadata
            if api_data.get('id'):
                market_data['market_id'] = api_data['id']
            if api_data.get('description'):
                market_data['description'] = api_data['description']
            if api_data.get('category'):
                market_data['category'] = api_data['category']
            if api_data.get('creator'):
                market_data['creator'] = api_data['creator']
                
            # Market status
            market_data['active'] = api_data.get('active', 'N/A')
            market_data['closed'] = api_data.get('closed', 'N/A')
            market_data['market_active'] = api_data.get('active', 'Unknown')
            market_data['market_closed'] = api_data.get('closed', 'Unknown')
            market_data['market_archived'] = api_data.get('archived', 'Unknown')
            
            # Timeline information from Gamma API
            if api_data.get('createdAt'):
                market_data['created_at'] = api_data['createdAt']
            if api_data.get('endDate'):
                market_data['end_date'] = api_data['endDate']
            if api_data.get('endDateIso'):
                market_data['end_date_iso'] = api_data['endDateIso']
                
            # Technical details from Gamma API
            if api_data.get('icon'):
                market_data['icon'] = api_data['icon']
            if api_data.get('marketMakerAddress'):
                market_data['fpmm'] = api_data['marketMakerAddress']
                
            # Trading volumes from Gamma API (comprehensive)
            if api_data.get('volumeNum'):
                market_data['trading_volume'] = f"${api_data['volumeNum']:,.2f}"
            elif api_data.get('volume'):
                # Parse string volume if needed
                try:
                    vol = float(api_data['volume'])
                    market_data['trading_volume'] = f"${vol:,.2f}"
                except:
                    market_data['trading_volume'] = api_data['volume']
                    
            if api_data.get('liquidityNum'):
                market_data['liquidity'] = f"${api_data['liquidityNum']:,.2f}"
            elif api_data.get('liquidity'):
                try:
                    liq = float(api_data['liquidity'])
                    market_data['liquidity'] = f"${liq:,.2f}"
                except:
                    market_data['liquidity'] = api_data['liquidity']
                    
            # Additional volume metrics from Gamma API
            if api_data.get('volume24hr'):
                market_data['volume_24hr'] = f"${api_data['volume24hr']:,.2f}"
            if api_data.get('volume1wk'):
                market_data['volume_1week'] = f"${api_data['volume1wk']:,.2f}"
            if api_data.get('volume1mo'):
                market_data['volume_1month'] = f"${api_data['volume1mo']:,.2f}"
            if api_data.get('volume1yr'):
                market_data['volume_1year'] = f"${api_data['volume1yr']:,.2f}"
                
            # Token IDs from Gamma API
            if api_data.get('clobTokenIds'):
                try:
                    token_ids = json.loads(api_data['clobTokenIds']) if isinstance(api_data['clobTokenIds'], str) else api_data['clobTokenIds']
                    market_data['token_ids'] = token_ids
                except:
                    pass
                    
            # Outcomes from Gamma API
            if api_data.get('outcomes'):
                try:
                    outcomes = json.loads(api_data['outcomes']) if isinstance(api_data['outcomes'], str) else api_data['outcomes']
                    market_data['outcomes'] = outcomes
                except:
                    pass
                    
            # Price data and probabilities
            if api_data.get('outcomePrices'):
                try:
                    prices = json.loads(api_data['outcomePrices']) if isinstance(api_data['outcomePrices'], str) else api_data['outcomePrices']
                    if len(prices) >= 2:
                        # Convert string prices to float
                        float_prices = []
                        for p in prices:
                            if isinstance(p, str):
                                float_prices.append(float(p))
                            else:
                                float_prices.append(float(p))
                                
                        market_data['yes_probability'] = f"{float_prices[0]*100:.1f}%"
                        market_data['no_probability'] = f"{float_prices[1]*100:.1f}%"
                        
                        # Store all outcome prices for display
                        market_data['outcome_prices'] = [f"{price*100:.1f}%" for price in float_prices]
                except Exception as e:
                    print(f"Error parsing outcome prices: {e}")
                    # Fallback to raw data
                    market_data['outcome_prices'] = api_data.get('outcomePrices', [])
                    
            # Rewards and incentives from Gamma API
            if api_data.get('rewardsMinSize'):
                market_data['min_reward_size'] = api_data['rewardsMinSize']
            if api_data.get('rewardsMaxSpread'):
                market_data['max_spread'] = api_data['rewardsMaxSpread']
                
            # Market type and additional info
            market_data['market_type'] = api_data.get('marketType', 'N/A')
            market_data['restricted'] = api_data.get('restricted', 'N/A')
            market_data['funded'] = api_data.get('funded', 'N/A')
            market_data['ready'] = api_data.get('ready', 'N/A')
            
            # Spread and price change info
            if api_data.get('spread'):
                market_data['spread'] = api_data['spread']
            if api_data.get('lastTradePrice'):
                market_data['last_trade_price'] = api_data['lastTradePrice']
            if api_data.get('oneDayPriceChange'):
                market_data['price_change_24hr'] = f"{api_data['oneDayPriceChange']:.2%}"
    
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


def format_market_analysis_markdown(market_data: Dict[str, str]) -> str:
    """Format comprehensive market data into markdown for web display."""
    
    output = []
    
    # Market header with markdown formatting
    output.append(f"# {market_data['title']}")
    output.append("")
    
    if market_data.get('market_id') != 'N/A':
        output.append(f"**Market ID:** {market_data['market_id']}")
    if market_data.get('condition_id') != 'N/A':
        output.append(f"**Condition ID:** `{market_data['condition_id']}`")
    if market_data.get('question_id') != 'N/A':
        output.append(f"**Question ID:** {market_data['question_id']}")
    output.append("")
    
    # Market configuration and settings
    config_data = []
    if market_data.get('minimum_order_size') != 'N/A':
        config_data.append(f"**Minimum Order Size:** {market_data['minimum_order_size']}")
    if market_data.get('minimum_tick_size') != 'N/A':
        config_data.append(f"**Minimum Tick Size:** {market_data['minimum_tick_size']}")
    if market_data.get('min_incentive_size') != 'N/A':
        config_data.append(f"**Minimum Incentive Size:** {market_data['min_incentive_size']}")
    if market_data.get('max_incentive_spread') != 'N/A':
        config_data.append(f"**Maximum Incentive Spread:** {market_data['max_incentive_spread']}")
    if market_data.get('seconds_delay') != 'N/A':
        config_data.append(f"**Trade Delay:** {market_data['seconds_delay']} seconds")
        
    if config_data:
        output.append("## Market Configuration")
        output.append("")
        for item in config_data:
            output.append(f"- {item}")
        output.append("")
    
    # Trading data section
    output.append("## Trading Data")
    output.append("")
    output.append(f"- **Yes Probability:** {market_data['yes_probability']}")
    output.append(f"- **No Probability:** {market_data['no_probability']}")
    output.append(f"- **Trading Volume:** {market_data['trading_volume']}")
    output.append(f"- **Liquidity:** {market_data['liquidity']}")
    if market_data.get('total_volume') != 'N/A':
        output.append(f"- **Total Volume:** {market_data['total_volume']}")
    
    # Additional volume metrics if available
    volume_metrics = []
    if market_data.get('volume_24hr') and market_data.get('volume_24hr') != 'N/A':
        volume_metrics.append(f"- **24hr Volume:** {market_data['volume_24hr']}")
    if market_data.get('volume_1week') and market_data.get('volume_1week') != 'N/A':
        volume_metrics.append(f"- **1 Week Volume:** {market_data['volume_1week']}")
    if market_data.get('volume_1month') and market_data.get('volume_1month') != 'N/A':
        volume_metrics.append(f"- **1 Month Volume:** {market_data['volume_1month']}")
    if market_data.get('volume_1year') and market_data.get('volume_1year') != 'N/A':
        volume_metrics.append(f"- **1 Year Volume:** {market_data['volume_1year']}")
        
    for metric in volume_metrics:
        output.append(metric)
    
    # Price change and spread info
    if market_data.get('price_change_24hr') and market_data.get('price_change_24hr') != 'N/A':
        output.append(f"- **24hr Price Change:** {market_data['price_change_24hr']}")
    if market_data.get('spread') and market_data.get('spread') != 'N/A':
        output.append(f"- **Spread:** {market_data['spread']}")
    if market_data.get('last_trade_price') and market_data.get('last_trade_price') != 'N/A':
        output.append(f"- **Last Trade Price:** {market_data['last_trade_price']}")
        
    output.append("")
    
    # Token information
    if market_data.get('tokens') or market_data.get('token_ids'):
        output.append("## Token Information")
        output.append("")
        if market_data.get('tokens') and len(market_data['tokens']) > 0:
            for i, token in enumerate(market_data['tokens']):
                if isinstance(token, dict):
                    token_info = f"**Token {i+1}:**"
                    if token.get('token_id'):
                        token_info += f" ID=`{token['token_id']}`"
                    if token.get('outcome'):
                        token_info += f" ({token['outcome']})"
                    output.append(f"- {token_info}")
                else:
                    output.append(f"- **Token {i+1}:** {token}")
        elif market_data.get('token_ids'):
            for i, token_id in enumerate(market_data['token_ids']):
                output.append(f"- **Token {i+1}:** `{token_id}`")
        output.append("")
    
    # All outcome prices if available
    if market_data.get('outcome_prices') and len(market_data['outcome_prices']) > 2:
        output.append("## All Outcome Probabilities")
        output.append("")
        for i, price in enumerate(market_data['outcome_prices']):
            outcome_name = ""
            if market_data.get('outcomes') and i < len(market_data['outcomes']):
                outcome_name = f" ({market_data['outcomes'][i]})"
            output.append(f"- **Outcome {i+1}:** {price}{outcome_name}")
        output.append("")
    
    # Market description
    if market_data['description'] != 'N/A':
        output.append("## Market Description")
        output.append("")
        output.append(market_data['description'])
        output.append("")
    
    # Trading outcomes
    if market_data['outcomes']:
        output.append("## Trading Outcomes")
        output.append("")
        for outcome in market_data['outcomes']:
            output.append(f"- {outcome}")
        output.append("")
    
    # Market status (comprehensive)
    status_data = []
    if market_data.get('active') != 'N/A':
        status_data.append(f"**Active:** {'Yes' if market_data['active'] else 'No'}")
    if market_data.get('closed') != 'N/A':
        status_data.append(f"**Closed:** {'Yes' if market_data['closed'] else 'No'}")
    if market_data.get('market_archived') != 'Unknown':
        status_data.append(f"**Archived:** {'Yes' if market_data['market_archived'] else 'No'}")
    
    if status_data:
        output.append("## Market Status")
        output.append("")
        for item in status_data:
            output.append(f"- {item}")
        output.append("")
    
    # Market timeline (comprehensive)
    timeline_data = []
    if market_data.get('created_at') != 'N/A':
        timeline_data.append(f"**Created:** {market_data['created_at']}")
    if market_data.get('end_date') != 'N/A':
        timeline_data.append(f"**End Date:** {market_data['end_date']}")
    if market_data.get('end_date_iso') != 'N/A':
        timeline_data.append(f"**End Date (ISO):** {market_data['end_date_iso']}")
    if market_data.get('game_start_time') != 'N/A':
        timeline_data.append(f"**Game Start:** {market_data['game_start_time']}")
    
    if timeline_data:
        output.append("## Market Timeline")
        output.append("")
        for item in timeline_data:
            output.append(f"- {item}")
        output.append("")
    
    # Technical details
    technical_data = []
    if market_data.get('fpmm') != 'N/A':
        technical_data.append(f"**FPMM Address:** `{market_data['fpmm']}`")
    if market_data.get('icon') != 'N/A':
        technical_data.append(f"**Icon:** {market_data['icon']}")
    if market_data.get('market_slug') != 'N/A':
        technical_data.append(f"**Market Slug:** {market_data['market_slug']}")
        
    if technical_data:
        output.append("## Technical Details")
        output.append("")
        for item in technical_data:
            output.append(f"- {item}")
        output.append("")
    
    # Market metadata
    metadata = []
    if market_data.get('creator') != 'N/A':
        creator_short = market_data['creator'][:12] + "..." if len(market_data['creator']) > 16 else market_data['creator']
        metadata.append(f"**Creator:** {creator_short}")
    if market_data.get('category') != 'N/A':
        metadata.append(f"**Category:** {market_data['category']}")
    if market_data.get('market_type') != 'N/A':
        metadata.append(f"**Market Type:** {market_data['market_type']}")
    if market_data.get('restricted') != 'N/A':
        metadata.append(f"**Restricted:** {'Yes' if market_data['restricted'] else 'No'}")
    if market_data.get('funded') != 'N/A':
        metadata.append(f"**Funded:** {'Yes' if market_data['funded'] else 'No'}")
    if market_data.get('ready') != 'N/A':
        metadata.append(f"**Ready:** {'Yes' if market_data['ready'] else 'No'}")
    
    if metadata:
        output.append("## Market Metadata")
        output.append("")
        for item in metadata:
            output.append(f"- {item}")
        output.append("")
    
    # Source info
    output.append("---")
    output.append("")
    output.append("**Source:** Polymarket.com + Gamma API")
    output.append("**Generated by:** [PolyIngest](https://github.com/polyingest)")
    
    # Error handling
    if 'error' in market_data:
        output.append("")
        output.append(f"**Extraction Notes:** {market_data['error']}")
    
    return "\n".join(output)


def format_market_analysis(market_data: Dict[str, str]) -> str:
    """Format comprehensive market data into LLM-ready plain text."""
    
    output = []
    
    # Market header with comprehensive identifiers
    output.append(f"Market: {market_data['title']}")
    if market_data.get('market_id') != 'N/A':
        output.append(f"Market ID: {market_data['market_id']}")
    if market_data.get('condition_id') != 'N/A':
        output.append(f"Condition ID: {market_data['condition_id']}")
    if market_data.get('question_id') != 'N/A':
        output.append(f"Question ID: {market_data['question_id']}")
    output.append("")
    
    # Market configuration and settings
    config_data = []
    if market_data.get('minimum_order_size') != 'N/A':
        config_data.append(f"Minimum Order Size: {market_data['minimum_order_size']}")
    if market_data.get('minimum_tick_size') != 'N/A':
        config_data.append(f"Minimum Tick Size: {market_data['minimum_tick_size']}")
    if market_data.get('min_incentive_size') != 'N/A':
        config_data.append(f"Minimum Incentive Size: {market_data['min_incentive_size']}")
    if market_data.get('max_incentive_spread') != 'N/A':
        config_data.append(f"Maximum Incentive Spread: {market_data['max_incentive_spread']}")
    if market_data.get('seconds_delay') != 'N/A':
        config_data.append(f"Trade Delay: {market_data['seconds_delay']} seconds")
        
    if config_data:
        output.append("Market Configuration:")
        for item in config_data:
            output.append(item)
        output.append("")
    
    # Trading data section
    output.append("Trading Data:")
    output.append(f"Yes Probability: {market_data['yes_probability']}")
    output.append(f"No Probability: {market_data['no_probability']}")
    output.append(f"Trading Volume: {market_data['trading_volume']}")
    output.append(f"Liquidity: {market_data['liquidity']}")
    if market_data.get('total_volume') != 'N/A':
        output.append(f"Total Volume: {market_data['total_volume']}")
    
    # Additional volume metrics if available
    volume_metrics = []
    if market_data.get('volume_24hr') and market_data.get('volume_24hr') != 'N/A':
        volume_metrics.append(f"24hr Volume: {market_data['volume_24hr']}")
    if market_data.get('volume_1week') and market_data.get('volume_1week') != 'N/A':
        volume_metrics.append(f"1 Week Volume: {market_data['volume_1week']}")
    if market_data.get('volume_1month') and market_data.get('volume_1month') != 'N/A':
        volume_metrics.append(f"1 Month Volume: {market_data['volume_1month']}")
    if market_data.get('volume_1year') and market_data.get('volume_1year') != 'N/A':
        volume_metrics.append(f"1 Year Volume: {market_data['volume_1year']}")
        
    for metric in volume_metrics:
        output.append(metric)
    
    # Price change and spread info
    if market_data.get('price_change_24hr') and market_data.get('price_change_24hr') != 'N/A':
        output.append(f"24hr Price Change: {market_data['price_change_24hr']}")
    if market_data.get('spread') and market_data.get('spread') != 'N/A':
        output.append(f"Spread: {market_data['spread']}")
    if market_data.get('last_trade_price') and market_data.get('last_trade_price') != 'N/A':
        output.append(f"Last Trade Price: {market_data['last_trade_price']}")
        
    output.append("")
    
    # Token information
    if market_data.get('tokens') or market_data.get('token_ids'):
        output.append("Token Information:")
        if market_data.get('tokens') and len(market_data['tokens']) > 0:
            for i, token in enumerate(market_data['tokens']):
                if isinstance(token, dict):
                    token_info = f"Token {i+1}:"
                    if token.get('token_id'):
                        token_info += f" ID={token['token_id']}"
                    if token.get('outcome'):
                        token_info += f" ({token['outcome']})"
                    output.append(token_info)
                else:
                    output.append(f"Token {i+1}: {token}")
        elif market_data.get('token_ids'):
            for i, token_id in enumerate(market_data['token_ids']):
                output.append(f"Token {i+1}: {token_id}")
        output.append("")
    
    # All outcome prices if available
    if market_data.get('outcome_prices') and len(market_data['outcome_prices']) > 2:
        output.append("All Outcome Probabilities:")
        for i, price in enumerate(market_data['outcome_prices']):
            outcome_name = ""
            if market_data.get('outcomes') and i < len(market_data['outcomes']):
                outcome_name = f" ({market_data['outcomes'][i]})"
            output.append(f"Outcome {i+1}: {price}{outcome_name}")
        output.append("")
    
    # Rewards system information
    if market_data.get('rewards') or any(market_data.get(key) != 'N/A' for key in ['min_reward_size', 'max_spread', 'event_start_date', 'event_end_date', 'in_game_multiplier', 'reward_epoch']):
        output.append("Rewards System:")
        if market_data.get('min_reward_size') != 'N/A':
            output.append(f"Minimum Reward Size: {market_data['min_reward_size']}")
        if market_data.get('max_spread') != 'N/A':
            output.append(f"Maximum Spread: {market_data['max_spread']}")
        if market_data.get('in_game_multiplier') != 'N/A':
            output.append(f"In-Game Multiplier: {market_data['in_game_multiplier']}")
        if market_data.get('reward_epoch') != 'N/A':
            output.append(f"Reward Epoch: {market_data['reward_epoch']}")
        if market_data.get('event_start_date') != 'N/A':
            output.append(f"Event Start: {market_data['event_start_date']}")
        if market_data.get('event_end_date') != 'N/A':
            output.append(f"Event End: {market_data['event_end_date']}")
        output.append("")
    
    # Market timeline (comprehensive)
    timeline_data = []
    if market_data.get('created_at') != 'N/A':
        timeline_data.append(f"Created: {market_data['created_at']}")
    if market_data.get('end_date') != 'N/A':
        timeline_data.append(f"End Date: {market_data['end_date']}")
    if market_data.get('end_date_iso') != 'N/A':
        timeline_data.append(f"End Date (ISO): {market_data['end_date_iso']}")
    if market_data.get('game_start_time') != 'N/A':
        timeline_data.append(f"Game Start: {market_data['game_start_time']}")
    
    if timeline_data:
        output.append("Market Timeline:")
        for item in timeline_data:
            output.append(item)
        output.append("")
    
    # Market description
    if market_data['description'] != 'N/A':
        output.append("Market Description:")
        output.append(market_data['description'])
        output.append("")
    
    # Trading outcomes
    if market_data['outcomes']:
        output.append("Trading Outcomes:")
        for outcome in market_data['outcomes']:
            output.append(outcome)
        output.append("")
    
    # Market status (comprehensive)
    status_data = []
    if market_data.get('active') != 'N/A':
        status_data.append(f"Active: {'Yes' if market_data['active'] else 'No'}")
    if market_data.get('closed') != 'N/A':
        status_data.append(f"Closed: {'Yes' if market_data['closed'] else 'No'}")
    if market_data.get('market_archived') != 'Unknown':
        status_data.append(f"Archived: {'Yes' if market_data['market_archived'] else 'No'}")
    
    if status_data:
        output.append("Market Status:")
        for item in status_data:
            output.append(item)
        output.append("")
    
    # Technical details
    technical_data = []
    if market_data.get('fpmm') != 'N/A':
        technical_data.append(f"FPMM Address: {market_data['fpmm']}")
    if market_data.get('icon') != 'N/A':
        technical_data.append(f"Icon: {market_data['icon']}")
    if market_data.get('market_slug') != 'N/A':
        technical_data.append(f"Market Slug: {market_data['market_slug']}")
        
    if technical_data:
        output.append("Technical Details:")
        for item in technical_data:
            output.append(item)
        output.append("")
    
    # Market metadata
    metadata = []
    if market_data.get('creator') != 'N/A':
        creator_short = market_data['creator'][:12] + "..." if len(market_data['creator']) > 16 else market_data['creator']
        metadata.append(f"Creator: {creator_short}")
    if market_data.get('category') != 'N/A':
        metadata.append(f"Category: {market_data['category']}")
    if market_data.get('market_type') != 'N/A':
        metadata.append(f"Market Type: {market_data['market_type']}")
    if market_data.get('restricted') != 'N/A':
        metadata.append(f"Restricted: {'Yes' if market_data['restricted'] else 'No'}")
    if market_data.get('funded') != 'N/A':
        metadata.append(f"Funded: {'Yes' if market_data['funded'] else 'No'}")
    if market_data.get('ready') != 'N/A':
        metadata.append(f"Ready: {'Yes' if market_data['ready'] else 'No'}")
    
    if metadata:
        output.append("Market Metadata:")
        for item in metadata:
            output.append(item)
        output.append("")
    
    # Source info
    output.append("Source: Polymarket.com + CLOB API + Gamma API")
    output.append("Generated by: PolyIngest")
    
    # Error handling
    if 'error' in market_data:
        output.append("")
        output.append(f"Extraction Notes: {market_data['error']}")
    
    return "\n".join(output)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint with web interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api", response_class=PlainTextResponse)
async def api_info():
    """API endpoint with usage instructions."""
    return """PolyIngest API

Turn any Polymarket URL into LLM-ready text

Usage:
Replace 'polymarket.com' with 'polyingest.com' in any Polymarket URL

Example:
https://polymarket.com/event/presidential-election-winner-2028?tid=1754301474937
becomes
https://polyingest.com/event/presidential-election-winner-2028?tid=1754301474937

Extract market data, probabilities, and trading information optimized for AI analysis.
"""


@app.get("/health", response_class=PlainTextResponse)
async def health_check():
    """Health check endpoint."""
    return "OK"


@app.get("/event/{event_path:path}", response_class=HTMLResponse)
async def analyze_polymarket_event_web(request: Request, event_path: str, tid: Optional[str] = None):
    """
    Analyze Polymarket event and display as HTML with markdown (mirrors Polymarket URL structure).
    This is the main endpoint users access by replacing polymarket.com with polyingest.com
    
    Args:
        request: FastAPI request object
        event_path: The event path from URL
        tid: Optional transaction ID parameter
    
    Returns:
        HTML page with formatted market analysis in markdown
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
        return templates.TemplateResponse("market.html", {
            "request": request, 
            "markdown_content": cached_response,
            "market_title": "Cached Market Data",
            "original_url": f"https://polymarket.com/event/{event_path}" + (f"?tid={tid}" if tid else "")
        })
    
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
        
        # Extract market data (now includes API integration)
        market_data = extract_market_data(html_content, event_path, polymarket_url)
        print(f"DEBUG: Extracted market data for {event_path}: {market_data.get('title', 'N/A')}")
        
        # Format as markdown for web display
        markdown_content = format_market_analysis_markdown(market_data)
        print(f"DEBUG: Markdown content length: {len(markdown_content)}")
        print(f"DEBUG: First 200 chars: {markdown_content[:200]}")
        
        # Cache the response
        cache_response(market_key, markdown_content)
        
        return templates.TemplateResponse("market.html", {
            "request": request,
            "markdown_content": markdown_content,
            "market_title": market_data.get('title', 'Market Analysis'),
            "original_url": polymarket_url
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/api/event/{event_path:path}", response_class=PlainTextResponse)
async def analyze_polymarket_event_api(event_path: str, tid: Optional[str] = None):
    """
    API endpoint for plain text market analysis (original functionality).
    
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
        
        # Extract market data (now includes API integration)
        market_data = extract_market_data(html_content, event_path, polymarket_url)
        
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