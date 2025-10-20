#!/usr/bin/env python3
"""
Test script for Binance interface integration.

Tests all major data endpoints:
- Price data
- 24-hour statistics
- Order book depth
- Recent trades
"""

import asyncio
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, '/workspaces/aws-BTC-Agent')

from src.data_interfaces.binance_interface import BinanceInterface
from src.data_interfaces.base_interface import DataRequest
from src.data_interfaces.metadata import DataType


async def test_binance_price():
    """Test basic price fetching"""
    print("\n" + "="*60)
    print("TEST 1: Binance Price Data")
    print("="*60)
    
    interface = BinanceInterface()
    
    request = DataRequest(
        data_type=DataType.PRICE,
        parameters={"symbol": "BTC"}
    )
    
    try:
        response = await interface.fetch(request)
        data = response.data
        
        print(f"✅ SUCCESS")
        print(f"   Symbol: {data['symbol']}")
        print(f"   Price: ${data['price']:,.2f}")
        print(f"   Timestamp: {data['timestamp']}")
        print(f"   Rate Limit (1m): {response.metadata['rate_limit_remaining_1m']}/1200")
        print(f"   Rate Limit (5m): {response.metadata['rate_limit_remaining_5m']}/6000")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def test_binance_24h_stats():
    """Test 24-hour statistics"""
    print("\n" + "="*60)
    print("TEST 2: Binance 24-Hour Statistics")
    print("="*60)
    
    interface = BinanceInterface()
    
    request = DataRequest(
        data_type=DataType.VOLUME,
        parameters={"symbol": "BTC"}
    )
    
    try:
        response = await interface.fetch(request)
        data = response.data
        
        print(f"✅ SUCCESS")
        print(f"   Symbol: {data['symbol']}")
        print(f"   Current Price: ${data['price']:,.2f}")
        print(f"   24h Change: {data['price_change_percent']:+.2f}%")
        print(f"   24h High: ${data['high_24h']:,.2f}")
        print(f"   24h Low: ${data['low_24h']:,.2f}")
        print(f"   24h Volume: {data['volume_24h']:,.2f} BTC")
        print(f"   24h Quote Volume: ${data['quote_volume_24h']:,.0f}")
        print(f"   Weighted Avg Price: ${data['weighted_avg_price']:,.2f}")
        print(f"   Bid: ${data['bid_price']:,.2f}")
        print(f"   Ask: ${data['ask_price']:,.2f}")
        print(f"   Spread: ${data['spread']:.2f} ({data['spread_percent']:.4f}%)")
        print(f"   Trade Count: {data['trade_count']:,}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def test_binance_order_book():
    """Test order book depth"""
    print("\n" + "="*60)
    print("TEST 3: Binance Order Book")
    print("="*60)
    
    interface = BinanceInterface()
    
    request = DataRequest(
        data_type=DataType.ORDER_BOOK,
        parameters={"symbol": "BTC", "limit": 100}
    )
    
    try:
        response = await interface.fetch(request)
        data = response.data
        
        print(f"✅ SUCCESS")
        print(f"   Symbol: {data['symbol']}")
        print(f"   Best Bid: ${data['best_bid']:,.2f}")
        print(f"   Best Ask: ${data['best_ask']:,.2f}")
        print(f"   Spread: ${data['spread']:.2f} ({data['spread_percent']:.4f}%)")
        print(f"   Mid Price: ${data['mid_price']:,.2f}")
        print(f"   Total Bid Volume: {data['total_bid_volume']:,.4f} BTC")
        print(f"   Total Ask Volume: {data['total_ask_volume']:,.4f} BTC")
        print(f"   Bid Levels: {data['bid_count']}")
        print(f"   Ask Levels: {data['ask_count']}")
        print(f"\n   Top 5 Bids:")
        for i, (price, qty) in enumerate(data['bids'][:5], 1):
            print(f"      {i}. ${price:,.2f} - {qty:.4f} BTC")
        print(f"\n   Top 5 Asks:")
        for i, (price, qty) in enumerate(data['asks'][:5], 1):
            print(f"      {i}. ${price:,.2f} - {qty:.4f} BTC")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def test_binance_trades():
    """Test recent trades"""
    print("\n" + "="*60)
    print("TEST 4: Binance Recent Trades")
    print("="*60)
    
    interface = BinanceInterface()
    
    request = DataRequest(
        data_type=DataType.TRADES,
        parameters={"symbol": "BTC", "limit": 100}
    )
    
    try:
        response = await interface.fetch(request)
        data = response.data
        
        print(f"✅ SUCCESS")
        print(f"   Symbol: {data['symbol']}")
        print(f"   Trade Count: {data['trade_count']}")
        print(f"   Total Volume: {data['total_volume']:,.4f} BTC")
        print(f"   Buy Volume: {data['buy_volume']:,.4f} BTC")
        print(f"   Sell Volume: {data['sell_volume']:,.4f} BTC")
        print(f"   Buy/Sell Ratio: {data['buy_sell_ratio']:.2f}")
        
        print(f"\n   Most Recent 5 Trades:")
        for i, trade in enumerate(data['trades'][:5], 1):
            side_emoji = "🟢" if trade['side'] == 'buy' else "🔴"
            print(f"      {i}. {side_emoji} ${trade['price']:,.2f} - {trade['quantity']:.4f} BTC ({trade['time']})")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def test_binance_health():
    """Test health check"""
    print("\n" + "="*60)
    print("TEST 5: Binance Health Check")
    print("="*60)
    
    interface = BinanceInterface()
    
    try:
        healthy = await interface.health_check()
        if healthy:
            print(f"✅ SUCCESS - API is healthy")
            return True
        else:
            print(f"❌ FAILED - API is unhealthy")
            return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("BINANCE INTERFACE TEST SUITE")
    print("="*60)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Run all tests
    results.append(await test_binance_health())
    results.append(await test_binance_price())
    results.append(await test_binance_24h_stats())
    results.append(await test_binance_order_book())
    results.append(await test_binance_trades())
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
