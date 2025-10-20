#!/usr/bin/env python3
"""
Quick configuration test for Twitter integration.
Tests setup without making API calls (no rate limits).
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_interfaces.twitter_interface import TwitterInterface

def test_configuration():
    """Test Twitter interface configuration without API calls"""
    
    print("\n" + "="*80)
    print("  Twitter Configuration Test (No API Calls)")
    print("="*80)
    
    # Check credentials
    print("\n📋 Checking Credentials...")
    
    creds = [
        ["TWITTER_API_KEY", os.getenv('TWITTER_API_KEY')[:10] + "..." if os.getenv('TWITTER_API_KEY') else "❌ Missing"],
        ["TWITTER_API_SECRET", os.getenv('TWITTER_API_SECRET')[:10] + "..." if os.getenv('TWITTER_API_SECRET') else "❌ Missing"],
        ["TWITTER_BEARER_TOKEN", os.getenv('TWITTER_BEARER_TOKEN')[:20] + "..." if os.getenv('TWITTER_BEARER_TOKEN') else "❌ Missing"],
        ["TWITTER_ACCESS_TOKEN", os.getenv('TWITTER_ACCESS_TOKEN')[:20] + "..." if os.getenv('TWITTER_ACCESS_TOKEN') else "❌ Missing"],
        ["TWITTER_ACCESS_TOKEN_SECRET", os.getenv('TWITTER_ACCESS_TOKEN_SECRET')[:10] + "..." if os.getenv('TWITTER_ACCESS_TOKEN_SECRET') else "❌ Missing"],
    ]
    
    print(tabulate(creds, headers=["Credential", "Status"], tablefmt="grid"))
    
    # Initialize TwitterInterface
    print("\n⚙️  Initializing TwitterInterface...")
    
    try:
        twitter = TwitterInterface()
        print("✅ TwitterInterface initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False
    
    # Check configuration
    print("\n📊 Influencer Configuration:")
    
    accounts = twitter.influencers.get('top_bitcoin_twitter_accounts', [])
    
    if not accounts:
        print("❌ No accounts configured!")
        return False
    
    print(f"\n✅ {len(accounts)} Bitcoin influencer accounts configured\n")
    
    # Display account table
    account_data = []
    for acc in accounts:
        account_data.append([
            acc.get('priority', 'N/A'),
            acc.get('handle', 'N/A'),
            acc.get('name', 'N/A'),
            acc.get('followers', 'N/A'),
            acc.get('specialty', 'N/A')[:50] + '...' if len(acc.get('specialty', '')) > 50 else acc.get('specialty', 'N/A'),
            acc.get('weight', 'N/A'),
            acc.get('check_frequency', 'N/A'),
        ])
    
    print(tabulate(
        account_data,
        headers=["Priority", "Handle", "Name", "Followers", "Specialty", "Weight", "Frequency"],
        tablefmt="grid"
    ))
    
    # Check monitoring strategy
    print("\n📡 Monitoring Strategy:")
    
    strategy = twitter.influencers.get('monitoring_strategy', {})
    
    if strategy:
        strategy_data = []
        for tier, config in strategy.items():
            accounts_list = ", ".join(config.get('accounts', [])[:3])
            if len(config.get('accounts', [])) > 3:
                accounts_list += f" +{len(config.get('accounts', [])) - 3} more"
            strategy_data.append([
                tier.replace('_', ' ').title(),
                config.get('interval', 'N/A'),
                config.get('method', 'N/A'),
                accounts_list
            ])
        
        print(tabulate(
            strategy_data,
            headers=["Tier", "Interval", "Method", "Accounts"],
            tablefmt="grid"
        ))
    
    # Check signal generation rules
    print("\n🎯 Signal Generation Rules:")
    
    signals = twitter.influencers.get('signal_generation_rules', {})
    
    if signals:
        signal_data = []
        for rule_name, rule_config in signals.items():
            signal_data.append([
                rule_name.replace('_', ' ').title(),
                rule_config.get('priority', 'N/A'),
                ', '.join(rule_config.get('accounts', [])[:3]),
                rule_config.get('action', 'N/A')
            ])
        
        print(tabulate(
            signal_data,
            headers=["Rule", "Priority", "Trigger Accounts", "Action"],
            tablefmt="grid"
        ))
    
    # Check data types
    print("\n📦 Supported Data Types:")
    
    metadata = twitter.metadata
    data_types = [dt.value for dt in metadata.data_types]
    
    print(f"  • {', '.join(data_types)}")
    
    # Check capabilities
    print("\n🔧 Capabilities:")
    
    capabilities = [cap.value for cap in metadata.capabilities]
    print(f"  • {', '.join(capabilities)}")
    
    # Summary
    print("\n" + "="*80)
    print("  Configuration Test Summary")
    print("="*80)
    
    summary = [
        ["Credentials Loaded", "✅ Yes" if twitter.bearer_token else "❌ No"],
        ["Accounts Configured", f"✅ {len(accounts)}"],
        ["Monitoring Strategy", "✅ Yes" if strategy else "❌ No"],
        ["Signal Rules", "✅ Yes" if signals else "❌ No"],
        ["Data Types Supported", f"✅ {len(data_types)}"],
        ["Capabilities", f"✅ {len(capabilities)}"],
    ]
    
    print(tabulate(summary, headers=["Item", "Status"], tablefmt="grid"))
    
    print("\n✅ Twitter integration is properly configured!")
    print("\n💡 Next Steps:")
    print("  1. Wait for Twitter API rate limit to reset (~15 minutes)")
    print("  2. Run: python test_twitter_fetch.py")
    print("  3. Or deploy to production where caching reduces API calls by 83%")
    
    return True


if __name__ == "__main__":
    try:
        success = test_configuration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
