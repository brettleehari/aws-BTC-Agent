"""
Integration example: Using Data Interfaces with Market Hunter Agent

This shows how to integrate the new data interfaces module with the 
existing Market Hunter Agent.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

# Import existing Market Hunter components
from src.market_hunter_agent import MarketHunterAgent
from src.llm_router import LLMRouter

# Import new Data Interfaces components
from src.data_interfaces import (
    DataRequest,
    DataType,
    Capability,
    get_manager,
    get_registry,
)


class EnhancedMarketHunterAgent(MarketHunterAgent):
    """
    Enhanced Market Hunter Agent with new data interfaces module.
    
    This extends the original agent with:
    - Multi-source data fetching
    - Intelligent source selection
    - Automatic fallback
    - Circuit breaker protection
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add data interface manager
        self.data_manager = get_manager()
        self.data_registry = get_registry()
        
        # Configure for reliability
        self.data_manager.enable_fallback = True
        self.data_manager.cache_ttl = 60  # 1 minute cache
    
    async def fetch_market_data(self, symbol: str = "BTC") -> Dict[str, Any]:
        """
        Fetch market data using new data interfaces.
        
        This replaces direct API calls with intelligent routing through
        the data interfaces module.
        """
        # Create request for price data
        price_request = DataRequest(
            data_type=DataType.PRICE,
            symbol=symbol,
            parameters={"vs_currency": "usd"}
        )
        
        # Fetch with automatic source selection and fallback
        price_response = await self.data_manager.fetch(price_request)
        
        if not price_response.success:
            self.logger.error(f"Failed to fetch price: {price_response.error}")
            return {}
        
        # Log which source provided the data
        self.logger.info(f"Price data from {price_response.source} ({price_response.latency_ms:.0f}ms)")
        
        return price_response.data
    
    async def fetch_on_chain_metrics(self, symbol: str = "BTC") -> Dict[str, Any]:
        """
        Fetch on-chain metrics using Glassnode or alternative sources.
        """
        request = DataRequest(
            data_type=DataType.ON_CHAIN,
            symbol=symbol,
            parameters={"metric": "addresses_active_count"}
        )
        
        response = await self.data_manager.fetch(request)
        
        if response.success:
            self.logger.info(f"On-chain data from {response.source}")
            return response.data
        else:
            self.logger.warning(f"On-chain fetch failed: {response.error}")
            return {}
    
    async def fetch_market_sentiment(self, symbol: str = "BTC") -> Dict[str, Any]:
        """
        Fetch market sentiment including Fear & Greed Index.
        """
        request = DataRequest(
            data_type=DataType.SOCIAL_SENTIMENT,
            symbol=symbol,
            timeframe="7d",
            parameters={"metric": "fear_greed"}
        )
        
        response = await self.data_manager.fetch(request)
        
        if response.success:
            current = response.data.get('current', {})
            interpretation = response.data.get('interpretation', {})
            
            self.logger.info(
                f"Sentiment: {current.get('value_classification')} "
                f"({current.get('value')} - {interpretation.get('signal')})"
            )
            
            return response.data
        else:
            self.logger.warning(f"Sentiment fetch failed: {response.error}")
            return {}
    
    async def analyze_market_conditions(self, symbol: str = "BTC") -> Dict[str, Any]:
        """
        Comprehensive market analysis using multiple data sources.
        
        This demonstrates parallel fetching from multiple sources and
        combining the results for holistic analysis.
        """
        self.logger.info(f"Analyzing market conditions for {symbol}")
        
        # Fetch data from multiple sources in parallel
        price_task = self.fetch_market_data(symbol)
        sentiment_task = self.fetch_market_sentiment(symbol)
        onchain_task = self.fetch_on_chain_metrics(symbol)
        
        # Wait for all to complete
        price_data, sentiment_data, onchain_data = await asyncio.gather(
            price_task,
            sentiment_task,
            onchain_task,
            return_exceptions=True
        )
        
        # Combine results
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'price': price_data,
            'sentiment': sentiment_data,
            'on_chain': onchain_data,
        }
        
        # Generate insights using LLM
        insights = await self.generate_insights(analysis)
        analysis['insights'] = insights
        
        return analysis
    
    async def generate_insights(self, analysis: Dict[str, Any]) -> str:
        """
        Generate insights from combined data using LLM router.
        """
        # Prepare prompt for LLM
        prompt = f"""
Based on the following market data, provide a concise analysis:

Price Data: {analysis.get('price', {})}
Sentiment: {analysis.get('sentiment', {}).get('interpretation', {})}
On-Chain: {analysis.get('on_chain', {})}

Provide:
1. Current market condition assessment
2. Key signals and indicators
3. Risk level
4. Recommended action
"""
        
        # Use LLM router for analysis
        response = await self.llm_router.route_and_execute(
            prompt=prompt,
            task_type="analysis",
            priority="medium"
        )
        
        return response.get('content', '')
    
    async def discover_available_sources(self) -> Dict[str, Any]:
        """
        Discover what data sources are available for the agent.
        
        This uses the capability registry to show what data the agent
        can access.
        """
        summary = {
            'total_sources': len(self.data_registry.list_sources()),
            'sources': {},
            'capabilities': {},
            'data_types': {},
        }
        
        # Get all sources
        for source_name in self.data_registry.list_sources():
            metadata = self.data_registry.get_metadata(source_name)
            
            summary['sources'][source_name] = {
                'provider': metadata.provider,
                'cost': metadata.cost_tier.value,
                'reliability': f"{metadata.reliability_score * 100:.0f}%",
                'data_types': [dt.value for dt in metadata.data_types],
                'capabilities': [cap.value for cap in metadata.capabilities],
            }
        
        # Group by data type
        for data_type in DataType:
            sources = self.data_registry.find_sources_for_data_type(data_type)
            if sources:
                summary['data_types'][data_type.value] = sources
        
        # Group by capability
        for capability in Capability:
            sources = self.data_registry.find_sources_with_capability(capability)
            if sources:
                summary['capabilities'][capability.value] = sources
        
        return summary
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Health check including data sources status.
        """
        health = {
            'agent': 'healthy',
            'llm_router': 'healthy',
            'data_sources': {},
            'manager_status': self.data_manager.get_status(),
        }
        
        # Check each data source
        for source_name in self.data_registry.list_sources():
            try:
                source = self.data_registry.create_source_instance(source_name)
                is_healthy = await source.health_check()
                health['data_sources'][source_name] = 'healthy' if is_healthy else 'unhealthy'
            except Exception as e:
                health['data_sources'][source_name] = f'error: {str(e)}'
        
        return health


async def demo_enhanced_agent():
    """
    Demonstration of the enhanced agent with data interfaces.
    """
    print("\n" + "="*60)
    print("ENHANCED MARKET HUNTER AGENT DEMO")
    print("="*60)
    
    # Initialize agent
    agent = EnhancedMarketHunterAgent(
        agent_id="enhanced-agent-001",
        agent_name="Enhanced Market Hunter",
        agent_description="Bitcoin market intelligence with multi-source data",
    )
    
    # 1. Discover available data sources
    print("\n1. Discovering Available Data Sources...")
    sources = await agent.discover_available_sources()
    print(f"   Total Sources: {sources['total_sources']}")
    for source_name, info in sources['sources'].items():
        print(f"   • {source_name} ({info['provider']}) - {info['cost']}")
    
    # 2. Health check
    print("\n2. Health Check...")
    health = await agent.health_check()
    print(f"   Agent: {health['agent']}")
    print(f"   Data Sources:")
    for source, status in health['data_sources'].items():
        print(f"     • {source}: {status}")
    
    # 3. Fetch market data
    print("\n3. Fetching Market Data...")
    market_data = await agent.fetch_market_data("BTC")
    if market_data:
        print(f"   BTC Price: ${market_data.get('price', 'N/A'):,.2f}")
        print(f"   24h Change: {market_data.get('price_change_24h_percent', 'N/A'):.2f}%")
    
    # 4. Fetch sentiment
    print("\n4. Fetching Market Sentiment...")
    sentiment = await agent.fetch_market_sentiment("BTC")
    if sentiment:
        current = sentiment.get('current', {})
        print(f"   Fear & Greed: {current.get('value')} ({current.get('value_classification')})")
        interp = sentiment.get('interpretation', {})
        print(f"   Signal: {interp.get('signal')}")
    
    # 5. Comprehensive analysis
    print("\n5. Running Comprehensive Analysis...")
    analysis = await agent.analyze_market_conditions("BTC")
    print(f"   Analysis completed at {analysis['timestamp']}")
    if analysis.get('insights'):
        print(f"\n   Insights:")
        print(f"   {analysis['insights'][:200]}...")
    
    # 6. Check manager status
    print("\n6. Data Manager Status...")
    status = agent.data_manager.get_status()
    print(f"   Cache Entries: {status['cache_size']}")
    print(f"   Fallback: {'Enabled' if status['enable_fallback'] else 'Disabled'}")
    print(f"   Circuit Breakers:")
    if status['circuit_breakers']:
        for source, info in status['circuit_breakers'].items():
            state = "OPEN" if info['is_open'] else "CLOSED"
            print(f"     • {source}: {state}")
    else:
        print(f"     All sources healthy")
    
    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60 + "\n")


async def integration_checklist():
    """
    Checklist for integrating data interfaces with existing agent.
    """
    print("\n" + "="*60)
    print("INTEGRATION CHECKLIST")
    print("="*60)
    
    checklist = [
        ("✓", "Import data interfaces module"),
        ("✓", "Initialize data manager in agent __init__"),
        ("✓", "Replace direct API calls with manager.fetch()"),
        ("✓", "Add error handling for failed fetches"),
        ("✓", "Configure fallback and caching"),
        ("✓", "Add health checks for data sources"),
        ("✓", "Log which source provided data"),
        ("✓", "Use parallel fetching for multiple requests"),
        ("⏳", "Deploy OpenAPI schemas to API Gateway"),
        ("⏳", "Create Lambda handler for Bedrock integration"),
        ("⏳", "Set up monitoring and alerting"),
        ("⏳", "Configure API keys in environment"),
    ]
    
    print("\nIntegration Tasks:")
    for status, task in checklist:
        print(f"  {status} {task}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_enhanced_agent())
    
    # Show integration checklist
    asyncio.run(integration_checklist())
