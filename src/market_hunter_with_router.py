"""
Market Hunter Agent with Dynamic LLM Routing
Updated to use the LLM Router for intelligent model selection
"""

from market_hunter_agent import MarketHunterAgent, MarketContext, AgentSignal
from llm_router import LLMRouter, RoutingCriteria, TaskType, ModelCapability
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MarketHunterAgentWithRouter(MarketHunterAgent):
    """
    Enhanced Market Hunter Agent with dynamic LLM routing
    
    Automatically selects the best Bedrock model for each task:
    - Fast, cheap models for simple data extraction
    - Advanced models for complex pattern recognition
    - Expert models for critical risk assessments
    """
    
    def __init__(
        self,
        bedrock_agent_id: str,
        bedrock_agent_alias_id: str,
        region_name: str = "us-east-1",
        learning_rate: float = 0.1,
        exploration_rate: float = 0.2,
        enable_llm_routing: bool = True
    ):
        """
        Initialize agent with LLM routing capability
        
        Args:
            enable_llm_routing: If True, uses dynamic model selection. If False, uses default model.
        """
        super().__init__(
            bedrock_agent_id=bedrock_agent_id,
            bedrock_agent_alias_id=bedrock_agent_alias_id,
            region_name=region_name,
            learning_rate=learning_rate,
            exploration_rate=exploration_rate
        )
        
        self.enable_llm_routing = enable_llm_routing
        
        if enable_llm_routing:
            self.llm_router = LLMRouter(region_name=region_name)
            logger.info("LLM Router enabled - will dynamically select models based on task")
        else:
            self.llm_router = None
            logger.info("LLM Router disabled - using default Bedrock Agent model")
    
    def query_data_source(self, source_name: str, context: MarketContext) -> Optional[Dict]:
        """
        Query a data source using the most appropriate LLM for the task
        
        Overrides parent method to add intelligent model selection
        """
        if not self.enable_llm_routing:
            # Use original method if routing disabled
            return super().query_data_source(source_name, context)
        
        # Determine task type based on data source
        task_type = self._get_task_type_for_source(source_name)
        
        # Create routing criteria
        criteria = RoutingCriteria(
            task_type=task_type,
            estimated_input_tokens=self._estimate_input_tokens(source_name, context),
            estimated_output_tokens=self._estimate_output_tokens(source_name),
            min_capability=self._get_min_capability(source_name),
            region=self.region_name
        )
        
        # Build prompt
        prompt = self._build_source_query_prompt(source_name, context)
        system_prompt = self._get_system_prompt_for_source(source_name)
        
        try:
            # Use LLM router to invoke with optimal model
            response = self.llm_router.invoke_model(
                prompt=prompt,
                criteria=criteria,
                temperature=0.3,  # Lower temperature for factual data
                max_tokens=1500,
                system_prompt=system_prompt
            )
            
            logger.info(
                f"Queried {source_name} using {response['model_name']} "
                f"(Provider: {response['provider']})"
            )
            
            return {
                'source': source_name,
                'data': response['text'],
                'timestamp': context.timestamp.isoformat(),
                'success': True,
                'model_used': response['model_name'],
                'provider': response['provider'],
                'usage': response.get('usage', {})
            }
            
        except Exception as e:
            logger.error(f"Error querying {source_name} with LLM Router: {str(e)}")
            return None
    
    def analyze_results_and_generate_signals(
        self,
        results: List[Dict],
        context: MarketContext
    ) -> List[AgentSignal]:
        """
        Analyze results using an advanced model for pattern recognition
        
        Overrides parent method to use expert-level models for critical analysis
        """
        if not self.enable_llm_routing:
            return super().analyze_results_and_generate_signals(results, context)
        
        # Use advanced model for pattern recognition
        criteria = RoutingCriteria(
            task_type=TaskType.PATTERN_RECOGNITION,
            estimated_input_tokens=5000,  # Combining multiple sources
            estimated_output_tokens=2000,
            min_capability=ModelCapability.ADVANCED,
            preferred_provider="Anthropic",  # Claude excels at pattern recognition
            region=self.region_name
        )
        
        # Build comprehensive analysis prompt
        prompt = self._build_analysis_prompt(results, context)
        system_prompt = """You are an expert cryptocurrency market analyst specializing in pattern recognition and signal generation.
        
Your task is to analyze multiple data sources and identify significant patterns that warrant trading signals.

For each pattern found:
1. Assign a signal type (WHALE_ACTIVITY, EXTREME_FUNDING, etc.)
2. Determine severity (critical, high, medium, low)
3. Calculate confidence (0.0-1.0)
4. Provide clear recommended action
5. Identify target agents that should receive this signal

Be conservative - only generate signals when patterns are clear and actionable."""
        
        try:
            response = self.llm_router.invoke_model(
                prompt=prompt,
                criteria=criteria,
                temperature=0.6,  # Moderate creativity for pattern detection
                max_tokens=2000,
                system_prompt=system_prompt
            )
            
            logger.info(
                f"Pattern analysis completed using {response['model_name']} "
                f"(Provider: {response['provider']})"
            )
            
            # Parse signals from response
            # In production, you'd parse structured JSON
            # For now, use the existing logic from parent class
            signals = super().analyze_results_and_generate_signals(results, context)
            
            # Add model info to signals
            for signal in signals:
                signal.data['analysis_model'] = response['model_name']
                signal.data['analysis_provider'] = response['provider']
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in pattern analysis: {str(e)}")
            return []
    
    def _get_task_type_for_source(self, source_name: str) -> TaskType:
        """Determine the appropriate task type for a data source"""
        task_mapping = {
            'whaleMovements': TaskType.DATA_EXTRACTION,  # Simple structured data
            'narrativeShifts': TaskType.SIMPLE_ANALYSIS,  # Sentiment analysis
            'arbitrageOpportunities': TaskType.DATA_EXTRACTION,  # Price comparisons
            'influencerSignals': TaskType.SIMPLE_ANALYSIS,  # Signal classification
            'technicalBreakouts': TaskType.PATTERN_RECOGNITION,  # Chart patterns
            'institutionalFlows': TaskType.DATA_EXTRACTION,  # Flow data
            'derivativesSignals': TaskType.COMPLEX_REASONING,  # Funding analysis
            'macroSignals': TaskType.SIMPLE_ANALYSIS  # Index reading
        }
        return task_mapping.get(source_name, TaskType.SIMPLE_ANALYSIS)
    
    def _get_min_capability(self, source_name: str) -> ModelCapability:
        """Determine minimum capability needed for a data source"""
        # Most sources can use basic/intermediate models
        # Only complex analysis needs advanced models
        if source_name in ['derivativesSignals', 'technicalBreakouts']:
            return ModelCapability.INTERMEDIATE
        return ModelCapability.BASIC
    
    def _estimate_input_tokens(self, source_name: str, context: MarketContext) -> int:
        """Estimate input tokens for a query"""
        # Base prompt is ~200 tokens
        # Context adds ~100 tokens
        # Source-specific varies
        base = 300
        
        source_additions = {
            'whaleMovements': 200,
            'narrativeShifts': 300,
            'arbitrageOpportunities': 200,
            'influencerSignals': 400,
            'technicalBreakouts': 500,
            'institutionalFlows': 300,
            'derivativesSignals': 400,
            'macroSignals': 200
        }
        
        return base + source_additions.get(source_name, 300)
    
    def _estimate_output_tokens(self, source_name: str) -> int:
        """Estimate output tokens for a query"""
        # Simple data extraction: ~200 tokens
        # Analysis tasks: ~500 tokens
        if source_name in ['whaleMovements', 'arbitrageOpportunities', 'macroSignals']:
            return 200
        return 500
    
    def _build_source_query_prompt(self, source_name: str, context: MarketContext) -> str:
        """Build optimized prompt for querying a data source"""
        return f"""
Query the {source_name} data source for Bitcoin market intelligence.

Current Market Context:
- Price: ${context.price:,.2f}
- 24h Change: {context.price_change_24h:+.2f}%
- Volatility: {context.volatility.value}
- Trend: {context.trend.value}
- Trading Session: {context.trading_session.value}

Retrieve the latest data from {source_name} and extract key actionable insights.
Focus on information relevant to the current {context.volatility.value} volatility and {context.trend.value} trend.

Provide a concise, structured response with specific data points and metrics.
"""
    
    def _get_system_prompt_for_source(self, source_name: str) -> str:
        """Get optimized system prompt for each source type"""
        prompts = {
            'whaleMovements': "You are a blockchain analyst specializing in large Bitcoin transactions. Extract and summarize whale movement data.",
            'narrativeShifts': "You are a social media analyst tracking cryptocurrency sentiment. Identify trending narratives and sentiment shifts.",
            'arbitrageOpportunities': "You are a cryptocurrency arbitrage specialist. Identify price discrepancies across exchanges.",
            'influencerSignals': "You are a technical analysis expert tracking influential traders. Summarize key signals and predictions.",
            'technicalBreakouts': "You are a chartist specializing in cryptocurrency technical analysis. Identify chart patterns and breakouts.",
            'institutionalFlows': "You are an institutional flow analyst. Track large holder movements and custody changes.",
            'derivativesSignals': "You are a derivatives market specialist. Analyze funding rates, open interest, and liquidation data.",
            'macroSignals': "You are a macro market analyst. Interpret Fear & Greed Index and market-wide sentiment."
        }
        return prompts.get(source_name, "You are a cryptocurrency market data analyst.")
    
    def _build_analysis_prompt(self, results: List[Dict], context: MarketContext) -> str:
        """Build prompt for comprehensive pattern analysis"""
        results_summary = "\n\n".join([
            f"Source: {r.get('source', 'Unknown')}\n"
            f"Model Used: {r.get('model_used', 'N/A')}\n"
            f"Data: {r.get('data', '')[:500]}"
            for r in results
        ])
        
        return f"""
Analyze the following market intelligence data and identify significant patterns or signals.

MARKET CONTEXT:
- Price: ${context.price:,.2f}
- 24h Change: {context.price_change_24h:+.2f}%
- Volatility: {context.volatility.value}
- Trend: {context.trend.value}
- Session: {context.trading_session.value}

DATA FROM {len(results)} SOURCES:
{results_summary}

TASK:
Identify any of these signal types if patterns are detected:
1. WHALE_ACTIVITY - Large transactions detected (threshold: >100 BTC moved)
2. POSITIVE_NARRATIVE - Multiple bullish trending topics
3. NEGATIVE_NARRATIVE - Multiple bearish trending topics  
4. INSTITUTIONAL_ACCUMULATION - Large institutional holdings increase
5. EXTREME_FUNDING - High funding rates (liquidation risk)
6. EXTREME_GREED - Fear & Greed Index >75
7. EXTREME_FEAR - Fear & Greed Index <25
8. ARBITRAGE_OPPORTUNITY - Significant cross-exchange spreads
9. TECHNICAL_BREAKOUT - Confirmed chart pattern breakouts

For each signal:
- Signal type
- Severity (critical/high/medium/low)
- Confidence (0.0-1.0)
- Brief explanation
- Recommended action
- Target agents (bitcoin-orchestrator, risk-manager, trading-agent, portfolio-optimizer)

Only generate signals when there is clear, actionable evidence.
"""
    
    def get_llm_usage_report(self) -> Dict:
        """Get LLM usage statistics from the router"""
        if not self.enable_llm_routing or not self.llm_router:
            return {'message': 'LLM routing not enabled'}
        
        return self.llm_router.get_usage_report()
    
    def get_enhanced_performance_report(self) -> Dict:
        """Get performance report including LLM usage"""
        base_report = super().get_performance_report()
        
        if self.enable_llm_routing and self.llm_router:
            base_report['llm_usage'] = self.get_llm_usage_report()
        
        return base_report
