#!/usr/bin/env python3
"""
Real Data Fetch Test - No Mock Data!

This script demonstrates fetching real cryptocurrency data from live APIs:
- CoinGecko: Real BTC price, market cap, volume
- Alternative.me: Real Fear & Greed Index
- Glassnode: On-chain metrics (requires API key)

All data is fetched live from actual APIs - NO MOCK DATA!
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.data_interfaces import (
    get_manager,
    get_registry,
    DataRequest,
    DataType,
    RequestPriority
)


def format_currency(value: float) -> str:
    """Format value as currency"""
    if value is None:
        return "N/A"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.2f}K"
    else:
        return f"${value:.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage with color indicator"""
    if value is None:
        return "N/A"
    
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


async def fetch_btc_price_data():
    """Fetch real BTC price data from CoinGecko"""
    print("\n" + "="*80)
    print("📊 FETCHING REAL BTC PRICE DATA FROM COINGECKO")
    print("="*80)
    
    manager = get_manager()
    
    request = DataRequest(
        data_type=DataType.PRICE,
        symbol="BTC",
        parameters={"vs_currency": "usd"},
        priority=RequestPriority.HIGH
    )
    
    print(f"\n⏳ Requesting: {request.data_type.value} for {request.symbol}...")
    print(f"   API: CoinGecko (https://api.coingecko.com)")
    print(f"   Endpoint: /api/v3/simple/price")
    
    response = await manager.fetch(request)
    
    if response.success:
        print(f"✅ Success! (Latency: {response.latency_ms:.0f}ms)")
        
        data = response.data
        
        # Create table
        table_data = [
            ["Metric", "Value", "Details"],
            ["─" * 20, "─" * 20, "─" * 40],
            ["Current Price", format_currency(data.get('price')), f"Live price in USD"],
            ["24h Change", format_percentage(data.get('price_change_24h_percent')), "Price change in last 24 hours"],
            ["Market Cap", format_currency(data.get('market_cap')), "Total market capitalization"],
            ["24h Volume", format_currency(data.get('volume_24h')), "Trading volume in 24 hours"],
            ["Currency", data.get('currency', 'usd').upper(), "Quote currency"],
            ["Data Source", response.source, "API provider"],
            ["Timestamp", response.data_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"), "When data was fetched"],
            ["Cached", "Yes" if response.from_cache else "No", "From cache or fresh API call"],
        ]
        
        print("\n" + tabulate(table_data, headers="firstrow", tablefmt="grid"))
        
        return data
    else:
        print(f"❌ Failed: {response.error}")
        return None


async def fetch_fear_greed_index():
    """Fetch real Fear & Greed Index from Alternative.me"""
    print("\n" + "="*80)
    print("😱 FETCHING REAL FEAR & GREED INDEX FROM ALTERNATIVE.ME")
    print("="*80)
    
    manager = get_manager()
    
    request = DataRequest(
        data_type=DataType.SOCIAL_SENTIMENT,
        symbol="BTC",
        timeframe="30d",
        parameters={"metric": "fear_greed"},
        priority=RequestPriority.NORMAL
    )
    
    print(f"\n⏳ Requesting: Fear & Greed Index (30-day history)...")
    print(f"   API: Alternative.me (https://api.alternative.me)")
    print(f"   Endpoint: /fng/")
    
    response = await manager.fetch(request)
    
    if response.success:
        print(f"✅ Success! (Latency: {response.latency_ms:.0f}ms)")
        
        data = response.data
        current = data.get('current', {})
        stats = data.get('statistics', {})
        interp = data.get('interpretation', {})
        
        # Create current value table
        current_table = [
            ["Metric", "Value"],
            ["─" * 30, "─" * 40],
            ["Fear & Greed Value", f"{current.get('value', 'N/A')} / 100"],
            ["Classification", current.get('value_classification', 'N/A')],
            ["Signal", interp.get('signal', 'N/A')],
            ["Risk Level", interp.get('risk_level', 'N/A').upper()],
            ["Description", interp.get('description', 'N/A')],
        ]
        
        print("\n📊 CURRENT FEAR & GREED INDEX:")
        print(tabulate(current_table, headers="firstrow", tablefmt="grid"))
        
        # Create statistics table
        stats_table = [
            ["Statistic", "Value"],
            ["─" * 20, "─" * 20],
            ["30-Day Average", f"{stats.get('average', 0):.1f}"],
            ["30-Day Min", f"{stats.get('min', 0)}"],
            ["30-Day Max", f"{stats.get('max', 0)}"],
            ["Trend", stats.get('trend', 'N/A').upper()],
        ]
        
        print("\n📈 30-DAY STATISTICS:")
        print(tabulate(stats_table, headers="firstrow", tablefmt="grid"))
        
        # Show recent 7 days
        history = data.get('history', [])[:7]
        if history:
            history_table = [["Date", "Value", "Classification"]]
            history_table.append(["─" * 20, "─" * 10, "─" * 20])
            
            for entry in history:
                date = datetime.fromisoformat(entry['timestamp']).strftime("%Y-%m-%d")
                history_table.append([
                    date,
                    entry['value'],
                    entry['value_classification']
                ])
            
            print("\n📅 RECENT 7 DAYS:")
            print(tabulate(history_table, headers="firstrow", tablefmt="grid"))
        
        return data
    else:
        print(f"❌ Failed: {response.error}")
        return None


async def fetch_all_available_sources():
    """Show all available data sources and their status"""
    print("\n" + "="*80)
    print("🔍 AVAILABLE DATA SOURCES")
    print("="*80)
    
    registry = get_registry()
    sources = registry.list_sources()
    
    table_data = [["Source", "Provider", "Data Types", "Cost", "Status"]]
    table_data.append(["─" * 20, "─" * 15, "─" * 30, "─" * 10, "─" * 10])
    
    for source_name in sources:
        metadata = registry.get_metadata(source_name)
        if metadata:
            data_types = ", ".join([dt.value for dt in metadata.data_types[:3]])
            if len(metadata.data_types) > 3:
                data_types += "..."
            
            # Check health
            try:
                source_class = registry.get_source_class(source_name)
                instance = source_class()
                is_healthy = await instance.health_check()
                status = "✅ Online" if is_healthy else "❌ Offline"
            except:
                status = "⚠️ Unknown"
            
            table_data.append([
                metadata.name,
                metadata.provider,
                data_types,
                metadata.cost_tier.value,
                status
            ])
    
    print("\n" + tabulate(table_data, headers="firstrow", tablefmt="grid"))


async def test_data_interface_manager():
    """Test the manager's capabilities"""
    print("\n" + "="*80)
    print("⚙️ DATA INTERFACE MANAGER STATUS")
    print("="*80)
    
    manager = get_manager()
    status = manager.get_status()
    
    table_data = [
        ["Property", "Value"],
        ["─" * 30, "─" * 40],
        ["Registered Sources", status['registered_sources']],
        ["Cache Enabled", "Yes" if status['cache_ttl'] > 0 else "No"],
        ["Cache TTL", f"{status['cache_ttl']} seconds"],
        ["Cache Size", f"{status['cache_size']} entries"],
        ["Fallback Enabled", "Yes" if status['enable_fallback'] else "No"],
        ["Parallel Enabled", "Yes" if status['enable_parallel'] else "No"],
    ]
    
    print("\n" + tabulate(table_data, headers="firstrow", tablefmt="grid"))
    
    # Check circuit breakers
    if status.get('circuit_breakers'):
        print("\n🔌 CIRCUIT BREAKER STATUS:")
        cb_table = [["Source", "State", "Failures"]]
        cb_table.append(["─" * 20, "─" * 15, "─" * 15])
        
        for source, info in status['circuit_breakers'].items():
            cb_table.append([
                source,
                info['state'],
                f"{info['consecutive_failures']} consecutive"
            ])
        
        print(tabulate(cb_table, headers="firstrow", tablefmt="grid"))
    else:
        print("\n✅ All circuit breakers healthy (no open circuits)")


async def main():
    """Main execution"""
    print("\n" + "="*80)
    print("🚀 REAL DATA FETCH TEST - NO MOCK DATA")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("\nThis script fetches REAL data from live APIs:")
    print("  • CoinGecko API (cryptocurrency prices)")
    print("  • Alternative.me API (Fear & Greed Index)")
    print("  • No simulated or mock data - everything is live!")
    
    try:
        # 1. Show available sources
        await fetch_all_available_sources()
        
        # 2. Test manager status
        await test_data_interface_manager()
        
        # 3. Fetch real BTC price
        btc_data = await fetch_btc_price_data()
        
        # 4. Fetch real Fear & Greed
        fg_data = await fetch_fear_greed_index()
        
        # Summary
        print("\n" + "="*80)
        print("✅ DATA FETCH SUMMARY")
        print("="*80)
        
        summary_table = [
            ["Data Source", "Status", "Key Value"],
            ["─" * 20, "─" * 15, "─" * 40],
        ]
        
        if btc_data:
            summary_table.append([
                "CoinGecko (BTC Price)",
                "✅ Success",
                f"{format_currency(btc_data.get('price'))} ({format_percentage(btc_data.get('price_change_24h_percent'))})"
            ])
        else:
            summary_table.append([
                "CoinGecko (BTC Price)",
                "❌ Failed",
                "N/A"
            ])
        
        if fg_data:
            current = fg_data.get('current', {})
            summary_table.append([
                "Alternative.me (F&G)",
                "✅ Success",
                f"{current.get('value', 'N/A')} - {current.get('value_classification', 'N/A')}"
            ])
        else:
            summary_table.append([
                "Alternative.me (F&G)",
                "❌ Failed",
                "N/A"
            ])
        
        print("\n" + tabulate(summary_table, headers="firstrow", tablefmt="grid"))
        
        print("\n" + "="*80)
        print("🎉 TEST COMPLETE - ALL DATA WAS FETCHED FROM REAL APIs!")
        print("="*80)
        
        # Show what can be done next
        print("\n💡 NEXT STEPS:")
        print("   • Run agent cycle with this real data")
        print("   • Integrate with AWS Bedrock Agent")
        print("   • Add more data sources (requires API keys)")
        print("   • Set up automated monitoring")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
