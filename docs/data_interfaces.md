# Data Interfaces Module

## Overview

The Data Interfaces module is a standalone component that provides unified access to multiple cryptocurrency data sources with intelligent routing, capability discovery, and seamless integration with Amazon Bedrock Agents.

## Architecture

### Key Components

1. **DataInterface** - Abstract base class for all data sources
2. **CapabilityRegistry** - Central registry for source discovery
3. **DataInterfaceManager** - Orchestrates requests across multiple sources
4. **OpenAPIGenerator** - Generates schemas for Bedrock Agent integration

### Capability Advertisement

The module uses a hybrid approach for capability advertisement:

- **OpenAPI Schemas** - For Bedrock Agent native discovery
- **Self-Describing Interfaces** - Each source has metadata property
- **Central Registry** - Enables intelligent routing and discovery

## Data Sources

### Currently Implemented

| Source | Data Types | Capabilities | Cost |
|--------|-----------|--------------|------|
| **CoinGecko** | Price, Market Cap, Volume | Real-time, Historical, Multi-currency | Free/Freemium |
| **Glassnode** | On-chain, Whale Transactions, Exchange Flows | Whale Tracking, Advanced Analytics | Subscription |
| **SentimentAnalyzer** | Social Sentiment, News | Sentiment Analysis, Fear & Greed Index | Free |

### Coming Soon

- CryptoQuant (Exchange data, derivatives)
- Messari (Fundamental metrics)
- LunarCrush (Social analytics)

## Usage

### Basic Usage

```python
from src.data_interfaces import (
    DataRequest,
    DataType,
    get_manager,
)

# Create a request
request = DataRequest(
    data_type=DataType.PRICE,
    symbol="BTC",
    parameters={"vs_currency": "usd"}
)

# Fetch data (manager automatically selects best source)
manager = get_manager()
response = await manager.fetch(request)

if response.success:
    print(f"BTC Price: ${response.data['price']}")
    print(f"Source: {response.source}")
else:
    print(f"Error: {response.error}")
```

### Source Discovery

```python
from src.data_interfaces import get_registry, DataType, Capability

registry = get_registry()

# Find sources for specific data type
price_sources = registry.find_sources_for_data_type(DataType.PRICE)
print(f"Price data sources: {price_sources}")

# Find sources with specific capability
realtime_sources = registry.find_sources_with_capability(Capability.REAL_TIME)
print(f"Real-time sources: {realtime_sources}")

# Get recommended source for request
request = DataRequest(data_type=DataType.ON_CHAIN, symbol="BTC")
recommendation = registry.recommend_source(request)
print(f"Best source: {recommendation}")
```

### Advanced Features

#### Intelligent Routing with Quality Scores

```python
# Request with preferences
request = DataRequest(
    data_type=DataType.PRICE,
    symbol="BTC",
    priority=RequestPriority.HIGH  # Prioritize speed
)

# Get ranked sources
rankings = registry.get_source_rankings(request)
for rank in rankings:
    print(f"{rank['name']}: {rank['score']:.2f}")
```

#### Fallback Mechanism

```python
# Manager automatically falls back to alternative sources
manager = DataInterfaceManager(enable_fallback=True)
response = await manager.fetch(request)

# If primary source fails, manager tries next best source
```

#### Parallel Fetching

```python
# Fetch from multiple sources in parallel (fastest wins)
manager = DataInterfaceManager(enable_parallel=True)
response = await manager.fetch(request)

# Returns first successful response
```

#### Caching

```python
# Enable caching with TTL
manager = DataInterfaceManager(cache_ttl=60)

# First request hits API
response1 = await manager.fetch(request)
print(f"Cached: {response1.cached}")  # False

# Second request within TTL uses cache
response2 = await manager.fetch(request)
print(f"Cached: {response2.cached}")  # True
print(f"Cache age: {response2.cache_age}s")
```

#### Circuit Breaker

```python
# Automatic circuit breaking on repeated failures
# After 5 consecutive failures, source is temporarily disabled (60s)

status = manager.get_status()
for source, info in status['circuit_breakers'].items():
    print(f"{source}: {'OPEN' if info['is_open'] else 'CLOSED'}")
    print(f"  Failures: {info['consecutive_failures']}")
```

## Integration with Bedrock Agents

### Generate OpenAPI Schemas

```python
from src.data_interfaces import OpenAPIGenerator

generator = OpenAPIGenerator()

# Generate complete schema
schema = generator.generate_schema()

# Generate separate action group schemas
action_groups = generator.generate_action_group_schemas()

for name, schema in action_groups.items():
    print(f"Action Group: {name}")
    print(f"Endpoints: {list(schema['paths'].keys())}")
```

### Action Groups

The module automatically organizes endpoints into Bedrock Agent action groups:

1. **PriceData** - Price, market cap, volume
2. **OnChainData** - On-chain metrics, whale transactions, exchange flows
3. **SentimentData** - Social sentiment, news analysis
4. **NetworkData** - Network health and metrics

### Lambda Handler (Coming Soon)

```python
# Lambda handler for Bedrock Agent invocations
def lambda_handler(event, context):
    """
    Handle Bedrock Agent action group invocations
    """
    from src.data_interfaces import get_manager, DataRequest, DataType
    
    # Parse Bedrock Agent event
    action = event['actionGroup']
    function = event['function']
    parameters = event['parameters']
    
    # Create request
    request = DataRequest(
        data_type=DataType[function.upper()],
        symbol=parameters.get('symbol', 'BTC'),
        parameters=parameters
    )
    
    # Fetch data
    manager = get_manager()
    response = await manager.fetch(request)
    
    # Return Bedrock Agent response
    return {
        'response': {
            'actionGroup': action,
            'function': function,
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps(response.data)
                    }
                }
            }
        }
    }
```

## Testing

### Run All Tests

```bash
# Run all data interfaces tests
python -m pytest tests/test_data_interfaces/ -v

# Run with coverage
python -m pytest tests/test_data_interfaces/ --cov=src.data_interfaces --cov-report=html
```

### Test Categories

1. **test_metadata.py** - Metadata models and capability definitions
2. **test_base_interface.py** - Abstract base class and request/response models
3. **test_registry.py** - Registry and source discovery
4. **test_integration.py** - End-to-end integration tests

### Example Test Output

```
tests/test_data_interfaces/test_metadata.py::TestDataSourceMetadata::test_quality_score_calculation PASSED
tests/test_data_interfaces/test_base_interface.py::TestDataInterface::test_can_handle PASSED
tests/test_data_interfaces/test_registry.py::TestCapabilityRegistry::test_recommend_source PASSED
tests/test_data_interfaces/test_integration.py::TestEndToEndIntegration::test_price_request_finds_coingecko PASSED

============================== 50+ tests passed in 2.34s ==============================
```

## Configuration

### Environment Variables

```bash
# API Keys
export COINGECKO_API_KEY="your_coingecko_key"  # Optional, increases rate limits
export GLASSNODE_API_KEY="your_glassnode_key"  # Required for Glassnode
export CRYPTOQUANT_API_KEY="your_cryptoquant_key"  # Coming soon

# Manager Configuration
export DATA_CACHE_TTL=60  # Cache TTL in seconds
export ENABLE_FALLBACK=true  # Enable automatic fallback
export ENABLE_PARALLEL=false  # Enable parallel fetching
```

### Programmatic Configuration

```python
from src.data_interfaces import DataInterfaceManager

manager = DataInterfaceManager(
    enable_fallback=True,
    enable_parallel=False,
    cache_ttl=60,
)
```

## Quality Scoring Algorithm

The registry uses a sophisticated quality scoring algorithm to rank sources:

```python
score = (
    base_score * 0.3 +           # Reliability
    capability_match * 0.3 +      # Feature match
    speed_score * 0.2 +           # Response time
    cost_score * 0.2              # Cost efficiency
)
```

Factors:
- **Reliability** - Historical uptime and error rates
- **Capability Match** - Supports required features
- **Speed** - Expected response time
- **Cost** - Free sources score higher

## Best Practices

### 1. Use Manager for Production

```python
# Don't instantiate sources directly
# BAD
source = CoinGeckoInterface()
response = await source.fetch(request)

# GOOD - Let manager handle routing
manager = get_manager()
response = await manager.fetch(request)
```

### 2. Enable Fallback for Reliability

```python
manager = DataInterfaceManager(enable_fallback=True)
# Automatically tries alternative sources if primary fails
```

### 3. Cache for Performance

```python
manager = DataInterfaceManager(cache_ttl=60)
# Reduces API calls and improves response time
```

### 4. Handle Failures Gracefully

```python
response = await manager.fetch(request)

if not response.success:
    logger.error(f"Data fetch failed: {response.error}")
    # Fall back to cached data or default values
    fallback_data = get_cached_or_default()
```

### 5. Monitor Circuit Breakers

```python
status = manager.get_status()

if any(info['is_open'] for info in status['circuit_breakers'].values()):
    logger.warning("Some sources have circuit breakers open")
    # Alert ops team or switch to manual mode
```

## Performance

### Benchmarks

- **Single source fetch**: 100-500ms (depends on source)
- **Parallel fetch (3 sources)**: 150-600ms (returns first success)
- **Cached fetch**: < 1ms
- **Registry lookup**: < 1ms

### Optimization Tips

1. Enable caching for frequently accessed data
2. Use parallel fetching for critical requests
3. Prefer faster sources (CoinGecko) for real-time needs
4. Use slower sources (Glassnode) for analytical data

## Troubleshooting

### Issue: No sources available for data type

```python
# Check registered sources
registry = get_registry()
sources = registry.list_sources()
print(f"Registered: {sources}")

# Check data type support
price_sources = registry.find_sources_for_data_type(DataType.PRICE)
print(f"Price sources: {price_sources}")
```

### Issue: Rate limit exceeded

```python
# Check rate limit status
source = CoinGeckoInterface()
status = source.get_rate_limit_status()
print(f"Calls made: {status['calls_made']}")

# Implement backoff or switch sources
if response.error_code == 'RATE_LIMIT':
    # Use alternative source
    response = await manager.fetch(request, preferred_source='Glassnode')
```

### Issue: Circuit breaker open

```python
# Reset circuit breakers if needed
manager.reset_circuit_breakers()

# Or wait for automatic reset (60 seconds)
```

## Contributing

### Adding New Data Sources

1. Implement `DataInterface` abstract class
2. Define comprehensive `metadata` property
3. Implement `fetch()` method
4. Implement `health_check()` method
5. Register in `__init__.py`
6. Add tests

Example:

```python
class MyNewSource(DataInterface):
    @property
    def metadata(self) -> DataSourceMetadata:
        return DataSourceMetadata(
            name="MySource",
            provider="MyProvider",
            data_types=[DataType.PRICE],
            capabilities=[Capability.REAL_TIME],
            # ... complete metadata
        )
    
    async def fetch(self, request: DataRequest) -> DataResponse:
        # Implementation
        pass
    
    async def health_check(self) -> bool:
        # Implementation
        pass
```

## License

Part of the AWS BTC Agent project.

## Support

For issues or questions, please open a GitHub issue or contact the development team.
