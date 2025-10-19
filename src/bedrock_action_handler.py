"""
AWS Lambda Handler for Bedrock Agent Integration

This Lambda function serves as the action group handler for Amazon Bedrock Agent.
It integrates the Market Hunter Agent with the Data Interfaces module, providing:

1. Capability discovery endpoints
2. Data query endpoints with rate limiting
3. Agent cycle management
4. Status and metrics endpoints
"""

import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from src.market_hunter_agent_integrated import IntegratedMarketHunterAgent, MarketContext
from src.data_interfaces import (
    get_manager,
    get_registry,
    DataType,
    Capability,
    RequestPriority
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize agent (singleton)
AGENT: Optional[IntegratedMarketHunterAgent] = None


def get_agent() -> IntegratedMarketHunterAgent:
    """Get or create the singleton agent instance"""
    global AGENT
    if AGENT is None:
        AGENT = IntegratedMarketHunterAgent(
            agent_name=os.environ.get("AGENT_NAME", "market-hunter"),
            learning_rate=float(os.environ.get("LEARNING_RATE", "0.1")),
            exploration_rate=float(os.environ.get("EXPLORATION_RATE", "0.2")),
            technical_weight=float(os.environ.get("TECHNICAL_WEIGHT", "0.7")),
            enable_cache=os.environ.get("ENABLE_CACHE", "true").lower() == "true",
            cache_ttl=int(os.environ.get("CACHE_TTL", "60"))
        )
    return AGENT


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for Bedrock Agent action group.
    
    Args:
        event: Lambda event from Bedrock Agent
        context: Lambda context
        
    Returns:
        Response in Bedrock Agent format
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract action group, API path, and parameters from event
        action_group = event.get("actionGroup", "")
        api_path = event.get("apiPath", "")
        parameters = event.get("parameters", [])
        request_body = event.get("requestBody", {})
        
        # Convert parameters list to dict
        params_dict = {p["name"]: p["value"] for p in parameters}
        
        # Route to appropriate handler
        if api_path == "/capabilities/discover":
            response = handle_discover_capabilities(params_dict)
        elif api_path == "/capabilities/sources":
            response = handle_list_sources(params_dict)
        elif api_path == "/data/query":
            response = handle_query_data(params_dict, request_body)
        elif api_path == "/agent/run-cycle":
            response = handle_run_cycle(params_dict, request_body)
        elif api_path == "/agent/status":
            response = handle_get_status(params_dict)
        elif api_path == "/metrics/sources":
            response = handle_get_metrics(params_dict)
        else:
            response = {
                "error": f"Unknown API path: {api_path}",
                "statusCode": 404
            }
        
        # Format response for Bedrock Agent
        return format_bedrock_response(event, response)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return format_bedrock_response(event, {
            "error": str(e),
            "statusCode": 500
        })


def handle_discover_capabilities(params: Dict[str, str]) -> Dict[str, Any]:
    """
    Discover available capabilities.
    
    Query parameters:
        - data_type (optional): Filter by data type
        - capability (optional): Filter by capability
    """
    registry = get_registry()
    
    data_type_filter = params.get("data_type")
    capability_filter = params.get("capability")
    
    # Get all capabilities
    all_capabilities = registry.get_all_capabilities()
    all_data_types = registry.get_all_data_types()
    
    # Filter if requested
    if data_type_filter:
        data_type_enum = DataType(data_type_filter)
        sources = registry.find_sources(data_types=[data_type_enum])
    elif capability_filter:
        capability_enum = Capability(capability_filter)
        sources = registry.find_sources(required_capabilities=[capability_enum])
    else:
        sources = [registry.get_source(sid) for sid in registry.list_sources()]
    
    return {
        "statusCode": 200,
        "capabilities": [c.value for c in all_capabilities],
        "data_types": [dt.value for dt in all_data_types],
        "sources": [
            {
                "source_id": s.source_id,
                "name": s.name,
                "data_types": [dt.value for dt in s.data_types],
                "capabilities": [c.value for c in s.capabilities],
                "quality_score": s.quality_score,
                "cost_tier": s.cost_tier.value,
                "response_time": s.response_time.value
            }
            for s in sources if s
        ]
    }


def handle_list_sources(params: Dict[str, str]) -> Dict[str, Any]:
    """List all available data sources with their metadata"""
    registry = get_registry()
    
    sources = registry.list_sources()
    detailed_sources = []
    
    for source_id in sources:
        metadata = registry.get_source(source_id)
        if metadata:
            detailed_sources.append({
                "source_id": metadata.source_id,
                "name": metadata.name,
                "description": metadata.description,
                "data_types": [dt.value for dt in metadata.data_types],
                "capabilities": [c.value for c in metadata.capabilities],
                "quality_score": metadata.quality_score,
                "cost_tier": metadata.cost_tier.value,
                "response_time": metadata.response_time.value,
                "rate_limits": {
                    "requests_per_second": metadata.rate_limits.requests_per_second,
                    "requests_per_minute": metadata.rate_limits.requests_per_minute,
                    "requests_per_hour": metadata.rate_limits.requests_per_hour,
                    "requests_per_day": metadata.rate_limits.requests_per_day
                } if metadata.rate_limits else None
            })
    
    return {
        "statusCode": 200,
        "total_sources": len(detailed_sources),
        "sources": detailed_sources
    }


def handle_query_data(params: Dict[str, str], body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query data with automatic source selection and rate limiting.
    
    Body parameters:
        - logical_source: Logical source name (e.g., "whaleMovements")
        - parameters: Query parameters (optional)
    """
    agent = get_agent()
    
    # Extract from body
    content = body.get("content", {})
    logical_source = content.get("logical_source")
    query_params = content.get("parameters", {})
    
    if not logical_source:
        return {
            "statusCode": 400,
            "error": "Missing required parameter: logical_source"
        }
    
    # Query asynchronously
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        agent.query_source_with_rate_limit_check(logical_source, query_params)
    )
    
    if result is None:
        return {
            "statusCode": 503,
            "error": f"Failed to query source: {logical_source} (rate limited or unavailable)"
        }
    
    return {
        "statusCode": 200,
        "source": result["source"],
        "technical_source": result["technical_source"],
        "data": result["data"],
        "quality": result["quality"],
        "from_cache": result["from_cache"],
        "timestamp": result["timestamp"].isoformat()
    }


def handle_run_cycle(params: Dict[str, str], body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a complete agent cycle.
    
    Body parameters:
        - current_price: Current BTC price
        - price_24h_ago: BTC price 24h ago
        - volume_24h: 24h trading volume
        - avg_volume: Average trading volume
    """
    agent = get_agent()
    
    # Extract market data from body
    content = body.get("content", {})
    market_data = {
        "current_price": float(content.get("current_price", 0)),
        "price_24h_ago": float(content.get("price_24h_ago", 0)),
        "volume_24h": float(content.get("volume_24h", 0)),
        "avg_volume": float(content.get("avg_volume", 1))
    }
    
    # Validate required fields
    if market_data["current_price"] == 0 or market_data["price_24h_ago"] == 0:
        return {
            "statusCode": 400,
            "error": "Missing required market data (current_price, price_24h_ago)"
        }
    
    # Run cycle asynchronously
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(agent.run_cycle(market_data))
    
    return {
        "statusCode": 200,
        **results
    }


def handle_get_status(params: Dict[str, str]) -> Dict[str, Any]:
    """Get agent and data interfaces status"""
    agent = get_agent()
    
    status = agent.get_source_status()
    
    return {
        "statusCode": 200,
        "agent_name": agent.agent_name,
        "current_cycle": agent.current_cycle,
        "learning_rate": agent.learning_rate,
        "exploration_rate": agent.exploration_rate,
        "technical_weight": agent.technical_weight,
        **status
    }


def handle_get_metrics(params: Dict[str, str]) -> Dict[str, Any]:
    """Get detailed source metrics"""
    agent = get_agent()
    
    # Get agent metrics
    source_metrics = {}
    for source, metrics in agent.source_metrics.items():
        success_rate = (
            metrics["successful_calls"] / metrics["total_calls"]
            if metrics["total_calls"] > 0 else 0
        )
        
        source_metrics[source] = {
            **metrics,
            "calculated_success_rate": success_rate,
            "last_query": (
                agent.last_query_times[source].isoformat()
                if source in agent.last_query_times else None
            )
        }
    
    # Get manager stats
    manager = get_manager()
    manager_stats = manager.get_stats()
    
    return {
        "statusCode": 200,
        "agent_metrics": source_metrics,
        "manager_stats": manager_stats,
        "timestamp": datetime.utcnow().isoformat()
    }


def format_bedrock_response(event: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format response for Bedrock Agent.
    
    Args:
        event: Original event
        response: Handler response
        
    Returns:
        Formatted Bedrock Agent response
    """
    status_code = response.pop("statusCode", 200)
    
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "apiPath": event.get("apiPath", ""),
            "httpMethod": event.get("httpMethod", "GET"),
            "httpStatusCode": status_code,
            "responseBody": {
                "application/json": {
                    "body": json.dumps(response)
                }
            }
        }
    }


# For local testing
if __name__ == "__main__":
    # Example event
    test_event = {
        "actionGroup": "MarketDataActions",
        "apiPath": "/capabilities/discover",
        "httpMethod": "GET",
        "parameters": [],
        "requestBody": {}
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
