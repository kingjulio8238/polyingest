# Deployment Instructions

## Local Development

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   python app.py
   ```

3. **Test the Application**
   - Visit `http://localhost:8000` for usage instructions
   - Test with: `http://localhost:8000/event/presidential-election-winner-2028?tid=1754301474937`
   - Health check: `http://localhost:8000/health`

## Deployment Options

### Option 1: Render (Recommended)

1. **Prerequisites**
   - Create a Render account at render.com
   - Connect your GitHub repository

2. **Deploy**
   - Push code to GitHub
   - In Render dashboard, create a new "Web Service"
   - Connect your repository
   - Render will automatically detect the `render.yaml` configuration
   - The buildpacks will install Chrome and ChromeDriver automatically

3. **Environment Variables**
   - No additional environment variables needed for basic functionality
   - Consider adding Redis URL for production caching if needed

### Option 2: Docker

1. **Build Image**
   ```bash
   docker build -t polyingest .
   ```

2. **Run Container**
   ```bash
   docker run -p 8000:8000 polyingest
   ```

3. **Deploy to Cloud**
   - Push to Docker Hub or container registry
   - Deploy to cloud platforms that support containers

### Option 3: Heroku

1. **Install Buildpacks**
   ```bash
   heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-google-chrome
   heroku buildpacks:add --index 2 https://github.com/heroku/heroku-buildpack-chromedriver
   heroku buildpacks:add --index 3 heroku/python
   ```

2. **Deploy**
   ```bash
   git push heroku main
   ```

### Option 4: Vercel

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Configure**
   - Add `vercel.json` configuration for Python runtime
   - Note: Chrome setup is more complex on Vercel

## Important Notes

### Rate Limiting
- The application implements a 1-minute rate limit per market
- Responses are cached for 5 minutes
- Respect Polymarket's terms of service

### HTML Selectors
- **CRITICAL**: The current HTML selectors are optimized for Polymarket's React structure
- Before production deployment, test with various Polymarket market pages
- Update the `extract_market_data()` function if Polymarket changes their layout
- Test thoroughly with actual market pages

### Monitoring
- Monitor application logs for scraping errors
- Set up alerts for high error rates
- Consider implementing structured logging for production

### Performance
- Chrome driver initialization can be slow (3-5 seconds)
- Consider implementing connection pooling for high traffic
- Monitor memory usage as Chrome instances can be memory-intensive

### Security
- The application runs Chrome in headless mode with security flags
- No sensitive data is logged or cached
- Consider adding request rate limiting at the infrastructure level