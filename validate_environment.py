#!/usr/bin/env python3
"""
Market Hunter Agent - Environment Validation Script

Run this script to validate your environment setup before starting the agent.
It checks for required API keys and verifies they're properly configured.

Usage:
    python validate_environment.py
"""

import os
import sys
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

def validate_environment():
    """
    Validate all required environment variables for Market Hunter Agent.
    
    Returns:
        bool: True if all required keys are present, False otherwise
    """
    print("\n" + "="*70)
    print("Market Hunter Agent - Environment Validation")
    print("="*70)
    
    # Required API keys
    required_keys = {
        'TWITTER_BEARER_TOKEN': {
            'description': 'Twitter API Bearer Token',
            'get_from': 'https://developer.twitter.com/en/portal/dashboard',
            'used_for': 'Influencer signals, narrative shifts, social sentiment',
            'cost': 'FREE (Essential tier: 10K tweets/month)'
        },
        'NEWSAPI_KEY': {
            'description': 'NewsAPI Key',
            'get_from': 'https://newsapi.org/register',
            'used_for': 'News sentiment, narrative analysis',
            'cost': 'FREE (Developer tier: 100 requests/day)'
        },
        'ALPHA_VANTAGE_API_KEY': {
            'description': 'Alpha Vantage API Key',
            'get_from': 'https://www.alphavantage.co/support/#api-key',
            'used_for': 'Price validation, technical indicators',
            'cost': 'FREE (500 requests/day)'
        }
    }
    
    # Optional API keys (for information only)
    optional_keys = {
        'TWITTER_API_KEY': 'Twitter API Key (Extended)',
        'COINGECKO_API_KEY': 'CoinGecko API Key',
        'GLASSNODE_API_KEY': 'Glassnode API Key'
    }
    
    # Check required keys
    print("\n📋 Checking Required API Keys...")
    print("-"*70)
    
    missing_keys = []
    present_keys = []
    
    for env_var, info in required_keys.items():
        value = os.getenv(env_var)
        
        if value and value != f'your_{env_var.lower()}_here':
            print(f"✅ {info['description']}")
            print(f"   └─ Value: {value[:10]}... (hidden for security)")
            present_keys.append(env_var)
        else:
            print(f"❌ {info['description']}")
            print(f"   └─ Environment Variable: {env_var}")
            print(f"   └─ Get From: {info['get_from']}")
            print(f"   └─ Used For: {info['used_for']}")
            print(f"   └─ Cost: {info['cost']}")
            missing_keys.append(env_var)
        print()
    
    # Check optional keys
    print("\n📋 Checking Optional API Keys...")
    print("-"*70)
    
    for env_var, description in optional_keys.items():
        value = os.getenv(env_var)
        
        if value and value != f'your_{env_var.lower()}_here':
            print(f"✅ {description}: Present")
        else:
            print(f"ℹ️  {description}: Not configured (optional)")
    
    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    if not missing_keys:
        print("✅ SUCCESS: All required API keys are configured!")
        print(f"\n   Present Keys: {len(present_keys)}/{len(required_keys)}")
        print("\n   You can now start the Market Hunter Agent:")
        print("   $ python test_market_hunter.py")
        print("\n" + "="*70)
        return True
    else:
        print(f"❌ FAILURE: {len(missing_keys)} required API key(s) missing!")
        print(f"\n   Present: {len(present_keys)}/{len(required_keys)}")
        print(f"   Missing: {', '.join(missing_keys)}")
        
        print("\n" + "-"*70)
        print("HOW TO FIX:")
        print("-"*70)
        print("\n1. Copy the example environment file:")
        print("   $ cp .env.example .env")
        
        print("\n2. Edit .env and add your API keys:")
        print("   $ nano .env  # or use your favorite editor")
        
        print("\n3. Get your API keys from:")
        for env_var in missing_keys:
            info = required_keys[env_var]
            print(f"\n   • {info['description']}:")
            print(f"     {info['get_from']}")
            print(f"     ({info['cost']})")
        
        print("\n4. Run this validation script again:")
        print("   $ python validate_environment.py")
        
        print("\n" + "="*70)
        return False


def test_imports():
    """Test that all required Python packages are installed."""
    print("\n" + "="*70)
    print("Testing Python Dependencies")
    print("="*70)
    
    required_packages = [
        'dotenv',
        'requests',
        'aiohttp',
        'numpy',
        'dataclasses'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'dotenv':
                import dotenv
            elif package == 'requests':
                import requests
            elif package == 'aiohttp':
                import aiohttp
            elif package == 'numpy':
                import numpy
            elif package == 'dataclasses':
                import dataclasses
            print(f"✅ {package}: Installed")
        except ImportError:
            print(f"❌ {package}: Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ {len(missing_packages)} package(s) missing!")
        print("\nInstall missing packages:")
        print(f"   $ pip install {' '.join(missing_packages)}")
        return False
    else:
        print("\n✅ All required packages installed!")
        return True


def main():
    """Main validation function."""
    print("\n🚀 Market Hunter Agent - Pre-Flight Check")
    
    # Test Python dependencies
    deps_ok = test_imports()
    
    # Test environment variables
    env_ok = validate_environment()
    
    # Overall status
    print("\n" + "="*70)
    print("OVERALL STATUS")
    print("="*70)
    
    if deps_ok and env_ok:
        print("✅ All checks passed! Agent is ready to launch! 🚀")
        print("\n   Start the agent with:")
        print("   $ python test_market_hunter.py")
        print("="*70 + "\n")
        return 0
    else:
        print("❌ Pre-flight checks failed. Please fix the issues above.")
        print("="*70 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
