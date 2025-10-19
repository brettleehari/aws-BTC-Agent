"""
OpenAPI Schema Generator for Bedrock Agent Integration.

Automatically generates OpenAPI 3.0 schemas from registered data interfaces,
enabling seamless integration with Amazon Bedrock Agents.
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from .registry import CapabilityRegistry, get_registry
from .metadata import DataType, Capability, ResponseTime, CostTier


class OpenAPIGenerator:
    """
    Generate OpenAPI 3.0 schemas for Bedrock Agent action groups.
    
    Features:
    - Automatic schema generation from interface metadata
    - Bedrock Agent-compatible format
    - Dynamic updates when sources change
    - Multiple action groups for different data categories
    """
    
    def __init__(self, registry: Optional[CapabilityRegistry] = None):
        """
        Initialize generator.
        
        Args:
            registry: Capability registry (uses global if not provided)
        """
        self.registry = registry or get_registry()
    
    def generate_schema(
        self,
        title: str = "Bitcoin Market Hunter Data Interfaces",
        version: str = "1.0.0",
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate complete OpenAPI schema for all registered sources.
        
        Args:
            title: API title
            version: API version
            description: API description
            
        Returns:
            OpenAPI 3.0 schema dict
        """
        schema = {
            "openapi": "3.0.0",
            "info": {
                "title": title,
                "version": version,
                "description": description or "Unified data interface for cryptocurrency market intelligence",
                "contact": {
                    "name": "Market Hunter Agent",
                },
            },
            "servers": [
                {
                    "url": "https://api.example.com",
                    "description": "Production API server"
                }
            ],
            "paths": {},
            "components": {
                "schemas": self._generate_schemas(),
                "securitySchemes": {
                    "ApiKeyAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key"
                    }
                }
            }
        }
        
        # Add paths for each data type
        for data_type in DataType:
            path = self._generate_path_for_data_type(data_type)
            if path:
                schema["paths"][f"/data/{data_type.value}"] = path
        
        return schema
    
    def generate_action_group_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Generate separate schemas for each Bedrock Agent action group.
        
        Returns:
            Dict mapping action group names to their schemas
        """
        action_groups = {
            "PriceData": [DataType.PRICE, DataType.MARKET_CAP, DataType.VOLUME],
            "OnChainData": [DataType.ON_CHAIN, DataType.WHALE_TRANSACTIONS, DataType.EXCHANGE_FLOWS],
            "SentimentData": [DataType.SOCIAL_SENTIMENT, DataType.NEWS],
            "NetworkData": [DataType.NETWORK_METRICS],
        }
        
        schemas = {}
        for group_name, data_types in action_groups.items():
            schemas[group_name] = self._generate_action_group_schema(
                group_name,
                data_types
            )
        
        return schemas
    
    def _generate_action_group_schema(
        self,
        name: str,
        data_types: List[DataType]
    ) -> Dict[str, Any]:
        """Generate schema for a specific action group"""
        schema = {
            "openapi": "3.0.0",
            "info": {
                "title": f"Market Hunter - {name}",
                "version": "1.0.0",
                "description": f"Action group for {name.lower()} operations"
            },
            "paths": {},
            "components": {
                "schemas": self._generate_schemas()
            }
        }
        
        for data_type in data_types:
            path = self._generate_path_for_data_type(data_type)
            if path:
                schema["paths"][f"/{data_type.value}"] = path
        
        return schema
    
    def _generate_path_for_data_type(self, data_type: DataType) -> Optional[Dict[str, Any]]:
        """Generate OpenAPI path for a data type"""
        sources = self.registry.find_sources_for_data_type(data_type)
        
        if not sources:
            return None
        
        # Get example from first source
        example_source = sources[0]
        metadata = self.registry.get_metadata(example_source)
        
        examples = metadata.example_queries if metadata else []
        example_request = examples[0]['request'] if examples else {}
        
        return {
            "get": {
                "summary": f"Fetch {data_type.value} data",
                "description": f"Retrieve {data_type.value} from available sources. "
                             f"Available sources: {', '.join(sources)}",
                "operationId": f"fetch_{data_type.value}",
                "parameters": [
                    {
                        "name": "symbol",
                        "in": "query",
                        "description": "Cryptocurrency symbol (e.g., BTC, ETH)",
                        "required": True,
                        "schema": {"type": "string", "example": "BTC"}
                    },
                    {
                        "name": "timeframe",
                        "in": "query",
                        "description": "Time range for historical data (e.g., 1d, 7d, 30d)",
                        "required": False,
                        "schema": {"type": "string", "example": "7d"}
                    },
                    {
                        "name": "source",
                        "in": "query",
                        "description": "Preferred data source",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": sources
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DataResponse"}
                            }
                        }
                    },
                    "400": {
                        "description": "Bad request",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "404": {
                        "description": "Data not available",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "429": {
                        "description": "Rate limit exceeded",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                },
                "tags": [data_type.value]
            }
        }
    
    def _generate_schemas(self) -> Dict[str, Any]:
        """Generate component schemas"""
        return {
            "DataResponse": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "description": "Whether the request was successful"
                    },
                    "source": {
                        "type": "string",
                        "description": "Data source that fulfilled the request"
                    },
                    "data": {
                        "type": "object",
                        "description": "The requested data"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata about the response"
                    },
                    "request_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "When the request was made"
                    },
                    "response_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "When the response was generated"
                    },
                    "data_timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Timestamp of the data itself"
                    },
                    "latency_ms": {
                        "type": "number",
                        "description": "Response latency in milliseconds"
                    },
                    "cached": {
                        "type": "boolean",
                        "description": "Whether this response was served from cache"
                    },
                    "error": {
                        "type": "string",
                        "description": "Error message if request failed"
                    },
                    "error_code": {
                        "type": "string",
                        "description": "Error code if request failed"
                    }
                },
                "required": ["success", "source", "data"]
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "description": "Error message"
                    },
                    "error_code": {
                        "type": "string",
                        "description": "Error code"
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "description": "When the error occurred"
                    }
                },
                "required": ["error", "error_code"]
            },
            "SourceCapability": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Source name"
                    },
                    "provider": {
                        "type": "string",
                        "description": "Provider name"
                    },
                    "data_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Supported data types"
                    },
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Available capabilities"
                    },
                    "response_time": {
                        "type": "string",
                        "enum": ["real_time", "fast", "moderate", "slow", "batch"],
                        "description": "Expected response time"
                    },
                    "cost_tier": {
                        "type": "string",
                        "enum": ["free", "freemium", "paid", "credits", "subscription"],
                        "description": "Cost tier"
                    },
                    "requires_api_key": {
                        "type": "boolean",
                        "description": "Whether API key is required"
                    }
                }
            }
        }
    
    def save_schema(self, filepath: str, pretty: bool = True):
        """
        Save generated schema to file.
        
        Args:
            filepath: Path to save schema
            pretty: Whether to format JSON with indentation
        """
        schema = self.generate_schema()
        
        with open(filepath, 'w') as f:
            if pretty:
                json.dump(schema, f, indent=2)
            else:
                json.dump(schema, f)
    
    def save_action_group_schemas(self, directory: str, pretty: bool = True):
        """
        Save action group schemas to directory.
        
        Args:
            directory: Directory to save schemas
            pretty: Whether to format JSON with indentation
        """
        import os
        os.makedirs(directory, exist_ok=True)
        
        schemas = self.generate_action_group_schemas()
        
        for name, schema in schemas.items():
            filepath = os.path.join(directory, f"{name.lower()}_schema.json")
            with open(filepath, 'w') as f:
                if pretty:
                    json.dump(schema, f, indent=2)
                else:
                    json.dump(schema, f)
    
    def generate_capability_summary(self) -> Dict[str, Any]:
        """
        Generate human-readable capability summary.
        
        Returns:
            Summary of all capabilities
        """
        return self.registry.generate_capability_summary()


def generate_bedrock_action_groups() -> Dict[str, Dict[str, Any]]:
    """
    Convenience function to generate Bedrock Agent action group schemas.
    
    Returns:
        Dict mapping action group names to their OpenAPI schemas
    """
    generator = OpenAPIGenerator()
    return generator.generate_action_group_schemas()
