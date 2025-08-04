# Testing HashIngest Application

This guide shows you how to test that HashIngest works as expected.

## Quick Test (Automated)

**1. Start the application:**
```bash
python app.py
```

**2. Run the test suite:**
```bash
python test_app.py
```

This will automatically test all endpoints and functionality.

## Manual Testing Steps

### Step 1: Basic Functionality Test

**Start the server:**
```bash
python app.py
```

**Test health endpoint:**
```bash
curl http://localhost:8000/health
# Expected: "OK"
```

**Test root endpoint:**
```bash
curl http://localhost:8000/
# Expected: Usage instructions
```

### Step 2: Market Analysis Test

**Test market endpoints:**
```bash
# Test with spaces in market name
curl "http://localhost:8000/US%20recession%20in%202025"

# Test with simple market name  
curl "http://localhost:8000/bitcoin"

# Test another market
curl "http://localhost:8000/AI%20predictions"
```

**Expected output format:**
```
## Market Analysis
- Title: [extracted title]
- Human Probability: [percentage or N/A]
- AI Probability: [percentage or N/A]
- Trading Volume: [volume data or N/A]
- Liquidity: [liquidity data or N/A]
- Smart Score: [score or N/A]

## Positions
- Position 1: [position details]
- Position 2: [position details]
...

## Trends
- [trend information]
```

### Step 3: Rate Limiting Test

```bash
# Make two quick requests to the same market
curl "http://localhost:8000/test%20market"
curl "http://localhost:8000/test%20market"

# Second response should be cached (identical)
# Wait 60+ seconds and try again - should fetch fresh data
```

### Step 4: Error Handling Test

```bash
# Test with very long market name
curl "http://localhost:8000/this%20is%20a%20very%20long%20market%20name%20that%20might%20cause%20issues"

# Test with special characters
curl "http://localhost:8000/market%20with%20%26%20special%20%24%20chars"
```

## Browser Testing

**Open in browser:**
- `http://localhost:8000/` - Should show usage instructions
- `http://localhost:8000/health` - Should show "OK"
- `http://localhost:8000/bitcoin price prediction` - Should show market analysis

## Performance Testing

**Test scraping speed:**
```bash
time curl "http://localhost:8000/performance%20test"
# Should complete within 10-15 seconds
```

**Test multiple concurrent requests:**
```bash
# Run these in separate terminals simultaneously
curl "http://localhost:8000/test1" &
curl "http://localhost:8000/test2" &  
curl "http://localhost:8000/test3" &
wait
```

## What to Look For

### ✅ Success Indicators

1. **Server starts without errors**
   - No Python exceptions on startup
   - Shows "Uvicorn running on http://0.0.0.0:8000"

2. **Endpoints respond correctly**
   - `/health` returns "OK"
   - `/` returns usage instructions
   - Market paths return formatted analysis

3. **Scraping works**
   - Selenium/Chrome initializes without errors
   - HTML content is fetched from Hashdive
   - Data extraction produces structured output

4. **Rate limiting functions**
   - Identical responses for repeated requests (caching)
   - No excessive requests to Hashdive

5. **Error handling**
   - Graceful failure messages for invalid markets
   - No server crashes on bad input

### ⚠️ Warning Signs

1. **Chrome/Selenium Issues**
   - "ChromeDriver not found" errors
   - Timeout errors during page loading
   - WebDriver initialization failures

2. **Scraping Problems**
   - All fields showing "N/A"
   - HTML parsing errors
   - Network connection issues

3. **Performance Issues**
   - Requests taking >30 seconds
   - Memory usage growing continuously
   - Server becoming unresponsive

### ❌ Failure Indicators

1. **Server won't start**
   - Import errors
   - Port already in use
   - Missing dependencies

2. **Endpoints return errors**
   - 500 Internal Server Error
   - Malformed responses
   - Wrong content types

3. **No data extraction**
   - Empty responses
   - HTML content not parsed
   - All market data shows as "N/A"

## Troubleshooting

### Chrome/Selenium Issues
```bash
# Install Chrome if missing
# On macOS:
brew install --cask google-chrome

# On Ubuntu:
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo apt-get update
sudo apt-get install google-chrome-stable
```

### Dependencies Issues
```bash
pip install --upgrade -r requirements.txt
```

### Network Issues
```bash
# Test direct connection to Hashdive
curl -I https://hashdive.com/
```

### Port Issues
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing processes
pkill -f "python app.py"
```

## Production Testing

Before deploying to production:

1. **Test with real Hashdive pages**
   - Update HTML selectors based on actual page inspection
   - Verify data extraction works with live data

2. **Load testing**
   - Test with multiple concurrent users
   - Monitor memory and CPU usage
   - Verify rate limiting prevents overload

3. **Deployment testing**
   - Test in containerized environment
   - Verify Chrome installation in deployment
   - Test with production environment variables

4. **Monitoring setup**
   - Log analysis for errors
   - Response time monitoring  
   - Uptime checks