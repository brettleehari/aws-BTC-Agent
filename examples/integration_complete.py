"""
Complete Integration Example

Demonstrates the full integration of Market Hunter Agent with Data Interfaces module.
Shows how the hybrid approach combines agent autonomy with technical reliability.
"""

import asyncio
import logging
from datetime import datetime
from pprint import pprint

from src.market_hunter_agent_integrated import IntegratedMarketHunterAgent, MarketContext
from src.data_interfaces import get_manager, get_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_1_basic_initialization():
    """Example 1: Initialize the integrated agent"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Initialization")
    print("="*80 + "\n")
    
    # Create integrated agent
    agent = IntegratedMarketHunterAgent(
        agent_name="btc-market-hunter",
        learning_rate=0.1,          # 10% weight to new observations
        exploration_rate=0.2,        # 20% chance to explore
        technical_weight=0.7,        # 70% technical, 30% agent learning
        enable_cache=True,
        cache_ttl=60
    )
    
    print(f"✅ Agent initialized: {agent.agent_name}")
    print(f"   - Logical sources: {len(agent.LOGICAL_SOURCES)}")
    print(f"   - Learning rate: {agent.learning_rate}")
    print(f"   - Technical weight: {agent.technical_weight}")
    print(f"   - Agent weight: {agent.agent_weight}")
    
    # Show source mapping
    print("\n📊 Source Mapping Status:")
    for source, mapping in agent.source_mapping.items():
        status = "✅ Available" if mapping["can_fulfill"] else "❌ No implementation"
        tech_sources = ", ".join(mapping["matching_technical_sources"])
        print(f"   {source}: {status}")
        if mapping["can_fulfill"]:
            print(f"      → Technical sources: {tech_sources}")
    
    return agent


async def example_2_discover_capabilities(agent):
    """Example 2: Discover available capabilities"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Discover Available Capabilities")
    print("="*80 + "\n")
    
    registry = get_registry()
    
    # Get all capabilities
    capabilities = registry.get_all_capabilities()
    data_types = registry.get_all_data_types()
    
    print(f"📋 Available Capabilities ({len(capabilities)}):")
    for cap in capabilities:
        print(f"   - {cap.value}")
    
    print(f"\n📊 Available Data Types ({len(data_types)}):")
    for dt in data_types:
        print(f"   - {dt.value}")
    
    # Show which logical sources can be fulfilled
    print("\n🔗 Logical → Technical Source Mapping:")
    for logical_source in agent.LOGICAL_SOURCES:
        mapping = agent.source_mapping[logical_source]
        if mapping["can_fulfill"]:
            print(f"\n   {logical_source}:")
            print(f"      Can fulfill: {mapping['can_fulfill']}")
            print(f"      Technical sources: {mapping['matching_technical_sources']}")
            
            # Show requirements
            reqs = mapping["requirements"]
            print(f"      Required data types: {[dt.value for dt in reqs['data_types']]}")
            print(f"      Required capabilities: {[c.value for c in reqs['required_capabilities']]}")


async def example_3_market_context_assessment(agent):
    """Example 3: Assess market context"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Market Context Assessment")
    print("="*80 + "\n")
    
    # Scenario 1: High volatility bullish
    print("📈 Scenario 1: High Volatility Bullish")
    context1 = agent.assess_market_context(
        current_price=65000,
        price_24h_ago=61000,  # +6.6% - high volatility
        volume_24h=1500000,
        avg_volume=1000000
    )
    print(f"   Context: {context1.value}")
    print(f"   Price change: +6.6%")
    print(f"   Volume ratio: 1.5x")
    
    # Scenario 2: Low volatility
    print("\n📊 Scenario 2: Low Volatility")
    context2 = agent.assess_market_context(
        current_price=60100,
        price_24h_ago=60000,  # +0.17% - low volatility
        volume_24h=700000,
        avg_volume=1000000
    )
    print(f"   Context: {context2.value}")
    print(f"   Price change: +0.17%")
    print(f"   Volume ratio: 0.7x")
    
    # Scenario 3: Bearish trend
    print("\n📉 Scenario 3: Bearish Trend")
    context3 = agent.assess_market_context(
        current_price=57000,
        price_24h_ago=60000,  # -5% - bearish
        volume_24h=1200000,
        avg_volume=1000000
    )
    print(f"   Context: {context3.value}")
    print(f"   Price change: -5.0%")
    print(f"   Volume ratio: 1.2x")
    
    return context1


async def example_4_source_selection(agent, context):
    """Example 4: Intelligent source selection"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Context-Aware Source Selection")
    print("="*80 + "\n")
    
    print(f"🎯 Market Context: {context.value}")
    
    # Select sources for high volatility (6 sources)
    selected = agent.select_sources(context, max_sources=6)
    
    print(f"\n📍 Selected {len(selected)} sources:")
    for i, source in enumerate(selected, 1):
        mapping = agent.source_mapping[source]
        tech_sources = mapping["matching_technical_sources"]
        importance = mapping["requirements"]["importance_score"]
        
        print(f"\n   {i}. {source}")
        print(f"      Importance: {importance:.2f}")
        print(f"      Technical sources: {tech_sources}")
        
        # Show combined quality score
        combined_score = agent._get_combined_quality_score(source, context)
        print(f"      Combined quality: {combined_score:.3f}")
    
    return selected


async def example_5_query_with_rate_limits(agent):
    """Example 5: Query source with rate limit awareness"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Query with Rate Limit Awareness")
    print("="*80 + "\n")
    
    # Query whale movements
    print("🐋 Querying whaleMovements...")
    
    try:
        result = await agent.query_source_with_rate_limit_check(
            logical_source="whaleMovements",
            parameters={"threshold": 100_000_000, "timeframe": "1h"}
        )
        
        if result:
            print("✅ Query successful!")
            print(f"   Logical source: {result['source']}")
            print(f"   Technical source: {result['technical_source']}")
            print(f"   From cache: {result['from_cache']}")
            print(f"   Quality: {result['quality']:.3f}" if result['quality'] else "   Quality: N/A")
            print(f"   Timestamp: {result['timestamp']}")
            
            if result['data']:
                print(f"\n   📊 Data preview:")
                pprint(result['data'], depth=2)
        else:
            print("❌ Query failed (rate limited or unavailable)")
            
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")


async def example_6_full_agent_cycle(agent):
    """Example 6: Run complete agent cycle"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Complete Agent Cycle")
    print("="*80 + "\n")
    
    # Market data
    market_data = {
        "current_price": 63500,
        "price_24h_ago": 60000,  # +5.8% - high volatility
        "volume_24h": 1800000,
        "avg_volume": 1200000    # 1.5x volume
    }
    
    print("📊 Market Data:")
    print(f"   Current price: ${market_data['current_price']:,}")
    print(f"   Price 24h ago: ${market_data['price_24h_ago']:,}")
    print(f"   Change: +{((market_data['current_price'] - market_data['price_24h_ago']) / market_data['price_24h_ago'] * 100):.2f}%")
    print(f"   Volume: ${market_data['volume_24h']:,}")
    print(f"   Volume ratio: {market_data['volume_24h'] / market_data['avg_volume']:.2f}x")
    
    print("\n🚀 Running agent cycle...")
    
    try:
        results = await agent.run_cycle(market_data)
        
        print(f"\n✅ Cycle {results['cycle']} completed in {results['duration_seconds']:.2f}s")
        print(f"\n📋 Cycle Summary:")
        print(f"   Context: {results['context']}")
        print(f"   Trading hours: {results['trading_hours']}")
        print(f"   Sources selected: {len(results['sources_selected'])}")
        print(f"   Sources queried: {results['sources_queried']}")
        print(f"   Signals generated: {len(results['signals_generated'])}")
        
        print(f"\n📍 Selected Sources:")
        for source in results['sources_selected']:
            print(f"   - {source}")
        
        if results['signals_generated']:
            print(f"\n🚨 Generated Signals:")
            for signal in results['signals_generated']:
                print(f"\n   Type: {signal['type']}")
                print(f"   Severity: {signal['severity']}")
                print(f"   Confidence: {signal['confidence']:.2f}")
                print(f"   Source: {signal['source']}")
                print(f"   Details: {signal['details']}")
                print(f"   Action: {signal['recommended_action']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Cycle failed: {str(e)}")


async def example_7_adaptive_learning(agent):
    """Example 7: Demonstrate adaptive learning over multiple cycles"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Adaptive Learning Over Multiple Cycles")
    print("="*80 + "\n")
    
    print("🧠 Running 5 cycles to demonstrate learning...")
    
    # Simulate different market conditions
    scenarios = [
        {"current_price": 60000, "price_24h_ago": 57000, "volume_24h": 1000000, "avg_volume": 800000},
        {"current_price": 61000, "price_24h_ago": 60500, "volume_24h": 700000, "avg_volume": 800000},
        {"current_price": 58000, "price_24h_ago": 61000, "volume_24h": 1200000, "avg_volume": 800000},
        {"current_price": 59000, "price_24h_ago": 58500, "volume_24h": 750000, "avg_volume": 800000},
        {"current_price": 62000, "price_24h_ago": 59000, "volume_24h": 1500000, "avg_volume": 800000},
    ]
    
    for i, market_data in enumerate(scenarios, 1):
        print(f"\n--- Cycle {i} ---")
        price_change = ((market_data['current_price'] - market_data['price_24h_ago']) / 
                       market_data['price_24h_ago'] * 100)
        print(f"Price change: {price_change:+.2f}%")
        
        try:
            results = await agent.run_cycle(market_data)
            print(f"Context: {results['context']}")
            print(f"Sources queried: {results['sources_queried']}")
            print(f"Signals: {len(results['signals_generated'])}")
        except Exception as e:
            logger.error(f"Cycle {i} failed: {str(e)}")
    
    # Show learned metrics
    print("\n📊 Learned Source Metrics:")
    for source, metrics in agent.source_metrics.items():
        if metrics['total_calls'] > 0:
            success_rate = metrics['successful_calls'] / metrics['total_calls']
            print(f"\n   {source}:")
            print(f"      Total calls: {metrics['total_calls']}")
            print(f"      Success rate: {success_rate:.2%}")
            print(f"      Quality score: {metrics['quality_score']:.3f}")
            print(f"      Signals generated: {metrics['signals_generated']}")
            print(f"      Last used: {metrics['last_used_cycles']} cycles ago")


async def example_8_status_and_metrics(agent):
    """Example 8: Get comprehensive status and metrics"""
    print("\n" + "="*80)
    print("EXAMPLE 8: Agent Status and Metrics")
    print("="*80 + "\n")
    
    status = agent.get_source_status()
    
    print("🤖 Agent Status:")
    print(f"   Name: {agent.agent_name}")
    print(f"   Current cycle: {agent.current_cycle}")
    print(f"   Learning rate: {agent.learning_rate}")
    print(f"   Exploration rate: {agent.exploration_rate}")
    print(f"   Technical weight: {agent.technical_weight}")
    
    print("\n📊 Technical Sources:")
    for source_id in status['technical_sources']:
        print(f"   - {source_id}")
    
    print("\n🎯 Logical Sources Status:")
    for source, info in status['logical_sources'].items():
        if info['can_fulfill']:
            metrics = info['agent_metrics']
            print(f"\n   {source}:")
            print(f"      ✅ Can fulfill: {info['can_fulfill']}")
            print(f"      Technical: {info['technical_sources']}")
            print(f"      Total calls: {metrics['total_calls']}")
            if metrics['total_calls'] > 0:
                success_rate = metrics['successful_calls'] / metrics['total_calls']
                print(f"      Success rate: {success_rate:.2%}")
    
    # Manager stats
    manager_stats = status['manager_stats']
    print("\n📈 Data Interface Manager Stats:")
    print(f"   Total requests: {manager_stats.get('total_requests', 0)}")
    print(f"   Cache hits: {manager_stats.get('cache_hits', 0)}")
    print(f"   Fallback uses: {manager_stats.get('fallback_count', 0)}")


async def example_9_bedrock_integration():
    """Example 9: Bedrock Agent action handler usage"""
    print("\n" + "="*80)
    print("EXAMPLE 9: Bedrock Agent Integration")
    print("="*80 + "\n")
    
    from src.bedrock_action_handler import lambda_handler
    
    # Example 1: Discover capabilities
    print("📋 1. Discover Capabilities")
    event1 = {
        "actionGroup": "MarketDataActions",
        "apiPath": "/capabilities/discover",
        "httpMethod": "GET",
        "parameters": [],
        "requestBody": {}
    }
    
    response1 = lambda_handler(event1, None)
    print(f"   Status: {response1['response']['httpStatusCode']}")
    body1 = eval(response1['response']['responseBody']['application/json']['body'])
    print(f"   Capabilities found: {len(body1['capabilities'])}")
    print(f"   Sources found: {len(body1['sources'])}")
    
    # Example 2: List sources
    print("\n📊 2. List Data Sources")
    event2 = {
        "actionGroup": "MarketDataActions",
        "apiPath": "/capabilities/sources",
        "httpMethod": "GET",
        "parameters": [],
        "requestBody": {}
    }
    
    response2 = lambda_handler(event2, None)
    body2 = eval(response2['response']['responseBody']['application/json']['body'])
    print(f"   Total sources: {body2['total_sources']}")
    for source in body2['sources'][:3]:  # Show first 3
        print(f"\n   {source['name']}:")
        print(f"      ID: {source['source_id']}")
        print(f"      Quality: {source['quality_score']:.2f}")
        print(f"      Cost: {source['cost_tier']}")
    
    # Example 3: Get status
    print("\n🤖 3. Get Agent Status")
    event3 = {
        "actionGroup": "MarketDataActions",
        "apiPath": "/agent/status",
        "httpMethod": "GET",
        "parameters": [],
        "requestBody": {}
    }
    
    response3 = lambda_handler(event3, None)
    body3 = eval(response3['response']['responseBody']['application/json']['body'])
    print(f"   Agent: {body3['agent_name']}")
    print(f"   Current cycle: {body3['current_cycle']}")
    print(f"   Logical sources: {len(body3['logical_sources'])}")


async def main():
    """Run all examples"""
    print("\n" + "="*80)
    print(" MARKET HUNTER AGENT + DATA INTERFACES INTEGRATION")
    print(" Complete Integration Example")
    print("="*80)
    
    try:
        # Example 1: Initialize
        agent = await example_1_basic_initialization()
        
        # Example 2: Discover capabilities
        await example_2_discover_capabilities(agent)
        
        # Example 3: Market context
        context = await example_3_market_context_assessment(agent)
        
        # Example 4: Source selection
        selected = await example_4_source_selection(agent, context)
        
        # Example 5: Query with rate limits
        await example_5_query_with_rate_limits(agent)
        
        # Example 6: Full cycle
        await example_6_full_agent_cycle(agent)
        
        # Example 7: Adaptive learning
        await example_7_adaptive_learning(agent)
        
        # Example 8: Status and metrics
        await example_8_status_and_metrics(agent)
        
        # Example 9: Bedrock integration
        await example_9_bedrock_integration()
        
        print("\n" + "="*80)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Example failed: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}\n")


if __name__ == "__main__":
    asyncio.run(main())
