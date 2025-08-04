#!/usr/bin/env python3
"""
Simple test script for HashIngest application
Run this to verify basic functionality works as expected
"""

import requests
import time
import sys
from urllib.parse import quote

# Configuration
BASE_URL = "http://localhost:8000"
TEST_MARKETS = [
    "US recession in 2025",
    "bitcoin price prediction",
    "AI will replace programmers",
    "climate change effects"
]

def test_endpoint(url, expected_content=None, should_contain=None):
    """Test a single endpoint"""
    try:
        print(f"Testing: {url}")
        response = requests.get(url, timeout=30)
        
        print(f"  Status Code: {response.status_code}")
        print(f"  Content Type: {response.headers.get('content-type', 'N/A')}")
        print(f"  Response Length: {len(response.text)} characters")
        
        if response.status_code != 200:
            print(f"  ❌ FAILED: Expected 200, got {response.status_code}")
            return False
        
        if expected_content and response.text.strip() != expected_content:
            print(f"  ❌ FAILED: Expected '{expected_content}', got '{response.text[:100]}...'")
            return False
            
        if should_contain:
            for content in should_contain:
                if content not in response.text:
                    print(f"  ❌ FAILED: Response missing '{content}'")
                    return False
        
        print(f"  ✅ PASSED")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ FAILED: Request error - {e}")
        return False
    except Exception as e:
        print(f"  ❌ FAILED: Unexpected error - {e}")
        return False

def test_basic_endpoints():
    """Test basic application endpoints"""
    print("=" * 60)
    print("TESTING BASIC ENDPOINTS")
    print("=" * 60)
    
    results = []
    
    # Test health endpoint
    results.append(test_endpoint(
        f"{BASE_URL}/health",
        expected_content="OK"
    ))
    
    # Test root endpoint
    results.append(test_endpoint(
        f"{BASE_URL}/",
        should_contain=["HashIngest", "Market Analysis", "Usage:", "Example:"]
    ))
    
    return results

def test_market_endpoints():
    """Test market analysis endpoints"""
    print("\n" + "=" * 60)
    print("TESTING MARKET ENDPOINTS")
    print("=" * 60)
    
    results = []
    
    for market in TEST_MARKETS:
        encoded_market = quote(market)
        url = f"{BASE_URL}/{encoded_market}"
        
        # Expected content in market analysis
        expected_sections = [
            "## Market Analysis",
            "- Title:",
            "- Human Probability:",
            "- AI Probability:",
            "- Trading Volume:",
            "- Liquidity:",
            "- Smart Score:",
            "## Positions",
            "## Trends"
        ]
        
        result = test_endpoint(url, should_contain=expected_sections)
        results.append(result)
        
        if result:
            print(f"  📊 Market data extracted successfully for: {market}")
        
        # Small delay to respect rate limiting
        time.sleep(2)
    
    return results

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n" + "=" * 60)
    print("TESTING RATE LIMITING")
    print("=" * 60)
    
    market = "rate limit test"
    url = f"{BASE_URL}/{quote(market)}"
    
    print("Making first request...")
    response1 = requests.get(url)
    print(f"  First request: {response1.status_code}")
    
    print("Making immediate second request (should be cached)...")
    response2 = requests.get(url)
    print(f"  Second request: {response2.status_code}")
    
    # Check if responses are identical (cached)
    if response1.text == response2.text:
        print("  ✅ PASSED: Caching working (identical responses)")
        return True
    else:
        print("  ⚠️  WARNING: Responses differ (caching may not be working)")
        return False

def test_error_handling():
    """Test error handling"""
    print("\n" + "=" * 60)
    print("TESTING ERROR HANDLING")
    print("=" * 60)
    
    results = []
    
    # Test empty market path
    try:
        print("Testing empty market path...")
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200 and "Usage:" in response.text:
            print("  ✅ PASSED: Root endpoint handles empty path correctly")
            results.append(True)
        else:
            print("  ❌ FAILED: Unexpected response for empty path")
            results.append(False)
    except Exception as e:
        print(f"  ❌ FAILED: Error testing empty path - {e}")
        results.append(False)
    
    return results

def check_server_running():
    """Check if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Run all tests"""
    print("🚀 HashIngest Application Test Suite")
    print("=" * 60)
    
    # Check if server is running
    if not check_server_running():
        print("❌ ERROR: Server not running!")
        print("\nTo start the server, run:")
        print("  python app.py")
        print("\nThen run this test script again.")
        sys.exit(1)
    
    print("✅ Server is running")
    
    # Run all tests
    all_results = []
    
    all_results.extend(test_basic_endpoints())
    all_results.extend(test_market_endpoints())
    all_results.extend([test_rate_limiting()])
    all_results.extend(test_error_handling())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(all_results)
    total = len(all_results)
    failed = total - passed
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! The application is working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {failed} tests failed. Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()