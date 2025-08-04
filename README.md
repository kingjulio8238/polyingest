# PolyIngest

PolyIngest is a web scraping application that mirrors the functionality of GitIngest but for Polymarket prediction markets. Simply replace `polymarket.com` with `polyingest.com` in any Polymarket URL to get LLM-ready market data.

## Usage

**Original Polymarket URL:**
```
https://polymarket.com/event/presidential-election-winner-2028?tid=1754301474937
```

**PolyIngest URL:**
```
https://polyingest.com/event/presidential-election-winner-2028?tid=1754301474937
```

## Features

- Extract market probabilities (Yes/No percentages)
- Get trading volume and liquidity data
- Retrieve market descriptions and outcomes
- Rate limiting and caching for performance
- Plain text output optimized for LLM consumption

## Development

```bash
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:8000` for usage instructions. 