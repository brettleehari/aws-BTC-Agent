#!/usr/bin/env python3
"""
Quick test to verify all data sources are working with real API keys.
"""

import asyncio
import sys
import os
sys.path.insert(0, 'src')

from dotenv import load_dotenv
load_dotenv()

from data_interfaces.newsapi_interface import NewsAPIInterface
from data_interfaces.coingecko_interface import CoinGeckoInterface
from data_interfaces.sentiment_interface import SentimentInterface
from data_interfaces.binance_interface import BinanceInterface
from data_interfaces.base_interface import DataRequest
from data_interfaces.metadata import DataType

# Colors
class C:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    END = '\033[0m'

async def test_coingecko():
    """Test CoinGecko price data"""
    print(f"\n{C.BLUE}{C.BOLD}1. Testing CoinGecko (Price Data){C.END}")
    print("-" * 70)
    
    try:
        interface = CoinGeckoInterface()
        request = DataRequest(
            data_type=DataType.PRICE,
            symbol="BTC"
        )
        
        response = await interface.fetch(request)
        
        if response.success:
            price = response.data.get('price', 0)
            market_cap = response.data.get('market_cap', 0)
            volume = response.data.get('volume_24h', 0)
            
            print(f"{C.GREEN}✅ SUCCESS{C.END}")
            print(f"   BTC Price: ${price:,.2f}")
            print(f"   Market Cap: ${market_cap:,.0f}")
            print(f"   24h Volume: ${volume:,.0f}")
            return True
        else:
            print(f"{C.RED}❌ FAILED: {response.error}{C.END}")
            return False
            
    except Exception as e:
        print(f"{C.RED}❌ EXCEPTION: {str(e)}{C.END}")
        return False


async def test_sentiment():
    """Test Fear & Greed Index"""
    print(f"\n{C.BLUE}{C.BOLD}2. Testing Fear & Greed Index (Market Sentiment){C.END}")
    print("-" * 70)
    
    try:
        interface = SentimentInterface()
        request = DataRequest(
            data_type=DataType.SOCIAL_SENTIMENT,
            symbol="BTC"
        )
        
        response = await interface.fetch(request)
        
        if response.success:
            value = response.data.get('value', 0)
            classification = response.data.get('value_classification', 'N/A')
            
            print(f"{C.GREEN}✅ SUCCESS{C.END}")
            print(f"   Fear & Greed Index: {value}")
            print(f"   Classification: {classification}")
            return True
        else:
            print(f"{C.RED}❌ FAILED: {response.error}{C.END}")
            return False
            
    except Exception as e:
        print(f"{C.RED}❌ EXCEPTION: {str(e)}{C.END}")
        return False


async def test_alphavantage():
    """Test Alpha Vantage"""
    print(f"\n{C.BLUE}{C.BOLD}3. Testing Alpha Vantage (Price Validation){C.END}")
    print("-" * 70)
    
    # Check API key first
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key or api_key == '':
        print(f"{C.YELLOW}⚠️  SKIPPED: ALPHA_VANTAGE_API_KEY not set{C.END}")
        return None
    
    try:
        from data_interfaces.alphavantage_interface import AlphaVantageInterface
        interface = AlphaVantageInterface(api_key=api_key)
        request = DataRequest(
            data_type=DataType.PRICE,
            symbol="BTC"
        )
        
        response = await interface.fetch(request)
        
        if response.success:
            data = response.data
            print(f"{C.GREEN}✅ SUCCESS{C.END}")
            print(f"   BTC Price: ${data.get('price', 0):,.2f}")
            print(f"   Bid: ${data.get('bid_price', 0):,.2f}")
            print(f"   Ask: ${data.get('ask_price', 0):,.2f}")
            print(f"   Spread: {data.get('spread_percent', 0):.4f}%")
            print(f"   Rate Limit: {response.metadata.get('rate_limit_remaining', 'N/A')}/500")
            return True
        else:
            print(f"{C.RED}❌ FAILED: {response.error}{C.END}")
            return False
            
    except Exception as e:
        print(f"{C.RED}❌ EXCEPTION: {str(e)}{C.END}")
        return False


async def test_blockchain():
    """Test Blockchain.com"""
    print(f"\n{C.BLUE}{C.BOLD}4. Testing Blockchain.com (On-Chain Data){C.END}")
    print("-" * 70)
    
    try:
        from data_interfaces.blockchain_interface import BlockchainDotComInterface
        interface = BlockchainDotComInterface()
        request = DataRequest(
            data_type=DataType.NETWORK_METRICS,
            symbol="BTC"
        )
        
        response = await interface.fetch(request)
        
        if response.success:
            data = response.data
            print(f"{C.GREEN}✅ SUCCESS{C.END}")
            print(f"   Network Health: {data.get('network_health_score', 0):.1f}/100")
            print(f"   Hash Rate: {data.get('hash_rate_ghs', 0):,.0f} GH/s")
            print(f"   Difficulty: {data.get('difficulty', 0):,.0f}")
            print(f"   Block Time: {data.get('average_block_time_minutes', 0):.1f} min")
            print(f"   Status: {data.get('interpretation', {}).get('overall', 'unknown').upper()}")
            return True
        else:
            print(f"{C.RED}❌ FAILED: {response.error}{C.END}")
            return False
            
    except Exception as e:
        print(f"{C.RED}❌ EXCEPTION: {str(e)}{C.END}")
        return False


async def test_newsapi():
    """Test NewsAPI"""
    print(f"\n{C.BLUE}{C.BOLD}5. Testing NewsAPI (Crypto News){C.END}")
    print("-" * 70)
    
    # Check API key first
    api_key = os.getenv('NEWSAPI_KEY')
    if not api_key or api_key == '':
        print(f"{C.YELLOW}⚠️  SKIPPED: NEWSAPI_KEY not set{C.END}")
        return None
    
    try:
        interface = NewsAPIInterface(api_key=api_key)
        request = DataRequest(
            data_type=DataType.NEWS,
            symbol="BTC",
            timeframe="24h"
        )
        
        response = await interface.fetch(request)
        
        if response.success:
            articles = response.data.get('articles', [])
            
            print(f"{C.GREEN}✅ SUCCESS{C.END}")
            print(f"   Articles Retrieved: {len(articles)}")
            
            if articles:
                # Show first 3 articles
                print(f"\n   Latest Articles:")
                for i, article in enumerate(articles[:3], 1):
                    title = article.get('title', 'N/A')
                    source = article.get('source', {}).get('name', 'N/A')
                    sentiment = article.get('sentiment_score', 0.5)
                    
                    # Color code sentiment
                    if sentiment >= 0.6:
                        sent_color = C.GREEN
                        sent_label = "Bullish"
                    elif sentiment >= 0.4:
                        sent_color = C.YELLOW
                        sent_label = "Neutral"
                    else:
                        sent_color = C.RED
                        sent_label = "Bearish"
                    
                    print(f"   {i}. {title[:50]}...")
                    print(f"      Source: {source} | Sentiment: {sent_color}{sentiment:.2f} ({sent_label}){C.END}")
            
            return True
        else:
            print(f"{C.RED}❌ FAILED: {response.error}{C.END}")
            return False
            
    except Exception as e:
        print(f"{C.RED}❌ EXCEPTION: {str(e)}{C.END}")
        import traceback
        traceback.print_exc()
        return False


async def test_binance():
    """Test Binance exchange data"""
    print(f"\n{C.BLUE}{C.BOLD}6. Testing Binance (Exchange Data){C.END}")
    print("-" * 70)
    
    try:
        interface = BinanceInterface()
        
        # Test 24h statistics
        request = DataRequest(
            data_type=DataType.VOLUME,
            parameters={"symbol": "BTC"}
        )
        
        response = await interface.fetch(request)
        
        if response.success:
            data = response.data
            price = data.get('price', 0)
            change_pct = data.get('price_change_percent', 0)
            volume = data.get('volume_24h', 0)
            quote_volume = data.get('quote_volume_24h', 0)
            high = data.get('high_24h', 0)
            low = data.get('low_24h', 0)
            spread = data.get('spread', 0)
            spread_pct = data.get('spread_percent', 0)
            
            print(f"{C.GREEN}✅ SUCCESS{C.END}")
            print(f"   BTC Price: ${price:,.2f}")
            
            # Color code price change
            if change_pct >= 0:
                change_color = C.GREEN
                change_symbol = "+"
            else:
                change_color = C.RED
                change_symbol = ""
            
            print(f"   24h Change: {change_color}{change_symbol}{change_pct:.2f}%{C.END}")
            print(f"   24h High: ${high:,.2f}")
            print(f"   24h Low: ${low:,.2f}")
            print(f"   24h Volume: {volume:,.2f} BTC")
            print(f"   24h Quote Volume: ${quote_volume:,.0f}")
            print(f"   Bid/Ask Spread: ${spread:.2f} ({spread_pct:.4f}%)")
            return True
        else:
            print(f"{C.RED}❌ FAILED: {response.metadata.get('error', 'Unknown error')}{C.END}")
            return False
            
    except Exception as e:
        print(f"{C.RED}❌ EXCEPTION: {str(e)}{C.END}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print(f"\n{C.BOLD}{'=' * 70}")
    print(f"{'BTC Agent - Data Source Integration Test':^70}")
    print(f"{'=' * 70}{C.END}\n")
    
    results = []
    
    # Test all sources
    results.append(await test_coingecko())
    results.append(await test_sentiment())
    results.append(await test_alphavantage())
    results.append(await test_blockchain())
    results.append(await test_newsapi())
    results.append(await test_binance())
    
    # Summary
    print(f"\n{C.BOLD}{'=' * 70}")
    print(f"{'SUMMARY':^70}")
    print(f"{'=' * 70}{C.END}\n")
    
    passed = sum(1 for r in results if r is True)
    skipped = sum(1 for r in results if r is None)
    failed = sum(1 for r in results if r is False)
    total = len([r for r in results if r is not None])
    
    print(f"   Passed:  {C.GREEN}{passed}/{total}{C.END}")
    print(f"   Failed:  {C.RED}{failed}/{total}{C.END}")
    if skipped > 0:
        print(f"   Skipped: {C.YELLOW}{skipped}{C.END}")
    
    if passed == total:
        print(f"\n{C.GREEN}{C.BOLD}   🎉 ALL TESTS PASSED!{C.END}")
        print(f"   Your BTC Agent has access to real market data.")
        return 0
    else:
        print(f"\n{C.YELLOW}   ⚠️  Some tests failed. Check errors above.{C.END}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
