"""
Data Interfaces Module

Standalone module for fetching data from multiple external sources
with capability advertisement for AWS Bedrock Agents.

This module provides:
- Self-describing data source interfaces
- Capability registry for intelligent source selection
- OpenAPI schema generation for Bedrock Agent integration
- Unified manager for orchestrating data sources
"""

from .metadata import (
    DataSourceMetadata,
    DataType,
    Capability,
    ResponseTime,
    CostTier,
    RateLimits,
)

from .base_interface import (
    DataInterface,
    DataRequest,
    DataResponse,
    RequestPriority,
    DataInterfaceError,
    RateLimitError,
    AuthenticationError,
    DataNotAvailableError,
    TimeoutError,
)

from .registry import CapabilityRegistry, get_registry, reset_registry

from .manager import DataInterfaceManager, get_manager, reset_manager

from .openapi_generator import OpenAPIGenerator, generate_bedrock_action_groups

# Available data source implementations
from .coingecko_interface import CoinGeckoInterface
from .glassnode_interface import GlassnodeInterface
from .sentiment_interface import SentimentInterface


# Auto-register all concrete implementations
def _register_default_sources():
    """Register all default data sources"""
    registry = get_registry()
    registry.register(CoinGeckoInterface)
    registry.register(GlassnodeInterface)
    registry.register(SentimentInterface)


# Register sources on module import
_register_default_sources()


__all__ = [
    # Metadata
    "DataSourceMetadata",
    "DataType",
    "Capability",
    "ResponseTime",
    "CostTier",
    "RateLimits",
    # Core interfaces
    "DataInterface",
    "DataRequest",
    "DataResponse",
    "RequestPriority",
    "DataInterfaceError",
    "RateLimitError",
    "AuthenticationError",
    "DataNotAvailableError",
    "TimeoutError",
    # Registry
    "CapabilityRegistry",
    "get_registry",
    "reset_registry",
    # Manager
    "DataInterfaceManager",
    "get_manager",
    "reset_manager",
    # OpenAPI Generator
    "OpenAPIGenerator",
    "generate_bedrock_action_groups",
    # Implementations
    "CoinGeckoInterface",
    "GlassnodeInterface",
    "SentimentInterface",
]

__version__ = "1.0.0"
