#!/usr/bin/env python3
"""
Test script to validate FastAPI application setup with minimal configuration.
"""
import os
import sys
import asyncio
from pathlib import Path

# Set required environment variables for testing
os.environ["POLYGON_RPC_URL"] = "https://polygon-rpc.com"
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_polymarket_client():
    """Test the Polymarket client initialization."""
    from app.data.polymarket_client import PolymarketClient
    
    print("Testing Polymarket client initialization...")
    try:
        async with PolymarketClient() as client:
            print("✓ Polymarket client initialized successfully")
            print(f"  GraphQL URL: {client.graphql_url}")
            print(f"  REST URL: {client.rest_url}")
    except Exception as e:
        print(f"✗ Error initializing Polymarket client: {e}")
        return False
    return True

def test_fastapi_import():
    """Test FastAPI application import."""
    print("Testing FastAPI application import...")
    try:
        from app.main import app
        print("✓ FastAPI application imported successfully")
        print(f"  App title: {app.title}")
        print(f"  App version: {app.version}")
        return True
    except Exception as e:
        print(f"✗ Error importing FastAPI app: {e}")
        return False

def test_models():
    """Test data models."""
    print("Testing data models...")
    try:
        from app.data.models import MarketData, MarketOutcome
        from decimal import Decimal
        from datetime import datetime
        
        # Test MarketOutcome
        outcome = MarketOutcome(
            id="test_outcome",
            name="Yes",
            current_price=Decimal("0.52"),
            volume_24h=Decimal("1000000"),
            liquidity=Decimal("500000")
        )
        
        # Test MarketData
        market = MarketData(
            id="test_market",
            title="Test Market",
            description="Test Description",
            category="Test",
            end_date=datetime.now(),
            resolution_criteria="Test criteria",
            status="active",
            creator="0x123...",
            total_volume=Decimal("2000000"),
            total_liquidity=Decimal("1000000"),
            outcomes=[outcome]
        )
        
        print("✓ Data models work correctly")
        return True
    except Exception as e:
        print(f"✗ Error with data models: {e}")
        return False

async def main():
    """Run all tests."""
    print("=== PolyIngest Backend Test Suite ===\n")
    
    tests = [
        test_fastapi_import,
        test_models,
        test_polymarket_client
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if asyncio.iscoroutinefunction(test):
            result = await test()
        else:
            result = test()
        if result:
            passed += 1
        print()
    
    print(f"=== Test Results: {passed}/{total} passed ===")
    
    if passed == total:
        print("🎉 All tests passed! Backend setup is complete.")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)