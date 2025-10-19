"""
Example usage of the Data Interfaces module.

Demonstrates:
- Basic data fetching
- Source discovery
- Intelligent routing
- Capability advertisement
- OpenAPI schema generation
"""

import asyncio
import json
from datetime import datetime

# Import data interfaces
from src.data_interfaces import (
    # Core types
    DataType,
    Capability,
    DataRequest,
    RequestPriority,
    
    # Registry and Manager
    get_registry,
    get_manager,
    
    # OpenAPI Generator
    OpenAPIGenerator,
    generate_bedrock_action_groups,
)


async def example_basic_fetch():
    """Example 1: Basic data fetching"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Data Fetching")
    print("="*60)
    
    manager = get_manager()
    
    # Fetch Bitcoin price
    request = DataRequest(
        data_type=DataType.PRICE,
        symbol="BTC",
        parameters={"vs_currency": "usd"}
    )
    
    print(f"\nFetching BTC price...")
    response = await manager.fetch(request)
    
    if response.success:
        print(f"✓ Success!")
        print(f"  Source: {response.source}")
        print(f"  Price: ${response.data.get('price', 'N/A'):,.2f}")
        print(f"  24h Change: {response.data.get('price_change_24h_percent', 'N/A'):.2f}%")
        print(f"  Latency: {response.latency_ms:.0f}ms")
    else:
        print(f"✗ Failed: {response.error}")


async def example_source_discovery():
    """Example 2: Discover available sources"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Source Discovery")
    print("="*60)
    
    registry = get_registry()
    
    # List all registered sources
    print("\nRegistered Data Sources:")
    sources = registry.list_sources()
    for source in sources:
        metadata = registry.get_metadata(source)
        print(f"\n  • {source}")
        print(f"    Provider: {metadata.provider}")
        print(f"    Data Types: {', '.join(dt.value for dt in metadata.data_types)}")
        print(f"    Cost: {metadata.cost_tier.value}")
        print(f"    Reliability: {metadata.reliability_score * 100:.0f}%")
    
    # Find sources for specific data type
    print("\n\nSources for On-Chain Data:")
    onchain_sources = registry.find_sources_for_data_type(DataType.ON_CHAIN)
    for source in onchain_sources:
        print(f"  • {source}")
    
    # Find sources with specific capability
    print("\n\nSources with Whale Tracking:")
    whale_sources = registry.find_sources_with_capability(Capability.WHALE_TRACKING)
    for source in whale_sources:
        print(f"  • {source}")


async def example_intelligent_routing():
    """Example 3: Intelligent source selection"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Intelligent Source Routing")
    print("="*60)
    
    registry = get_registry()
    
    # Create request
    request = DataRequest(
        data_type=DataType.PRICE,
        symbol="BTC",
        priority=RequestPriority.HIGH
    )
    
    # Get ranked sources
    print("\nSource Rankings for BTC Price:")
    rankings = registry.get_source_rankings(request)
    
    for i, rank in enumerate(rankings, 1):
        print(f"\n  {i}. {rank['name']} (Score: {rank['score']:.2f})")
        metadata = rank['metadata']
        print(f"     Response Time: {metadata.response_time.value}")
        print(f"     Cost: {metadata.cost_tier.value}")
        print(f"     Reliability: {metadata.reliability_score * 100:.0f}%")
    
    # Get recommendation
    recommendation = registry.recommend_source(request)
    print(f"\n✓ Recommended Source: {recommendation}")


async def example_sentiment_analysis():
    """Example 4: Fetch sentiment data"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Sentiment Analysis")
    print("="*60)
    
    manager = get_manager()
    
    # Fetch Fear & Greed Index
    request = DataRequest(
        data_type=DataType.SOCIAL_SENTIMENT,
        symbol="BTC",
        timeframe="30d",
        parameters={"metric": "fear_greed"}
    )
    
    print(f"\nFetching Fear & Greed Index (30-day history)...")
    response = await manager.fetch(request)
    
    if response.success:
        print(f"✓ Success!")
        print(f"  Source: {response.source}")
        
        current = response.data.get('current', {})
        stats = response.data.get('statistics', {})
        interp = response.data.get('interpretation', {})
        
        print(f"\n  Current Value: {current.get('value', 'N/A')}")
        print(f"  Classification: {current.get('value_classification', 'N/A')}")
        print(f"  Signal: {interp.get('signal', 'N/A')}")
        print(f"  Risk Level: {interp.get('risk_level', 'N/A').upper()}")
        print(f"\n  30-Day Statistics:")
        print(f"    Average: {stats.get('average', 0):.1f}")
        print(f"    Range: {stats.get('min', 0)} - {stats.get('max', 0)}")
        print(f"    Trend: {stats.get('trend', 'N/A')}")
    else:
        print(f"✗ Failed: {response.error}")


async def example_multiple_requests():
    """Example 5: Fetch from multiple sources"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Multiple Data Requests")
    print("="*60)
    
    manager = get_manager()
    
    requests = [
        DataRequest(DataType.PRICE, "BTC", parameters={"vs_currency": "usd"}),
        DataRequest(DataType.SOCIAL_SENTIMENT, "BTC", parameters={"metric": "fear_greed"}),
        DataRequest(DataType.VOLUME, "BTC", parameters={"vs_currency": "usd"}),
    ]
    
    print(f"\nFetching {len(requests)} different data points...")
    
    # Fetch all concurrently
    responses = await asyncio.gather(
        *[manager.fetch(req) for req in requests]
    )
    
    print(f"\nResults:")
    for request, response in zip(requests, responses):
        status = "✓" if response.success else "✗"
        print(f"  {status} {request.data_type.value}: {response.source} ({response.latency_ms:.0f}ms)")


def example_openapi_generation():
    """Example 6: Generate OpenAPI schemas for Bedrock"""
    print("\n" + "="*60)
    print("EXAMPLE 6: OpenAPI Schema Generation")
    print("="*60)
    
    generator = OpenAPIGenerator()
    
    # Generate complete schema
    print("\nGenerating OpenAPI 3.0 Schema...")
    schema = generator.generate_schema()
    
    print(f"  Title: {schema['info']['title']}")
    print(f"  Version: {schema['info']['version']}")
    print(f"  Endpoints: {len(schema['paths'])}")
    
    print("\n  Available Endpoints:")
    for path in schema['paths']:
        print(f"    GET {path}")
    
    # Generate action group schemas
    print("\n\nGenerating Bedrock Action Group Schemas...")
    action_groups = generate_bedrock_action_groups()
    
    for group_name, group_schema in action_groups.items():
        print(f"\n  Action Group: {group_name}")
        print(f"    Endpoints: {len(group_schema['paths'])}")
        for path in group_schema['paths']:
            print(f"      • {path}")
    
    # Save schemas (optional)
    # generator.save_schema("openapi_schema.json")
    # generator.save_action_group_schemas("action_groups/")


def example_capability_summary():
    """Example 7: Generate capability summary"""
    print("\n" + "="*60)
    print("EXAMPLE 7: Capability Summary")
    print("="*60)
    
    registry = get_registry()
    summary = registry.generate_capability_summary()
    
    print(f"\nTotal Data Sources: {summary['total_sources']}")
    
    print(f"\nData Types Coverage:")
    for data_type, sources in summary['data_types'].items():
        print(f"  • {data_type}: {len(sources)} source(s)")
    
    print(f"\nCapabilities Available:")
    for capability, sources in summary['capabilities'].items():
        print(f"  • {capability}: {len(sources)} source(s)")
    
    print(f"\nSource Details:")
    for source_info in summary['sources']:
        print(f"\n  {source_info['name']}:")
        print(f"    Data Types: {', '.join(source_info['data_types'])}")
        print(f"    Response Time: {source_info['response_time']}")
        print(f"    Cost: {source_info['cost_tier']}")


async def example_caching():
    """Example 8: Demonstrate caching"""
    print("\n" + "="*60)
    print("EXAMPLE 8: Response Caching")
    print("="*60)
    
    manager = get_manager()
    
    request = DataRequest(
        data_type=DataType.PRICE,
        symbol="BTC",
        parameters={"vs_currency": "usd"}
    )
    
    # First fetch (no cache)
    print("\nFirst fetch (no cache)...")
    response1 = await manager.fetch(request)
    print(f"  Cached: {response1.cached}")
    print(f"  Latency: {response1.latency_ms:.0f}ms")
    
    # Second fetch (should use cache)
    print("\nSecond fetch (should use cache)...")
    response2 = await manager.fetch(request)
    print(f"  Cached: {response2.cached}")
    if response2.cached:
        print(f"  Cache Age: {response2.cache_age:.1f}s")
    
    # Check manager status
    status = manager.get_status()
    print(f"\nCache Status:")
    print(f"  Size: {status['cache_size']} entries")
    print(f"  TTL: {status['cache_ttl']}s")


def example_manager_status():
    """Example 9: Manager status and monitoring"""
    print("\n" + "="*60)
    print("EXAMPLE 9: Manager Status & Monitoring")
    print("="*60)
    
    manager = get_manager()
    status = manager.get_status()
    
    print(f"\nManager Configuration:")
    print(f"  Fallback Enabled: {status['enable_fallback']}")
    print(f"  Parallel Enabled: {status['enable_parallel']}")
    print(f"  Cache TTL: {status['cache_ttl']}s")
    print(f"  Registered Sources: {status['registered_sources']}")
    
    print(f"\nCache:")
    print(f"  Entries: {status['cache_size']}")
    
    print(f"\nCircuit Breakers:")
    if status['circuit_breakers']:
        for source, info in status['circuit_breakers'].items():
            state = "OPEN" if info['is_open'] else "CLOSED"
            print(f"  {source}: {state}")
            print(f"    Consecutive Failures: {info['consecutive_failures']}")
            print(f"    Total Failures: {info['total_failures']}")
    else:
        print(f"  All sources healthy")


async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("DATA INTERFACES MODULE - EXAMPLES")
    print("="*60)
    
    # Run async examples
    await example_basic_fetch()
    await example_source_discovery()
    await example_intelligent_routing()
    await example_sentiment_analysis()
    await example_multiple_requests()
    await example_caching()
    
    # Run sync examples
    example_openapi_generation()
    example_capability_summary()
    example_manager_status()
    
    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Run all examples
    asyncio.run(main())
