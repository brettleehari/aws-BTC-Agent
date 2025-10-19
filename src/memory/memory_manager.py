"""
Memory Manager for Agent Memory System

Provides CRUD operations for short-term and long-term memory, patterns, and state.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from .models import (
    DecisionRecord, MemoryPattern, AgentState, AgentSignal,
    DecisionContext, DecisionReasoning, DecisionOutcome
)
from .enums import DecisionType, MemoryType, SignalType, AgentStatus, StateType
from .aws_clients import get_client_manager, AWSClientManager

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages agent memory operations (STM, LTM, patterns, state)"""
    
    def __init__(
        self,
        agent_id: str,
        client_manager: Optional[AWSClientManager] = None,
        decisions_table: str = "agent_decisions",
        memory_table: str = "agent_memory_ltm",
        state_table: str = "agent_state",
        signals_table: str = "agent_signals"
    ):
        """
        Initialize memory manager
        
        Args:
            agent_id: Agent identifier
            client_manager: AWS client manager (optional, uses singleton if None)
            decisions_table: DynamoDB table name for decisions
            memory_table: DynamoDB table name for long-term memory
            state_table: DynamoDB table name for agent state
            signals_table: DynamoDB table name for signals
        """
        self.agent_id = agent_id
        self.client_manager = client_manager or get_client_manager()
        
        # Get table resources
        self.decisions_table = self.client_manager.get_table(decisions_table)
        self.memory_table = self.client_manager.get_table(memory_table)
        self.state_table = self.client_manager.get_table(state_table)
        self.signals_table = self.client_manager.get_table(signals_table)
        
        logger.info(f"Initialized MemoryManager for agent {agent_id}")
    
    # ================== DECISION OPERATIONS ==================
    
    def store_decision(self, decision: DecisionRecord) -> bool:
        """
        Store a decision record
        
        Args:
            decision: DecisionRecord to store
        
        Returns:
            True if successful
        """
        try:
            item = decision.to_dynamodb_item()
            self.decisions_table.put_item(Item=item)
            logger.debug(f"Stored decision {decision.decision_id}")
            return True
        except ClientError as e:
            logger.error(f"Failed to store decision: {e}")
            return False
    
    def get_decision(self, decision_id: str, decision_type: DecisionType) -> Optional[DecisionRecord]:
        """
        Retrieve a specific decision by ID and type
        
        Args:
            decision_id: Decision ID
            decision_type: Type of decision
        
        Returns:
            DecisionRecord if found, None otherwise
        """
        try:
            pk = f"agent:{self.agent_id}#decision#{decision_type.value}"
            
            # Query with begins_with on SK since SK includes timestamp
            response = self.decisions_table.query(
                KeyConditionExpression=Key('PK').eq(pk) & Key('SK').begins_with(''),
                FilterExpression=Attr('decision_id').eq(decision_id),
                Limit=1
            )
            
            if response['Items']:
                return DecisionRecord.from_dynamodb_item(response['Items'][0])
            return None
            
        except ClientError as e:
            logger.error(f"Failed to get decision {decision_id}: {e}")
            return None
    
    def query_decisions(
        self,
        decision_type: Optional[DecisionType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        is_stm: Optional[bool] = None,
        successful_only: bool = False
    ) -> List[DecisionRecord]:
        """
        Query decisions with various filters
        
        Args:
            decision_type: Filter by decision type
            start_time: Filter decisions after this time
            end_time: Filter decisions before this time
            limit: Maximum number of results
            is_stm: Filter by short-term (True) or long-term (False) memory
            successful_only: Only return successful decisions
        
        Returns:
            List of DecisionRecord objects
        """
        try:
            decisions = []
            
            # Use appropriate index based on filters
            if successful_only:
                # Use SuccessIndex (GSI1)
                pk = f"agent:{self.agent_id}#success:true"
                response = self.decisions_table.query(
                    IndexName='SuccessIndex',
                    KeyConditionExpression=Key('GSI1_PK').eq(pk),
                    Limit=limit,
                    ScanIndexForward=False  # Most recent first
                )
            elif is_stm is not None:
                # Use STMIndex (GSI3)
                pk = f"agent:{self.agent_id}#stm:{str(is_stm).lower()}"
                response = self.decisions_table.query(
                    IndexName='STMIndex',
                    KeyConditionExpression=Key('GSI3_PK').eq(pk),
                    Limit=limit,
                    ScanIndexForward=False
                )
            elif decision_type:
                # Use main table with decision type in PK
                pk = f"agent:{self.agent_id}#decision#{decision_type.value}"
                key_condition = Key('PK').eq(pk)
                
                if start_time:
                    key_condition &= Key('SK').gte(start_time.isoformat())
                
                response = self.decisions_table.query(
                    KeyConditionExpression=key_condition,
                    Limit=limit,
                    ScanIndexForward=False
                )
            else:
                # Query all decision types (requires multiple queries or scan)
                # For now, use scan with filter (not optimal for large datasets)
                filter_expr = Attr('agent_id').eq(self.agent_id)
                
                if start_time:
                    filter_expr &= Attr('timestamp').gte(start_time.isoformat())
                if end_time:
                    filter_expr &= Attr('timestamp').lte(end_time.isoformat())
                
                response = self.decisions_table.scan(
                    FilterExpression=filter_expr,
                    Limit=limit
                )
            
            # Convert items to DecisionRecord objects
            for item in response.get('Items', []):
                decision = DecisionRecord.from_dynamodb_item(item)
                
                # Apply time filters if needed
                if start_time and decision.timestamp < start_time:
                    continue
                if end_time and decision.timestamp > end_time:
                    continue
                
                decisions.append(decision)
            
            logger.debug(f"Retrieved {len(decisions)} decisions")
            return decisions
            
        except ClientError as e:
            logger.error(f"Failed to query decisions: {e}")
            return []
    
    def get_decision_chain(self, decision_id: str, decision_type: DecisionType) -> List[DecisionRecord]:
        """
        Get the full chain of decisions (parent → child relationships)
        
        Args:
            decision_id: Starting decision ID
            decision_type: Type of starting decision
        
        Returns:
            List of DecisionRecord objects in chronological order
        """
        chain = []
        current_decision = self.get_decision(decision_id, decision_type)
        
        if not current_decision:
            return chain
        
        # Walk backwards to root
        chain.insert(0, current_decision)
        while current_decision.context.parent_decision_id:
            # Need to query to find parent (we don't store parent type)
            # This is inefficient - consider storing parent_decision_type
            parent_id = current_decision.context.parent_decision_id
            
            # Try to find parent in recent decisions
            found = False
            for dtype in DecisionType:
                parent = self.get_decision(parent_id, dtype)
                if parent:
                    chain.insert(0, parent)
                    current_decision = parent
                    found = True
                    break
            
            if not found:
                break
        
        return chain
    
    # ================== PATTERN OPERATIONS (LTM) ==================
    
    def store_pattern(self, pattern: MemoryPattern) -> bool:
        """
        Store a memory pattern (long-term memory)
        
        Args:
            pattern: MemoryPattern to store
        
        Returns:
            True if successful
        """
        try:
            item = pattern.to_dynamodb_item()
            self.memory_table.put_item(Item=item)
            logger.debug(f"Stored pattern {pattern.pattern_id}")
            return True
        except ClientError as e:
            logger.error(f"Failed to store pattern: {e}")
            return False
    
    def get_pattern(self, pattern_id: str, memory_type: MemoryType) -> Optional[MemoryPattern]:
        """
        Retrieve a specific pattern
        
        Args:
            pattern_id: Pattern ID
            memory_type: Type of memory pattern
        
        Returns:
            MemoryPattern if found, None otherwise
        """
        try:
            pk = f"agent:{self.agent_id}#{memory_type.value}"
            response = self.memory_table.get_item(
                Key={'PK': pk, 'SK': pattern_id}
            )
            
            if 'Item' in response:
                return MemoryPattern.from_dynamodb_item(response['Item'])
            return None
            
        except ClientError as e:
            logger.error(f"Failed to get pattern {pattern_id}: {e}")
            return None
    
    def query_patterns(
        self,
        memory_type: Optional[MemoryType] = None,
        min_confidence: float = 0.0,
        min_success_rate: float = 0.0,
        limit: int = 100,
        include_shared: bool = True
    ) -> List[MemoryPattern]:
        """
        Query patterns with filters
        
        Args:
            memory_type: Filter by memory type
            min_confidence: Minimum confidence threshold
            min_success_rate: Minimum success rate threshold
            limit: Maximum number of results
            include_shared: Include patterns shared by other agents
        
        Returns:
            List of MemoryPattern objects
        """
        try:
            patterns = []
            
            if memory_type:
                # Query specific memory type
                pk = f"agent:{self.agent_id}#{memory_type.value}"
                response = self.memory_table.query(
                    KeyConditionExpression=Key('PK').eq(pk),
                    Limit=limit
                )
                
                for item in response.get('Items', []):
                    pattern = MemoryPattern.from_dynamodb_item(item)
                    
                    # Apply filters
                    if pattern.confidence >= min_confidence and pattern.success_rate >= min_success_rate:
                        patterns.append(pattern)
            else:
                # Query all memory types
                for mtype in MemoryType:
                    pk = f"agent:{self.agent_id}#{mtype.value}"
                    response = self.memory_table.query(
                        KeyConditionExpression=Key('PK').eq(pk),
                        Limit=limit
                    )
                    
                    for item in response.get('Items', []):
                        pattern = MemoryPattern.from_dynamodb_item(item)
                        
                        if pattern.confidence >= min_confidence and pattern.success_rate >= min_success_rate:
                            patterns.append(pattern)
            
            # Add shared patterns if requested
            if include_shared:
                # Query SharedPatternIndex (GSI2)
                pk = f"shared:true"
                response = self.memory_table.query(
                    IndexName='SharedPatternIndex',
                    KeyConditionExpression=Key('GSI2_PK').eq(pk),
                    FilterExpression=Attr('shared_with').contains(self.agent_id),
                    Limit=limit
                )
                
                for item in response.get('Items', []):
                    pattern = MemoryPattern.from_dynamodb_item(item)
                    
                    if pattern.confidence >= min_confidence and pattern.success_rate >= min_success_rate:
                        if pattern.agent_id != self.agent_id:  # Don't duplicate own patterns
                            patterns.append(pattern)
            
            # Sort by confidence (descending)
            patterns.sort(key=lambda p: p.confidence, reverse=True)
            
            logger.debug(f"Retrieved {len(patterns)} patterns")
            return patterns[:limit]
            
        except ClientError as e:
            logger.error(f"Failed to query patterns: {e}")
            return []
    
    def update_pattern_metrics(
        self,
        pattern_id: str,
        memory_type: MemoryType,
        success: bool,
        new_confidence: Optional[float] = None
    ) -> bool:
        """
        Update pattern metrics after usage
        
        Args:
            pattern_id: Pattern ID
            memory_type: Type of memory pattern
            success: Whether the pattern usage was successful
            new_confidence: Optional new confidence score
        
        Returns:
            True if successful
        """
        try:
            pk = f"agent:{self.agent_id}#{memory_type.value}"
            
            # Build update expression
            update_expr = "SET access_count = access_count + :inc, last_accessed = :now"
            expr_values = {
                ':inc': 1,
                ':now': datetime.utcnow().isoformat()
            }
            
            if success:
                update_expr += ", success_count = success_count + :inc"
            
            update_expr += ", sample_size = sample_size + :inc"
            update_expr += ", success_rate = success_count / sample_size"
            
            if new_confidence is not None:
                update_expr += ", confidence = :conf"
                expr_values[':conf'] = new_confidence
            
            self.memory_table.update_item(
                Key={'PK': pk, 'SK': pattern_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values
            )
            
            logger.debug(f"Updated pattern {pattern_id} metrics")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to update pattern metrics: {e}")
            return False
    
    # ================== STATE OPERATIONS ==================
    
    def save_state(self, state: AgentState) -> bool:
        """
        Save agent state
        
        Args:
            state: AgentState to save
        
        Returns:
            True if successful
        """
        try:
            item = state.to_dynamodb_item()
            self.state_table.put_item(Item=item)
            logger.debug(f"Saved state {state.state_type} for agent {state.agent_id}")
            return True
        except ClientError as e:
            logger.error(f"Failed to save state: {e}")
            return False
    
    def load_state(self, state_type: StateType = StateType.CURRENT) -> Optional[AgentState]:
        """
        Load agent state
        
        Args:
            state_type: Type of state to load (CURRENT, CHECKPOINT, etc.)
        
        Returns:
            AgentState if found, None otherwise
        """
        try:
            pk = f"agent:{self.agent_id}"
            response = self.state_table.get_item(
                Key={'PK': pk, 'SK': state_type.value}
            )
            
            if 'Item' in response:
                return AgentState.from_dynamodb_item(response['Item'])
            return None
            
        except ClientError as e:
            logger.error(f"Failed to load state: {e}")
            return None
    
    def checkpoint_state(self) -> bool:
        """
        Create a checkpoint of current state
        
        Returns:
            True if successful
        """
        try:
            current = self.load_state(StateType.CURRENT)
            if not current:
                logger.warning("No current state to checkpoint")
                return False
            
            # Create checkpoint with same data but different state_type
            checkpoint = AgentState(
                agent_id=current.agent_id,
                agent_version=current.agent_version,
                state_type=StateType.CHECKPOINT,
                status=current.status,
                current_cycle=current.current_cycle,
                source_metrics=current.source_metrics,
                context_performance=current.context_performance,
                configuration=current.configuration,
                version=current.version
            )
            
            return self.save_state(checkpoint)
            
        except Exception as e:
            logger.error(f"Failed to checkpoint state: {e}")
            return False
    
    def rollback_state(self) -> bool:
        """
        Rollback to last checkpoint
        
        Returns:
            True if successful
        """
        try:
            checkpoint = self.load_state(StateType.CHECKPOINT)
            if not checkpoint:
                logger.warning("No checkpoint found for rollback")
                return False
            
            # Restore checkpoint as current state
            current = AgentState(
                agent_id=checkpoint.agent_id,
                agent_version=checkpoint.agent_version,
                state_type=StateType.CURRENT,
                status=checkpoint.status,
                current_cycle=checkpoint.current_cycle,
                source_metrics=checkpoint.source_metrics,
                context_performance=checkpoint.context_performance,
                configuration=checkpoint.configuration,
                version=checkpoint.version + 1  # Increment version
            )
            
            logger.warning(f"Rolling back agent {self.agent_id} to checkpoint")
            return self.save_state(current)
            
        except Exception as e:
            logger.error(f"Failed to rollback state: {e}")
            return False
    
    # ================== SIGNAL OPERATIONS ==================
    
    def publish_signal(self, signal: AgentSignal) -> bool:
        """
        Publish a signal to other agents
        
        Args:
            signal: AgentSignal to publish
        
        Returns:
            True if successful
        """
        try:
            item = signal.to_dynamodb_item()
            self.signals_table.put_item(Item=item)
            logger.debug(f"Published signal {signal.signal_id} of type {signal.signal_type}")
            return True
        except ClientError as e:
            logger.error(f"Failed to publish signal: {e}")
            return False
    
    def get_pending_signals(
        self,
        signal_types: Optional[List[SignalType]] = None,
        limit: int = 100
    ) -> List[AgentSignal]:
        """
        Get pending signals for this agent
        
        Args:
            signal_types: Optional list of signal types to filter
            limit: Maximum number of signals
        
        Returns:
            List of AgentSignal objects
        """
        try:
            signals = []
            
            # Query TargetAgentIndex (GSI1)
            pk = f"target:{self.agent_id}"
            response = self.signals_table.query(
                IndexName='TargetAgentIndex',
                KeyConditionExpression=Key('GSI1_PK').eq(pk),
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
            
            for item in response.get('Items', []):
                signal = AgentSignal.from_dynamodb_item(item)
                
                # Check if pending for this agent
                status = signal.processing_status.get(self.agent_id, 'PENDING')
                if status == 'PENDING':
                    # Apply signal type filter if provided
                    if signal_types is None or signal.signal_type in signal_types:
                        signals.append(signal)
            
            logger.debug(f"Retrieved {len(signals)} pending signals")
            return signals
            
        except ClientError as e:
            logger.error(f"Failed to get pending signals: {e}")
            return []
    
    def mark_signal_processed(
        self,
        signal_id: str,
        signal_type: SignalType,
        status: str = 'PROCESSED'
    ) -> bool:
        """
        Mark a signal as processed by this agent
        
        Args:
            signal_id: Signal ID
            signal_type: Type of signal
            status: Processing status (PROCESSED, FAILED, IGNORED)
        
        Returns:
            True if successful
        """
        try:
            # We need timestamp to construct SK, so retrieve the signal first
            # In production, consider storing signal location separately
            # or using a different access pattern
            
            pk = f"signal#{signal_type.value}"
            
            # Query to find the signal
            response = self.signals_table.query(
                KeyConditionExpression=Key('PK').eq(pk),
                FilterExpression=Attr('signal_id').eq(signal_id),
                Limit=1
            )
            
            if not response.get('Items'):
                logger.warning(f"Signal {signal_id} not found")
                return False
            
            item = response['Items'][0]
            sk = item['SK']
            
            # Update processing status
            self.signals_table.update_item(
                Key={'PK': pk, 'SK': sk},
                UpdateExpression=f"SET processing_status.#agent = :status",
                ExpressionAttributeNames={'#agent': self.agent_id},
                ExpressionAttributeValues={':status': status}
            )
            
            logger.debug(f"Marked signal {signal_id} as {status}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to mark signal processed: {e}")
            return False
    
    # ================== CLEANUP OPERATIONS ==================
    
    def cleanup_stm(self, older_than_hours: int = 24) -> int:
        """
        Clean up old short-term memory (decisions marked as STM)
        
        Args:
            older_than_hours: Delete STM decisions older than this
        
        Returns:
            Number of items deleted
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            
            # Query STM decisions
            decisions = self.query_decisions(is_stm=True, end_time=cutoff_time, limit=1000)
            
            deleted_count = 0
            for decision in decisions:
                pk = f"agent:{decision.agent_id}#decision#{decision.decision_type.value}"
                sk = f"{decision.timestamp.isoformat()}#{decision.decision_id}"
                
                self.decisions_table.delete_item(Key={'PK': pk, 'SK': sk})
                deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} STM decisions")
            return deleted_count
            
        except ClientError as e:
            logger.error(f"Failed to cleanup STM: {e}")
            return 0


__all__ = ['MemoryManager']
