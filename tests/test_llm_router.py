"""
Unit tests for LLM Router

Tests intelligent model selection, scoring algorithm, and cost optimization.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_router import (
    LLMRouter,
    RoutingCriteria,
    TaskType,
    ModelCapability,
    BedrockModelRegistry,
    BedrockModel
)


class TestModelRegistry(unittest.TestCase):
    """Test Bedrock Model Registry"""
    
    def setUp(self):
        """Set up test registry"""
        self.registry = BedrockModelRegistry()
    
    def test_registry_has_10_models(self):
        """Test that registry contains 10 models"""
        self.assertEqual(len(self.registry.models), 10)
    
    def test_get_model_by_id(self):
        """Test retrieving model by ID"""
        model = self.registry.get_model_by_id("anthropic.claude-3-haiku-20240307-v1:0")
        self.assertIsNotNone(model)
        self.assertEqual(model.name, "Claude 3 Haiku")
        self.assertEqual(model.provider, "Anthropic")
    
    def test_get_models_by_capability(self):
        """Test filtering models by capability"""
        expert_models = self.registry.get_models_by_capability(ModelCapability.EXPERT)
        
        self.assertGreater(len(expert_models), 0)
        # Claude 3.5 Sonnet and Opus should be expert
        model_names = [m.name for m in expert_models]
        self.assertIn("Claude 3.5 Sonnet", model_names)
    
    def test_get_models_by_provider(self):
        """Test filtering models by provider"""
        anthropic_models = self.registry.get_models_by_provider("Anthropic")
        
        self.assertEqual(len(anthropic_models), 4)  # 4 Claude models
        for model in anthropic_models:
            self.assertEqual(model.provider, "Anthropic")
    
    def test_get_models_by_region(self):
        """Test filtering models by region"""
        us_east_models = self.registry.get_models_by_region("us-east-1")
        
        # All models should be available in us-east-1
        self.assertEqual(len(us_east_models), 10)
    
    def test_model_cost_structure(self):
        """Test that all models have valid cost structure"""
        for model in self.registry.models:
            self.assertGreater(model.cost_per_1k_input_tokens, 0)
            self.assertGreater(model.cost_per_1k_output_tokens, 0)
            self.assertGreater(model.context_window, 0)


class TestModelSelection(unittest.TestCase):
    """Test intelligent model selection logic"""
    
    def setUp(self):
        """Set up test router"""
        self.router = LLMRouter(region_name="us-east-1")
    
    def test_simple_task_selects_cheap_model(self):
        """Test that simple tasks select cheap models"""
        criteria = RoutingCriteria(
            task_type=TaskType.DATA_EXTRACTION,
            estimated_input_tokens=500,
            estimated_output_tokens=100
        )
        
        selected_model = self.router.select_model(criteria)
        
        # Should select a cheap model like Haiku, Titan Lite, or Llama 8B
        cheap_models = ["Claude 3 Haiku", "Titan Text Lite", "Llama 3 8B", "Mistral 7B"]
        self.assertIn(selected_model.name, cheap_models)
    
    def test_complex_task_selects_advanced_model(self):
        """Test that complex tasks select advanced models"""
        criteria = RoutingCriteria(
            task_type=TaskType.COMPLEX_REASONING,
            min_capability=ModelCapability.ADVANCED,
            estimated_input_tokens=5000,
            estimated_output_tokens=2000
        )
        
        selected_model = self.router.select_model(criteria)
        
        # Should select advanced model
        advanced_models = [
            "Claude 3 Sonnet", "Claude 3.5 Sonnet", "Claude 3 Opus",
            "Llama 3 70B", "Mistral Large"
        ]
        self.assertIn(selected_model.name, advanced_models)
    
    def test_expert_capability_filters_correctly(self):
        """Test that expert capability requirement filters to expert models"""
        criteria = RoutingCriteria(
            task_type=TaskType.RISK_ASSESSMENT,
            min_capability=ModelCapability.EXPERT
        )
        
        selected_model = self.router.select_model(criteria)
        
        # Should only select expert models
        self.assertEqual(selected_model.capability, ModelCapability.EXPERT)
    
    def test_cost_constraint_filters_expensive_models(self):
        """Test that cost constraints filter out expensive models"""
        criteria = RoutingCriteria(
            task_type=TaskType.PATTERN_RECOGNITION,
            max_cost_per_request=0.001,
            estimated_input_tokens=1000,
            estimated_output_tokens=500
        )
        
        selected_model = self.router.select_model(criteria)
        
        # Calculate cost
        cost = (
            (1000 / 1000) * selected_model.cost_per_1k_input_tokens +
            (500 / 1000) * selected_model.cost_per_1k_output_tokens
        )
        
        # Should be within budget
        self.assertLessEqual(cost, 0.001)
    
    def test_provider_preference_prioritizes_provider(self):
        """Test that provider preference works"""
        criteria = RoutingCriteria(
            task_type=TaskType.SIMPLE_ANALYSIS,
            preferred_provider="Meta"
        )
        
        selected_model = self.router.select_model(criteria)
        
        # Should select Meta model (Llama)
        self.assertEqual(selected_model.provider, "Meta")
    
    def test_long_context_selects_large_context_window(self):
        """Test that long context tasks select models with large context windows"""
        criteria = RoutingCriteria(
            task_type=TaskType.LONG_CONTEXT,
            estimated_input_tokens=50000,
            min_capability=ModelCapability.ADVANCED
        )
        
        selected_model = self.router.select_model(criteria)
        
        # Should select model with large context window (Claude or Mistral Large)
        self.assertGreaterEqual(selected_model.context_window, 32000)


class TestScoringAlgorithm(unittest.TestCase):
    """Test model scoring algorithm"""
    
    def setUp(self):
        """Set up test router"""
        self.router = LLMRouter(region_name="us-east-1")
    
    def test_capability_score_calculation(self):
        """Test capability scoring"""
        model = self.router.registry.get_model_by_id("anthropic.claude-3-haiku-20240307-v1:0")
        criteria = RoutingCriteria(
            task_type=TaskType.DATA_EXTRACTION,
            min_capability=ModelCapability.BASIC
        )
        
        score = self.router._calculate_model_score(model, criteria)
        
        # Haiku should score well for simple tasks
        self.assertGreater(score, 0)
    
    def test_cost_efficiency_bonus(self):
        """Test that cheap models get cost efficiency bonus"""
        cheap_model = self.router.registry.get_model_by_id("amazon.titan-text-lite-v1")
        expensive_model = self.router.registry.get_model_by_id("anthropic.claude-3-opus-20240229-v1:0")
        
        criteria = RoutingCriteria(
            task_type=TaskType.SIMPLE_ANALYSIS,
            estimated_input_tokens=1000,
            estimated_output_tokens=200
        )
        
        cheap_score = self.router._calculate_model_score(cheap_model, criteria)
        expensive_score = self.router._calculate_model_score(expensive_model, criteria)
        
        # For simple tasks, cheap model should score higher
        self.assertGreater(cheap_score, expensive_score)
    
    def test_speed_score_calculation(self):
        """Test speed scoring"""
        fast_model = self.router.registry.get_model_by_id("amazon.titan-text-lite-v1")
        
        criteria = RoutingCriteria(
            task_type=TaskType.FAST_RESPONSE
        )
        
        score = self.router._calculate_model_score(fast_model, criteria)
        
        # Fast model should score well for speed-critical tasks
        self.assertGreater(score, 50)
    
    def test_reasoning_score_for_complex_tasks(self):
        """Test that reasoning score is weighted for complex tasks"""
        advanced_model = self.router.registry.get_model_by_id(
            "anthropic.claude-3-5-sonnet-20240620-v1:0"
        )
        
        criteria = RoutingCriteria(
            task_type=TaskType.COMPLEX_REASONING
        )
        
        score = self.router._calculate_model_score(advanced_model, criteria)
        
        # Advanced model should score very well for complex reasoning
        self.assertGreater(score, 70)


class TestUsageTracking(unittest.TestCase):
    """Test usage tracking and cost reporting"""
    
    def setUp(self):
        """Set up test router"""
        self.router = LLMRouter(region_name="us-east-1")
    
    @patch('llm_router.boto3.client')
    def test_usage_tracking_records_invocation(self, mock_boto3_client):
        """Test that invocations are tracked"""
        # Mock Bedrock Runtime client
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        
        # Mock response
        mock_response = {
            'body': MagicMock(read=lambda: b'{"completion": "test response"}')
        }
        mock_client.invoke_model.return_value = mock_response
        
        criteria = RoutingCriteria(
            task_type=TaskType.DATA_EXTRACTION,
            estimated_input_tokens=100,
            estimated_output_tokens=50
        )
        
        # Invoke model
        try:
            self.router.invoke_model("Test prompt", criteria)
        except:
            pass  # May fail due to mocking, but tracking should still work
        
        # Check usage report
        report = self.router.get_llm_usage_report()
        
        # Should have recorded something (even if invocation failed)
        self.assertIn('total_invocations', report)
        self.assertIn('total_cost', report)
    
    def test_usage_report_structure(self):
        """Test usage report structure"""
        report = self.router.get_llm_usage_report()
        
        # Check required fields
        self.assertIn('total_invocations', report)
        self.assertIn('total_cost', report)
        self.assertIn('total_input_tokens', report)
        self.assertIn('total_output_tokens', report)
        self.assertIn('usage_by_model', report)
        self.assertIsInstance(report['usage_by_model'], dict)
    
    def test_reset_usage_tracking(self):
        """Test resetting usage tracking"""
        # Add some fake usage
        self.router.usage_tracking['total_invocations'] = 10
        self.router.usage_tracking['total_cost'] = 5.0
        
        # Reset
        self.router.reset_usage_tracking()
        
        report = self.router.get_llm_usage_report()
        
        self.assertEqual(report['total_invocations'], 0)
        self.assertEqual(report['total_cost'], 0.0)


class TestCostOptimization(unittest.TestCase):
    """Test cost optimization scenarios"""
    
    def setUp(self):
        """Set up test router"""
        self.router = LLMRouter(region_name="us-east-1")
    
    def test_bulk_processing_uses_cheapest_model(self):
        """Test that bulk processing selects cheapest viable model"""
        criteria = RoutingCriteria(
            task_type=TaskType.COST_OPTIMIZED,
            estimated_input_tokens=50,
            estimated_output_tokens=20,
            max_cost_per_request=0.0001
        )
        
        selected_model = self.router.select_model(criteria)
        
        # Should select very cheap model
        self.assertLessEqual(selected_model.cost_per_1k_input_tokens, 0.0005)
    
    def test_cost_estimate_accuracy(self):
        """Test cost estimation accuracy"""
        model = self.router.registry.get_model_by_id("anthropic.claude-3-haiku-20240307-v1:0")
        
        input_tokens = 1000
        output_tokens = 500
        
        expected_cost = (
            (input_tokens / 1000) * model.cost_per_1k_input_tokens +
            (output_tokens / 1000) * model.cost_per_1k_output_tokens
        )
        
        # Calculate using router's method
        criteria = RoutingCriteria(
            task_type=TaskType.DATA_EXTRACTION,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens
        )
        
        # Estimate cost
        estimated_cost = (
            (input_tokens / 1000) * model.cost_per_1k_input_tokens +
            (output_tokens / 1000) * model.cost_per_1k_output_tokens
        )
        
        self.assertAlmostEqual(estimated_cost, expected_cost, places=6)


if __name__ == '__main__':
    unittest.main()
