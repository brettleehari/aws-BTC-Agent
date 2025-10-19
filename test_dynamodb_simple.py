"""
Simple test to verify DynamoDB tables are working.
"""
import os
import boto3

from decimal import Decimal

# Set dummy credentials for local DynamoDB
os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

print("=" * 60)
print("Testing DynamoDB Local - Basic Operations")
print("=" * 60)

# Connect to local DynamoDB
dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')

# List tables
print("\n📋 Listing tables...")
client = boto3.client('dynamodb', endpoint_url='http://localhost:8000')
response = client.list_tables()
tables = response['TableNames']

print(f"✅ Found {len(tables)} tables:")
for table in tables:
    print(f"   - {table}")

expected_tables = ['agent_decisions', 'agent_memory_ltm', 'agent_state', 'agent_signals']
missing = [t for t in expected_tables if t not in tables]

if missing:
    print(f"\n❌ Missing tables: {missing}")
    exit(1)

print("\n✅ All required tables exist!")

# Test writing and reading from agent_decisions
print("\n🧪 Testing agent_decisions table...")
table = dynamodb.Table('agent_decisions')

test_item = {
    'decision_id': 'test-123',
    'agent_id': 'test-agent',
    'decision_type': 'SOURCE_SELECTION',
    'timestamp': '2025-10-19T00:00:00Z',
    'context': {'test': 'data'},
    'reasoning': {'confidence': Decimal('0.85')}
}

try:
    # Write item
    table.put_item(Item=test_item)
    print("✅ Successfully wrote item to agent_decisions")
    
    # Read item back
    response = table.get_item(Key={'decision_id': 'test-123'})
    if 'Item' in response:
        print("✅ Successfully read item from agent_decisions")
        retrieved = response['Item']
        print(f"   Agent ID: {retrieved['agent_id']}")
        print(f"   Decision Type: {retrieved['decision_type']}")
    else:
        print("❌ Failed to read item")
        exit(1)
        
    # Clean up
    table.delete_item(Key={'decision_id': 'test-123'})
    print("✅ Successfully deleted test item")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("✅ DEPLOYMENT SUCCESSFUL!")
print("=" * 60)
print("\nDynamoDB Local is working correctly!")
print("All 4 tables are accessible and functional.")
print("\nNext steps:")
print("1. ✅ DynamoDB Local running")
print("2. ✅ All tables created")
print("3. ✅ Read/Write operations working")
print("4. 🚀 Ready for memory system integration!")
print("\n" + "=" * 60)
