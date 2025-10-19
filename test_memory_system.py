"""
Quick manual test to verify memory system is working.
"""
import asyncio
from datetime import datetime, timezone
import sys
sys.path.insert(0, '/workspaces/aws-BTC-Agent')

from src.memory.decision_logger import DecisionLogger
from src.memory.memory_manager import MemoryManager
from src.memory.models import DecisionContext, DecisionReasoning, DecisionOutcome
from src.memory.enums import DecisionType

async def test_basic_operations():
    print("=" * 60)
    print("Testing Memory System - Basic Operations")
    print("=" * 60)
    
    # Set dummy AWS credentials for local DynamoDB
    import os
    os.environ['AWS_ACCESS_KEY_ID'] = 'test'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    
    # Initialize client manager with local endpoint
    from src.memory.aws_clients import AWSClientManager
    client_manager = AWSClientManager(region="us-east-1", endpoint_url="http://localhost:8000")
    
    memory = MemoryManager(agent_id="market-hunter-test", client_manager=client_manager)
    logger = DecisionLogger(memory_manager=memory)
    
    try:
        # Test 1: Log a decision
        print("\n🧪 Test 1: Logging a decision...")
        context = DecisionContext(
            market_conditions={"btc_price": 45000, "trend": "bullish"},
            agent_state={"confidence": 0.8},
            available_resources=["coindesk", "twitter"]
        )
        
        reasoning = DecisionReasoning(
            confidence_score=0.85,
            alternative_options=["reddit", "news_api"],
            risk_assessment={"level": "medium"}
        )
        
        decision_id = logger.log_decision(
            decision_type=DecisionType.SOURCE_SELECTION,
            context=context.dict(),
            reasoning=reasoning.dict()
        )
        
        print(f"✅ Logged decision: {decision_id}")
        
        # Test 2: Retrieve the decision
        print("\n🧪 Test 2: Retrieving decision...")
        decision = logger.get_decision(decision_id)
        if decision:
            print(f"✅ Retrieved decision: {decision.decision_id}")
            print(f"   Agent: {decision.agent_id}")
            print(f"   Type: {decision.decision_type}")
        else:
            print("❌ Failed to retrieve decision")
            return False
        
        # Test 3: Update with outcome
        print("\n🧪 Test 3: Updating with outcome...")
        outcome = DecisionOutcome(
            success=True,
            actual_result={"data_quality": 0.9, "latency_ms": 120},
            execution_time_ms=150,
            metrics={"accuracy": 0.92}
        )
        
        logger.log_outcome(decision_id, outcome.dict())
        print(f"✅ Updated decision with outcome")
        
        # Test 4: Query recent decisions
        print("\n🧪 Test 4: Querying recent decisions...")
        recent = logger.query_decisions()
        print(f"✅ Found {len(recent)} recent decisions")
        
        # Test 5: Check memory manager is working
        print("\n🧪 Test 5: Checking memory manager...")
        decisions_from_memory = memory.query_decisions_by_agent()
        print(f"✅ Memory manager returned {len(decisions_from_memory)} decisions")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nMemory system is working correctly!")
        print("- DynamoDB tables are accessible")
        print("- Decision logging is functional")
        print("- Data retrieval is working")
        print("- Ready for integration!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(test_basic_operations())
    sys.exit(0 if success else 1)
