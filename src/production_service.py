"""
Integration example showing Market Hunter Agent with database storage
and continuous operation
"""

import time
import schedule
import logging
from datetime import datetime
from market_hunter_agent import MarketHunterAgent
from database import MarketHunterDatabase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarketHunterService:
    """
    Production service wrapper for Market Hunter Agent
    Handles database integration, error recovery, and continuous operation
    """
    
    def __init__(
        self,
        bedrock_agent_id: str,
        bedrock_agent_alias_id: str,
        database_connection_string: str,
        region_name: str = "us-east-1"
    ):
        """
        Initialize the service
        
        Args:
            bedrock_agent_id: Bedrock Agent ID
            bedrock_agent_alias_id: Bedrock Agent Alias ID
            database_connection_string: PostgreSQL connection string
            region_name: AWS region
        """
        logger.info("Initializing Market Hunter Service...")
        
        # Initialize agent
        self.agent = MarketHunterAgent(
            bedrock_agent_id=bedrock_agent_id,
            bedrock_agent_alias_id=bedrock_agent_alias_id,
            region_name=region_name,
            learning_rate=0.1,
            exploration_rate=0.2
        )
        
        # Initialize database
        self.db = MarketHunterDatabase(database_connection_string)
        self.db.create_tables()
        
        logger.info("Market Hunter Service initialized successfully")
    
    def fetch_market_data(self) -> dict:
        """
        Fetch current market data from external sources
        
        Returns:
            Market data dictionary
            
        Note: This is a placeholder. Implement real API calls to:
        - CoinGecko API
        - Binance API
        - CoinMarketCap API
        - etc.
        """
        # TODO: Implement real market data fetching
        # Example implementation:
        # import requests
        # response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true')
        # data = response.json()
        
        # For now, return simulated data
        import random
        return {
            'price': 62000 + random.uniform(-1000, 1000),
            'price_change_24h_percent': random.uniform(-5, 5),
            'volume_ratio': random.uniform(0.8, 1.3)
        }
    
    def run_cycle(self):
        """
        Execute one complete agent cycle with database storage
        """
        try:
            logger.info("Starting new agent cycle...")
            
            # Fetch current market data
            market_data = self.fetch_market_data()
            logger.info(f"Market data: BTC ${market_data['price']:,.2f} ({market_data['price_change_24h_percent']:+.2f}%)")
            
            # Execute agent cycle
            result = self.agent.execute_cycle(market_data)
            
            # Store results in database
            execution_id = self.db.store_execution(result)
            logger.info(f"Stored execution with ID: {execution_id}")
            
            # Store signals
            if result['signals']:
                self.db.store_signals(execution_id, result['signals'])
                logger.info(f"Stored {len(result['signals'])} signals")
            
            # Store metrics
            self.db.store_source_metrics(execution_id, result['metrics'])
            logger.info("Stored source metrics")
            
            # Process signals for other agents
            self.process_signals()
            
            logger.info("Agent cycle completed successfully\n")
            
        except Exception as e:
            logger.error(f"Error in agent cycle: {str(e)}", exc_info=True)
    
    def process_signals(self):
        """
        Process unprocessed signals and send to target agents
        
        Note: This is a placeholder. Implement real integration with:
        - AWS EventBridge
        - SQS queues
        - SNS topics
        - Direct agent invocation
        """
        try:
            signals = self.db.get_unprocessed_signals(limit=50)
            
            if not signals:
                return
            
            logger.info(f"Processing {len(signals)} unprocessed signals...")
            
            # TODO: Implement signal routing to other agents
            # Example:
            # for signal in signals:
            #     for target_agent in signal['targets']:
            #         send_to_agent(target_agent, signal)
            
            # Mark as processed
            signal_ids = [s['id'] for s in signals]
            self.db.mark_signals_processed(signal_ids)
            logger.info(f"Marked {len(signal_ids)} signals as processed")
            
        except Exception as e:
            logger.error(f"Error processing signals: {str(e)}")
    
    def generate_daily_report(self):
        """Generate daily performance report"""
        try:
            logger.info("\n" + "="*80)
            logger.info("DAILY PERFORMANCE REPORT")
            logger.info("="*80)
            
            # Get agent performance
            agent_report = self.agent.get_performance_report()
            logger.info(f"Total Cycles: {agent_report['total_cycles']}")
            logger.info(f"Overall Efficiency: {agent_report.get('overall_efficiency', 0):.3f}")
            
            # Get database summary
            db_summary = self.db.get_performance_summary(days=1)
            logger.info(f"\nDatabase Summary:")
            logger.info(f"  Total Signals: {db_summary['total_signals']}")
            logger.info(f"  Avg Duration: {db_summary['avg_duration']:.2f}s")
            logger.info(f"  Avg Results: {db_summary['avg_results_per_cycle']:.1f}")
            
            # Source performance
            logger.info(f"\nTop Performing Sources:")
            sorted_sources = sorted(
                agent_report['source_performance'].items(),
                key=lambda x: x[1]['efficiency'],
                reverse=True
            )
            for source, metrics in sorted_sources[:5]:
                logger.info(f"  {source}: {metrics['efficiency']:.3f}")
            
            logger.info("="*80 + "\n")
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
    
    def start(self):
        """
        Start the service with scheduled execution
        Runs every 10 minutes
        """
        logger.info("Starting Market Hunter Service...")
        logger.info("Agent will run every 10 minutes")
        logger.info("Press Ctrl+C to stop\n")
        
        # Schedule agent cycles
        schedule.every(10).minutes.do(self.run_cycle)
        
        # Schedule daily report
        schedule.every().day.at("00:00").do(self.generate_daily_report)
        
        # Run first cycle immediately
        self.run_cycle()
        
        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nShutting down Market Hunter Service...")
            self.db.close()
            logger.info("Service stopped")


def main():
    """
    Production deployment example
    """
    import os
    
    # Configuration from environment variables
    config = {
        'bedrock_agent_id': os.getenv('BEDROCK_AGENT_ID', 'YOUR_AGENT_ID'),
        'bedrock_agent_alias_id': os.getenv('BEDROCK_AGENT_ALIAS_ID', 'YOUR_ALIAS_ID'),
        'database_connection_string': os.getenv(
            'DATABASE_URL',
            'postgresql://user:password@localhost:5432/market_hunter'
        ),
        'region_name': os.getenv('AWS_REGION', 'us-east-1')
    }
    
    # Validate configuration
    if config['bedrock_agent_id'] == 'YOUR_AGENT_ID':
        logger.error("Please set BEDROCK_AGENT_ID environment variable")
        return
    
    if config['bedrock_agent_alias_id'] == 'YOUR_ALIAS_ID':
        logger.error("Please set BEDROCK_AGENT_ALIAS_ID environment variable")
        return
    
    # Initialize and start service
    service = MarketHunterService(**config)
    service.start()


if __name__ == "__main__":
    main()
