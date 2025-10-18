"""
Database schema and storage for Market Hunter Agent
Stores decision logs, metrics, and signals
"""

import psycopg2
from psycopg2.extras import Json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MarketHunterDatabase:
    """
    Database handler for Market Hunter Agent
    Stores all agent decisions, metrics, and generated signals
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize database connection
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string
        self.conn = None
        self.connect()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
    
    def create_tables(self):
        """Create all required tables"""
        
        create_tables_sql = """
        -- Market Hunter execution logs
        CREATE TABLE IF NOT EXISTS agent_executions (
            id SERIAL PRIMARY KEY,
            cycle_number INTEGER NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL,
            duration_seconds FLOAT NOT NULL,
            market_context JSONB NOT NULL,
            selected_sources TEXT[] NOT NULL,
            source_scores JSONB NOT NULL,
            results_count INTEGER NOT NULL,
            signals_count INTEGER NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Whale movements data
        CREATE TABLE IF NOT EXISTS whale_movements (
            id SERIAL PRIMARY KEY,
            execution_id INTEGER REFERENCES agent_executions(id),
            transaction_hash TEXT,
            amount_btc DECIMAL(20, 8),
            from_address TEXT,
            to_address TEXT,
            transaction_type TEXT,
            timestamp TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Narrative shifts data
        CREATE TABLE IF NOT EXISTS narrative_shifts (
            id SERIAL PRIMARY KEY,
            execution_id INTEGER REFERENCES agent_executions(id),
            topic TEXT NOT NULL,
            sentiment_score FLOAT,
            engagement_count INTEGER,
            platform TEXT,
            timestamp TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Arbitrage opportunities
        CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
            id SERIAL PRIMARY KEY,
            execution_id INTEGER REFERENCES agent_executions(id),
            exchange_1 TEXT NOT NULL,
            exchange_2 TEXT NOT NULL,
            spread_percent DECIMAL(10, 4),
            buy_price DECIMAL(20, 2),
            sell_price DECIMAL(20, 2),
            timestamp TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Influencer signals
        CREATE TABLE IF NOT EXISTS influencer_signals (
            id SERIAL PRIMARY KEY,
            execution_id INTEGER REFERENCES agent_executions(id),
            influencer_name TEXT NOT NULL,
            signal_type TEXT,
            target_price DECIMAL(20, 2),
            confidence FLOAT,
            follower_count INTEGER,
            timestamp TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Technical breakouts
        CREATE TABLE IF NOT EXISTS technical_breakouts (
            id SERIAL PRIMARY KEY,
            execution_id INTEGER REFERENCES agent_executions(id),
            pattern_type TEXT NOT NULL,
            timeframe TEXT,
            breakout_price DECIMAL(20, 2),
            target_price DECIMAL(20, 2),
            confidence FLOAT,
            timestamp TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Institutional flows
        CREATE TABLE IF NOT EXISTS institutional_flows (
            id SERIAL PRIMARY KEY,
            execution_id INTEGER REFERENCES agent_executions(id),
            institution_name TEXT,
            flow_type TEXT,
            amount_btc DECIMAL(20, 8),
            total_holdings DECIMAL(20, 8),
            timestamp TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Derivatives signals
        CREATE TABLE IF NOT EXISTS derivatives_signals (
            id SERIAL PRIMARY KEY,
            execution_id INTEGER REFERENCES agent_executions(id),
            exchange TEXT NOT NULL,
            funding_rate DECIMAL(10, 6),
            open_interest_change DECIMAL(10, 4),
            liquidations_24h DECIMAL(20, 2),
            timestamp TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Macro signals
        CREATE TABLE IF NOT EXISTS macro_signals (
            id SERIAL PRIMARY KEY,
            execution_id INTEGER REFERENCES agent_executions(id),
            fear_greed_index INTEGER,
            market_cap_total DECIMAL(20, 2),
            btc_dominance DECIMAL(10, 4),
            sentiment TEXT,
            timestamp TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- System alerts/signals generated for other agents
        CREATE TABLE IF NOT EXISTS system_alerts (
            id SERIAL PRIMARY KEY,
            execution_id INTEGER REFERENCES agent_executions(id),
            signal_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            confidence FLOAT NOT NULL,
            message TEXT NOT NULL,
            recommended_action TEXT,
            target_agents TEXT[] NOT NULL,
            signal_data JSONB,
            timestamp TIMESTAMPTZ NOT NULL,
            processed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Source performance metrics (historical)
        CREATE TABLE IF NOT EXISTS source_metrics_history (
            id SERIAL PRIMARY KEY,
            execution_id INTEGER REFERENCES agent_executions(id),
            source_name TEXT NOT NULL,
            success_rate FLOAT,
            signal_quality FLOAT,
            total_calls INTEGER,
            successful_calls INTEGER,
            quality_contributions INTEGER,
            last_used_cycles_ago INTEGER,
            timestamp TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Create indexes for better query performance
        CREATE INDEX IF NOT EXISTS idx_agent_executions_timestamp ON agent_executions(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_system_alerts_severity ON system_alerts(severity, timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_system_alerts_processed ON system_alerts(processed, timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_whale_movements_timestamp ON whale_movements(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_derivatives_signals_timestamp ON derivatives_signals(timestamp DESC);
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(create_tables_sql)
                self.conn.commit()
                logger.info("Database tables created successfully")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error creating tables: {str(e)}")
            raise
    
    def store_execution(self, execution_data: Dict) -> int:
        """
        Store agent execution results
        
        Args:
            execution_data: Execution summary from agent cycle
            
        Returns:
            execution_id for referencing related data
        """
        sql = """
        INSERT INTO agent_executions (
            cycle_number, timestamp, duration_seconds, market_context,
            selected_sources, source_scores, results_count, signals_count
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (
                    execution_data['cycle_number'],
                    execution_data['timestamp'],
                    execution_data['duration_seconds'],
                    Json(execution_data['context']),
                    execution_data['selected_sources'],
                    Json(execution_data['source_scores']),
                    execution_data['results_count'],
                    execution_data['signals_generated']
                ))
                execution_id = cur.fetchone()[0]
                self.conn.commit()
                logger.info(f"Stored execution {execution_id}")
                return execution_id
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error storing execution: {str(e)}")
            raise
    
    def store_signals(self, execution_id: int, signals: List[Dict]):
        """
        Store generated signals
        
        Args:
            execution_id: Reference to execution
            signals: List of signal dictionaries
        """
        sql = """
        INSERT INTO system_alerts (
            execution_id, signal_type, severity, confidence,
            message, recommended_action, target_agents, signal_data, timestamp
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            with self.conn.cursor() as cur:
                for signal in signals:
                    cur.execute(sql, (
                        execution_id,
                        signal['type'],
                        signal['severity'],
                        signal['confidence'],
                        signal['message'],
                        signal.get('recommended_action'),
                        signal['targets'],
                        Json(signal.get('data', {})),
                        datetime.fromisoformat(signal['timestamp']) if isinstance(signal['timestamp'], str) else signal['timestamp']
                    ))
                self.conn.commit()
                logger.info(f"Stored {len(signals)} signals")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error storing signals: {str(e)}")
            raise
    
    def store_source_metrics(self, execution_id: int, metrics: Dict):
        """
        Store source performance metrics
        
        Args:
            execution_id: Reference to execution
            metrics: Dictionary of source metrics
        """
        sql = """
        INSERT INTO source_metrics_history (
            execution_id, source_name, success_rate, signal_quality,
            total_calls, successful_calls, quality_contributions,
            last_used_cycles_ago, timestamp
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            with self.conn.cursor() as cur:
                for source_name, source_metrics in metrics.items():
                    cur.execute(sql, (
                        execution_id,
                        source_name,
                        source_metrics['success_rate'],
                        source_metrics['signal_quality'],
                        source_metrics['total_calls'],
                        source_metrics.get('successful_calls', 0),
                        source_metrics.get('quality_contributions', 0),
                        source_metrics['last_used'],
                        datetime.now()
                    ))
                self.conn.commit()
                logger.info(f"Stored metrics for {len(metrics)} sources")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error storing metrics: {str(e)}")
            raise
    
    def get_unprocessed_signals(self, limit: int = 100) -> List[Dict]:
        """
        Retrieve unprocessed signals for other agents
        
        Args:
            limit: Maximum number of signals to return
            
        Returns:
            List of signal dictionaries
        """
        sql = """
        SELECT id, signal_type, severity, confidence, message,
               recommended_action, target_agents, signal_data, timestamp
        FROM system_alerts
        WHERE processed = FALSE
        ORDER BY timestamp DESC
        LIMIT %s
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (limit,))
                rows = cur.fetchall()
                
                signals = []
                for row in rows:
                    signals.append({
                        'id': row[0],
                        'type': row[1],
                        'severity': row[2],
                        'confidence': row[3],
                        'message': row[4],
                        'recommended_action': row[5],
                        'targets': row[6],
                        'data': row[7],
                        'timestamp': row[8]
                    })
                
                return signals
        except Exception as e:
            logger.error(f"Error retrieving signals: {str(e)}")
            raise
    
    def mark_signals_processed(self, signal_ids: List[int]):
        """
        Mark signals as processed
        
        Args:
            signal_ids: List of signal IDs to mark
        """
        sql = "UPDATE system_alerts SET processed = TRUE WHERE id = ANY(%s)"
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (signal_ids,))
                self.conn.commit()
                logger.info(f"Marked {len(signal_ids)} signals as processed")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error marking signals: {str(e)}")
            raise
    
    def get_performance_summary(self, days: int = 7) -> Dict:
        """
        Get performance summary over time period
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Performance summary dictionary
        """
        sql = """
        SELECT 
            COUNT(*) as total_cycles,
            AVG(duration_seconds) as avg_duration,
            SUM(signals_count) as total_signals,
            AVG(results_count) as avg_results_per_cycle
        FROM agent_executions
        WHERE timestamp >= NOW() - INTERVAL '%s days'
        """
        
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (days,))
                row = cur.fetchone()
                
                return {
                    'total_cycles': row[0],
                    'avg_duration': float(row[1]) if row[1] else 0,
                    'total_signals': row[2] or 0,
                    'avg_results_per_cycle': float(row[3]) if row[3] else 0
                }
        except Exception as e:
            logger.error(f"Error getting performance summary: {str(e)}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
