# HashIngest
You are Claude, an expert Python developer specializing in web scraping, API development, and building deployable web services. Your task is to create a complete, functional web application called "Hashingest" that mirrors the functionality of "Gitingest" (where swapping "github.com" to "gitingest.com" in a repo URL provides a plain text digest of the repo). For Hashingest, users will visit a URL like "hashingest.com/{specific market}" (e.g., hashingest.com/US recession in 2025), which should automatically:


Map the {specific market} path to a corresponding Hashdive URL: https://hashdive.com/Analyze_Market?market={URL-encoded market name} (e.g., https://hashdive.com/Analyze_Market?market=US%20recession%20in%202025).


Fetch and scrape the dynamic content from that Hashdive market analysis page, handling JavaScript-rendered elements.


Extract key data points such as:

Market title
Human probability
AI probability
Trading volume
Liquidity
Smart score
Positions (e.g., Yes/No breakdowns, entry prices, profit/loss distributions if available)
Trends or charts (described textually, e.g., "Price trend: Upward over the last week")
Any other relevant metrics like top traders, sentiment, or historical data.

Note: You must inspect the actual HTML structure of a sample Hashdive market page (e.g., browse to https://hashdive.com/ and click a market to get a real URL, then use browser dev tools to find precise CSS selectors or IDs for elements). Use placeholders in your code with comments indicating where to update based on real inspection. If exact selectors are unknown, provide a robust parsing approach that can handle tables, divs, or lists commonly used in such analytics sites.


Format the extracted data into pure, LLM-ready text (no HTML, JSON, or markup beyond simple markdown-like structures for readability). Use a hierarchical format with sections like:
text## Market Analysis
- Title: [title]
  Human Probability: [value]
  AI Probability: [value]
  Trading Volume: [value]
  Liquidity: [value]
  Smart Score: [value]

## Positions
- Position 1: [details]
- Position 2: [details]

## Trends
- [Textual description of any charts or insights]
Ensure the output is concise, factual, and optimized for feeding into an LLM (e.g., key-value pairs, lists for enumerations).


Serve this formatted text as a plain text response (Content-Type: text/plain) directly in the browser or via API call.


Technical Requirements:

Framework: Use FastAPI for the web server (simple, async, and easy to deploy).
Scraping: Use Selenium with headless Chrome for fetching dynamic content (as Hashdive likely loads data via JS). Include webdriver setup with options for no-sandbox and disable-dev-shm-usage for deployment compatibility. Fall back to requests + BeautifulSoup if possible, but prioritize Selenium for reliability.
Parsing: Use BeautifulSoup to extract data from the HTML source.
URL Handling: Capture the full path after the root (e.g., /US recession in 2025) using FastAPI's :path parameter. URL-encode it properly when constructing the Hashdive URL (import urllib.parse).
Error Handling: If the market doesn't exist or scraping fails, return a plain text error like "Market not found or error fetching data."
Performance: Add a short sleep (e.g., 3-5 seconds) after page load in Selenium to ensure content renders. Consider caching (e.g., with a simple dict or Redis if deployed) to avoid repeated scrapes for the same market within a short time.
Libraries: Stick to requests, beautifulsoup4, selenium, fastapi, uvicorn. Assume the user will install via pip. No additional installs in code.
Running: Include code to run locally with uvicorn (e.g., if name == "main": uvicorn.run(...)). Provide instructions for local testing (e.g., python app.py, then visit http://localhost:8000/{market}).
Deployment: Add notes on deploying to platforms like Vercel, Render, or Heroku. Mention needing to set up ChromeDriver in the environment (e.g., via build packs on Render).
Ethics: Include a comment reminding to respect Hashdive's terms of service, rate-limit requests (e.g., no more than 1 per minute if scaled), and avoid overloading their site.
Extensions: Make it extensible for other Hashdive features, like user analysis (e.g., hashingest.com/user/{wallet_address}), but focus on market analysis first. Comment on how to add this.

Output Format:

Provide the complete Python code in a single file (e.g., app.py).
Follow with brief deployment instructions.
End with an example of what the output text might look like for a hypothetical market.
Ensure the code is clean, commented, and Pythonic. Use type hints where appropriate.

Do not make assumptions about Hashdive's HTML structure beyond common patterns; emphasize in comments that selectors need real-world validation. If needed, suggest a way to dynamically discover selectors or use more flexible parsing (e.g., finding text labels and adjacent values).


