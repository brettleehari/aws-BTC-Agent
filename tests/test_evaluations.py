"""
Evaluation framework for Market Hunter Agent

Evaluates agent performance, decision quality, and cost efficiency
using Amazon Bedrock AgentCore metrics and custom evaluation criteria.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import statistics
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from market_hunter_agent import MarketHunterAgent, DataSource, MarketContext


@dataclass
class EvaluationMetrics:
    """Metrics for evaluating agent performance"""
    # Decision quality
    source_selection_accuracy: float  # How well sources match context
    exploration_balance: float  # Balance between exploration and exploitation
    learning_effectiveness: float  # How well agent learns from experience
    
    # Performance
    avg_execution_time: float  # Average cycle time
    success_rate: float  # Percentage of successful queries
    signal_quality_score: float  # Quality of generated signals
    
    # Cost efficiency
    cost_per_cycle: float  # Average cost per cycle
    cost_per_signal: float  # Cost to generate each signal
    roi_estimate: float  # Estimated return on investment
    
    # Bedrock-specific
    bedrock_invocation_success_rate: float
    bedrock_avg_latency: float
    bedrock_error_rate: float


@dataclass
class EvaluationScenario:
    """A test scenario for evaluation"""
    name: str
    description: str
    market_data: Dict
    expected_sources: List[DataSource]
    expected_signal_types: List[str]
    context_type: str  # high_volatility, low_volatility, bullish, bearish


class AgentEvaluator:
    """Comprehensive evaluation framework for Market Hunter Agent"""
    
    def __init__(self, agent: MarketHunterAgent):
        self.agent = agent
        self.evaluation_results = []
        self.performance_history = []
    
    def create_evaluation_scenarios(self) -> List[EvaluationScenario]:
        """Create comprehensive test scenarios"""
        scenarios = [
            # High volatility scenarios
            EvaluationScenario(
                name="High Volatility Bullish",
                description="High volatility with bullish trend - should query 5-6 sources",
                market_data={
                    "btc_price": 45000,
                    "volatility_24h": 6.2,
                    "volume_24h": 35000000000,
                    "trend": "bullish"
                },
                expected_sources=[
                    DataSource.WHALE_MOVEMENTS,
                    DataSource.INSTITUTIONAL_FLOWS,
                    DataSource.SOCIAL_SENTIMENT,
                    DataSource.DERIVATIVES
                ],
                expected_signal_types=["WHALE_ACTIVITY", "INSTITUTIONAL_ACCUMULATION"],
                context_type="high_volatility_bullish"
            ),
            
            EvaluationScenario(
                name="High Volatility Bearish",
                description="High volatility with bearish trend - should prioritize risk signals",
                market_data={
                    "btc_price": 42000,
                    "volatility_24h": 7.5,
                    "volume_24h": 38000000000,
                    "trend": "bearish"
                },
                expected_sources=[
                    DataSource.DERIVATIVES,
                    DataSource.WHALE_MOVEMENTS,
                    DataSource.ON_CHAIN_METRICS
                ],
                expected_signal_types=["EXTREME_FUNDING", "WHALE_ACTIVITY"],
                context_type="high_volatility_bearish"
            ),
            
            # Low volatility scenarios
            EvaluationScenario(
                name="Low Volatility Sideways",
                description="Low volatility sideways market - should query 3-4 sources",
                market_data={
                    "btc_price": 44500,
                    "volatility_24h": 1.8,
                    "volume_24h": 18000000000,
                    "trend": "sideways"
                },
                expected_sources=[
                    DataSource.SOCIAL_SENTIMENT,
                    DataSource.NARRATIVE_SHIFTS,
                    DataSource.ON_CHAIN_METRICS
                ],
                expected_signal_types=["POSITIVE_NARRATIVE"],
                context_type="low_volatility_sideways"
            ),
            
            # Medium volatility scenarios
            EvaluationScenario(
                name="Medium Volatility Breakout",
                description="Medium volatility with potential breakout",
                market_data={
                    "btc_price": 46000,
                    "volatility_24h": 3.8,
                    "volume_24h": 28000000000,
                    "trend": "bullish"
                },
                expected_sources=[
                    DataSource.TECHNICAL_BREAKOUTS,
                    DataSource.WHALE_MOVEMENTS,
                    DataSource.SOCIAL_SENTIMENT
                ],
                expected_signal_types=["TECHNICAL_BREAKOUT", "POSITIVE_NARRATIVE"],
                context_type="medium_volatility_breakout"
            ),
            
            # Extreme scenarios
            EvaluationScenario(
                name="Extreme Fear",
                description="Market in extreme fear - should detect sentiment extreme",
                market_data={
                    "btc_price": 38000,
                    "volatility_24h": 8.5,
                    "volume_24h": 42000000000,
                    "trend": "bearish",
                    "fear_greed_index": 15  # Extreme fear
                },
                expected_sources=[
                    DataSource.MACRO_SIGNALS,
                    DataSource.DERIVATIVES,
                    DataSource.WHALE_MOVEMENTS
                ],
                expected_signal_types=["EXTREME_FEAR"],
                context_type="extreme_fear"
            ),
            
            EvaluationScenario(
                name="Extreme Greed",
                description="Market in extreme greed - should detect sentiment extreme",
                market_data={
                    "btc_price": 52000,
                    "volatility_24h": 5.2,
                    "volume_24h": 40000000000,
                    "trend": "bullish",
                    "fear_greed_index": 85  # Extreme greed
                },
                expected_sources=[
                    DataSource.MACRO_SIGNALS,
                    DataSource.SOCIAL_SENTIMENT,
                    DataSource.INSTITUTIONAL_FLOWS
                ],
                expected_signal_types=["EXTREME_GREED"],
                context_type="extreme_greed"
            ),
        ]
        
        return scenarios
    
    def evaluate_source_selection_accuracy(
        self,
        selected_sources: List[DataSource],
        expected_sources: List[DataSource],
        context: MarketContext
    ) -> float:
        """
        Evaluate how well selected sources match expected sources
        
        Returns: Score from 0.0 to 1.0
        """
        # Check if key expected sources were selected
        matches = sum(1 for src in expected_sources if src in selected_sources)
        
        # Calculate base accuracy
        if len(expected_sources) == 0:
            return 1.0
        
        base_accuracy = matches / len(expected_sources)
        
        # Bonus for appropriate number of sources based on volatility
        if context.volatility == "high":
            expected_count = 5.5
        elif context.volatility == "low":
            expected_count = 3.5
        else:
            expected_count = 4.5
        
        count_accuracy = 1.0 - abs(len(selected_sources) - expected_count) / expected_count
        count_accuracy = max(0, min(1, count_accuracy))
        
        # Weighted score
        score = 0.7 * base_accuracy + 0.3 * count_accuracy
        
        return score
    
    def evaluate_signal_quality(
        self,
        signals: List[Dict],
        expected_signal_types: List[str],
        scenario: EvaluationScenario
    ) -> float:
        """
        Evaluate quality of generated signals
        
        Returns: Score from 0.0 to 1.0
        """
        if len(expected_signal_types) == 0:
            return 1.0 if len(signals) == 0 else 0.8
        
        # Check if expected signals were generated
        generated_types = [s['signal_type'] for s in signals]
        matches = sum(1 for expected in expected_signal_types if expected in generated_types)
        
        type_accuracy = matches / len(expected_signal_types)
        
        # Check signal completeness (has required fields)
        complete_signals = 0
        for signal in signals:
            if all(key in signal for key in ['signal_type', 'severity', 'description']):
                complete_signals += 1
        
        completeness = complete_signals / len(signals) if signals else 0
        
        # Check severity is appropriate
        severity_appropriate = 0
        for signal in signals:
            if scenario.context_type in ["high_volatility_bearish", "extreme_fear"]:
                if signal.get('severity') in ['high', 'critical']:
                    severity_appropriate += 1
            else:
                severity_appropriate += 1
        
        severity_score = severity_appropriate / len(signals) if signals else 0
        
        # Weighted score
        score = 0.5 * type_accuracy + 0.3 * completeness + 0.2 * severity_score
        
        return score
    
    def evaluate_learning_effectiveness(self) -> float:
        """
        Evaluate how well agent learns over time
        
        Analyzes metric trends to see if agent improves.
        Returns: Score from 0.0 to 1.0
        """
        if len(self.performance_history) < 5:
            return 0.5  # Not enough data
        
        # Check if success rates are improving
        recent_success_rates = [
            p['success_rate'] for p in self.performance_history[-10:]
        ]
        
        if len(recent_success_rates) < 2:
            return 0.5
        
        # Calculate trend (positive = improving)
        early_avg = statistics.mean(recent_success_rates[:len(recent_success_rates)//2])
        late_avg = statistics.mean(recent_success_rates[len(recent_success_rates)//2:])
        
        improvement = (late_avg - early_avg) / max(early_avg, 0.1)
        
        # Convert to 0-1 score (0.1 improvement = perfect score)
        score = min(1.0, max(0.0, 0.5 + improvement * 5))
        
        return score
    
    def evaluate_exploration_balance(self, num_cycles: int = 10) -> float:
        """
        Evaluate balance between exploration and exploitation
        
        Returns: Score from 0.0 to 1.0
        """
        # Track which sources are queried
        source_query_counts = {source: 0 for source in DataSource}
        
        # Run several cycles
        for _ in range(num_cycles):
            context = MarketContext(
                btc_price=45000,
                volatility="medium",
                trend="sideways",
                trading_session="us",
                timestamp=datetime.utcnow()
            )
            
            selected = self.agent.select_sources(context)
            for source in selected:
                source_query_counts[source] += 1
        
        # Calculate diversity (all sources should be queried at least once)
        sources_used = sum(1 for count in source_query_counts.values() if count > 0)
        diversity_score = sources_used / len(DataSource)
        
        # Calculate balance (no source should dominate)
        total_queries = sum(source_query_counts.values())
        if total_queries == 0:
            return 0.0
        
        query_percentages = [count / total_queries for count in source_query_counts.values()]
        
        # Perfect balance would be equal percentages
        expected_percentage = 1.0 / len(DataSource)
        balance_deviation = statistics.mean([
            abs(pct - expected_percentage) for pct in query_percentages
        ])
        
        balance_score = 1.0 - (balance_deviation * len(DataSource))
        balance_score = max(0, min(1, balance_score))
        
        # Weighted score (diversity matters more than perfect balance)
        score = 0.7 * diversity_score + 0.3 * balance_score
        
        return score
    
    def evaluate_scenario(self, scenario: EvaluationScenario) -> Dict:
        """Evaluate agent on a single scenario"""
        print(f"\n🧪 Evaluating: {scenario.name}")
        print(f"   {scenario.description}")
        
        start_time = time.time()
        
        try:
            # Execute agent cycle
            result = self.agent.execute_cycle(scenario.market_data)
            
            execution_time = time.time() - start_time
            
            # Evaluate source selection
            source_accuracy = self.evaluate_source_selection_accuracy(
                result['selected_sources'],
                scenario.expected_sources,
                result['context']
            )
            
            # Evaluate signal quality
            signal_quality = self.evaluate_signal_quality(
                result['signals'],
                scenario.expected_signal_types,
                scenario
            )
            
            # Track performance
            self.performance_history.append({
                'scenario': scenario.name,
                'success_rate': 1.0,  # Successful execution
                'execution_time': execution_time,
                'signals_generated': len(result['signals']),
                'timestamp': datetime.utcnow()
            })
            
            eval_result = {
                'scenario_name': scenario.name,
                'success': True,
                'source_selection_accuracy': source_accuracy,
                'signal_quality': signal_quality,
                'execution_time': execution_time,
                'sources_selected': len(result['selected_sources']),
                'signals_generated': len(result['signals']),
                'selected_sources': [str(s) for s in result['selected_sources']],
                'signal_types': [s['signal_type'] for s in result['signals']]
            }
            
            print(f"   ✅ Success")
            print(f"   Source Accuracy: {source_accuracy:.2%}")
            print(f"   Signal Quality: {signal_quality:.2%}")
            print(f"   Execution Time: {execution_time:.2f}s")
            
        except Exception as e:
            eval_result = {
                'scenario_name': scenario.name,
                'success': False,
                'error': str(e),
                'source_selection_accuracy': 0.0,
                'signal_quality': 0.0
            }
            
            print(f"   ❌ Failed: {str(e)}")
        
        return eval_result
    
    def run_comprehensive_evaluation(self) -> EvaluationMetrics:
        """Run complete evaluation suite"""
        print("\n" + "="*80)
        print("🎯 MARKET HUNTER AGENT - COMPREHENSIVE EVALUATION")
        print("="*80)
        
        scenarios = self.create_evaluation_scenarios()
        
        # Evaluate each scenario
        for scenario in scenarios:
            result = self.evaluate_scenario(scenario)
            self.evaluation_results.append(result)
        
        # Calculate aggregate metrics
        successful_evals = [r for r in self.evaluation_results if r['success']]
        
        if len(successful_evals) == 0:
            print("\n❌ No successful evaluations")
            return None
        
        # Decision quality metrics
        avg_source_accuracy = statistics.mean([
            r['source_selection_accuracy'] for r in successful_evals
        ])
        
        avg_signal_quality = statistics.mean([
            r['signal_quality'] for r in successful_evals
        ])
        
        exploration_balance = self.evaluate_exploration_balance(num_cycles=20)
        learning_effectiveness = self.evaluate_learning_effectiveness()
        
        # Performance metrics
        avg_execution_time = statistics.mean([
            r['execution_time'] for r in successful_evals
        ])
        
        success_rate = len(successful_evals) / len(self.evaluation_results)
        
        # Cost efficiency (if router enabled)
        cost_per_cycle = 0.0
        cost_per_signal = 0.0
        
        if hasattr(self.agent, 'llm_router') and self.agent.llm_router:
            llm_report = self.agent.get_llm_usage_report()
            total_cost = llm_report['total_cost']
            total_signals = sum(r['signals_generated'] for r in successful_evals)
            
            cost_per_cycle = total_cost / len(successful_evals) if successful_evals else 0
            cost_per_signal = total_cost / total_signals if total_signals > 0 else 0
        
        # Bedrock-specific metrics
        bedrock_success_rate = success_rate  # Same as overall for now
        bedrock_avg_latency = avg_execution_time
        bedrock_error_rate = 1.0 - success_rate
        
        # Create metrics object
        metrics = EvaluationMetrics(
            source_selection_accuracy=avg_source_accuracy,
            exploration_balance=exploration_balance,
            learning_effectiveness=learning_effectiveness,
            avg_execution_time=avg_execution_time,
            success_rate=success_rate,
            signal_quality_score=avg_signal_quality,
            cost_per_cycle=cost_per_cycle,
            cost_per_signal=cost_per_signal,
            roi_estimate=0.0,  # Would need actual trading results
            bedrock_invocation_success_rate=bedrock_success_rate,
            bedrock_avg_latency=bedrock_avg_latency,
            bedrock_error_rate=bedrock_error_rate
        )
        
        # Print summary
        self.print_evaluation_summary(metrics)
        
        return metrics
    
    def print_evaluation_summary(self, metrics: EvaluationMetrics):
        """Print formatted evaluation summary"""
        print("\n" + "="*80)
        print("📊 EVALUATION SUMMARY")
        print("="*80)
        
        print("\n🎯 Decision Quality")
        print(f"   Source Selection Accuracy: {metrics.source_selection_accuracy:.2%}")
        print(f"   Signal Quality Score:      {metrics.signal_quality_score:.2%}")
        print(f"   Exploration Balance:       {metrics.exploration_balance:.2%}")
        print(f"   Learning Effectiveness:    {metrics.learning_effectiveness:.2%}")
        
        print("\n⚡ Performance")
        print(f"   Success Rate:              {metrics.success_rate:.2%}")
        print(f"   Avg Execution Time:        {metrics.avg_execution_time:.2f}s")
        print(f"   Bedrock Invocation Rate:   {metrics.bedrock_invocation_success_rate:.2%}")
        print(f"   Bedrock Avg Latency:       {metrics.bedrock_avg_latency:.2f}s")
        print(f"   Bedrock Error Rate:        {metrics.bedrock_error_rate:.2%}")
        
        print("\n💰 Cost Efficiency")
        print(f"   Cost per Cycle:            ${metrics.cost_per_cycle:.4f}")
        print(f"   Cost per Signal:           ${metrics.cost_per_signal:.4f}")
        
        print("\n🏆 Overall Grade")
        overall_score = (
            0.3 * metrics.source_selection_accuracy +
            0.2 * metrics.signal_quality_score +
            0.2 * metrics.exploration_balance +
            0.15 * metrics.learning_effectiveness +
            0.15 * metrics.success_rate
        )
        
        if overall_score >= 0.9:
            grade = "A+ (Excellent)"
        elif overall_score >= 0.8:
            grade = "A (Very Good)"
        elif overall_score >= 0.7:
            grade = "B (Good)"
        elif overall_score >= 0.6:
            grade = "C (Acceptable)"
        else:
            grade = "D (Needs Improvement)"
        
        print(f"   Overall Score: {overall_score:.2%} - {grade}")
        print("="*80)
    
    def export_results(self, filename: str = "evaluation_results.json"):
        """Export evaluation results to JSON file"""
        export_data = {
            'evaluation_timestamp': datetime.utcnow().isoformat(),
            'agent_configuration': {
                'bedrock_agent_id': self.agent.bedrock_agent_id,
                'learning_rate': self.agent.learning_rate,
                'exploration_rate': self.agent.exploration_rate,
            },
            'scenario_results': self.evaluation_results,
            'performance_history': [
                {**p, 'timestamp': p['timestamp'].isoformat()}
                for p in self.performance_history
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\n💾 Results exported to: {filename}")


def main():
    """Run evaluation"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate Market Hunter Agent')
    parser.add_argument('--agent-id', required=False, help='Bedrock Agent ID')
    parser.add_argument('--alias-id', required=False, help='Bedrock Agent Alias ID')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--use-router', action='store_true', help='Enable LLM routing')
    parser.add_argument('--export', default='evaluation_results.json', help='Export filename')
    
    args = parser.parse_args()
    
    # Create agent
    if args.use_router:
        agent = MarketHunterAgentWithRouter(
            bedrock_agent_id=args.agent_id or os.getenv('BEDROCK_AGENT_ID', 'test-agent'),
            bedrock_agent_alias_id=args.alias_id or os.getenv('BEDROCK_AGENT_ALIAS_ID', 'test-alias'),
            region_name=args.region,
            enable_llm_routing=True
        )
    else:
        agent = MarketHunterAgent(
            bedrock_agent_id=args.agent_id or os.getenv('BEDROCK_AGENT_ID', 'test-agent'),
            bedrock_agent_alias_id=args.alias_id or os.getenv('BEDROCK_AGENT_ALIAS_ID', 'test-alias'),
            region_name=args.region
        )
    
    # Run evaluation
    evaluator = AgentEvaluator(agent)
    metrics = evaluator.run_comprehensive_evaluation()
    
    # Export results
    if metrics:
        evaluator.export_results(args.export)


if __name__ == '__main__':
    main()
