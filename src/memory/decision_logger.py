"""
Decision Logger for Agent Decision Tracking

Provides high-level API for logging decisions with context, reasoning, and outcomes.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from .models import (
    DecisionRecord, DecisionContext, DecisionReasoning, DecisionOutcome
)
from .enums import DecisionType, AgentStatus
from .memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class DecisionLogger:
    """High-level API for logging agent decisions"""
    
    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize decision logger
        
        Args:
            memory_manager: MemoryManager instance
        """
        self.memory_manager = memory_manager
        self.agent_id = memory_manager.agent_id
        
        # Track current decision chain
        self._current_decision_id: Optional[str] = None
        self._decision_stack: List[str] = []
        
        logger.info(f"Initialized DecisionLogger for agent {self.agent_id}")
    
    def log_decision(
        self,
        decision_type: DecisionType,
        context: Dict[str, Any],
        reasoning: Dict[str, Any],
        parent_decision_id: Optional[str] = None,
        agent_version: str = "1.0.0",
        is_stm: bool = True
    ) -> str:
        """
        Log a decision with context and reasoning
        
        Args:
            decision_type: Type of decision being made
            context: Decision context (market conditions, cycle info, etc.)
            reasoning: Decision reasoning (scores, selections, patterns applied)
            parent_decision_id: Optional parent decision ID for chaining
            agent_version: Agent version string
            is_stm: Whether this is short-term memory (True) or long-term (False)
        
        Returns:
            Decision ID
        """
        try:
            # Build decision context
            decision_context = DecisionContext(
                market=context.get('market', {}),
                cycle=context.get('cycle'),
                trading_hours=context.get('trading_hours'),
                parent_decision_id=parent_decision_id or self._current_decision_id,
                agent_state=context.get('agent_state', {})
            )
            
            # Build decision reasoning
            decision_reasoning = DecisionReasoning(
                scores=reasoning.get('scores', {}),
                selected=reasoning.get('selected', []),
                memory_influenced=reasoning.get('memory_influenced', False),
                patterns_applied=reasoning.get('patterns_applied', []),
                exploration=reasoning.get('exploration', False),
                confidence=reasoning.get('confidence', 0.5)
            )
            
            # Create decision record (outcome to be filled later)
            decision = DecisionRecord(
                agent_id=self.agent_id,
                agent_version=agent_version,
                decision_type=decision_type,
                timestamp=datetime.utcnow(),
                context=decision_context,
                reasoning=decision_reasoning,
                outcome=DecisionOutcome(success=True),  # Default, updated later
                is_stm=is_stm
            )
            
            # Store decision
            if self.memory_manager.store_decision(decision):
                # Update current decision tracking
                self._current_decision_id = decision.decision_id
                
                logger.info(
                    f"Logged decision {decision.decision_id} "
                    f"[{decision_type.value}] with confidence {decision_reasoning.confidence:.2f}"
                )
                
                return decision.decision_id
            else:
                logger.error("Failed to store decision")
                return ""
                
        except Exception as e:
            logger.error(f"Failed to log decision: {e}")
            return ""
    
    def log_outcome(
        self,
        decision_id: str,
        decision_type: DecisionType,
        success: bool,
        signals_generated: Optional[List[str]] = None,
        quality_score: Optional[float] = None,
        latency_ms: Optional[float] = None,
        errors: Optional[List[str]] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log the outcome of a decision
        
        Args:
            decision_id: Decision ID to update
            decision_type: Type of decision
            success: Whether the decision was successful
            signals_generated: List of signal IDs generated
            quality_score: Quality score (0.0-1.0)
            latency_ms: Decision latency in milliseconds
            errors: List of error messages
            metrics: Additional outcome metrics
        
        Returns:
            True if successful
        """
        try:
            # Retrieve the decision
            decision = self.memory_manager.get_decision(decision_id, decision_type)
            
            if not decision:
                logger.error(f"Decision {decision_id} not found")
                return False
            
            # Update outcome
            decision.outcome = DecisionOutcome(
                success=success,
                signals_generated=signals_generated or [],
                quality_score=quality_score,
                latency_ms=latency_ms,
                errors=errors or [],
                metrics=metrics or {}
            )
            
            # Store updated decision
            if self.memory_manager.store_decision(decision):
                logger.info(
                    f"Logged outcome for decision {decision_id}: "
                    f"{'SUCCESS' if success else 'FAILURE'}"
                )
                return True
            else:
                logger.error("Failed to update decision outcome")
                return False
                
        except Exception as e:
            logger.error(f"Failed to log outcome: {e}")
            return False
    
    def start_decision_chain(self, decision_id: str):
        """
        Start a new decision chain (for hierarchical decisions)
        
        Args:
            decision_id: Root decision ID
        """
        self._decision_stack.append(self._current_decision_id)
        self._current_decision_id = decision_id
        logger.debug(f"Started decision chain with root {decision_id}")
    
    def end_decision_chain(self):
        """End the current decision chain and restore parent"""
        if self._decision_stack:
            self._current_decision_id = self._decision_stack.pop()
            logger.debug(f"Ended decision chain, restored parent {self._current_decision_id}")
        else:
            self._current_decision_id = None
            logger.debug("Ended decision chain, no parent to restore")
    
    def get_recent_decisions(
        self,
        decision_type: Optional[DecisionType] = None,
        limit: int = 100,
        successful_only: bool = False
    ) -> List[DecisionRecord]:
        """
        Get recent decisions
        
        Args:
            decision_type: Optional filter by decision type
            limit: Maximum number of results
            successful_only: Only return successful decisions
        
        Returns:
            List of DecisionRecord objects
        """
        return self.memory_manager.query_decisions(
            decision_type=decision_type,
            limit=limit,
            successful_only=successful_only
        )
    
    def get_decision_chain(self, decision_id: str, decision_type: DecisionType) -> List[DecisionRecord]:
        """
        Get the full chain of decisions (parent → child)
        
        Args:
            decision_id: Starting decision ID
            decision_type: Type of starting decision
        
        Returns:
            List of DecisionRecord objects in chronological order
        """
        return self.memory_manager.get_decision_chain(decision_id, decision_type)
    
    def get_decision_stats(
        self,
        decision_type: Optional[DecisionType] = None,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get statistics about recent decisions
        
        Args:
            decision_type: Optional filter by decision type
            time_window_hours: Time window for statistics
        
        Returns:
            Dict with statistics (success_rate, avg_confidence, count, etc.)
        """
        try:
            # Query recent decisions
            start_time = datetime.utcnow() - timedelta(hours=time_window_hours)
            decisions = self.memory_manager.query_decisions(
                decision_type=decision_type,
                start_time=start_time,
                limit=1000
            )
            
            if not decisions:
                return {
                    'count': 0,
                    'success_rate': 0.0,
                    'avg_confidence': 0.0,
                    'avg_latency_ms': 0.0
                }
            
            # Calculate statistics
            total = len(decisions)
            successful = sum(1 for d in decisions if d.outcome.success)
            confidences = [d.reasoning.confidence for d in decisions]
            latencies = [
                d.outcome.latency_ms for d in decisions 
                if d.outcome.latency_ms is not None
            ]
            
            stats = {
                'count': total,
                'success_rate': successful / total if total > 0 else 0.0,
                'avg_confidence': sum(confidences) / len(confidences) if confidences else 0.0,
                'avg_latency_ms': sum(latencies) / len(latencies) if latencies else 0.0,
                'time_window_hours': time_window_hours
            }
            
            # Add per-type breakdown if not filtered
            if decision_type is None:
                type_counts = {}
                for d in decisions:
                    type_name = d.decision_type.value
                    if type_name not in type_counts:
                        type_counts[type_name] = {'count': 0, 'successful': 0}
                    type_counts[type_name]['count'] += 1
                    if d.outcome.success:
                        type_counts[type_name]['successful'] += 1
                
                # Calculate success rate per type
                for type_name in type_counts:
                    counts = type_counts[type_name]
                    counts['success_rate'] = counts['successful'] / counts['count']
                
                stats['by_type'] = type_counts
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get decision stats: {e}")
            return {
                'count': 0,
                'success_rate': 0.0,
                'avg_confidence': 0.0,
                'error': str(e)
            }
    
    def log_source_selection(
        self,
        sources: List[str],
        scores: Dict[str, float],
        selected: List[str],
        context: Dict[str, Any],
        confidence: float,
        parent_decision_id: Optional[str] = None
    ) -> str:
        """
        Helper to log a source selection decision
        
        Args:
            sources: All available sources
            scores: Source quality scores
            selected: Selected sources
            context: Market and cycle context
            confidence: Decision confidence
            parent_decision_id: Optional parent decision
        
        Returns:
            Decision ID
        """
        return self.log_decision(
            decision_type=DecisionType.SOURCE_SELECTION,
            context=context,
            reasoning={
                'scores': scores,
                'selected': selected,
                'confidence': confidence,
                'memory_influenced': False  # Can be updated if using patterns
            },
            parent_decision_id=parent_decision_id
        )
    
    def log_query_execution(
        self,
        query: str,
        sources: List[str],
        context: Dict[str, Any],
        parent_decision_id: Optional[str] = None
    ) -> str:
        """
        Helper to log a query execution decision
        
        Args:
            query: The query being executed
            sources: Sources to query
            context: Market and cycle context
            parent_decision_id: Optional parent decision
        
        Returns:
            Decision ID
        """
        return self.log_decision(
            decision_type=DecisionType.QUERY_EXECUTION,
            context=context,
            reasoning={
                'selected': [query],
                'scores': {'query_relevance': 1.0},
                'confidence': 0.8
            },
            parent_decision_id=parent_decision_id
        )
    
    def log_signal_generation(
        self,
        signal_type: str,
        signal_data: Dict[str, Any],
        confidence: float,
        context: Dict[str, Any],
        parent_decision_id: Optional[str] = None
    ) -> str:
        """
        Helper to log a signal generation decision
        
        Args:
            signal_type: Type of signal generated
            signal_data: Signal data
            confidence: Signal confidence
            context: Market and cycle context
            parent_decision_id: Optional parent decision
        
        Returns:
            Decision ID
        """
        return self.log_decision(
            decision_type=DecisionType.SIGNAL_GENERATION,
            context=context,
            reasoning={
                'selected': [signal_type],
                'scores': {'confidence': confidence},
                'confidence': confidence
            },
            parent_decision_id=parent_decision_id
        )
    
    def log_risk_assessment(
        self,
        risk_factors: Dict[str, float],
        risk_level: str,
        confidence: float,
        context: Dict[str, Any],
        parent_decision_id: Optional[str] = None
    ) -> str:
        """
        Helper to log a risk assessment decision
        
        Args:
            risk_factors: Risk factor scores
            risk_level: Overall risk level
            confidence: Assessment confidence
            context: Market and cycle context
            parent_decision_id: Optional parent decision
        
        Returns:
            Decision ID
        """
        return self.log_decision(
            decision_type=DecisionType.RISK_ASSESSMENT,
            context=context,
            reasoning={
                'scores': risk_factors,
                'selected': [risk_level],
                'confidence': confidence
            },
            parent_decision_id=parent_decision_id
        )


__all__ = ['DecisionLogger']
