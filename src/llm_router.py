"""
Dynamic LLM Router for Amazon Bedrock
Intelligently selects the best model based on task requirements
"""

from enum import Enum
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
import boto3
import logging
import json

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks requiring LLM inference"""
    SIMPLE_ANALYSIS = "simple_analysis"  # Quick data parsing, simple questions
    COMPLEX_REASONING = "complex_reasoning"  # Multi-step analysis, pattern detection
    DATA_EXTRACTION = "data_extraction"  # Structured data extraction
    SIGNAL_GENERATION = "signal_generation"  # Generate trading signals
    PATTERN_RECOGNITION = "pattern_recognition"  # Identify market patterns
    RISK_ASSESSMENT = "risk_assessment"  # Evaluate risks
    LONG_CONTEXT = "long_context"  # Large documents, many data sources
    FAST_RESPONSE = "fast_response"  # Speed critical tasks
    COST_OPTIMIZED = "cost_optimized"  # Budget-conscious tasks


class ModelCapability(Enum):
    """Model capability levels"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class BedrockModel:
    """Bedrock model configuration"""
    model_id: str
    name: str
    provider: str
    capability: ModelCapability
    context_window: int  # tokens
    cost_per_1k_input: float  # USD
    cost_per_1k_output: float  # USD
    speed_score: int  # 1-10, higher is faster
    reasoning_score: int  # 1-10, higher is better
    best_for: List[TaskType]
    region_available: List[str]


class BedrockModelRegistry:
    """Registry of available Bedrock models"""
    
    # Anthropic Claude Models
    CLAUDE_3_HAIKU = BedrockModel(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        name="Claude 3 Haiku",
        provider="Anthropic",
        capability=ModelCapability.INTERMEDIATE,
        context_window=200000,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00125,
        speed_score=10,
        reasoning_score=7,
        best_for=[TaskType.SIMPLE_ANALYSIS, TaskType.DATA_EXTRACTION, TaskType.FAST_RESPONSE, TaskType.COST_OPTIMIZED],
        region_available=["us-east-1", "us-west-2", "eu-west-1"]
    )
    
    CLAUDE_3_SONNET = BedrockModel(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        name="Claude 3 Sonnet",
        provider="Anthropic",
        capability=ModelCapability.ADVANCED,
        context_window=200000,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        speed_score=7,
        reasoning_score=9,
        best_for=[TaskType.COMPLEX_REASONING, TaskType.PATTERN_RECOGNITION, TaskType.SIGNAL_GENERATION],
        region_available=["us-east-1", "us-west-2", "eu-west-1"]
    )
    
    CLAUDE_3_5_SONNET = BedrockModel(
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        name="Claude 3.5 Sonnet",
        provider="Anthropic",
        capability=ModelCapability.EXPERT,
        context_window=200000,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        speed_score=7,
        reasoning_score=10,
        best_for=[TaskType.COMPLEX_REASONING, TaskType.RISK_ASSESSMENT, TaskType.LONG_CONTEXT],
        region_available=["us-east-1", "us-west-2", "eu-west-1"]
    )
    
    CLAUDE_3_OPUS = BedrockModel(
        model_id="anthropic.claude-3-opus-20240229-v1:0",
        name="Claude 3 Opus",
        provider="Anthropic",
        capability=ModelCapability.EXPERT,
        context_window=200000,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        speed_score=4,
        reasoning_score=10,
        best_for=[TaskType.COMPLEX_REASONING, TaskType.RISK_ASSESSMENT],
        region_available=["us-east-1", "us-west-2"]
    )
    
    # Amazon Titan Models
    TITAN_TEXT_EXPRESS = BedrockModel(
        model_id="amazon.titan-text-express-v1",
        name="Titan Text Express",
        provider="Amazon",
        capability=ModelCapability.INTERMEDIATE,
        context_window=8000,
        cost_per_1k_input=0.0008,
        cost_per_1k_output=0.0016,
        speed_score=9,
        reasoning_score=6,
        best_for=[TaskType.SIMPLE_ANALYSIS, TaskType.DATA_EXTRACTION, TaskType.COST_OPTIMIZED],
        region_available=["us-east-1", "us-west-2", "eu-west-1"]
    )
    
    TITAN_TEXT_LITE = BedrockModel(
        model_id="amazon.titan-text-lite-v1",
        name="Titan Text Lite",
        provider="Amazon",
        capability=ModelCapability.BASIC,
        context_window=4000,
        cost_per_1k_input=0.0003,
        cost_per_1k_output=0.0004,
        speed_score=10,
        reasoning_score=5,
        best_for=[TaskType.SIMPLE_ANALYSIS, TaskType.FAST_RESPONSE, TaskType.COST_OPTIMIZED],
        region_available=["us-east-1", "us-west-2", "eu-west-1"]
    )
    
    # Meta Llama Models
    LLAMA_3_8B_INSTRUCT = BedrockModel(
        model_id="meta.llama3-8b-instruct-v1:0",
        name="Llama 3 8B Instruct",
        provider="Meta",
        capability=ModelCapability.INTERMEDIATE,
        context_window=8000,
        cost_per_1k_input=0.0003,
        cost_per_1k_output=0.0006,
        speed_score=9,
        reasoning_score=7,
        best_for=[TaskType.SIMPLE_ANALYSIS, TaskType.DATA_EXTRACTION, TaskType.COST_OPTIMIZED],
        region_available=["us-east-1", "us-west-2"]
    )
    
    LLAMA_3_70B_INSTRUCT = BedrockModel(
        model_id="meta.llama3-70b-instruct-v1:0",
        name="Llama 3 70B Instruct",
        provider="Meta",
        capability=ModelCapability.ADVANCED,
        context_window=8000,
        cost_per_1k_input=0.00265,
        cost_per_1k_output=0.0035,
        speed_score=6,
        reasoning_score=8,
        best_for=[TaskType.COMPLEX_REASONING, TaskType.PATTERN_RECOGNITION],
        region_available=["us-east-1", "us-west-2"]
    )
    
    # Mistral Models
    MISTRAL_7B_INSTRUCT = BedrockModel(
        model_id="mistral.mistral-7b-instruct-v0:2",
        name="Mistral 7B Instruct",
        provider="Mistral AI",
        capability=ModelCapability.INTERMEDIATE,
        context_window=32000,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0002,
        speed_score=9,
        reasoning_score=7,
        best_for=[TaskType.SIMPLE_ANALYSIS, TaskType.DATA_EXTRACTION, TaskType.COST_OPTIMIZED],
        region_available=["us-east-1", "us-west-2", "eu-west-1"]
    )
    
    MISTRAL_LARGE = BedrockModel(
        model_id="mistral.mistral-large-2402-v1:0",
        name="Mistral Large",
        provider="Mistral AI",
        capability=ModelCapability.ADVANCED,
        context_window=32000,
        cost_per_1k_input=0.004,
        cost_per_1k_output=0.012,
        speed_score=7,
        reasoning_score=9,
        best_for=[TaskType.COMPLEX_REASONING, TaskType.LONG_CONTEXT, TaskType.PATTERN_RECOGNITION],
        region_available=["us-east-1", "us-west-2", "eu-west-1"]
    )
    
    @classmethod
    def get_all_models(cls) -> List[BedrockModel]:
        """Get all available models"""
        return [
            cls.CLAUDE_3_HAIKU,
            cls.CLAUDE_3_SONNET,
            cls.CLAUDE_3_5_SONNET,
            cls.CLAUDE_3_OPUS,
            cls.TITAN_TEXT_EXPRESS,
            cls.TITAN_TEXT_LITE,
            cls.LLAMA_3_8B_INSTRUCT,
            cls.LLAMA_3_70B_INSTRUCT,
            cls.MISTRAL_7B_INSTRUCT,
            cls.MISTRAL_LARGE
        ]
    
    @classmethod
    def get_models_by_task(cls, task_type: TaskType) -> List[BedrockModel]:
        """Get models suitable for a specific task"""
        return [model for model in cls.get_all_models() if task_type in model.best_for]
    
    @classmethod
    def get_model_by_id(cls, model_id: str) -> Optional[BedrockModel]:
        """Get model by ID"""
        for model in cls.get_all_models():
            if model.model_id == model_id:
                return model
        return None


@dataclass
class RoutingCriteria:
    """Criteria for selecting a model"""
    task_type: TaskType
    estimated_input_tokens: int = 1000
    estimated_output_tokens: int = 500
    max_latency_ms: Optional[int] = None  # Maximum acceptable latency
    max_cost_per_request: Optional[float] = None  # Maximum cost per request
    min_capability: ModelCapability = ModelCapability.INTERMEDIATE
    preferred_provider: Optional[str] = None
    region: str = "us-east-1"


class LLMRouter:
    """
    Intelligent LLM Router for Amazon Bedrock
    Dynamically selects the best model based on task requirements
    """
    
    def __init__(self, region_name: str = "us-east-1", default_model: Optional[str] = None):
        """
        Initialize the LLM Router
        
        Args:
            region_name: AWS region
            default_model: Default model ID to use if routing fails
        """
        self.region_name = region_name
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
        self.default_model = default_model or BedrockModelRegistry.CLAUDE_3_SONNET.model_id
        
        # Track usage for cost optimization
        self.usage_stats: Dict[str, Dict] = {}
        
        logger.info(f"LLM Router initialized in region {region_name}")
    
    def select_model(self, criteria: RoutingCriteria) -> BedrockModel:
        """
        Select the best model based on routing criteria
        
        Args:
            criteria: Routing criteria
            
        Returns:
            Selected BedrockModel
        """
        # Get candidate models
        candidates = BedrockModelRegistry.get_models_by_task(criteria.task_type)
        
        # Filter by region availability
        candidates = [m for m in candidates if criteria.region in m.region_available]
        
        # Filter by minimum capability
        capability_order = {
            ModelCapability.BASIC: 1,
            ModelCapability.INTERMEDIATE: 2,
            ModelCapability.ADVANCED: 3,
            ModelCapability.EXPERT: 4
        }
        min_cap_level = capability_order[criteria.min_capability]
        candidates = [m for m in candidates if capability_order[m.capability] >= min_cap_level]
        
        # Filter by provider preference
        if criteria.preferred_provider:
            provider_candidates = [m for m in candidates if m.provider == criteria.preferred_provider]
            if provider_candidates:
                candidates = provider_candidates
        
        if not candidates:
            logger.warning(f"No suitable models found for {criteria.task_type}, using default")
            return BedrockModelRegistry.get_model_by_id(self.default_model)
        
        # Score each candidate
        scored_candidates = []
        for model in candidates:
            score = self._calculate_model_score(model, criteria)
            scored_candidates.append((model, score))
        
        # Sort by score (higher is better)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        selected_model = scored_candidates[0][0]
        logger.info(
            f"Selected {selected_model.name} for {criteria.task_type.value} "
            f"(score: {scored_candidates[0][1]:.2f})"
        )
        
        return selected_model
    
    def _calculate_model_score(self, model: BedrockModel, criteria: RoutingCriteria) -> float:
        """
        Calculate a score for a model based on criteria
        Higher score is better
        
        Args:
            model: Model to score
            criteria: Routing criteria
            
        Returns:
            Score (0-100)
        """
        score = 0.0
        
        # Base score from capability
        capability_scores = {
            ModelCapability.BASIC: 20,
            ModelCapability.INTERMEDIATE: 40,
            ModelCapability.ADVANCED: 60,
            ModelCapability.EXPERT: 80
        }
        score += capability_scores[model.capability]
        
        # Cost score (inverse - lower cost is better)
        estimated_cost = (
            (criteria.estimated_input_tokens / 1000) * model.cost_per_1k_input +
            (criteria.estimated_output_tokens / 1000) * model.cost_per_1k_output
        )
        
        if criteria.max_cost_per_request:
            if estimated_cost > criteria.max_cost_per_request:
                score -= 50  # Heavy penalty for exceeding budget
            else:
                # Reward staying under budget
                cost_efficiency = 1 - (estimated_cost / criteria.max_cost_per_request)
                score += cost_efficiency * 20
        else:
            # General cost optimization (prefer cheaper when no budget constraint)
            max_cost = 0.10  # Assume max $0.10 per request for normalization
            cost_score = (1 - min(estimated_cost / max_cost, 1.0)) * 15
            score += cost_score
        
        # Speed score
        if criteria.max_latency_ms:
            # Map speed_score (1-10) to expected latency
            # Higher speed_score = lower latency
            score += model.speed_score * 2
        else:
            score += model.speed_score * 1  # Less weight if latency not critical
        
        # Reasoning score (important for complex tasks)
        if criteria.task_type in [
            TaskType.COMPLEX_REASONING,
            TaskType.RISK_ASSESSMENT,
            TaskType.PATTERN_RECOGNITION
        ]:
            score += model.reasoning_score * 3
        else:
            score += model.reasoning_score * 1
        
        # Context window bonus for long context tasks
        if criteria.task_type == TaskType.LONG_CONTEXT:
            if model.context_window >= 100000:
                score += 20
            elif model.context_window >= 32000:
                score += 10
        
        return score
    
    def invoke_model(
        self,
        prompt: str,
        criteria: RoutingCriteria,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Invoke a model with automatic selection
        
        Args:
            prompt: User prompt
            criteria: Routing criteria
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            
        Returns:
            Model response
        """
        # Select best model
        model = self.select_model(criteria)
        
        # Build request based on provider
        try:
            if model.provider == "Anthropic":
                response = self._invoke_claude(model, prompt, temperature, max_tokens, system_prompt)
            elif model.provider == "Amazon":
                response = self._invoke_titan(model, prompt, temperature, max_tokens)
            elif model.provider == "Meta":
                response = self._invoke_llama(model, prompt, temperature, max_tokens)
            elif model.provider == "Mistral AI":
                response = self._invoke_mistral(model, prompt, temperature, max_tokens)
            else:
                raise ValueError(f"Unsupported provider: {model.provider}")
            
            # Track usage
            self._track_usage(model, response)
            
            # Add model info to response
            response['model_used'] = model.model_id
            response['model_name'] = model.name
            response['provider'] = model.provider
            
            return response
            
        except Exception as e:
            logger.error(f"Error invoking {model.name}: {str(e)}")
            raise
    
    def _invoke_claude(
        self,
        model: BedrockModel,
        prompt: str,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str]
    ) -> Dict:
        """Invoke Claude model"""
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        if system_prompt:
            request_body["system"] = system_prompt
        
        response = self.bedrock_runtime.invoke_model(
            modelId=model.model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        return {
            'text': response_body['content'][0]['text'],
            'usage': response_body.get('usage', {}),
            'stop_reason': response_body.get('stop_reason')
        }
    
    def _invoke_titan(
        self,
        model: BedrockModel,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> Dict:
        """Invoke Titan model"""
        request_body = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": temperature,
                "topP": 0.9
            }
        }
        
        response = self.bedrock_runtime.invoke_model(
            modelId=model.model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        return {
            'text': response_body['results'][0]['outputText'],
            'usage': {
                'input_tokens': response_body.get('inputTextTokenCount', 0),
                'output_tokens': response_body['results'][0].get('tokenCount', 0)
            }
        }
    
    def _invoke_llama(
        self,
        model: BedrockModel,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> Dict:
        """Invoke Llama model"""
        request_body = {
            "prompt": prompt,
            "max_gen_len": max_tokens,
            "temperature": temperature,
            "top_p": 0.9
        }
        
        response = self.bedrock_runtime.invoke_model(
            modelId=model.model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        return {
            'text': response_body['generation'],
            'usage': {
                'input_tokens': response_body.get('prompt_token_count', 0),
                'output_tokens': response_body.get('generation_token_count', 0)
            }
        }
    
    def _invoke_mistral(
        self,
        model: BedrockModel,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> Dict:
        """Invoke Mistral model"""
        request_body = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9
        }
        
        response = self.bedrock_runtime.invoke_model(
            modelId=model.model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        return {
            'text': response_body['outputs'][0]['text'],
            'usage': {
                'input_tokens': 0,  # Mistral doesn't return token counts
                'output_tokens': 0
            }
        }
    
    def _track_usage(self, model: BedrockModel, response: Dict):
        """Track model usage for analytics"""
        if model.model_id not in self.usage_stats:
            self.usage_stats[model.model_id] = {
                'model_name': model.name,
                'invocations': 0,
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'total_cost': 0.0
            }
        
        stats = self.usage_stats[model.model_id]
        stats['invocations'] += 1
        
        usage = response.get('usage', {})
        input_tokens = usage.get('input_tokens', 0)
        output_tokens = usage.get('output_tokens', 0)
        
        stats['total_input_tokens'] += input_tokens
        stats['total_output_tokens'] += output_tokens
        
        cost = (
            (input_tokens / 1000) * model.cost_per_1k_input +
            (output_tokens / 1000) * model.cost_per_1k_output
        )
        stats['total_cost'] += cost
    
    def get_usage_report(self) -> Dict:
        """Get usage statistics report"""
        return {
            'usage_by_model': self.usage_stats,
            'total_cost': sum(stats['total_cost'] for stats in self.usage_stats.values()),
            'total_invocations': sum(stats['invocations'] for stats in self.usage_stats.values())
        }


# Convenience functions for common tasks
def get_router_for_task(task_type: TaskType, **kwargs) -> tuple[LLMRouter, RoutingCriteria]:
    """
    Get a configured router and criteria for a specific task
    
    Returns:
        Tuple of (router, criteria)
    """
    router = LLMRouter(**kwargs)
    criteria = RoutingCriteria(task_type=task_type)
    return router, criteria
