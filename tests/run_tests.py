"""
Test runner for Market Hunter Agent test suite

Runs unit tests, integration tests, and evaluations.
"""

import unittest
import sys
import os
from pathlib import Path

# Add tests and src to path
test_dir = Path(__file__).parent
sys.path.insert(0, str(test_dir.parent / 'src'))
sys.path.insert(0, str(test_dir))


def run_unit_tests():
    """Run all unit tests"""
    print("\n" + "="*80)
    print("🧪 RUNNING UNIT TESTS")
    print("="*80)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Load unit tests
    suite.addTests(loader.loadTestsFromName('test_agent_core'))
    suite.addTests(loader.loadTestsFromName('test_llm_router'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_integration_tests():
    """Run integration tests (requires AWS credentials)"""
    print("\n" + "="*80)
    print("🔗 RUNNING INTEGRATION TESTS")
    print("="*80)
    
    # Check if AWS credentials are configured
    required_vars = ['BEDROCK_AGENT_ID', 'BEDROCK_AGENT_ALIAS_ID']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"\n⚠️  Skipping integration tests - missing environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nSet these variables to run integration tests.")
        return True  # Return True to not fail the test run
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Load integration tests
    suite.addTests(loader.loadTestsFromName('test_integration'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_evaluations():
    """Run agent evaluations"""
    print("\n" + "="*80)
    print("📊 RUNNING AGENT EVALUATIONS")
    print("="*80)
    
    try:
        from test_evaluations import AgentEvaluator, MarketHunterAgent
        
        # Check for agent credentials
        agent_id = os.getenv('BEDROCK_AGENT_ID', 'test-agent')
        alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID', 'test-alias')
        
        print(f"\nAgent ID: {agent_id}")
        print(f"Alias ID: {alias_id}")
        
        # Create agent
        agent = MarketHunterAgent(
            bedrock_agent_id=agent_id,
            bedrock_agent_alias_id=alias_id,
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        # Run evaluation
        evaluator = AgentEvaluator(agent)
        metrics = evaluator.run_comprehensive_evaluation()
        
        # Export results
        evaluator.export_results('evaluation_results.json')
        
        return metrics is not None
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {str(e)}")
        return False


def print_summary(unit_success, integration_success, eval_success):
    """Print test summary"""
    print("\n" + "="*80)
    print("📋 TEST SUMMARY")
    print("="*80)
    
    print(f"\n{'Test Suite':<30} {'Status':<15}")
    print("-" * 45)
    print(f"{'Unit Tests':<30} {'✅ PASSED' if unit_success else '❌ FAILED':<15}")
    print(f"{'Integration Tests':<30} {'✅ PASSED' if integration_success else '❌ FAILED':<15}")
    print(f"{'Agent Evaluations':<30} {'✅ PASSED' if eval_success else '❌ FAILED':<15}")
    
    print("\n" + "="*80)
    
    all_passed = unit_success and integration_success and eval_success
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("="*80 + "\n")
    
    return all_passed


def main():
    """Run all tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Market Hunter Agent tests')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--eval', action='store_true', help='Run evaluations only')
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    
    args = parser.parse_args()
    
    # Default to all if no specific test type selected
    if not (args.unit or args.integration or args.eval):
        args.all = True
    
    unit_success = True
    integration_success = True
    eval_success = True
    
    try:
        if args.all or args.unit:
            unit_success = run_unit_tests()
        
        if args.all or args.integration:
            integration_success = run_integration_tests()
        
        if args.all or args.eval:
            eval_success = run_evaluations()
        
        # Print summary
        all_passed = print_summary(unit_success, integration_success, eval_success)
        
        # Exit with appropriate code
        sys.exit(0 if all_passed else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test runner failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
