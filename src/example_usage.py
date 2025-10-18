"""
Example usage of the Market Hunter Agent with Amazon Bedrock
"""

import json
import time
from market_hunter_agent import MarketHunterAgent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def simulate_market_data(cycle: int) -> dict:
    """
    Simulate market data for demonstration
    In production, this would fetch real market data
    """
    import random
    
    # Simulate different market conditions
    scenarios = [
        # High volatility bullish
        {
            'price': 62500 + random.uniform(-1000, 1000),
            'price_change_24h_percent': random.uniform(4, 6),
            'volume_ratio': random.uniform(1.1, 1.3)
        },
        # Medium volatility neutral
        {
            'price': 60000 + random.uniform(-500, 500),
            'price_change_24h_percent': random.uniform(-2, 2),
            'volume_ratio': random.uniform(0.9, 1.1)
        },
        # Low volatility bearish
        {
            'price': 58000 + random.uniform(-300, 300),
            'price_change_24h_percent': random.uniform(-3, -1),
            'volume_ratio': random.uniform(0.7, 0.9)
        }
    ]
    
    return scenarios[cycle % len(scenarios)]


def main():
    """
    Main execution function demonstrating the Market Hunter Agent
    """
    
    # Configuration
    # IMPORTANT: Replace these with your actual Bedrock Agent details
    BEDROCK_AGENT_ID = "YOUR_AGENT_ID"  # e.g., "ABCDEF1234"
    BEDROCK_AGENT_ALIAS_ID = "YOUR_ALIAS_ID"  # e.g., "TSTALIASID"
    AWS_REGION = "us-east-1"
    
    print("\n" + "="*80)
    print("AUTONOMOUS MARKET HUNTER AGENT")
    print("Powered by Amazon Bedrock AgentCore")
    print("="*80 + "\n")
    
    # Initialize the agent
    print("Initializing Market Hunter Agent...")
    agent = MarketHunterAgent(
        bedrock_agent_id=BEDROCK_AGENT_ID,
        bedrock_agent_alias_id=BEDROCK_AGENT_ALIAS_ID,
        region_name=AWS_REGION,
        learning_rate=0.1,  # 10% weight to new observations
        exploration_rate=0.2  # 20% chance to explore new sources
    )
    
    print(f"✓ Agent initialized")
    print(f"  - Learning Rate: {agent.learning_rate}")
    print(f"  - Exploration Rate: {agent.exploration_rate}")
    print(f"  - Available Sources: {len(agent.DATA_SOURCES)}")
    print()
    
    # Run multiple cycles to demonstrate learning
    NUM_CYCLES = 5  # In production, this runs continuously every 10 minutes
    
    print(f"Running {NUM_CYCLES} agent cycles...\n")
    
    for cycle in range(NUM_CYCLES):
        print(f"\n{'='*80}")
        print(f"CYCLE {cycle + 1} of {NUM_CYCLES}")
        print(f"{'='*80}\n")
        
        # Get market data (simulated for demo)
        market_data = simulate_market_data(cycle)
        
        print(f"Market Data:")
        print(f"  Price: ${market_data['price']:,.2f}")
        print(f"  24h Change: {market_data['price_change_24h_percent']:+.2f}%")
        print(f"  Volume Ratio: {market_data['volume_ratio']:.2f}x")
        print()
        
        try:
            # Execute agent cycle
            result = agent.execute_cycle(market_data)
            
            # Display results
            print(f"\n{'─'*80}")
            print("CYCLE RESULTS")
            print(f"{'─'*80}")
            print(f"Duration: {result['duration_seconds']:.2f}s")
            print(f"Market Condition: {result['context']['volatility']} volatility, {result['context']['trend']} trend")
            print(f"Trading Session: {result['context']['trading_session']}")
            print(f"\nSources Selected: {len(result['selected_sources'])}")
            for source in result['selected_sources']:
                score = result['source_scores'][source]
                print(f"  - {source}: {score:.3f}")
            
            print(f"\nResults Retrieved: {result['results_count']}/{len(result['selected_sources'])}")
            print(f"Signals Generated: {result['signals_generated']}")
            
            if result['signals']:
                print("\nSignals:")
                for signal in result['signals']:
                    print(f"  [{signal['severity'].upper()}] {signal['type']}")
                    print(f"    Confidence: {signal['confidence']:.2f}")
                    print(f"    {signal['message']}")
                    print(f"    Targets: {', '.join(signal['targets'])}")
            
            # Show learning progress
            if cycle > 0:
                print(f"\n{'─'*80}")
                print("LEARNING PROGRESS")
                print(f"{'─'*80}")
                print(f"{'Source':<25} {'Success Rate':<15} {'Signal Quality':<15} {'Calls':<10}")
                print(f"{'─'*65}")
                for source, metrics in result['metrics'].items():
                    if metrics['total_calls'] > 0:
                        print(
                            f"{source:<25} "
                            f"{metrics['success_rate']:<15.3f} "
                            f"{metrics['signal_quality']:<15.3f} "
                            f"{metrics['total_calls']:<10}"
                        )
            
        except Exception as e:
            logger.error(f"Error in cycle {cycle + 1}: {str(e)}")
            continue
        
        # Wait before next cycle (shortened for demo, normally 10 minutes)
        if cycle < NUM_CYCLES - 1:
            print(f"\nWaiting before next cycle...")
            time.sleep(2)  # In production: time.sleep(600) for 10 minutes
    
    # Generate final performance report
    print(f"\n\n{'='*80}")
    print("FINAL PERFORMANCE REPORT")
    print(f"{'='*80}\n")
    
    report = agent.get_performance_report()
    
    print(f"Total Cycles Completed: {report['total_cycles']}")
    print(f"Overall Efficiency: {report.get('overall_efficiency', 0):.3f}")
    print()
    
    print("Source Performance Ranking:")
    print(f"{'─'*80}")
    print(f"{'Source':<25} {'Efficiency':<12} {'Quality':<12} {'Success':<12} {'Calls':<10}")
    print(f"{'─'*80}")
    
    # Sort by efficiency
    sorted_sources = sorted(
        report['source_performance'].items(),
        key=lambda x: x[1]['efficiency'],
        reverse=True
    )
    
    for source, metrics in sorted_sources:
        print(
            f"{source:<25} "
            f"{metrics['efficiency']:<12.3f} "
            f"{metrics['signal_quality']:<12.3f} "
            f"{metrics['success_rate']:<12.3f} "
            f"{metrics['total_calls']:<10}"
        )
    
    print(f"\n{'='*80}")
    print("Agent execution complete!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
