"""
AWS Client Management for Memory System

Provides DynamoDB clients with retry logic, table creation, and connection management.
"""

import boto3
import logging
from typing import Optional, Dict, Any
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class AWSClientManager:
    """Manages AWS service clients for the memory system"""
    
    def __init__(
        self,
        region: str = "us-east-1",
        profile_name: Optional[str] = None,
        endpoint_url: Optional[str] = None  # For DynamoDB Local
    ):
        """
        Initialize AWS client manager
        
        Args:
            region: AWS region
            profile_name: AWS profile name (optional)
            endpoint_url: Override endpoint (for DynamoDB Local testing)
        """
        self.region = region
        self.profile_name = profile_name
        self.endpoint_url = endpoint_url
        
        # Boto3 configuration with retries
        self.config = Config(
            region_name=region,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            connect_timeout=5,
            read_timeout=10
        )
        
        # Initialize session
        if profile_name:
            self.session = boto3.Session(profile_name=profile_name)
        else:
            self.session = boto3.Session()
        
        # Clients (lazy initialized)
        self._dynamodb_resource = None
        self._dynamodb_client = None
        self._cloudwatch = None
    
    @property
    def dynamodb_resource(self):
        """Get DynamoDB resource (lazy initialization)"""
        if self._dynamodb_resource is None:
            self._dynamodb_resource = self.session.resource(
                'dynamodb',
                config=self.config,
                endpoint_url=self.endpoint_url
            )
            logger.info(f"Initialized DynamoDB resource in {self.region}")
        return self._dynamodb_resource
    
    @property
    def dynamodb_client(self):
        """Get DynamoDB client (lazy initialization)"""
        if self._dynamodb_client is None:
            self._dynamodb_client = self.session.client(
                'dynamodb',
                config=self.config,
                endpoint_url=self.endpoint_url
            )
            logger.info(f"Initialized DynamoDB client in {self.region}")
        return self._dynamodb_client
    
    @property
    def cloudwatch(self):
        """Get CloudWatch client (lazy initialization)"""
        if self._cloudwatch is None:
            self._cloudwatch = self.session.client(
                'cloudwatch',
                config=self.config
            )
            logger.info(f"Initialized CloudWatch client in {self.region}")
        return self._cloudwatch
    
    def get_table(self, table_name: str):
        """Get DynamoDB table resource"""
        return self.dynamodb_resource.Table(table_name)
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a DynamoDB table exists"""
        try:
            self.dynamodb_client.describe_table(TableName=table_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            raise
    
    def create_decisions_table(self, table_name: str = "agent_decisions") -> bool:
        """
        Create the agent_decisions table
        
        Returns:
            True if created, False if already exists
        """
        if self.table_exists(table_name):
            logger.info(f"Table {table_name} already exists")
            return False
        
        try:
            table = self.dynamodb_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'},
                    {'AttributeName': 'GSI1_PK', 'AttributeType': 'S'},
                    {'AttributeName': 'GSI1_SK', 'AttributeType': 'N'},
                    {'AttributeName': 'GSI2_PK', 'AttributeType': 'S'},
                    {'AttributeName': 'GSI2_SK', 'AttributeType': 'N'},
                    {'AttributeName': 'GSI3_PK', 'AttributeType': 'S'},
                    {'AttributeName': 'GSI3_SK', 'AttributeType': 'N'},
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'SuccessIndex',
                        'KeySchema': [
                            {'AttributeName': 'GSI1_PK', 'KeyType': 'HASH'},
                            {'AttributeName': 'GSI1_SK', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    },
                    {
                        'IndexName': 'DecisionTypeIndex',
                        'KeySchema': [
                            {'AttributeName': 'GSI2_PK', 'KeyType': 'HASH'},
                            {'AttributeName': 'GSI2_SK', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    },
                    {
                        'IndexName': 'STMIndex',
                        'KeySchema': [
                            {'AttributeName': 'GSI3_PK', 'KeyType': 'HASH'},
                            {'AttributeName': 'GSI3_SK', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                StreamSpecification={
                    'StreamEnabled': True,
                    'StreamViewType': 'NEW_AND_OLD_IMAGES'
                },
                TimeToLiveSpecification={
                    'Enabled': True,
                    'AttributeName': 'ttl'
                }
            )
            
            # Wait for table to be created
            table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
            logger.info(f"Created table {table_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            raise
    
    def create_memory_ltm_table(self, table_name: str = "agent_memory_ltm") -> bool:
        """
        Create the agent_memory_ltm table
        
        Returns:
            True if created, False if already exists
        """
        if self.table_exists(table_name):
            logger.info(f"Table {table_name} already exists")
            return False
        
        try:
            table = self.dynamodb_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'},
                    {'AttributeName': 'GSI1_PK', 'AttributeType': 'S'},
                    {'AttributeName': 'GSI1_SK', 'AttributeType': 'N'},
                    {'AttributeName': 'GSI2_PK', 'AttributeType': 'S'},
                    {'AttributeName': 'GSI2_SK', 'AttributeType': 'N'},
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'ConfidenceIndex',
                        'KeySchema': [
                            {'AttributeName': 'GSI1_PK', 'KeyType': 'HASH'},
                            {'AttributeName': 'GSI1_SK', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    },
                    {
                        'IndexName': 'SharedPatternIndex',
                        'KeySchema': [
                            {'AttributeName': 'GSI2_PK', 'KeyType': 'HASH'},
                            {'AttributeName': 'GSI2_SK', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                StreamSpecification={
                    'StreamEnabled': True,
                    'StreamViewType': 'NEW_AND_OLD_IMAGES'
                }
            )
            
            # Wait for table to be created
            table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
            logger.info(f"Created table {table_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            raise
    
    def create_agent_state_table(self, table_name: str = "agent_state") -> bool:
        """
        Create the agent_state table
        
        Returns:
            True if created, False if already exists
        """
        if self.table_exists(table_name):
            logger.info(f"Table {table_name} already exists")
            return False
        
        try:
            table = self.dynamodb_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'},
                ],
                BillingMode='PAY_PER_REQUEST',
                StreamSpecification={
                    'StreamEnabled': True,
                    'StreamViewType': 'NEW_AND_OLD_IMAGES'
                }
            )
            
            # Wait for table to be created
            table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
            logger.info(f"Created table {table_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            raise
    
    def create_signals_table(self, table_name: str = "agent_signals") -> bool:
        """
        Create the agent_signals table
        
        Returns:
            True if created, False if already exists
        """
        if self.table_exists(table_name):
            logger.info(f"Table {table_name} already exists")
            return False
        
        try:
            table = self.dynamodb_resource.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'},
                    {'AttributeName': 'GSI1_PK', 'AttributeType': 'S'},
                    {'AttributeName': 'GSI1_SK', 'AttributeType': 'N'},
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'TargetAgentIndex',
                        'KeySchema': [
                            {'AttributeName': 'GSI1_PK', 'KeyType': 'HASH'},
                            {'AttributeName': 'GSI1_SK', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'BillingMode': 'PAY_PER_REQUEST'
                    }
                ],
                BillingMode='PAY_PER_REQUEST',
                StreamSpecification={
                    'StreamEnabled': True,
                    'StreamViewType': 'NEW_AND_OLD_IMAGES'
                },
                TimeToLiveSpecification={
                    'Enabled': True,
                    'AttributeName': 'ttl'
                }
            )
            
            # Wait for table to be created
            table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
            logger.info(f"Created table {table_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            raise
    
    def create_all_tables(self) -> Dict[str, bool]:
        """
        Create all memory system tables
        
        Returns:
            Dict mapping table name to whether it was created
        """
        results = {}
        
        results['agent_decisions'] = self.create_decisions_table()
        results['agent_memory_ltm'] = self.create_memory_ltm_table()
        results['agent_state'] = self.create_agent_state_table()
        results['agent_signals'] = self.create_signals_table()
        
        created_count = sum(results.values())
        logger.info(f"Created {created_count} new tables out of {len(results)}")
        
        return results
    
    def delete_table(self, table_name: str) -> bool:
        """
        Delete a DynamoDB table (use with caution!)
        
        Returns:
            True if deleted, False if didn't exist
        """
        if not self.table_exists(table_name):
            logger.info(f"Table {table_name} does not exist")
            return False
        
        try:
            table = self.dynamodb_resource.Table(table_name)
            table.delete()
            table.meta.client.get_waiter('table_not_exists').wait(TableName=table_name)
            logger.warning(f"Deleted table {table_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete table {table_name}: {e}")
            raise
    
    def put_metric(
        self,
        namespace: str,
        metric_name: str,
        value: float,
        unit: str = 'None',
        dimensions: Optional[Dict[str, str]] = None
    ):
        """
        Put a custom metric to CloudWatch
        
        Args:
            namespace: CloudWatch namespace (e.g., "BTCAgent/Memory")
            metric_name: Metric name
            value: Metric value
            unit: Unit (Count, Percent, Seconds, etc.)
            dimensions: Optional dimensions dict
        """
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit
        }
        
        if dimensions:
            metric_data['Dimensions'] = [
                {'Name': k, 'Value': v} for k, v in dimensions.items()
            ]
        
        try:
            self.cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=[metric_data]
            )
        except ClientError as e:
            logger.error(f"Failed to put metric {metric_name}: {e}")


# Singleton instance
_client_manager: Optional[AWSClientManager] = None


def get_client_manager(
    region: str = "us-east-1",
    profile_name: Optional[str] = None,
    endpoint_url: Optional[str] = None
) -> AWSClientManager:
    """
    Get or create singleton AWS client manager
    
    Args:
        region: AWS region
        profile_name: AWS profile name (optional)
        endpoint_url: Override endpoint (for DynamoDB Local testing)
    
    Returns:
        AWSClientManager instance
    """
    global _client_manager
    
    if _client_manager is None:
        _client_manager = AWSClientManager(region, profile_name, endpoint_url)
    
    return _client_manager


__all__ = ['AWSClientManager', 'get_client_manager']
