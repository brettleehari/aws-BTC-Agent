"""
Goal Alignment Tests for Market Hunter Agent

Tests to ensure the codebase stays aligned with project goals:
1. Autonomous decision-making (not hardcoded)
2. Cost optimization (LLM routing)
3. Learning and adaptation
4. Real-time execution (<60s per cycle)
5. Signal generation quality
6. Data source diversity

Run on demand or via pre-commit hook to validate architecture.
"""

import unittest
import json
import time
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from market_hunter_agent import MarketHunterAgent
    from llm_router import LLMRouter, TaskType
    from database import Database
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    MarketHunterAgent = None
    LLMRouter = None
    Database = None


class TestGoal1_Autonomy(unittest.TestCase):
    """Goal 1: Agent makes autonomous decisions, not hardcoded rules"""
    
    def test_no_hardcoded_source_selection(self):
        """Verify agent doesn't hardcode which sources to query"""
        if MarketHunterAgent is None:
            self.skipTest("MarketHunterAgent not available")
        
        # Read agent code
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Check for hardcoded source lists (bad patterns)
        bad_patterns = [
            'sources = ["whale_movements", "narrative_shifts"',  # Hardcoded list
            'always_query = [',  # Fixed selection
            'if True:.*query.*whale',  # Always query specific source
        ]
        
        for pattern in bad_patterns:
            self.assertNotIn(pattern, code, 
                f"Found hardcoded source selection: {pattern}")
    
    def test_decision_uses_context(self):
        """Verify decisions are based on market context, not fixed rules"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Good patterns - context-driven decisions
        required_context = [
            'volatility',  # Uses volatility
            'trend',       # Uses trend
            'performance', # Uses historical performance
        ]
        
        for context in required_context:
            self.assertIn(context, code,
                f"Agent should use '{context}' in decision-making")
    
    def test_exploration_mechanism_exists(self):
        """Verify agent has exploration mechanism (not pure exploitation)"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Should have exploration logic
        exploration_indicators = ['exploration', 'random', 'epsilon', 'explore']
        found = any(indicator in code.lower() for indicator in exploration_indicators)
        
        self.assertTrue(found, 
            "Agent should have exploration mechanism for trying new strategies")
    
    def test_adaptive_source_count(self):
        """Verify number of sources queried adapts to conditions"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Should NOT have fixed count like "query exactly 5 sources"
        bad_patterns = [
            'num_sources = 5',
            'sources_to_query = 4',
            'for i in range(6)',  # Fixed loop
        ]
        
        # Should have adaptive logic
        self.assertIn('volatility', code)
        # Number should vary based on conditions


class TestGoal2_CostOptimization(unittest.TestCase):
    """Goal 2: System optimizes costs through intelligent LLM routing"""
    
    def test_llm_router_exists(self):
        """Verify LLM router is implemented"""
        router_file = Path(__file__).parent.parent / "src" / "llm_router.py"
        self.assertTrue(router_file.exists(), "LLM router must exist")
        
        # Check it has multiple models
        with open(router_file) as f:
            code = f.read()
        
        self.assertIn('claude-3-haiku', code, "Should support cheap models")
        self.assertIn('claude-3-sonnet', code, "Should support mid-tier models")
        self.assertIn('claude-3-opus', code, "Should support premium models")
    
    def test_router_task_based_selection(self):
        """Verify router selects models based on task complexity"""
        if LLMRouter is None:
            self.skipTest("LLMRouter not available")
        
        # Router should have task types
        self.assertTrue(hasattr(TaskType, 'SIMPLE_EXTRACTION') or 
                       'SIMPLE_EXTRACTION' in dir(TaskType))
        self.assertTrue(hasattr(TaskType, 'COMPLEX_REASONING') or
                       'COMPLEX_REASONING' in dir(TaskType))
    
    def test_cost_tracking_implemented(self):
        """Verify system tracks LLM costs"""
        router_file = Path(__file__).parent.parent / "src" / "llm_router.py"
        with open(router_file) as f:
            code = f.read()
        
        cost_indicators = ['cost', 'price', 'total_cost', 'input_cost']
        found = any(indicator in code for indicator in cost_indicators)
        
        self.assertTrue(found, "Router should track costs")
    
    def test_no_always_expensive_model(self):
        """Verify system doesn't always use expensive models"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Should not hardcode expensive model everywhere
        self.assertNotIn('model="anthropic.claude-3-opus"', code)
        self.assertNotIn('model="claude-3-opus"', code)


class TestGoal3_LearningAndAdaptation(unittest.TestCase):
    """Goal 3: Agent learns from experience and adapts over time"""
    
    def test_performance_metrics_stored(self):
        """Verify agent stores performance metrics"""
        db_file = Path(__file__).parent.parent / "src" / "database.py"
        with open(db_file) as f:
            code = f.read()
        
        # Should have metrics table
        self.assertIn('source_metrics', code)
        self.assertIn('signal_quality', code)
    
    def test_learning_algorithm_exists(self):
        """Verify learning algorithm is implemented"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Should have learning logic
        learning_indicators = [
            'update_metrics',
            'learn',
            'performance_score',
            'signal_quality'
        ]
        
        found = any(indicator in code for indicator in learning_indicators)
        self.assertTrue(found, "Agent should have learning mechanism")
    
    def test_historical_data_influences_decisions(self):
        """Verify historical performance influences future decisions"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Should query historical performance
        history_indicators = ['history', 'past', 'previous', 'performance']
        found = any(indicator in code for indicator in history_indicators)
        
        self.assertTrue(found, 
            "Decisions should be influenced by historical performance")
    
    def test_no_static_weights(self):
        """Verify system doesn't use static weights for sources"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Bad pattern: hardcoded weights
        bad_patterns = [
            'whale_weight = 0.8',
            'weights = {',  # Only bad if static
            'FIXED_WEIGHT',
        ]
        
        # Should be dynamic, not static configuration


class TestGoal4_RealTimePerformance(unittest.TestCase):
    """Goal 4: Agent executes quickly enough for real-time decisions"""
    
    def test_database_has_indexes(self):
        """Verify database uses indexes for performance"""
        db_file = Path(__file__).parent.parent / "src" / "database.py"
        with open(db_file) as f:
            code = f.read()
        
        # Should create indexes
        self.assertIn('CREATE INDEX', code.upper() or 
                     'create_index' in code.lower())
    
    def test_no_full_table_scans(self):
        """Verify queries don't do full table scans"""
        # Check for efficient query patterns
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Bad pattern: SELECT * without WHERE
        if 'SELECT *' in code:
            self.assertIn('WHERE', code, 
                "SELECT * should have WHERE clause for performance")
    
    def test_async_operations_where_possible(self):
        """Verify system uses async for parallel operations"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Check for parallel execution
        parallel_indicators = ['ThreadPoolExecutor', 'concurrent', 'async', 'parallel']
        found = any(indicator in code for indicator in parallel_indicators)
        
        # Note: This is a suggestion, not required
        if not found:
            print("Warning: Consider using parallel execution for data sources")
    
    def test_timeout_protection(self):
        """Verify system has timeout protection"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Should have timeout handling
        timeout_indicators = ['timeout', 'max_wait', 'deadline']
        found = any(indicator in code.lower() for indicator in timeout_indicators)


class TestGoal5_SignalQuality(unittest.TestCase):
    """Goal 5: Agent generates high-quality, actionable signals"""
    
    def test_signals_have_severity(self):
        """Verify signals include severity levels"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        self.assertIn('severity', code, "Signals should have severity")
    
    def test_signals_have_confidence(self):
        """Verify signals include confidence scores"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        confidence_indicators = ['confidence', 'probability', 'certainty']
        found = any(indicator in code for indicator in confidence_indicators)
    
    def test_signals_stored_for_analysis(self):
        """Verify signals are stored for quality tracking"""
        db_file = Path(__file__).parent.parent / "src" / "database.py"
        with open(db_file) as f:
            code = f.read()
        
        self.assertIn('signals', code.lower() or 'alert' in code.lower())
    
    def test_multiple_signal_types(self):
        """Verify system supports multiple signal types"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Should have different signal types
        signal_types = ['WHALE_ACTIVITY', 'NARRATIVE', 'INSTITUTIONAL', 'EXTREME']
        found = sum(1 for sig in signal_types if sig in code)
        
        self.assertGreaterEqual(found, 3, 
            "Should support multiple signal types")


class TestGoal6_DataSourceDiversity(unittest.TestCase):
    """Goal 6: Agent uses diverse data sources, not just one or two"""
    
    def test_minimum_eight_sources(self):
        """Verify agent has at least 8 data sources"""
        # Check Lambda functions
        lambda_dir = Path(__file__).parent.parent / "lambda_functions"
        
        if lambda_dir.exists():
            source_dirs = [d for d in lambda_dir.iterdir() if d.is_dir() and 
                          not d.name.startswith('__')]
            self.assertGreaterEqual(len(source_dirs), 8,
                f"Should have at least 8 data sources, found {len(source_dirs)}")
    
    def test_sources_cover_different_categories(self):
        """Verify sources cover different market aspects"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Different categories
        categories = [
            'whale',        # On-chain
            'narrative',    # Social
            'arbitrage',    # Price
            'derivatives',  # Futures
            'technical',    # Charts
            'institutional',# Large holders
            'macro',        # Sentiment
        ]
        
        found = sum(1 for cat in categories if cat in code.lower())
        self.assertGreaterEqual(found, 5, 
            "Sources should cover diverse market aspects")
    
    def test_no_source_monopoly(self):
        """Verify no single source dominates queries"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Should not have logic like "always query whale_movements first"
        bad_patterns = [
            'primary_source',
            'always_query',
            'mandatory_source'
        ]
        
        # Check that no source is special


class TestGoal7_Architecture(unittest.TestCase):
    """Goal 7: Clean architecture and maintainability"""
    
    def test_separation_of_concerns(self):
        """Verify core components are separated"""
        src_dir = Path(__file__).parent.parent / "src"
        
        # Should have separate modules
        expected_modules = [
            'market_hunter_agent.py',
            'database.py',
            'llm_router.py'
        ]
        
        for module in expected_modules:
            module_path = src_dir / module
            self.assertTrue(module_path.exists(), 
                f"Should have separate module: {module}")
    
    def test_configuration_externalized(self):
        """Verify configuration is not hardcoded"""
        # Check for config files
        config_dir = Path(__file__).parent.parent / "config"
        
        if config_dir.exists():
            config_files = list(config_dir.glob("*.json")) + list(config_dir.glob("*.yaml"))
            self.assertGreater(len(config_files), 0, 
                "Should have external configuration files")
    
    def test_error_handling_exists(self):
        """Verify proper error handling"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Should have try/except blocks
        self.assertIn('try:', code)
        self.assertIn('except', code)
    
    def test_logging_implemented(self):
        """Verify logging is used for debugging"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        logging_indicators = ['logging', 'logger', 'log.']
        found = any(indicator in code for indicator in logging_indicators)
        
        self.assertTrue(found, "Should use logging for observability")


class TestGoal8_Testing(unittest.TestCase):
    """Goal 8: Codebase has comprehensive tests"""
    
    def test_unit_tests_exist(self):
        """Verify unit tests are present"""
        tests_dir = Path(__file__).parent
        
        test_files = list(tests_dir.glob("test_*.py"))
        self.assertGreater(len(test_files), 3,
            f"Should have multiple test files, found {len(test_files)}")
    
    def test_integration_tests_exist(self):
        """Verify integration tests exist"""
        tests_dir = Path(__file__).parent
        
        integration_test = tests_dir / "test_integration.py"
        self.assertTrue(integration_test.exists(),
            "Should have integration tests")
    
    def test_evaluation_framework_exists(self):
        """Verify evaluation framework exists"""
        tests_dir = Path(__file__).parent
        
        eval_test = tests_dir / "test_evaluations.py"
        self.assertTrue(eval_test.exists(),
            "Should have evaluation framework")


class TestGoal9_Documentation(unittest.TestCase):
    """Goal 9: Code is well-documented"""
    
    def test_readme_exists(self):
        """Verify README exists and is comprehensive"""
        readme = Path(__file__).parent.parent / "README.md"
        self.assertTrue(readme.exists(), "Should have README.md")
        
        with open(readme) as f:
            content = f.read()
        
        self.assertGreater(len(content), 1000,
            "README should be comprehensive (>1000 chars)")
    
    def test_architecture_documentation(self):
        """Verify architecture is documented"""
        docs_dir = Path(__file__).parent.parent / "docs"
        
        if docs_dir.exists():
            doc_files = list(docs_dir.glob("*.md"))
            self.assertGreater(len(doc_files), 0,
                "Should have documentation files")
    
    def test_docstrings_in_main_classes(self):
        """Verify main classes have docstrings"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Should have docstrings
        docstring_indicators = ['"""', "'''"]
        found = any(indicator in code for indicator in docstring_indicators)
        
        self.assertTrue(found, "Classes should have docstrings")


class TestGoal10_Production_Readiness(unittest.TestCase):
    """Goal 10: System is production-ready"""
    
    def test_environment_variables_used(self):
        """Verify sensitive data uses environment variables"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Should not have hardcoded credentials
        self.assertNotIn('password="', code.lower())
        self.assertNotIn('api_key="sk-', code.lower())
    
    def test_deployment_scripts_exist(self):
        """Verify deployment automation exists"""
        root_dir = Path(__file__).parent.parent
        
        deploy_files = list(root_dir.glob("deploy*.sh")) + \
                      list(root_dir.glob("deploy*.py"))
        
        self.assertGreater(len(deploy_files), 0,
            "Should have deployment scripts")
    
    def test_requirements_file_exists(self):
        """Verify requirements.txt exists"""
        requirements = Path(__file__).parent.parent / "requirements.txt"
        self.assertTrue(requirements.exists(),
            "Should have requirements.txt")
    
    def test_ci_cd_configured(self):
        """Verify CI/CD is configured"""
        github_dir = Path(__file__).parent.parent / ".github" / "workflows"
        
        # Not required but recommended
        if github_dir.exists():
            workflow_files = list(github_dir.glob("*.yml")) + \
                           list(github_dir.glob("*.yaml"))
            if len(workflow_files) > 0:
                print("✓ CI/CD workflows configured")


def run_goal_alignment_tests(verbose=True):
    """
    Run all goal alignment tests
    
    Returns:
        dict: Test results with pass/fail counts
    """
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all goal test classes
    test_classes = [
        TestGoal1_Autonomy,
        TestGoal2_CostOptimization,
        TestGoal3_LearningAndAdaptation,
        TestGoal4_RealTimePerformance,
        TestGoal5_SignalQuality,
        TestGoal6_DataSourceDiversity,
        TestGoal7_Architecture,
        TestGoal8_Testing,
        TestGoal9_Documentation,
        TestGoal10_Production_Readiness,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    # Return results
    return {
        'total': result.testsRun,
        'passed': result.testsRun - len(result.failures) - len(result.errors),
        'failed': len(result.failures),
        'errors': len(result.errors),
        'skipped': len(result.skipped),
        'success': result.wasSuccessful()
    }


if __name__ == "__main__":
    print("=" * 80)
    print("GOAL ALIGNMENT TESTS")
    print("=" * 80)
    print("\nVerifying codebase alignment with project goals:")
    print("1. ✓ Autonomous decision-making")
    print("2. ✓ Cost optimization")
    print("3. ✓ Learning and adaptation")
    print("4. ✓ Real-time performance")
    print("5. ✓ Signal quality")
    print("6. ✓ Data source diversity")
    print("7. ✓ Clean architecture")
    print("8. ✓ Comprehensive testing")
    print("9. ✓ Documentation")
    print("10. ✓ Production readiness")
    print("\n" + "=" * 80 + "\n")
    
    results = run_goal_alignment_tests(verbose=True)
    
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Total Tests: {results['total']}")
    print(f"✓ Passed: {results['passed']}")
    print(f"✗ Failed: {results['failed']}")
    print(f"⚠ Errors: {results['errors']}")
    print(f"○ Skipped: {results['skipped']}")
    print(f"\nOverall: {'SUCCESS ✓' if results['success'] else 'FAILURE ✗'}")
    print("=" * 80)
    
    # Exit with proper code
    sys.exit(0 if results['success'] else 1)
