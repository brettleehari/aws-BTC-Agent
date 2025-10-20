"""
Metadata models for data source capability advertisement.

Defines the schema for describing data source capabilities so agents
can intelligently select the right source for their needs.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Set


class DataType(Enum):
    """Types of data that can be fetched"""
    PRICE = "price"
    MARKET_CAP = "market_cap"
    VOLUME = "volume"
    ON_CHAIN = "on_chain"
    WHALE_TRANSACTIONS = "whale_transactions"
    EXCHANGE_FLOWS = "exchange_flows"
    SOCIAL_SENTIMENT = "social_sentiment"
    NEWS = "news"  # News articles and media coverage
    FEAR_GREED_INDEX = "fear_greed_index"
    DERIVATIVES = "derivatives"
    FUNDING_RATES = "funding_rates"
    OPEN_INTEREST = "open_interest"
    LIQUIDATIONS = "liquidations"
    TECHNICAL_INDICATORS = "technical_indicators"
    ORDER_BOOK = "order_book"
    TRADES = "trades"
    NETWORK_METRICS = "network_metrics"  # Add missing network metrics
    INFLUENCER_ACTIVITY = "influencer_activity"  # Twitter influencer monitoring


class Capability(Enum):
    """Specific capabilities a data source can provide"""
    REAL_TIME = "real_time"
    HISTORICAL = "historical"
    MULTI_CURRENCY = "multi_currency"
    MULTI_EXCHANGE = "multi_exchange"
    WHALE_TRACKING = "whale_tracking"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    ALERTS = "alerts"
    WEBSOCKET_STREAMING = "websocket_streaming"
    BATCH_QUERIES = "batch_queries"
    AGGREGATION = "aggregation"
    TIME_SERIES = "time_series"
    STATISTICAL_ANALYSIS = "statistical_analysis"
    TECHNICAL_ANALYSIS = "technical_analysis"  # Technical indicators (RSI, MACD, etc.)
    MARKET_DEPTH = "market_depth"
    RATE_LIMITED = "rate_limited"
    REQUIRES_AUTH = "requires_auth"
    INFLUENCER_TRACKING = "influencer_tracking"  # Track specific influencers
    EXCHANGE_MONITORING = "exchange_monitoring"  # Monitor exchange flows
    ADVANCED_ANALYTICS = "advanced_analytics"  # Complex analysis capabilities
    DERIVATIVES_TRACKING = "derivatives_tracking"  # Track derivatives markets


class ResponseTime(Enum):
    """Expected response time for data"""
    REAL_TIME = "real_time"  # < 1 second
    FAST = "fast"  # 1-3 seconds
    MODERATE = "moderate"  # 3-10 seconds
    SLOW = "slow"  # 10-30 seconds
    BATCH = "batch"  # > 30 seconds


class CostTier(Enum):
    """Cost structure for API access"""
    FREE = "free"
    FREEMIUM = "freemium"  # Free with limits
    PAID = "paid"
    CREDITS = "credits"  # Pay per call
    SUBSCRIPTION = "subscription"


@dataclass
class RateLimits:
    """Rate limiting information"""
    requests_per_minute: Optional[int] = None
    requests_per_hour: Optional[int] = None
    requests_per_day: Optional[int] = None
    burst_limit: Optional[int] = None
    concurrent_requests: Optional[int] = None


@dataclass
class DataSourceMetadata:
    """
    Complete metadata describing a data source's capabilities.
    
    This metadata allows agents to:
    1. Discover available data sources
    2. Select appropriate sources for specific tasks
    3. Understand limitations and costs
    4. Generate OpenAPI schemas automatically
    """
    
    # Basic identification
    name: str
    provider: str
    description: str
    version: str = "1.0.0"
    
    # Capabilities
    data_types: List[DataType] = field(default_factory=list)
    capabilities: List[Capability] = field(default_factory=list)
    
    # Performance characteristics
    response_time: ResponseTime = ResponseTime.MODERATE
    reliability_score: float = 0.95  # 0-1 score
    
    # Cost and limits
    cost_tier: CostTier = CostTier.FREE
    rate_limits: Optional[RateLimits] = None
    
    # Use case recommendations
    best_for: List[str] = field(default_factory=list)
    not_recommended_for: List[str] = field(default_factory=list)
    
    # API information
    base_url: Optional[str] = None
    requires_api_key: bool = False
    api_key_env_var: Optional[str] = None
    
    # Documentation
    documentation_url: Optional[str] = None
    example_queries: List[Dict] = field(default_factory=list)
    
    # Quality metrics
    data_freshness: str = "unknown"  # e.g., "real-time", "5min delay"
    historical_data_available: bool = False
    historical_data_range: Optional[str] = None  # e.g., "2015-present"
    
    def supports_data_type(self, data_type: DataType) -> bool:
        """Check if this source supports a specific data type"""
        return data_type in self.data_types
    
    def has_capability(self, capability: Capability) -> bool:
        """Check if this source has a specific capability"""
        return capability in self.capabilities
    
    def quality_score(self, requirements: Dict) -> float:
        """
        Calculate quality score (0-1) based on requirements.
        
        Args:
            requirements: Dict with keys like 'data_type', 'speed', 'cost', etc.
            
        Returns:
            Score from 0 (unsuitable) to 1 (perfect match)
        """
        score = 0.0
        weight_sum = 0.0
        
        # Check data type match (weight: 0.4)
        if 'data_type' in requirements:
            weight = 0.4
            weight_sum += weight
            required_type = requirements['data_type']
            if isinstance(required_type, str):
                required_type = DataType(required_type)
            if self.supports_data_type(required_type):
                score += weight
        
        # Check speed requirements (weight: 0.2)
        if 'speed' in requirements:
            weight = 0.2
            weight_sum += weight
            speed_priority = requirements['speed']  # 'critical', 'important', 'not_important'
            
            speed_scores = {
                ResponseTime.REAL_TIME: 1.0,
                ResponseTime.FAST: 0.8,
                ResponseTime.MODERATE: 0.5,
                ResponseTime.SLOW: 0.3,
                ResponseTime.BATCH: 0.1
            }
            
            if speed_priority == 'critical':
                score += weight * speed_scores.get(self.response_time, 0.5)
            elif speed_priority == 'important':
                score += weight * (0.5 + 0.5 * speed_scores.get(self.response_time, 0.5))
            else:
                score += weight * 0.8  # Speed not critical
        
        # Check cost preferences (weight: 0.2)
        if 'cost' in requirements:
            weight = 0.2
            weight_sum += weight
            cost_preference = requirements['cost']  # 'free_only', 'low', 'any'
            
            cost_scores = {
                CostTier.FREE: 1.0,
                CostTier.FREEMIUM: 0.8,
                CostTier.PAID: 0.5,
                CostTier.CREDITS: 0.6,
                CostTier.SUBSCRIPTION: 0.4
            }
            
            if cost_preference == 'free_only':
                score += weight if self.cost_tier == CostTier.FREE else 0
            elif cost_preference == 'low':
                score += weight * cost_scores.get(self.cost_tier, 0.5)
            else:
                score += weight * 0.8
        
        # Check required capabilities (weight: 0.2)
        if 'capabilities' in requirements:
            weight = 0.2
            weight_sum += weight
            required_caps = requirements['capabilities']
            if not isinstance(required_caps, list):
                required_caps = [required_caps]
            
            matching_caps = sum(1 for cap in required_caps if self.has_capability(cap))
            if required_caps:
                score += weight * (matching_caps / len(required_caps))
            else:
                score += weight
        
        # Normalize score
        if weight_sum > 0:
            return score / weight_sum * self.reliability_score
        return self.reliability_score * 0.5
    
    def to_dict(self) -> Dict:
        """Convert metadata to dictionary for serialization"""
        return {
            'name': self.name,
            'provider': self.provider,
            'description': self.description,
            'version': self.version,
            'data_types': [dt.value for dt in self.data_types],
            'capabilities': [cap.value for cap in self.capabilities],
            'response_time': self.response_time.value,
            'reliability_score': self.reliability_score,
            'cost_tier': self.cost_tier.value,
            'rate_limits': {
                'requests_per_minute': self.rate_limits.requests_per_minute,
                'requests_per_hour': self.rate_limits.requests_per_hour,
                'requests_per_day': self.rate_limits.requests_per_day,
            } if self.rate_limits else None,
            'best_for': self.best_for,
            'not_recommended_for': self.not_recommended_for,
            'requires_api_key': self.requires_api_key,
            'data_freshness': self.data_freshness,
            'historical_data_available': self.historical_data_available,
        }
    
    def to_openapi_operation(self) -> Dict:
        """Generate OpenAPI operation spec for this data source"""
        return {
            'summary': f'Query {self.name} - {self.description}',
            'description': f"""
Fetch data from {self.provider}.

Supported data types: {', '.join(dt.value for dt in self.data_types)}
Capabilities: {', '.join(cap.value for cap in self.capabilities)}
Response time: {self.response_time.value}
Cost: {self.cost_tier.value}

Best for: {', '.join(self.best_for)}
            """.strip(),
            'operationId': f'query_{self.name.lower().replace(" ", "_")}',
            'requestBody': {
                'required': True,
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'required': ['data_type'],
                            'properties': {
                                'data_type': {
                                    'type': 'string',
                                    'enum': [dt.value for dt in self.data_types],
                                    'description': 'Type of data to fetch'
                                },
                                'symbol': {
                                    'type': 'string',
                                    'description': 'Asset symbol (e.g., BTC, ETH)',
                                    'default': 'BTC'
                                },
                                'timeframe': {
                                    'type': 'string',
                                    'description': 'Time period for data',
                                    'examples': ['1h', '24h', '7d', '30d']
                                },
                                'parameters': {
                                    'type': 'object',
                                    'description': 'Additional source-specific parameters'
                                }
                            }
                        }
                    }
                }
            },
            'responses': {
                '200': {
                    'description': 'Successful response',
                    'content': {
                        'application/json': {
                            'schema': {
                                'type': 'object',
                                'properties': {
                                    'success': {'type': 'boolean'},
                                    'source': {'type': 'string'},
                                    'data': {'type': 'object'},
                                    'metadata': {'type': 'object'}
                                }
                            }
                        }
                    }
                },
                '400': {'description': 'Invalid request'},
                '429': {'description': 'Rate limit exceeded'},
                '500': {'description': 'Server error'}
            }
        }
