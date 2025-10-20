#!/usr/bin/env python3
"""
Test script for NewsAPI integration.
Verifies that news articles and sentiment analysis work correctly.

Usage:
    python test_newsapi_fetch.py

Requirements:
    - NEWSAPI_KEY must be set in .env file
    - Get free key from: https://newsapi.org/register
"""

import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables
load_dotenv()

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_interfaces.newsapi_interface import NewsAPIInterface
from data_interfaces.base_interface import DataRequest
from data_interfaces.metadata import DataType


# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def format_sentiment_color(score):
    """Color code sentiment score."""
    if score >= 0.65:
        return f"{Colors.OKGREEN}{score:.3f}{Colors.ENDC}"
    elif score >= 0.55:
        return f"{Colors.OKCYAN}{score:.3f}{Colors.ENDC}"
    elif score >= 0.45:
        return f"{Colors.WARNING}{score:.3f}{Colors.ENDC}"
    else:
        return f"{Colors.FAIL}{score:.3f}{Colors.ENDC}"


def classify_sentiment(score):
    """Classify sentiment based on score."""
    if score >= 0.70:
        return f"{Colors.OKGREEN}Very Bullish 🚀{Colors.ENDC}"
    elif score >= 0.55:
        return f"{Colors.OKGREEN}Bullish 📈{Colors.ENDC}"
    elif score >= 0.45:
        return f"{Colors.WARNING}Neutral ➡️{Colors.ENDC}"
    elif score >= 0.30:
        return f"{Colors.FAIL}Bearish 📉{Colors.ENDC}"
    else:
        return f"{Colors.FAIL}Very Bearish 🔻{Colors.ENDC}"


async def test_api_key():
    """Test 1: Verify API key is configured."""
    print_header("Test 1: API Key Configuration")
    
    api_key = os.getenv("NEWSAPI_KEY")
    
    if not api_key:
        print_error("NEWSAPI_KEY not found in environment variables")
        print_info("Get your free API key from: https://newsapi.org/register")
        print_info("Add it to your .env file: NEWSAPI_KEY=your_key_here")
        return False
    
    if api_key == "your_newsapi_key_here":
        print_error("NEWSAPI_KEY still has placeholder value")
        print_info("Replace with your actual API key from newsapi.org")
        return False
    
    print_success(f"API key found: {api_key[:8]}...{api_key[-4:]}")
    return True


async def test_health_check():
    """Test 2: Verify NewsAPI health check."""
    print_header("Test 2: NewsAPI Health Check")
    
    interface = NewsAPIInterface()
    
    try:
        health = await interface.health_check()
        
        if health["status"] == "healthy":
            print_success("NewsAPI is accessible")
            print_info(f"Latency: {health['latency_ms']:.1f}ms")
            
            if "metadata" in health:
                meta = health["metadata"]
                print_info(f"Rate Limit: {meta.get('requests_per_day', 'N/A')} requests/day")
                print_info(f"Sources: {len(meta.get('sources', []))} news outlets")
            
            return True
        else:
            print_error(f"Health check failed: {health.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print_error(f"Health check error: {str(e)}")
        return False


async def test_fetch_news_articles():
    """Test 3: Fetch recent Bitcoin news articles."""
    print_header("Test 3: Fetch Bitcoin News Articles")
    
    interface = NewsAPIInterface()
    
    # Request news from last 24 hours
    request = DataRequest(
        data_type=DataType.NEWS,
        symbol="BTC",
        timeframe="24h"
    )
    
    try:
        print_info("Fetching Bitcoin news from last 24 hours...")
        response = await interface.fetch(request)
        
        if not response.success:
            print_error(f"Failed to fetch news: {response.error}")
            return False
        
        articles = response.data.get("articles", [])
        
        if not articles:
            print_warning("No articles found (this might be normal during quiet periods)")
            return True
        
        print_success(f"Retrieved {len(articles)} articles")
        
        # Display articles in a table
        table_data = []
        for i, article in enumerate(articles[:10], 1):  # Show first 10
            title = article.get("title", "N/A")[:50] + "..."
            source = article.get("source", {}).get("name", "N/A")
            published = article.get("published_at", "N/A")
            sentiment = article.get("sentiment_score", 0.5)
            
            table_data.append([
                i,
                source,
                title,
                format_sentiment_color(sentiment),
                published[:10] if published != "N/A" else "N/A"
            ])
        
        print(f"\n{tabulate(table_data, headers=['#', 'Source', 'Title', 'Sentiment', 'Date'], tablefmt='grid')}\n")
        
        # Show article details
        print_info(f"\nSample Article Details (Article #1):")
        first = articles[0]
        print(f"  Title: {first.get('title', 'N/A')}")
        print(f"  Source: {first.get('source', {}).get('name', 'N/A')}")
        print(f"  Author: {first.get('author', 'N/A')}")
        print(f"  Published: {first.get('published_at', 'N/A')}")
        print(f"  Sentiment Score: {format_sentiment_color(first.get('sentiment_score', 0.5))}")
        print(f"  Sentiment: {first.get('sentiment', 'N/A')}")
        print(f"  URL: {first.get('url', 'N/A')[:60]}...")
        
        if "description" in first:
            print(f"  Description: {first['description'][:150]}...")
        
        return True
        
    except Exception as e:
        print_error(f"Error fetching news: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_fetch_sentiment():
    """Test 4: Fetch aggregated news sentiment."""
    print_header("Test 4: Fetch News Sentiment Analysis")
    
    interface = NewsAPIInterface()
    
    # Request sentiment analysis from last 24 hours
    request = DataRequest(
        data_type=DataType.SOCIAL_SENTIMENT,
        symbol="BTC",
        timeframe="24h"
    )
    
    try:
        print_info("Analyzing sentiment from Bitcoin news (last 24 hours)...")
        response = await interface.fetch(request)
        
        if not response.success:
            print_error(f"Failed to fetch sentiment: {response.error}")
            return False
        
        sentiment_data = response.data
        
        # Display overall sentiment
        overall_score = sentiment_data.get("overall_sentiment_score", 0.5)
        confidence = sentiment_data.get("confidence", 0.0)
        classification = sentiment_data.get("sentiment_classification", "Neutral")
        article_count = sentiment_data.get("article_count", 0)
        
        print_success("Sentiment Analysis Complete")
        print(f"\n  Overall Sentiment Score: {format_sentiment_color(overall_score)}")
        print(f"  Classification: {classify_sentiment(overall_score)}")
        print(f"  Confidence: {format_sentiment_color(confidence)}")
        print(f"  Articles Analyzed: {article_count}")
        
        # Show sentiment breakdown
        if "bullish_count" in sentiment_data:
            bullish = sentiment_data["bullish_count"]
            bearish = sentiment_data["bearish_count"]
            neutral = sentiment_data["neutral_count"]
            
            print(f"\n  Sentiment Breakdown:")
            print(f"    {Colors.OKGREEN}Bullish:{Colors.ENDC} {bullish} articles")
            print(f"    {Colors.FAIL}Bearish:{Colors.ENDC} {bearish} articles")
            print(f"    {Colors.WARNING}Neutral:{Colors.ENDC} {neutral} articles")
        
        # Show top sources
        if "sources" in sentiment_data:
            sources = sentiment_data["sources"]
            print(f"\n  News Sources ({len(sources)}):")
            for source in sources[:5]:  # Top 5
                print(f"    • {source}")
        
        # Show timeframe
        if "start_time" in sentiment_data and "end_time" in sentiment_data:
            start = sentiment_data["start_time"]
            end = sentiment_data["end_time"]
            print(f"\n  Time Range:")
            print(f"    From: {start}")
            print(f"    To:   {end}")
        
        return True
        
    except Exception as e:
        print_error(f"Error fetching sentiment: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_metadata():
    """Test 5: Verify interface metadata."""
    print_header("Test 5: Interface Metadata")
    
    interface = NewsAPIInterface()
    metadata = interface.metadata
    
    print_success("Metadata loaded successfully")
    
    print(f"\n  Name: {metadata.name}")
    print(f"  Provider: {metadata.provider}")
    print(f"  Description: {metadata.description[:80]}...")
    print(f"\n  Data Types:")
    for dt in metadata.data_types:
        print(f"    • {dt.value}")
    
    print(f"\n  Capabilities:")
    for cap in metadata.capabilities:
        print(f"    • {cap.value}")
    
    print(f"\n  Rate Limits:")
    print(f"    Requests per day: {metadata.rate_limits.requests_per_day}")
    
    print(f"\n  Performance:")
    print(f"    Expected Response Time: {metadata.expected_response_time.value}")
    print(f"    Reliability Score: {metadata.reliability_score:.2f}")
    print(f"    Quality Score: {metadata.quality_score:.2f}")
    
    if metadata.supported_sources:
        print(f"\n  News Sources ({len(metadata.supported_sources)}):")
        for source in metadata.supported_sources[:10]:  # First 10
            print(f"    • {source}")
        if len(metadata.supported_sources) > 10:
            print(f"    ... and {len(metadata.supported_sources) - 10} more")
    
    return True


async def test_integration_with_manager():
    """Test 6: Verify integration with DataInterfaceManager."""
    print_header("Test 6: Integration with Data Interface Manager")
    
    try:
        from data_interfaces import get_registry
        
        registry = get_registry()
        sources = registry.list_sources()
        
        print_success(f"Found {len(sources)} registered data sources")
        
        # Check if NewsAPI is registered
        if "NewsAPI" in sources:
            print_success("NewsAPI is registered in the interface manager")
        else:
            print_error("NewsAPI is NOT registered in the interface manager")
            print_warning("Available sources:", sources)
            return False
        
        # Display all registered sources
        print(f"\n  Registered Sources:")
        for source_name in sources:
            print(f"    • {source_name}")
        
        # Try to get NewsAPI capabilities
        try:
            newsapi_interface = registry.get_interface("NewsAPI")
            capabilities = newsapi_interface.metadata.capabilities
            print(f"\n  NewsAPI Capabilities:")
            for cap in capabilities:
                print(f"    • {cap.value}")
        except Exception as e:
            print_warning(f"Could not retrieve NewsAPI from registry: {e}")
        
        return True
        
    except Exception as e:
        print_error(f"Error testing integration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests in sequence."""
    print_header("NewsAPI Integration Test Suite")
    print_info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test 1: API Key
    results["API Key"] = await test_api_key()
    if not results["API Key"]:
        print_warning("\nSkipping remaining tests - API key not configured")
        return results
    
    # Test 2: Health Check
    results["Health Check"] = await test_health_check()
    if not results["Health Check"]:
        print_warning("\nSkipping remaining tests - health check failed")
        return results
    
    # Test 3: Fetch News
    results["Fetch News"] = await test_fetch_news_articles()
    
    # Test 4: Fetch Sentiment
    results["Fetch Sentiment"] = await test_fetch_sentiment()
    
    # Test 5: Metadata
    results["Metadata"] = await test_metadata()
    
    # Test 6: Manager Integration
    results["Manager Integration"] = await test_integration_with_manager()
    
    # Summary
    print_header("Test Summary")
    
    table_data = []
    for test_name, passed in results.items():
        status = f"{Colors.OKGREEN}PASS ✓{Colors.ENDC}" if passed else f"{Colors.FAIL}FAIL ✗{Colors.ENDC}"
        table_data.append([test_name, status])
    
    print(tabulate(table_data, headers=['Test', 'Status'], tablefmt='grid'))
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.ENDC}")
    
    if passed == total:
        print_success("\n🎉 All tests passed! NewsAPI integration is working correctly.")
        print_info("\nNext steps:")
        print_info("  1. NewsAPI is now available to your BTC Agent")
        print_info("  2. The agent will automatically fetch news sentiment")
        print_info("  3. Monitor your rate limit: 100 requests/day (free tier)")
    else:
        print_warning("\n⚠️  Some tests failed. Please review the errors above.")
        print_info("\nTroubleshooting:")
        print_info("  • Check your API key is correct")
        print_info("  • Verify you haven't exceeded rate limits (100/day)")
        print_info("  • Check your internet connection")
        print_info("  • Visit https://newsapi.org/account to check your account status")
    
    return results


if __name__ == "__main__":
    # Run tests
    results = asyncio.run(run_all_tests())
    
    # Exit with appropriate code
    exit(0 if all(results.values()) else 1)
