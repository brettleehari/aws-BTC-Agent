#!/usr/bin/env python3
"""
Test script for Advanced Sentiment Analyzer.

Demonstrates:
- Multi-source sentiment aggregation
- Weighted composite scoring
- Trend analysis
- Confidence metrics
"""

import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, '/workspaces/aws-BTC-Agent')

from src.data_interfaces.sentiment_analyzer import SentimentAnalyzer, UnifiedSentiment
from src.data_interfaces.newsapi_interface import NewsAPIInterface
from src.data_interfaces.twitter_interface import TwitterInterface
from src.data_interfaces.sentiment_interface import SentimentInterface
from src.data_interfaces.coingecko_interface import CoinGeckoInterface


# Colors
class C:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_sentiment_gauge(score: float, label: str):
    """Print visual sentiment gauge"""
    # Convert -1 to 1 scale to 0-100 for display
    percentage = ((score + 1) / 2) * 100
    
    # Create bar
    bar_width = 50
    filled = int((percentage / 100) * bar_width)
    empty = bar_width - filled
    
    # Color based on sentiment
    if score > 0.6:
        color = C.GREEN
        emoji = "🚀"
    elif score > 0.2:
        color = C.CYAN
        emoji = "📈"
    elif score > -0.2:
        color = C.YELLOW
        emoji = "➡️"
    elif score > -0.6:
        color = C.YELLOW
        emoji = "📉"
    else:
        color = C.RED
        emoji = "⚠️"
    
    bar = f"{color}{'█' * filled}{C.END}{'░' * empty}"
    
    print(f"\n   {emoji} Sentiment Gauge: {label}")
    print(f"   [{bar}] {score:+.3f}")
    print(f"   {percentage:.1f}%")


async def test_sentiment_analyzer():
    """Test the advanced sentiment analyzer"""
    print(f"\n{C.BOLD}{'=' * 70}")
    print(f"{'ADVANCED SENTIMENT ANALYZER TEST':^70}")
    print(f"{'=' * 70}{C.END}\n")
    
    print(f"{C.BLUE}Initializing data sources...{C.END}")
    
    # Initialize interfaces
    try:
        newsapi = NewsAPIInterface()
        print(f"   ✅ NewsAPI initialized")
    except Exception as e:
        print(f"   ⚠️  NewsAPI unavailable: {e}")
        newsapi = None
    
    try:
        twitter = TwitterInterface()
        print(f"   ✅ Twitter initialized")
    except Exception as e:
        print(f"   ⚠️  Twitter unavailable: {e}")
        twitter = None
    
    try:
        sentiment = SentimentInterface()
        print(f"   ✅ Fear & Greed initialized")
    except Exception as e:
        print(f"   ⚠️  Fear & Greed unavailable: {e}")
        sentiment = None
    
    # Initialize analyzer
    analyzer = SentimentAnalyzer(
        newsapi_interface=newsapi,
        twitter_interface=twitter,
        sentiment_interface=sentiment
    )
    
    print(f"\n{C.BOLD}{'─' * 70}{C.END}")
    print(f"{C.BLUE}Analyzing Bitcoin sentiment...{C.END}")
    print(f"{C.BOLD}{'─' * 70}{C.END}\n")
    
    # Perform analysis
    try:
        unified = await analyzer.analyze(
            symbol="BTC",
            include_trends=True,
            detect_divergence=False  # Need price data for this
        )
        
        # Display results
        print(f"{C.GREEN}✅ ANALYSIS COMPLETE{C.END}\n")
        
        # Composite score
        print_sentiment_gauge(unified.composite_score, unified.sentiment_label)
        
        # Confidence
        confidence_pct = unified.confidence * 100
        conf_color = C.GREEN if confidence_pct > 70 else C.YELLOW if confidence_pct > 40 else C.RED
        print(f"\n   {conf_color}🎯 Confidence: {confidence_pct:.1f}%{C.END}")
        
        # Individual sources
        print(f"\n{C.BOLD}   📊 Individual Source Scores:{C.END}")
        
        if unified.news_score is not None:
            print(f"      News Sentiment:       {unified.news_score:+.3f}")
        else:
            print(f"      News Sentiment:       {C.YELLOW}N/A{C.END}")
        
        if unified.social_score is not None:
            print(f"      Social Sentiment:     {unified.social_score:+.3f}")
        else:
            print(f"      Social Sentiment:     {C.YELLOW}N/A{C.END}")
        
        if unified.fear_greed_score is not None:
            print(f"      Fear & Greed:         {unified.fear_greed_score:+.3f}")
        else:
            print(f"      Fear & Greed:         {C.YELLOW}N/A{C.END}")
        
        # Trends
        if unified.trend_24h:
            trend_emoji = {
                "IMPROVING": "📈",
                "STABLE": "➡️",
                "DETERIORATING": "📉",
                "INSUFFICIENT_DATA": "❓"
            }
            trend_color = {
                "IMPROVING": C.GREEN,
                "STABLE": C.YELLOW,
                "DETERIORATING": C.RED,
                "INSUFFICIENT_DATA": C.YELLOW
            }
            
            print(f"\n{C.BOLD}   📈 Sentiment Trends:{C.END}")
            
            t24_emoji = trend_emoji.get(unified.trend_24h, "❓")
            t24_color = trend_color.get(unified.trend_24h, C.YELLOW)
            print(f"      24-Hour Trend:        {t24_color}{t24_emoji} {unified.trend_24h}{C.END}")
            
            if unified.trend_7d:
                t7d_emoji = trend_emoji.get(unified.trend_7d, "❓")
                t7d_color = trend_color.get(unified.trend_7d, C.YELLOW)
                print(f"      7-Day Trend:          {t7d_color}{t7d_emoji} {unified.trend_7d}{C.END}")
        
        # Divergence
        if unified.divergence_detected:
            div_emoji = "🔔" if unified.divergence_type == "BULLISH_DIVERGENCE" else "⚠️"
            print(f"\n{C.BOLD}   {div_emoji} DIVERGENCE DETECTED!{C.END}")
            print(f"      Type: {unified.divergence_type}")
            print(f"      Strength: {unified.divergence_strength:.2%}")
        
        # Metadata
        print(f"\n{C.BOLD}   ℹ️  Metadata:{C.END}")
        print(f"      Sources Used:         {', '.join(unified.sources_used)}")
        print(f"      Timestamp:            {unified.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Summary statistics
        summary = analyzer.get_sentiment_summary()
        if "error" not in summary:
            print(f"\n{C.BOLD}   📊 Historical Summary:{C.END}")
            print(f"      Current Score:        {summary['current']:+.3f}")
            print(f"      24h Average:          {summary['avg_24h']:+.3f}")
            print(f"      24h Range:            {summary['min_24h']:+.3f} to {summary['max_24h']:+.3f}")
            print(f"      Volatility:           {summary['volatility']:.3f}")
            print(f"      Readings Count:       {summary['readings_count']}")
            print(f"      Active Sources:       {summary['sources_active']}")
        
        return True
        
    except Exception as e:
        print(f"{C.RED}❌ ANALYSIS FAILED: {e}{C.END}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_price_divergence():
    """Test sentiment analyzer with price divergence detection"""
    print(f"\n\n{C.BOLD}{'=' * 70}")
    print(f"{'DIVERGENCE DETECTION TEST':^70}")
    print(f"{'=' * 70}{C.END}\n")
    
    print(f"{C.BLUE}Fetching Bitcoin price data...{C.END}")
    
    # Get price data
    try:
        coingecko = CoinGeckoInterface()
        from src.data_interfaces.base_interface import DataRequest
        from src.data_interfaces.metadata import DataType
        
        request = DataRequest(
            data_type=DataType.PRICE,
            parameters={"symbol": "BTC", "days": 7}
        )
        
        price_response = await coingecko.fetch(request)
        
        if price_response.success:
            # Create mock price history (for demonstration)
            current_price = price_response.data.get("price", 109000)
            price_data = [
                {"price": current_price * (1 + (i - 5) * 0.01), "timestamp": datetime.now()}
                for i in range(10)
            ]
            
            print(f"   ✅ Price data retrieved: ${current_price:,.2f}")
            
            # Initialize analyzer
            try:
                newsapi = NewsAPIInterface()
            except Exception:
                newsapi = None
            
            sentiment = SentimentInterface()
            
            analyzer = SentimentAnalyzer(
                newsapi_interface=newsapi,
                sentiment_interface=sentiment
            )
            
            # Perform analysis with divergence detection
            print(f"\n{C.BLUE}Analyzing for divergences...{C.END}\n")
            
            unified = await analyzer.analyze(
                symbol="BTC",
                include_trends=True,
                detect_divergence=True,
                price_data=price_data
            )
            
            if unified.divergence_detected:
                print(f"{C.GREEN}✅ DIVERGENCE DETECTED!{C.END}")
                print(f"   Type: {unified.divergence_type}")
                print(f"   Strength: {unified.divergence_strength:.2%}")
                
                if unified.divergence_type == "BULLISH_DIVERGENCE":
                    print(f"\n   💡 {C.GREEN}Interpretation:{C.END}")
                    print(f"      Price is declining but sentiment is improving.")
                    print(f"      This could signal a potential reversal to the upside.")
                elif unified.divergence_type == "BEARISH_DIVERGENCE":
                    print(f"\n   💡 {C.YELLOW}Interpretation:{C.END}")
                    print(f"      Price is rising but sentiment is deteriorating.")
                    print(f"      This could signal a potential reversal to the downside.")
            else:
                print(f"{C.YELLOW}ℹ️  No significant divergences detected{C.END}")
                print(f"   Price and sentiment are moving in alignment.")
            
            return True
        else:
            print(f"{C.YELLOW}⚠️  Could not fetch price data{C.END}")
            return False
            
    except Exception as e:
        print(f"{C.RED}❌ TEST FAILED: {e}{C.END}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    results = []
    
    # Test 1: Basic sentiment analysis
    results.append(await test_sentiment_analyzer())
    
    # Test 2: Divergence detection
    results.append(await test_with_price_divergence())
    
    # Summary
    print(f"\n\n{C.BOLD}{'=' * 70}")
    print(f"{'TEST SUMMARY':^70}")
    print(f"{'=' * 70}{C.END}\n")
    
    passed = sum(results)
    total = len(results)
    
    print(f"   Passed: {C.GREEN}{passed}/{total}{C.END}")
    print(f"   Failed: {C.RED}{total - passed}/{total}{C.END}")
    
    if passed == total:
        print(f"\n   {C.GREEN}🎉 ALL TESTS PASSED!{C.END}")
        return 0
    else:
        print(f"\n   {C.YELLOW}⚠️  Some tests failed{C.END}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
