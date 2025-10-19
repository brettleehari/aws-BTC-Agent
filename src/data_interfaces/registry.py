"""
Capability Registry for data source discovery and selection.

Provides a central registry where agents can:
1. Discover available data sources
2. Find sources that support specific data types
3. Get intelligent recommendations based on requirements
"""

from typing import List, Dict, Optional, Type, Set
import logging

from .metadata import DataSourceMetadata, DataType, Capability
from .base_interface import DataInterface, DataRequest

logger = logging.getLogger(__name__)


class CapabilityRegistry:
    """
    Central registry for data source capabilities.
    
    Agents use this registry to discover and select appropriate
    data sources for their needs.
    """
    
    def __init__(self):
        self._sources: Dict[str, Type[DataInterface]] = {}
        self._metadata_cache: Dict[str, DataSourceMetadata] = {}
    
    def register(self, source_class: Type[DataInterface]) -> None:
        """
        Register a data source in the registry.
        
        Args:
            source_class: DataInterface subclass to register
        """
        # Create temporary instance to get metadata
        try:
            instance = source_class()
            metadata = instance.metadata
            
            self._sources[metadata.name] = source_class
            self._metadata_cache[metadata.name] = metadata
            
            logger.info(f"Registered data source: {metadata.name} ({metadata.provider})")
        except Exception as e:
            logger.error(f"Failed to register {source_class.__name__}: {e}")
    
    def unregister(self, source_name: str) -> None:
        """
        Remove a data source from the registry.
        
        Args:
            source_name: Name of the source to remove
        """
        if source_name in self._sources:
            del self._sources[source_name]
            del self._metadata_cache[source_name]
            logger.info(f"Unregistered data source: {source_name}")
    
    def list_sources(self) -> List[str]:
        """
        List all registered data sources.
        
        Returns:
            List of source names
        """
        return list(self._sources.keys())
    
    def get_metadata(self, source_name: str) -> Optional[DataSourceMetadata]:
        """
        Get metadata for a specific source.
        
        Args:
            source_name: Name of the source
            
        Returns:
            DataSourceMetadata or None if not found
        """
        return self._metadata_cache.get(source_name)
    
    def get_all_metadata(self) -> Dict[str, DataSourceMetadata]:
        """
        Get metadata for all registered sources.
        
        Returns:
            Dictionary mapping source names to metadata
        """
        return self._metadata_cache.copy()
    
    def get_all_capabilities(self) -> Set[Capability]:
        """
        Get all unique capabilities across all registered sources.
        
        Returns:
            Set of all capabilities
        """
        all_caps = set()
        for metadata in self._metadata_cache.values():
            all_caps.update(metadata.capabilities)
        return all_caps
    
    def get_all_data_types(self) -> Set[DataType]:
        """
        Get all unique data types across all registered sources.
        
        Returns:
            Set of all data types
        """
        all_types = set()
        for metadata in self._metadata_cache.values():
            all_types.update(metadata.data_types)
        return all_types
    
    def get_source(self, source_id: str) -> Optional[DataSourceMetadata]:
        """
        Get source metadata by ID (alias for get_metadata).
        
        Args:
            source_id: ID/name of the source
            
        Returns:
            DataSourceMetadata or None if not found
        """
        return self.get_metadata(source_id)
    
    def find_sources_for_data_type(self, data_type: DataType) -> List[str]:
        """
        Find all sources that support a specific data type.
        
        Args:
            data_type: Type of data needed
            
        Returns:
            List of source names that support this data type
        """
        matching_sources = []
        
        for name, metadata in self._metadata_cache.items():
            if metadata.supports_data_type(data_type):
                matching_sources.append(name)
        
        logger.debug(f"Found {len(matching_sources)} sources for {data_type.value}")
        return matching_sources
    
    def find_sources_with_capability(self, capability: Capability) -> List[str]:
        """
        Find all sources with a specific capability.
        
        Args:
            capability: Required capability
            
        Returns:
            List of source names with this capability
        """
        matching_sources = []
        
        for name, metadata in self._metadata_cache.items():
            if metadata.has_capability(capability):
                matching_sources.append(name)
        
        return matching_sources
    
    def find_sources(
        self,
        data_type: Optional[DataType] = None,
        data_types: Optional[List[DataType]] = None,
        capabilities: Optional[List[Capability]] = None,
        required_capabilities: Optional[List[Capability]] = None,
        free_only: bool = False,
        requires_auth: Optional[bool] = None
    ) -> List[str]:
        """
        Find sources matching multiple criteria.
        
        Args:
            data_type: Required data type (optional, singular)
            data_types: Required data types (optional, plural - sources must support ALL)
            capabilities: Required capabilities (optional)
            required_capabilities: Alias for capabilities
            free_only: Only return free sources
            requires_auth: Filter by authentication requirement
            
        Returns:
            List of matching source names
        """
        matching_sources = set(self._sources.keys())
        
        # Handle both data_type and data_types parameters
        types_to_check = []
        if data_type:
            types_to_check.append(data_type)
        if data_types:
            types_to_check.extend(data_types)
        
        # Filter by data types (source must support ALL specified types)
        for dt in types_to_check:
            type_matches = set(self.find_sources_for_data_type(dt))
            matching_sources &= type_matches
        
        # Handle both capabilities and required_capabilities parameters
        caps_to_check = capabilities or required_capabilities or []
        
        # Filter by capabilities
        if caps_to_check:
            for capability in caps_to_check:
                cap_matches = set(self.find_sources_with_capability(capability))
                matching_sources &= cap_matches
        
        # Filter by cost
        if free_only:
            from .metadata import CostTier
            free_sources = {
                name for name, metadata in self._metadata_cache.items()
                if metadata.cost_tier == CostTier.FREE
            }
            matching_sources &= free_sources
        
        # Filter by authentication
        if requires_auth is not None:
            auth_sources = {
                name for name, metadata in self._metadata_cache.items()
                if metadata.requires_api_key == requires_auth
            }
            matching_sources &= auth_sources
        
        result = list(matching_sources)
        logger.debug(f"Found {len(result)} sources matching criteria")
        return result
    
    def recommend_source(
        self,
        request: DataRequest,
        exclude: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Recommend the best data source for a request.
        
        Uses quality scoring to find the most suitable source.
        
        Args:
            request: Data request to fulfill
            exclude: Sources to exclude from consideration
            
        Returns:
            Name of recommended source, or None if no suitable source
        """
        exclude = exclude or []
        candidates = self.find_sources_for_data_type(request.data_type)
        candidates = [c for c in candidates if c not in exclude]
        
        if not candidates:
            logger.warning(f"No sources available for {request.data_type.value}")
            return None
        
        # Score each candidate
        scores = {}
        for source_name in candidates:
            try:
                source_class = self._sources[source_name]
                instance = source_class()
                score = instance.quality_score(request)
                scores[source_name] = score
            except Exception as e:
                logger.error(f"Error scoring {source_name}: {e}")
                scores[source_name] = 0.0
        
        # Return best scoring source
        best_source = max(scores, key=scores.get)
        best_score = scores[best_source]
        
        logger.info(
            f"Recommended {best_source} for {request.data_type.value} "
            f"(score: {best_score:.2f})"
        )
        
        return best_source if best_score > 0 else None
    
    def get_source_rankings(
        self,
        request: DataRequest,
        exclude: Optional[List[str]] = None
    ) -> List[tuple[str, float]]:
        """
        Get ranked list of sources for a request.
        
        Args:
            request: Data request to evaluate
            exclude: Sources to exclude
            
        Returns:
            List of (source_name, score) tuples, sorted by score descending
        """
        exclude = exclude or []
        candidates = self.find_sources_for_data_type(request.data_type)
        candidates = [c for c in candidates if c not in exclude]
        
        scores = []
        for source_name in candidates:
            try:
                source_class = self._sources[source_name]
                instance = source_class()
                score = instance.quality_score(request)
                scores.append((source_name, score))
            except Exception as e:
                logger.error(f"Error scoring {source_name}: {e}")
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores
    
    def get_source_class(self, source_name: str) -> Optional[Type[DataInterface]]:
        """
        Get the class for a registered source.
        
        Args:
            source_name: Name of the source
            
        Returns:
            DataInterface subclass or None
        """
        return self._sources.get(source_name)
    
    def create_source_instance(
        self,
        source_name: str,
        api_key: Optional[str] = None,
        config: Optional[Dict] = None
    ) -> Optional[DataInterface]:
        """
        Create an instance of a registered source.
        
        Args:
            source_name: Name of the source
            api_key: Optional API key
            config: Optional configuration
            
        Returns:
            DataInterface instance or None
        """
        source_class = self.get_source_class(source_name)
        if not source_class:
            return None
        
        try:
            return source_class(api_key=api_key, config=config)
        except Exception as e:
            logger.error(f"Failed to create {source_name} instance: {e}")
            return None
    
    def generate_capability_summary(self) -> Dict[str, any]:
        """
        Generate a summary of all available capabilities.
        
        Returns:
            Dictionary with capability information
        """
        summary = {
            'total_sources': len(self._sources),
            'sources': [],
            'data_types_supported': set(),
            'capabilities_available': set(),
        }
        
        for name, metadata in self._metadata_cache.items():
            summary['sources'].append({
                'name': name,
                'provider': metadata.provider,
                'data_types': [dt.value for dt in metadata.data_types],
                'capabilities': [cap.value for cap in metadata.capabilities],
                'cost': metadata.cost_tier.value,
                'response_time': metadata.response_time.value,
            })
            
            summary['data_types_supported'].update(metadata.data_types)
            summary['capabilities_available'].update(metadata.capabilities)
        
        summary['data_types_supported'] = [dt.value for dt in summary['data_types_supported']]
        summary['capabilities_available'] = [cap.value for cap in summary['capabilities_available']]
        
        return summary


# Global registry instance
_global_registry: Optional[CapabilityRegistry] = None


def get_registry() -> CapabilityRegistry:
    """
    Get the global capability registry.
    
    Returns:
        Global CapabilityRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = CapabilityRegistry()
    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (useful for testing)"""
    global _global_registry
    _global_registry = None
