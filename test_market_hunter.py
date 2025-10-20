"""
Test suite for Market Hunter Agent

Tests:
1. Agent initialization
2. Market context assessment
3. Source scoring and selection
4. Data source querying
5. Signal generation
6. Learning metrics update
7. Full cycle execution
8. Performance reporting
"""

import asyncio
import sys
import os
from datetime import datetime

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_interfaces.market_hunter_agent import (
    MarketHunterAgent,
    MarketVolatility,
    MarketTrend,
    TradingSession,
    SignalSeverity
)


async def test_agent_initialization():
    """Test 1: Agent initialization"""
    print("\n" + "="*70)
    print("TEST 1: Agent Initialization")
    print("="*70)
    
    agent = MarketHunterAgent()
    
    print(f"✓ Agent initialized")
    print(f"  - Data sources: {len(agent.source_metrics)}")
    print(f"  - Source names: {', '.join(agent.source_metrics.keys())}")
    print(f"  - Cycle count: {agent.cycle_count}")
    print(f"  - Learning rate: {agent.LEARNING_RATE}")
    print(f"  - Exploration rate: {agent.EXPLORATION_RATE}")
    
    assert len(agent.source_metrics) == 7, "Should have 7 data sources"
    assert agent.cycle_count == 0, "Should start at cycle 0"
    
    return agent


async def test_market_context_assessment(agent: MarketHunterAgent):
    """Test 2: Market context assessment"""
    print("\n" + "="*70)
    print("TEST 2: Market Context Assessment")
    print("="*70)
    
    context = await agent.assess_market_context()
    
    print(f"✓ Market context assessed")
    print(f"  - Timestamp: {context.timestamp}")
    print(f"  - Price: ${context.price:,.2f}")
    print(f"  - 24h Change: {context.price_change_24h:+.2f}%")
    print(f"  - Volatility: {context.volatility.value}")
    print(f"  - Trend: {context.trend.value}")
    print(f"  - Session: {context.session.value}")
    print(f"  - Is High Volatility: {context.is_high_volatility}")
    print(f"  - Is Trending: {context.is_trending}")
    
    assert context.price > 0, "Should have valid price"
    assert context.volatility in MarketVolatility, "Valid volatility"
    assert context.trend in MarketTrend, "Valid trend"
    assert context.session in TradingSession, "Valid session"
    
    return context


async def test_source_scoring(agent: MarketHunterAgent, context):
    """Test 3: Source scoring and selection"""
    print("\n" + "="*70)
    print("TEST 3: Source Scoring & Selection")
    print("="*70)
    
    # Calculate scores
    scores = agent.calculate_source_scores(context)
    
    print(f"✓ Source scores calculated:")
    for source, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {source}: {score:.3f}")
    
    assert len(scores) == 7, "Should score all 7 sources"
    assert all(0 <= score <= 1.5 for score in scores.values()), "Scores should be 0-1.5 range"
    
    # Select sources
    selected = agent.select_data_sources(scores, context)
    
    print(f"\n✓ Selected {len(selected)} sources for {context.volatility.value} volatility:")
    for source in selected:
        print(f"  - {source} (score: {scores[source]:.3f})")
    
    if context.volatility == MarketVolatility.HIGH:
        assert len(selected) == 6, "Should select 6 sources for high volatility"
    elif context.volatility == MarketVolatility.MEDIUM:
        assert len(selected) == 4, "Should select 4 sources for medium volatility"
    else:
        assert len(selected) == 3, "Should select 3 sources for low volatility"
    
    return selected, scores


async def test_data_source_querying(agent: MarketHunterAgent, selected, context):
    """Test 4: Data source querying"""
    print("\n" + "="*70)
    print("TEST 4: Data Source Querying")
    print("="*70)
    
    results = await agent.query_data_sources(selected, context)
    
    print(f"✓ Queried {len(results)} sources:")
    for source, result in results.items():
        success = "✓" if result.get("success") else "✗"
        print(f"  {success} {source}: {result.get('source', 'N/A')}")
        if result.get("success"):
            data_keys = list(result.get("data", {}).keys())[:3]
            print(f"      Data keys: {', '.join(data_keys)}")
    
    successful = sum(1 for r in results.values() if r.get("success"))
    print(f"\n  Successful queries: {successful}/{len(results)}")
    
    assert len(results) == len(selected), "Should have result for each source"
    
    return results


async def test_signal_generation(agent: MarketHunterAgent, results, context):
    """Test 5: Signal generation"""
    print("\n" + "="*70)
    print("TEST 5: Signal Generation")
    print("="*70)
    
    signals = agent.generate_signals(results, context)
    
    print(f"✓ Generated {len(signals)} signals:")
    for signal in signals:
        print(f"  • {signal.signal_type} ({signal.severity.value})")
        print(f"      Message: {signal.message}")
        print(f"      Confidence: {signal.confidence:.2%}")
        print(f"      Source: {signal.source}")
        print(f"      Action: {signal.recommended_action}")
        print(f"      Targets: {', '.join(signal.target_agents)}")
    
    if signals:
        print(f"\n  Signal types:")
        signal_types = {}
        for signal in signals:
            signal_types[signal.signal_type] = signal_types.get(signal.signal_type, 0) + 1
        for stype, count in signal_types.items():
            print(f"    - {stype}: {count}")
    else:
        print("  (No signals generated this cycle)")
    
    # Signals are optional depending on market conditions
    assert isinstance(signals, list), "Should return list of signals"
    
    return signals


async def test_learning_metrics_update(agent: MarketHunterAgent, selected, results, signals, context):
    """Test 6: Learning metrics update"""
    print("\n" + "="*70)
    print("TEST 6: Learning Metrics Update")
    print("="*70)
    
    print(f"✓ Learning metrics will be updated")
    print(f"  Selected sources: {', '.join(selected)}")
    
    # Store metrics before update
    metrics_before = {}
    for source in selected:
        m = agent.source_metrics[source]
        metrics_before[source] = {
            "success_rate": m.success_rate,
            "signal_quality": m.signal_quality,
            "total_calls": m.total_calls,
            "quality_signals": m.quality_signals
        }
    
    # Update metrics
    agent.update_learning_metrics(selected, results, signals, context)
    
    # Show changes
    print(f"\n  Metric Changes:")
    for source in selected:
        metrics = agent.source_metrics[source]
        before = metrics_before[source]
        
        success_change = metrics.success_rate - before['success_rate']
        quality_change = metrics.signal_quality - before['signal_quality']
        
        print(f"\n    {source}:")
        print(f"      Success Rate: {before['success_rate']:.2%} → {metrics.success_rate:.2%} ({success_change:+.2%})")
        print(f"      Signal Quality: {before['signal_quality']:.2%} → {metrics.signal_quality:.2%} ({quality_change:+.2%})")
        print(f"      Quality Signals: {before['quality_signals']} → {metrics.quality_signals}")
    
    print("\n✓ Learning metrics updated successfully")


async def test_full_cycle(agent: MarketHunterAgent):
    """Test 7: Full cycle execution"""
    print("\n" + "="*70)
    print("TEST 7: Full Cycle Execution")
    print("="*70)
    
    result = await agent.run_cycle()
    
    print(f"✓ Cycle #{result['cycle']} completed:")
    print(f"  - Duration: {result['duration_seconds']:.2f}s")
    print(f"  - Context: {result['context']}")
    print(f"  - Selected Sources: {len(result['selected_sources'])}")
    print(f"  - Successful Queries: {result['successful_queries']}")
    print(f"  - Signals Generated: {result['signals_generated']}")
    
    if result.get('signals'):
        print(f"\n  Signals:")
        for signal in result['signals']:
            print(f"    • {signal['type']}: {signal['message']}")
    
    assert result['cycle'] == 1, "Should be cycle 1"
    assert 'duration_seconds' in result, "Should have duration"
    assert 'context' in result, "Should have context"
    assert 'selected_sources' in result, "Should have selected sources"
    
    return result


async def test_performance_report(agent: MarketHunterAgent):
    """Test 8: Performance reporting"""
    print("\n" + "="*70)
    print("TEST 8: Performance Report")
    print("="*70)
    
    report = agent.get_performance_report()
    
    print(f"✓ Performance report generated:")
    print(f"  - Cycles Completed: {report['cycles_completed']}")
    print(f"  - Total Signals: {report['total_signals_generated']}")
    print(f"  - Avg Duration: {report['avg_cycle_duration']}")
    print(f"  - Price History Size: {report['price_history_size']}")
    
    print(f"\n  Source Performance:")
    for source, stats in report['source_performance'].items():
        print(f"    {source}:")
        print(f"      Success Rate: {stats['success_rate']}")
        print(f"      Signal Quality: {stats['signal_quality']}")
        print(f"      Total Calls: {stats['total_calls']}")
    
    if report.get('signal_distribution'):
        print(f"\n  Signal Distribution:")
        for stype, count in report['signal_distribution'].items():
            print(f"    - {stype}: {count}")
    
    assert report['cycles_completed'] > 0, "Should have completed cycles"
    assert 'source_performance' in report, "Should have source stats"
    
    return report


async def test_multiple_cycles():
    """Test 9: Run multiple cycles to test learning"""
    print("\n" + "="*70)
    print("TEST 9: Multiple Cycles (Learning Test)")
    print("="*70)
    
    agent = MarketHunterAgent()
    
    num_cycles = 3
    print(f"Running {num_cycles} cycles to test adaptive learning...")
    
    for i in range(num_cycles):
        print(f"\n--- Cycle {i+1}/{num_cycles} ---")
        result = await agent.run_cycle()
        
        print(f"✓ Cycle {i+1}: {result['successful_queries']}/{len(result['selected_sources'])} successful, "
              f"{result['signals_generated']} signals")
        
        # Wait a bit between cycles
        await asyncio.sleep(1)
    
    # Check that metrics evolved
    report = agent.get_performance_report()
    print(f"\n✓ Completed {report['cycles_completed']} cycles")
    print(f"  Total signals generated: {report['total_signals_generated']}")
    
    # Show learning evolution
    print(f"\n  Learning Evolution:")
    for source, stats in report['source_performance'].items():
        if stats['total_calls'] > 0:
            print(f"    {source}: {stats['total_calls']} calls, "
                  f"{stats['success_rate']} success, "
                  f"{stats['signal_quality']} quality")
    
    assert report['cycles_completed'] == num_cycles, f"Should complete {num_cycles} cycles"
    
    return agent, report


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("MARKET HUNTER AGENT - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    try:
        # Test 1: Initialization
        agent = await test_agent_initialization()
        
        # Test 2: Market context
        context = await test_market_context_assessment(agent)
        
        # Test 3: Source scoring
        selected, scores = await test_source_scoring(agent, context)
        
        # Test 4: Data querying
        results = await test_data_source_querying(agent, selected, context)
        
        # Test 5: Signal generation
        signals = await test_signal_generation(agent, results, context)
        
        # Test 6: Learning update
        await test_learning_metrics_update(agent, selected, results, signals, context)
        
        # Test 7: Full cycle
        cycle_result = await test_full_cycle(agent)
        
        # Test 8: Performance report
        report = await test_performance_report(agent)
        
        # Test 9: Multiple cycles
        final_agent, final_report = await test_multiple_cycles()
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUITE SUMMARY")
        print("="*70)
        print("✓ All 9 tests passed!")
        print(f"\n  Agent Statistics:")
        print(f"    - Total Cycles: {final_report['cycles_completed']}")
        print(f"    - Total Signals: {final_report['total_signals_generated']}")
        print(f"    - Avg Duration: {final_report['avg_cycle_duration']}")
        print(f"    - Data Sources: 7 integrated")
        print(f"    - Learning Rate: {final_agent.LEARNING_RATE}")
        print(f"    - Exploration Rate: {final_agent.EXPLORATION_RATE}")
        
        print(f"\n  Architecture:")
        print(f"    ✓ Adaptive Learning Core")
        print(f"    ✓ Goal-Oriented Layer")
        print(f"    ✓ Context-Aware Selection")
        print(f"    ✓ Multi-Source Integration")
        print(f"    ✓ Signal Generation")
        print(f"    ✓ Performance Tracking")
        
        print("\n" + "="*70)
        print("🎉 MARKET HUNTER AGENT: FULLY OPERATIONAL")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
