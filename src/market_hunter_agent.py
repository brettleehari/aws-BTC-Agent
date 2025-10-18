"""
Autonomous Market Hunter Agent using Amazon Bedrock AgentCore
A truly agentic Bitcoin market intelligence system with autonomous decision-making
"""

import json
import boto3
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import random
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketTrend(Enum):
    """Market trend types"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class Volatility(Enum):
    """Market volatility levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TradingSession(Enum):
    """Trading time sessions"""
    ASIAN = "asian"
    EUROPEAN = "european"
    AMERICAN = "american"
    OVERLAP = "overlap"


class SignalSeverity(Enum):
    """Signal severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class MarketContext:
    """Current market conditions"""
    price: float
    price_change_24h: float
    volatility: Volatility
    trend: MarketTrend
    volume_ratio: float  # Ratio to average volume
    trading_session: TradingSession
    timestamp: datetime


@dataclass
class SourceMetrics:
    """Performance metrics for each data source"""
    name: str
    success_rate: float = 0.5  # % of calls that return data
    signal_quality: float = 0.5  # % that contribute to actionable signals
    last_used_cycles_ago: int = 0  # Cycles since last use
    total_calls: int = 0
    successful_calls: int = 0
    quality_contributions: int = 0


@dataclass
class AgentSignal:
    """Signal generated for other agents"""
    signal_type: str
    severity: SignalSeverity
    confidence: float
    message: str
    recommended_action: str
    target_agents: List[str]
    data: Dict
    timestamp: datetime


class MarketHunterAgent:
    """
    Autonomous Market Hunter Agent using Amazon Bedrock AgentCore
    
    This agent independently decides which data sources to query based on:
    - Current market conditions
    - Historical performance data
    - Learning from past results
    - Context-aware optimization
    """
    
    # Available data sources
    DATA_SOURCES = [
        "whaleMovements",
        "narrativeShifts",
        "arbitrageOpportunities",
        "influencerSignals",
        "technicalBreakouts",
        "institutionalFlows",
        "derivativesSignals",
        "macroSignals"
    ]
    
    def __init__(
        self,
        bedrock_agent_id: str,
        bedrock_agent_alias_id: str,
        region_name: str = "us-east-1",
        learning_rate: float = 0.1,
        exploration_rate: float = 0.2
    ):
        """
        Initialize the Market Hunter Agent
        
        Args:
            bedrock_agent_id: Amazon Bedrock Agent ID
            bedrock_agent_alias_id: Amazon Bedrock Agent Alias ID
            region_name: AWS region
            learning_rate: Weight given to new observations (0.0-1.0)
            exploration_rate: Probability of exploring underused sources (0.0-1.0)
        """
        self.bedrock_agent_id = bedrock_agent_id
        self.bedrock_agent_alias_id = bedrock_agent_alias_id
        self.region_name = region_name
        self.learning_rate = learning_rate
        self.exploration_rate = exploration_rate
        
        # Initialize AWS clients
        self.bedrock_agent_runtime = boto3.client(
            'bedrock-agent-runtime',
            region_name=region_name
        )
        self.bedrock_agent = boto3.client(
            'bedrock-agent',
            region_name=region_name
        )
        
        # Initialize source metrics
        self.source_metrics = {
            source: SourceMetrics(name=source)
            for source in self.DATA_SOURCES
        }
        
        # Session tracking
        self.session_id = None
        self.execution_count = 0
        
        logger.info(f"Market Hunter Agent initialized with agent_id={bedrock_agent_id}")
    
    def assess_market_context(self, market_data: Dict) -> MarketContext:
        """
        Assess current market conditions
        
        Args:
            market_data: Current market data including price, volume, etc.
            
        Returns:
            MarketContext with assessed conditions
        """
        price = market_data.get('price', 0)
        price_change = market_data.get('price_change_24h_percent', 0)
        volume_ratio = market_data.get('volume_ratio', 1.0)
        
        # Determine volatility
        if abs(price_change) > 5:
            volatility = Volatility.HIGH
        elif abs(price_change) > 2:
            volatility = Volatility.MEDIUM
        else:
            volatility = Volatility.LOW
        
        # Determine trend
        if price_change > 2:
            trend = MarketTrend.BULLISH
        elif price_change < -2:
            trend = MarketTrend.BEARISH
        else:
            trend = MarketTrend.NEUTRAL
        
        # Determine trading session based on UTC time
        current_hour = datetime.now(timezone.utc).hour
        if 0 <= current_hour < 8:
            trading_session = TradingSession.ASIAN
        elif 8 <= current_hour < 13:
            trading_session = TradingSession.OVERLAP
        elif 13 <= current_hour < 16:
            trading_session = TradingSession.EUROPEAN
        else:
            trading_session = TradingSession.AMERICAN
        
        context = MarketContext(
            price=price,
            price_change_24h=price_change,
            volatility=volatility,
            trend=trend,
            volume_ratio=volume_ratio,
            trading_session=trading_session,
            timestamp=datetime.now(timezone.utc)
        )
        
        logger.info(f"Market context assessed: {context}")
        return context
    
    def calculate_source_scores(self, context: MarketContext) -> Dict[str, float]:
        """
        Calculate relevance scores for each data source based on context
        
        Args:
            context: Current market context
            
        Returns:
            Dictionary of source names to scores
        """
        scores = {}
        
        for source_name, metrics in self.source_metrics.items():
            # Base score from historical performance
            base_score = (metrics.success_rate + metrics.signal_quality) / 2
            
            # Context-based bonuses
            context_bonus = 0.0
            
            # Volatility bonuses
            if context.volatility == Volatility.HIGH:
                if source_name in ['derivativesSignals', 'whaleMovements']:
                    context_bonus += 0.4
            
            # Trend bonuses
            if context.trend == MarketTrend.BULLISH:
                if source_name in ['institutionalFlows', 'influencerSignals']:
                    context_bonus += 0.2
            elif context.trend == MarketTrend.BEARISH:
                if source_name in ['derivativesSignals', 'whaleMovements']:
                    context_bonus += 0.2
            else:  # NEUTRAL
                if source_name in ['macroSignals', 'narrativeShifts']:
                    context_bonus += 0.2
            
            # Trading session bonuses
            if context.trading_session == TradingSession.ASIAN:
                if source_name == 'whaleMovements':
                    context_bonus += 0.3
            elif context.trading_session == TradingSession.EUROPEAN:
                if source_name == 'narrativeShifts':
                    context_bonus += 0.3
            elif context.trading_session == TradingSession.AMERICAN:
                if source_name == 'institutionalFlows':
                    context_bonus += 0.3
            elif context.trading_session == TradingSession.OVERLAP:
                if source_name == 'arbitrageOpportunities':
                    context_bonus += 0.3
            
            # Recency bonus (encourage exploration of unused sources)
            recency_bonus = min(metrics.last_used_cycles_ago * 0.05, 0.2)
            
            # Exploration bonus (random chance to boost underused sources)
            exploration_bonus = 0.0
            if random.random() < self.exploration_rate:
                exploration_bonus = random.uniform(0.1, 0.3)
            
            # Calculate final score
            final_score = min(base_score + context_bonus + recency_bonus + exploration_bonus, 1.0)
            scores[source_name] = final_score
        
        logger.info(f"Source scores calculated: {scores}")
        return scores
    
    def select_sources(self, context: MarketContext, scores: Dict[str, float]) -> List[str]:
        """
        Select which data sources to query based on context and scores
        
        Args:
            context: Current market context
            scores: Source relevance scores
            
        Returns:
            List of selected source names
        """
        # Determine number of sources based on volatility
        if context.volatility == Volatility.HIGH:
            num_sources = 6
        elif context.volatility == Volatility.MEDIUM:
            num_sources = 4
        else:
            num_sources = 3
        
        # Sort sources by score and select top N
        sorted_sources = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        selected = [source for source, score in sorted_sources[:num_sources]]
        
        logger.info(f"Selected {len(selected)} sources: {selected}")
        return selected
    
    def invoke_bedrock_agent(self, prompt: str, session_attributes: Optional[Dict] = None) -> Dict:
        """
        Invoke Amazon Bedrock Agent to process market data
        
        Args:
            prompt: The prompt/query for the agent
            session_attributes: Optional session attributes
            
        Returns:
            Agent response
        """
        try:
            # Create or reuse session
            if not self.session_id:
                self.session_id = f"market-hunter-{datetime.now(timezone.utc).isoformat()}"
            
            request_params = {
                'agentId': self.bedrock_agent_id,
                'agentAliasId': self.bedrock_agent_alias_id,
                'sessionId': self.session_id,
                'inputText': prompt
            }
            
            if session_attributes:
                request_params['sessionState'] = {
                    'sessionAttributes': session_attributes
                }
            
            logger.info(f"Invoking Bedrock Agent with prompt: {prompt[:100]}...")
            
            response = self.bedrock_agent_runtime.invoke_agent(**request_params)
            
            # Process streaming response
            result = {
                'completion': '',
                'trace': [],
                'citations': []
            }
            
            event_stream = response.get('completion', [])
            for event in event_stream:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        result['completion'] += chunk['bytes'].decode('utf-8')
                
                if 'trace' in event:
                    result['trace'].append(event['trace'])
            
            logger.info(f"Agent response received: {result['completion'][:200]}...")
            return result
            
        except Exception as e:
            logger.error(f"Error invoking Bedrock Agent: {str(e)}")
            raise
    
    def query_data_source(self, source_name: str, context: MarketContext) -> Optional[Dict]:
        """
        Query a specific data source using Bedrock Agent
        
        Args:
            source_name: Name of the data source to query
            context: Current market context
            
        Returns:
            Data from the source or None if unsuccessful
        """
        # Construct prompt for the agent
        prompt = f"""
        Query the {source_name} data source for Bitcoin market intelligence.
        
        Current Market Context:
        - Price: ${context.price:,.2f}
        - 24h Change: {context.price_change_24h:+.2f}%
        - Volatility: {context.volatility.value}
        - Trend: {context.trend.value}
        - Trading Session: {context.trading_session.value}
        
        Please retrieve and analyze the latest data from {source_name}.
        Focus on actionable insights relevant to the current market conditions.
        """
        
        session_attributes = {
            'source': source_name,
            'context': json.dumps(asdict(context), default=str)
        }
        
        try:
            response = self.invoke_bedrock_agent(prompt, session_attributes)
            
            # Parse response
            if response.get('completion'):
                return {
                    'source': source_name,
                    'data': response['completion'],
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'success': True
                }
            return None
            
        except Exception as e:
            logger.error(f"Error querying {source_name}: {str(e)}")
            return None
    
    def analyze_results_and_generate_signals(
        self,
        results: List[Dict],
        context: MarketContext
    ) -> List[AgentSignal]:
        """
        Analyze query results and generate signals for other agents
        
        Args:
            results: List of query results from data sources
            context: Current market context
            
        Returns:
            List of generated signals
        """
        signals = []
        
        # Use Bedrock Agent to analyze combined results
        results_summary = json.dumps([
            {'source': r.get('source'), 'data': r.get('data', '')[:500]}
            for r in results
        ], indent=2)
        
        analysis_prompt = f"""
        Analyze the following market intelligence data and identify significant patterns or signals:
        
        Market Context:
        - Price: ${context.price:,.2f}
        - 24h Change: {context.price_change_24h:+.2f}%
        - Volatility: {context.volatility.value}
        - Trend: {context.trend.value}
        
        Data from Sources:
        {results_summary}
        
        Identify any of the following signal types and provide details:
        1. WHALE_ACTIVITY - Large transactions detected
        2. POSITIVE_NARRATIVE - Bullish trending topics
        3. NEGATIVE_NARRATIVE - Bearish trending topics
        4. INSTITUTIONAL_ACCUMULATION - Large institutional holdings
        5. EXTREME_FUNDING - High funding rates (liquidation risk)
        6. EXTREME_GREED - Fear & Greed Index >75
        7. EXTREME_FEAR - Fear & Greed Index <25
        8. ARBITRAGE_OPPORTUNITY - Cross-exchange spreads
        9. TECHNICAL_BREAKOUT - Chart pattern breakouts
        
        For each signal, provide:
        - Signal type
        - Severity (critical/high/medium/low)
        - Confidence (0.0-1.0)
        - Recommended action
        - Relevant data
        
        Format as JSON array.
        """
        
        try:
            response = self.invoke_bedrock_agent(analysis_prompt)
            
            # Parse agent's analysis
            # In a real implementation, you would parse the JSON response
            # For now, we'll demonstrate the structure
            
            # Example signal generation based on simple heuristics
            for result in results:
                source = result.get('source', '')
                data_text = result.get('data', '').lower()
                
                # Detect whale activity
                if source == 'whaleMovements' and 'large transaction' in data_text:
                    signals.append(AgentSignal(
                        signal_type='WHALE_ACTIVITY',
                        severity=SignalSeverity.HIGH,
                        confidence=0.85,
                        message='Large whale transactions detected',
                        recommended_action='Monitor for potential market impact',
                        target_agents=['bitcoin-orchestrator', 'risk-manager'],
                        data={'source': source, 'context': asdict(context)},
                        timestamp=datetime.now(timezone.utc)
                    ))
                
                # Detect extreme sentiment
                if source == 'macroSignals':
                    if 'fear' in data_text and 'extreme' in data_text:
                        signals.append(AgentSignal(
                            signal_type='EXTREME_FEAR',
                            severity=SignalSeverity.MEDIUM,
                            confidence=0.75,
                            message='Extreme fear detected in market sentiment',
                            recommended_action='Consider contrarian opportunities',
                            target_agents=['bitcoin-orchestrator', 'trading-agent'],
                            data={'source': source, 'context': asdict(context)},
                            timestamp=datetime.now(timezone.utc)
                        ))
            
            logger.info(f"Generated {len(signals)} signals")
            
        except Exception as e:
            logger.error(f"Error analyzing results: {str(e)}")
        
        return signals
    
    def update_metrics(self, source_name: str, success: bool, quality_contribution: bool):
        """
        Update performance metrics for a data source using adaptive learning
        
        Args:
            source_name: Name of the source
            success: Whether the query was successful
            quality_contribution: Whether it contributed to actionable signals
        """
        metrics = self.source_metrics[source_name]
        
        # Update total calls
        metrics.total_calls += 1
        
        # Update success tracking
        if success:
            metrics.successful_calls += 1
        
        # Update quality tracking
        if quality_contribution:
            metrics.quality_contributions += 1
        
        # Calculate new rates using adaptive learning
        # new_metric = (1 - learning_rate) × old_metric + learning_rate × new_observation
        new_success_obs = 1.0 if success else 0.0
        metrics.success_rate = (
            (1 - self.learning_rate) * metrics.success_rate +
            self.learning_rate * new_success_obs
        )
        
        new_quality_obs = 1.0 if quality_contribution else 0.0
        metrics.signal_quality = (
            (1 - self.learning_rate) * metrics.signal_quality +
            self.learning_rate * new_quality_obs
        )
        
        # Reset cycles counter
        metrics.last_used_cycles_ago = 0
        
        logger.info(
            f"Updated metrics for {source_name}: "
            f"success_rate={metrics.success_rate:.3f}, "
            f"quality={metrics.signal_quality:.3f}"
        )
    
    def increment_unused_sources(self, used_sources: List[str]):
        """
        Increment the cycles counter for unused sources
        
        Args:
            used_sources: List of sources that were used this cycle
        """
        for source_name in self.DATA_SOURCES:
            if source_name not in used_sources:
                self.source_metrics[source_name].last_used_cycles_ago += 1
    
    def execute_cycle(self, market_data: Dict) -> Dict:
        """
        Execute one complete agent cycle (called every 10 minutes)
        
        Args:
            market_data: Current market data
            
        Returns:
            Execution results including decisions, signals, and metrics
        """
        self.execution_count += 1
        cycle_start = datetime.now(timezone.utc)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"MARKET HUNTER AGENT - CYCLE {self.execution_count}")
        logger.info(f"{'='*80}\n")
        
        # Step 1: Assess market context
        logger.info("Step 1: Assessing market context...")
        context = self.assess_market_context(market_data)
        
        # Step 2: Calculate source scores
        logger.info("Step 2: Calculating source relevance scores...")
        scores = self.calculate_source_scores(context)
        
        # Step 3: Select sources to query
        logger.info("Step 3: Selecting data sources...")
        selected_sources = self.select_sources(context, scores)
        
        # Step 4: Query selected sources
        logger.info("Step 4: Querying data sources...")
        results = []
        for source in selected_sources:
            logger.info(f"  Querying {source}...")
            result = self.query_data_source(source, context)
            if result:
                results.append(result)
                self.update_metrics(source, success=True, quality_contribution=False)
            else:
                self.update_metrics(source, success=False, quality_contribution=False)
        
        # Step 5: Analyze and generate signals
        logger.info("Step 5: Analyzing results and generating signals...")
        signals = self.analyze_results_and_generate_signals(results, context)
        
        # Update quality metrics for sources that contributed to signals
        contributing_sources = set(s.data.get('source') for s in signals if 'source' in s.data)
        for source in contributing_sources:
            metrics = self.source_metrics[source]
            metrics.quality_contributions += 1
            # Recalculate quality with new contribution
            new_quality = metrics.quality_contributions / metrics.total_calls
            metrics.signal_quality = (
                (1 - self.learning_rate) * metrics.signal_quality +
                self.learning_rate * new_quality
            )
        
        # Step 6: Update unused source metrics
        self.increment_unused_sources(selected_sources)
        
        cycle_duration = (datetime.now(timezone.utc) - cycle_start).total_seconds()
        
        # Prepare execution summary
        execution_summary = {
            'cycle_number': self.execution_count,
            'timestamp': cycle_start.isoformat(),
            'duration_seconds': cycle_duration,
            'context': asdict(context),
            'selected_sources': selected_sources,
            'source_scores': scores,
            'results_count': len(results),
            'signals_generated': len(signals),
            'signals': [
                {
                    'type': s.signal_type,
                    'severity': s.severity.value,
                    'confidence': s.confidence,
                    'message': s.message,
                    'targets': s.target_agents
                }
                for s in signals
            ],
            'metrics': {
                name: {
                    'success_rate': m.success_rate,
                    'signal_quality': m.signal_quality,
                    'last_used': m.last_used_cycles_ago,
                    'total_calls': m.total_calls
                }
                for name, m in self.source_metrics.items()
            }
        }
        
        logger.info(f"\n{'='*80}")
        logger.info(f"CYCLE {self.execution_count} COMPLETE")
        logger.info(f"Duration: {cycle_duration:.2f}s")
        logger.info(f"Sources queried: {len(results)}/{len(selected_sources)}")
        logger.info(f"Signals generated: {len(signals)}")
        logger.info(f"{'='*80}\n")
        
        return execution_summary
    
    def get_performance_report(self) -> Dict:
        """
        Generate a performance report of the agent's learning and decisions
        
        Returns:
            Performance metrics and analysis
        """
        report = {
            'total_cycles': self.execution_count,
            'learning_rate': self.learning_rate,
            'exploration_rate': self.exploration_rate,
            'source_performance': {}
        }
        
        for name, metrics in self.source_metrics.items():
            if metrics.total_calls > 0:
                report['source_performance'][name] = {
                    'success_rate': metrics.success_rate,
                    'signal_quality': metrics.signal_quality,
                    'total_calls': metrics.total_calls,
                    'successful_calls': metrics.successful_calls,
                    'quality_contributions': metrics.quality_contributions,
                    'efficiency': (
                        metrics.quality_contributions / metrics.total_calls
                        if metrics.total_calls > 0 else 0
                    )
                }
        
        # Calculate overall performance
        if self.execution_count > 0:
            total_calls = sum(m.total_calls for m in self.source_metrics.values())
            total_quality = sum(m.quality_contributions for m in self.source_metrics.values())
            report['overall_efficiency'] = total_quality / total_calls if total_calls > 0 else 0
        
        return report
