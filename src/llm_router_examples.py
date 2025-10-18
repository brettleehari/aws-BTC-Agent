"""
Example usage of the LLM Router with Market Hunter Agent
Demonstrates dynamic model selection for different tasks
"""

import logging
from llm_router import (
    LLMRouter,
    RoutingCriteria,
    TaskType,
    ModelCapability,
    BedrockModelRegistry
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_1_simple_data_extraction():
    """Example: Extract whale transaction data (use fast, cheap model)"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Simple Data Extraction (Fast & Cheap)")
    print("="*80)
    
    router = LLMRouter(region_name="us-east-1")
    
    criteria = RoutingCriteria(
        task_type=TaskType.DATA_EXTRACTION,
        estimated_input_tokens=500,
        estimated_output_tokens=200,
        max_cost_per_request=0.001,  # Max $0.001 per request
        max_latency_ms=1000,  # Need fast response
        min_capability=ModelCapability.BASIC
    )
    
    prompt = """
    Parse the following whale transaction data and extract key fields:
    
    Transaction: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh sent 150.5 BTC 
    to bc1q5j9w3kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh at 2025-10-18 14:30:00 UTC
    
    Extract: amount, from_address, to_address, timestamp
    """
    
    response = router.invoke_model(
        prompt=prompt,
        criteria=criteria,
        temperature=0.1,  # Low temperature for structured extraction
        max_tokens=200
    )
    
    print(f"\nSelected Model: {response['model_name']}")
    print(f"Provider: {response['provider']}")
    print(f"\nResponse:\n{response['text'][:300]}")
    print(f"\nUsage: {response.get('usage', {})}")


def example_2_complex_pattern_recognition():
    """Example: Detect complex market patterns (use advanced model)"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Complex Pattern Recognition (Advanced Reasoning)")
    print("="*80)
    
    router = LLMRouter(region_name="us-east-1")
    
    criteria = RoutingCriteria(
        task_type=TaskType.PATTERN_RECOGNITION,
        estimated_input_tokens=3000,
        estimated_output_tokens=1000,
        min_capability=ModelCapability.ADVANCED,
        preferred_provider="Anthropic"  # Prefer Claude for complex reasoning
    )
    
    prompt = """
    Analyze the following market data and identify patterns:
    
    - Whale movements: 3 large transactions >100 BTC in last 2 hours
    - Funding rate: 0.06% (extremely high, indicating bullish pressure)
    - Social sentiment: 5 bullish trending topics on Twitter
    - Institutional flows: $50M inflow to Coinbase custody
    - Fear & Greed Index: 78 (extreme greed)
    - Technical: BTC broke above $62,500 resistance
    
    What patterns do you see? What signals should be generated?
    """
    
    response = router.invoke_model(
        prompt=prompt,
        criteria=criteria,
        temperature=0.7,
        max_tokens=1000,
        system_prompt="You are an expert cryptocurrency market analyst specializing in pattern recognition."
    )
    
    print(f"\nSelected Model: {response['model_name']}")
    print(f"Provider: {response['provider']}")
    print(f"\nResponse:\n{response['text'][:500]}...")
    print(f"\nUsage: {response.get('usage', {})}")


def example_3_risk_assessment():
    """Example: Assess trading risks (use expert model)"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Risk Assessment (Expert Level)")
    print("="*80)
    
    router = LLMRouter(region_name="us-east-1")
    
    criteria = RoutingCriteria(
        task_type=TaskType.RISK_ASSESSMENT,
        estimated_input_tokens=2000,
        estimated_output_tokens=800,
        min_capability=ModelCapability.EXPERT  # Need best reasoning
    )
    
    prompt = """
    Assess the risk of entering a long Bitcoin position given:
    
    Current Context:
    - BTC Price: $62,500 (+4.2% in 24h)
    - High volatility detected (>5% daily change)
    - Extreme funding rate (0.06% - risk of long liquidations)
    - Extreme greed (Fear & Greed: 78)
    - Recent whale accumulation (+2,500 BTC)
    
    Risk Factors to Consider:
    1. Liquidation risk from extreme funding
    2. Market overheating (extreme greed)
    3. Volatility impact on stop losses
    4. Counterparty risks
    
    Provide risk score (1-10) and mitigation strategies.
    """
    
    response = router.invoke_model(
        prompt=prompt,
        criteria=criteria,
        temperature=0.5,
        max_tokens=800,
        system_prompt="You are a professional risk manager for cryptocurrency trading operations."
    )
    
    print(f"\nSelected Model: {response['model_name']}")
    print(f"Provider: {response['provider']}")
    print(f"\nResponse:\n{response['text'][:500]}...")
    print(f"\nUsage: {response.get('usage', {})}")


def example_4_cost_optimized_bulk_analysis():
    """Example: Analyze many simple queries with cost optimization"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Bulk Analysis (Cost Optimized)")
    print("="*80)
    
    router = LLMRouter(region_name="us-east-1")
    
    # Process 10 simple sentiment analysis tasks with minimal cost
    sentiments = [
        "Bitcoin to the moon! 🚀",
        "Major correction incoming, sell everything",
        "Steady accumulation by institutions",
        "Fear in the market, good time to buy?",
        "Breakout confirmed, targeting $70k"
    ]
    
    criteria = RoutingCriteria(
        task_type=TaskType.SIMPLE_ANALYSIS,
        estimated_input_tokens=100,
        estimated_output_tokens=50,
        max_cost_per_request=0.0001,  # Very tight budget
        min_capability=ModelCapability.BASIC
    )
    
    total_cost = 0
    for i, sentiment in enumerate(sentiments, 1):
        prompt = f"Classify sentiment (bullish/bearish/neutral): {sentiment}"
        
        response = router.invoke_model(
            prompt=prompt,
            criteria=criteria,
            temperature=0.1,
            max_tokens=50
        )
        
        usage = response.get('usage', {})
        input_tokens = usage.get('input_tokens', 0)
        output_tokens = usage.get('output_tokens', 0)
        
        # Calculate cost
        model = BedrockModelRegistry.get_model_by_id(response['model_used'])
        cost = (input_tokens / 1000) * model.cost_per_1k_input + (output_tokens / 1000) * model.cost_per_1k_output
        total_cost += cost
        
        print(f"\n{i}. Sentiment: {sentiment}")
        print(f"   Model: {response['model_name']}")
        print(f"   Classification: {response['text'][:100]}")
        print(f"   Cost: ${cost:.6f}")
    
    print(f"\n{'─'*80}")
    print(f"Total Cost for 5 analyses: ${total_cost:.6f}")
    print(f"Average cost per analysis: ${total_cost/5:.6f}")


def example_5_long_context_analysis():
    """Example: Analyze long documents with large context window"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Long Context Analysis (200K tokens)")
    print("="*80)
    
    router = LLMRouter(region_name="us-east-1")
    
    criteria = RoutingCriteria(
        task_type=TaskType.LONG_CONTEXT,
        estimated_input_tokens=50000,  # Very long input
        estimated_output_tokens=2000,
        min_capability=ModelCapability.ADVANCED
    )
    
    # Simulate long document (truncated for demo)
    prompt = """
    Analyze the following comprehensive market report (50,000 tokens):
    
    [Simulated long document with multiple data sources...]
    
    Summary of 8 data sources:
    1. Whale movements: [detailed data]
    2. Narrative shifts: [detailed data]
    3. Arbitrage opportunities: [detailed data]
    ... (continues for 50K tokens)
    
    Synthesize all data and provide top 3 trading signals.
    """
    
    selected_model = router.select_model(criteria)
    
    print(f"\nSelected Model: {selected_model.name}")
    print(f"Context Window: {selected_model.context_window:,} tokens")
    print(f"Cost per 1K input: ${selected_model.cost_per_1k_input}")
    print(f"Estimated cost for 50K input + 2K output:")
    print(f"  ${(50000/1000) * selected_model.cost_per_1k_input + (2000/1000) * selected_model.cost_per_1k_output:.4f}")


def example_6_provider_preference():
    """Example: Prefer specific provider"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Provider Preference (Meta Llama)")
    print("="*80)
    
    router = LLMRouter(region_name="us-east-1")
    
    criteria = RoutingCriteria(
        task_type=TaskType.SIGNAL_GENERATION,
        estimated_input_tokens=1000,
        estimated_output_tokens=500,
        preferred_provider="Meta",  # Prefer Meta Llama models
        min_capability=ModelCapability.INTERMEDIATE
    )
    
    selected_model = router.select_model(criteria)
    
    print(f"\nSelected Model: {selected_model.name}")
    print(f"Provider: {selected_model.provider}")
    print(f"Model ID: {selected_model.model_id}")


def example_7_usage_tracking():
    """Example: Track usage across multiple invocations"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Usage Tracking & Cost Analytics")
    print("="*80)
    
    router = LLMRouter(region_name="us-east-1")
    
    # Make several different requests
    tasks = [
        (TaskType.SIMPLE_ANALYSIS, 100, 50),
        (TaskType.COMPLEX_REASONING, 2000, 800),
        (TaskType.DATA_EXTRACTION, 300, 100),
        (TaskType.PATTERN_RECOGNITION, 3000, 1000),
    ]
    
    for task_type, input_tokens, output_tokens in tasks:
        criteria = RoutingCriteria(
            task_type=task_type,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens
        )
        
        # Simulate model invocation (not actually calling API for demo)
        model = router.select_model(criteria)
        
        # Simulate response
        simulated_response = {
            'text': 'Sample response',
            'usage': {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens
            }
        }
        
        router._track_usage(model, simulated_response)
    
    # Get usage report
    report = router.get_usage_report()
    
    print("\nUsage Report:")
    print(f"{'─'*80}")
    print(f"Total Invocations: {report['total_invocations']}")
    print(f"Total Cost: ${report['total_cost']:.6f}")
    print(f"\nBreakdown by Model:")
    for model_id, stats in report['usage_by_model'].items():
        print(f"\n  {stats['model_name']}:")
        print(f"    Invocations: {stats['invocations']}")
        print(f"    Input Tokens: {stats['total_input_tokens']:,}")
        print(f"    Output Tokens: {stats['total_output_tokens']:,}")
        print(f"    Total Cost: ${stats['total_cost']:.6f}")


def show_all_models():
    """Display all available models"""
    print("\n" + "="*80)
    print("ALL AVAILABLE BEDROCK MODELS")
    print("="*80)
    
    models = BedrockModelRegistry.get_all_models()
    
    for model in models:
        print(f"\n{model.name} ({model.provider})")
        print(f"  Model ID: {model.model_id}")
        print(f"  Capability: {model.capability.value}")
        print(f"  Context Window: {model.context_window:,} tokens")
        print(f"  Cost: ${model.cost_per_1k_input:.5f} in / ${model.cost_per_1k_output:.5f} out per 1K tokens")
        print(f"  Speed Score: {model.speed_score}/10")
        print(f"  Reasoning Score: {model.reasoning_score}/10")
        print(f"  Best For: {', '.join(t.value for t in model.best_for)}")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("BEDROCK LLM ROUTER - EXAMPLES")
    print("="*80)
    
    # Show all available models first
    show_all_models()
    
    # Note: Examples 1-3 require actual AWS credentials and will make API calls
    # Comment them out if you just want to see model selection logic
    
    # example_1_simple_data_extraction()
    # example_2_complex_pattern_recognition()
    # example_3_risk_assessment()
    # example_4_cost_optimized_bulk_analysis()
    
    # These examples just show model selection without API calls
    example_5_long_context_analysis()
    example_6_provider_preference()
    example_7_usage_tracking()
    
    print("\n" + "="*80)
    print("EXAMPLES COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
