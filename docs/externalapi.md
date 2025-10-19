Bitcoin data sources · JSON
Download

{
  "bitcoin_data_sources": {
    "metadata": {
      "version": "1.0",
      "last_updated": "2025-01-18",
      "description": "Comprehensive free Bitcoin data sources with API limits for agentic systems",
      "total_sources": 28
    },
    "categories": {
      "price_market_data": {
        "description": "Real-time and historical price, volume, market cap data",
        "sources": [
          {
            "name": "CoinGecko API",
            "url": "https://www.coingecko.com/en/api",
            "category": "price_market_data",
            "data_types": [
              "price",
              "volume",
              "market_cap",
              "historical_data",
              "exchanges"
            ],
            "free_tier": {
              "rate_limit": "100 calls/minute",
              "monthly_limit": "unlimited",
              "daily_limit": "unlimited",
              "restrictions": "demo plan only"
            },
            "authentication": "api_key_optional",
            "reliability": "high",
            "data_quality": "excellent",
            "latency": "1-5 seconds",
            "endpoints": {
              "current_price": "/simple/price",
              "historical": "/coins/{id}/history",
              "market_data": "/coins/{id}"
            },
            "sample_response": {
              "bitcoin": {
                "usd": 42000,
                "usd_market_cap": 825000000000,
                "usd_24h_vol": 18000000000,
                "usd_24h_change": 2.5
              }
            }
          },
          {
            "name": "CoinMarketCap API",
            "url": "https://coinmarketcap.com/api/",
            "category": "price_market_data",
            "data_types": [
              "price",
              "market_cap",
              "volume",
              "rankings"
            ],
            "free_tier": {
              "rate_limit": "333 calls/month",
              "monthly_limit": "333",
              "daily_limit": "10",
              "restrictions": "basic plan"
            },
            "authentication": "api_key_required",
            "reliability": "high",
            "data_quality": "excellent",
            "latency": "1-3 seconds"
          },
          {
            "name": "Binance Public API",
            "url": "https://api.binance.com",
            "category": "price_market_data",
            "data_types": [
              "price",
              "orderbook",
              "trades",
              "klines"
            ],
            "free_tier": {
              "rate_limit": "1200 requests/minute",
              "monthly_limit": "unlimited",
              "daily_limit": "unlimited",
              "restrictions": "no auth required for public endpoints"
            },
            "authentication": "none_for_public",
            "reliability": "excellent",
            "data_quality": "excellent",
            "latency": "100-500ms"
          },
          {
            "name": "Kraken Public API",
            "url": "https://api.kraken.com",
            "category": "price_market_data",
            "data_types": [
              "price",
              "orderbook",
              "trades",
              "ohlc"
            ],
            "free_tier": {
              "rate_limit": "1 call/second",
              "monthly_limit": "unlimited",
              "daily_limit": "unlimited",
              "restrictions": "public endpoints only"
            },
            "authentication": "none_for_public",
            "reliability": "high",
            "data_quality": "excellent",
            "latency": "500ms-2s"
          },
          {
            "name": "Alpha Vantage",
            "url": "https://www.alphavantage.co",
            "category": "price_market_data",
            "data_types": [
              "price",
              "technical_indicators",
              "forex"
            ],
            "free_tier": {
              "rate_limit": "5 calls/minute",
              "monthly_limit": "unlimited",
              "daily_limit": "500",
              "restrictions": "25 requests/day on free tier"
            },
            "authentication": "api_key_required",
            "reliability": "medium",
            "data_quality": "good",
            "latency": "2-5 seconds"
          }
        ]
      },
      "sentiment_social": {
        "description": "Market sentiment, social media sentiment, fear & greed indicators",
        "sources": [
          {
            "name": "Fear & Greed Index",
            "url": "https://api.alternative.me/fng/",
            "category": "sentiment_social",
            "data_types": [
              "fear_greed_index",
              "historical_sentiment"
            ],
            "free_tier": {
              "rate_limit": "unlimited",
              "monthly_limit": "unlimited",
              "daily_limit": "unlimited",
              "restrictions": "none"
            },
            "authentication": "none",
            "reliability": "high",
            "data_quality": "good",
            "latency": "1-2 seconds",
            "endpoints": {
              "current": "/?limit=1",
              "historical": "/?limit=30"
            }
          },
          {
            "name": "NewsAPI",
            "url": "https://newsapi.org",
            "category": "sentiment_social",
            "data_types": [
              "news_articles",
              "headlines",
              "sources"
            ],
            "free_tier": {
              "rate_limit": "1000 requests/day",
              "monthly_limit": "30000",
              "daily_limit": "1000",
              "restrictions": "developer plan, 30-day history limit"
            },
            "authentication": "api_key_required",
            "reliability": "high",
            "data_quality": "good",
            "latency": "1-3 seconds"
          },
          {
            "name": "Reddit API",
            "url": "https://www.reddit.com/dev/api/",
            "category": "sentiment_social",
            "data_types": [
              "posts",
              "comments",
              "subreddit_data"
            ],
            "free_tier": {
              "rate_limit": "60 requests/minute",
              "monthly_limit": "unlimited",
              "daily_limit": "unlimited",
              "restrictions": "oauth required"
            },
            "authentication": "oauth_required",
            "reliability": "medium",
            "data_quality": "variable",
            "latency": "2-5 seconds"
          },
          {
            "name": "Twitter API v2 Free",
            "url": "https://developer.twitter.com/en/docs/twitter-api",
            "category": "sentiment_social",
            "data_types": [
              "tweets",
              "user_data",
              "trends"
            ],
            "free_tier": {
              "rate_limit": "300 requests/15min",
              "monthly_limit": "500000 tweet reads",
              "daily_limit": "16666 tweet reads",
              "restrictions": "basic tier, limited endpoints"
            },
            "authentication": "bearer_token_required",
            "reliability": "high",
            "data_quality": "excellent",
            "latency": "1-3 seconds"
          }
        ]
      },
      "onchain_analytics": {
        "description": "Blockchain data, whale movements, exchange flows",
        "sources": [
          {
            "name": "Blockchain.info API",
            "url": "https://www.blockchain.com/api",
            "category": "onchain_analytics",
            "data_types": [
              "transactions",
              "addresses",
              "blocks",
              "charts"
            ],
            "free_tier": {
              "rate_limit": "unlimited",
              "monthly_limit": "unlimited",
              "daily_limit": "unlimited",
              "restrictions": "public data only"
            },
            "authentication": "none",
            "reliability": "high",
            "data_quality": "excellent",
            "latency": "1-3 seconds"
          },
          {
            "name": "BlockCypher API",
            "url": "https://www.blockcypher.com/dev/",
            "category": "onchain_analytics",
            "data_types": [
              "addresses",
              "transactions",
              "blocks"
            ],
            "free_tier": {
              "rate_limit": "3 requests/second",
              "monthly_limit": "unlimited",
              "daily_limit": "200000",
              "restrictions": "rate limited without token"
            },
            "authentication": "token_optional",
            "reliability": "high",
            "data_quality": "excellent",
            "latency": "500ms-2s"
          },
          {
            "name": "Whale Alert API",
            "url": "https://docs.whale-alert.io/",
            "category": "onchain_analytics",
            "data_types": [
              "large_transactions",
              "whale_movements"
            ],
            "free_tier": {
              "rate_limit": "10 calls/minute",
              "monthly_limit": "unlimited",
              "daily_limit": "unlimited",
              "restrictions": "free plan available"
            },
            "authentication": "api_key_required",
            "reliability": "high",
            "data_quality": "excellent",
            "latency": "1-2 seconds"
          }
        ]
      },
      "technical_analysis": {
        "description": "Technical indicators, charting data, trading signals",
        "sources": [
          {
            "name": "Twelve Data",
            "url": "https://twelvedata.com",
            "category": "technical_analysis",
            "data_types": [
              "ohlcv",
              "technical_indicators",
              "real_time"
            ],
            "free_tier": {
              "rate_limit": "8 requests/minute",
              "monthly_limit": "unlimited",
              "daily_limit": "800",
              "restrictions": "free plan"
            },
            "authentication": "api_key_required",
            "reliability": "high",
            "data_quality": "excellent",
            "latency": "1-2 seconds"
          },
          {
            "name": "Yahoo Finance API (Unofficial)",
            "url": "https://pypi.org/project/yfinance/",
            "category": "technical_analysis",
            "data_types": [
              "historical_data",
              "real_time",
              "fundamentals"
            ],
            "free_tier": {
              "rate_limit": "2000 requests/hour",
              "monthly_limit": "unlimited",
              "daily_limit": "unlimited",
              "restrictions": "unofficial, no guarantee"
            },
            "authentication": "none",
            "reliability": "medium",
            "data_quality": "good",
            "latency": "1-5 seconds"
          },
          {
            "name": "TradingView (Unofficial)",
            "url": "https://github.com/rongardF/tvdatafeed",
            "category": "technical_analysis",
            "data_types": [
              "charts",
              "indicators",
              "real_time"
            ],
            "free_tier": {
              "rate_limit": "variable",
              "monthly_limit": "unlimited",
              "daily_limit": "unlimited",
              "restrictions": "unofficial scraping"
            },
            "authentication": "none",
            "reliability": "low",
            "data_quality": "excellent",
            "latency": "3-10 seconds"
          }
        ]
      },
      "derivatives_futures": {
        "description": "Futures, options, funding rates, liquidations",
        "sources": [
          {
            "name": "Bybit Public API",
            "url": "https://bybit-exchange.github.io/docs/",
            "category": "derivatives_futures",
            "data_types": [
              "funding_rates",
              "open_interest",
              "liquidations"
            ],
            "free_tier": {
              "rate_limit": "120 requests/minute",
              "monthly_limit": "unlimited",
              "daily_limit": "unlimited",
              "restrictions": "public endpoints only"
            },
            "authentication": "none_for_public",
            "reliability": "high",
            "data_quality": "excellent",
            "latency": "200-800ms"
          },
          {
            "name": "Deribit Public API",
            "url": "https://docs.deribit.com/",
            "category": "derivatives_futures",
            "data_types": [
              "options",
              "futures",
              "volatility"
            ],
            "free_tier": {
              "rate_limit": "20 requests/second",
              "monthly_limit": "unlimited",
              "daily_limit": "unlimited",
              "restrictions": "public endpoints"
            },
            "authentication": "none_for_public",
            "reliability": "high",
            "data_quality": "excellent",
            "latency": "100-500ms"
          },
          {
            "name": "BitMEX Public API",
            "url": "https://www.bitmex.com/api/explorer/",
            "category": "derivatives_futures",
            "data_types": [
              "funding",
              "liquidations",
              "insurance"
            ],
            "free_tier": {
              "rate_limit": "300 requests/5min",
              "monthly_limit": "unlimited",
              "daily_limit": "unlimited",
              "restrictions": "public data only"
            },
            "authentication": "none_for_public",
            "reliability": "high",
            "data_quality": "excellent",
            "latency": "500ms-2s"
          }
        ]
      },
      "news_events": {
        "description": "Crypto news, events, regulatory updates",
        "sources": [
          {
            "name": "CoinDesk RSS",
            "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "category": "news_events",
            "data_types": [
              "news_articles",
              "headlines"
            ],
            "free_tier": {
              "rate_limit": "unlimited",
              "monthly_limit": "unlimited",
              "daily_limit": "unlimited",
              "restrictions": "rss only"
            },
            "authentication": "none",
            "reliability": "high",
            "data_quality": "excellent",
            "latency": "5-15 minutes delay"
          },
          {
            "name": "CryptoPanic Free",
            "url": "https://cryptopanic.com/developers/api/",
            "category": "news_events",
            "data_types": [
              "crypto_news",
              "sentiment",
              "votes"
            ],
            "free_tier": {
              "rate_limit": "5000 requests/month",
              "monthly_limit": "5000",
              "daily_limit": "166",
              "restrictions": "free plan"
            },
            "authentication": "api_key_required",
            "reliability": "high",
            "data_quality": "good",
            "latency": "1-3 seconds"
          },
          {
            "name": "CoinMarketCal API",
            "url": "https://coinmarketcal.com/en/doc/api",
            "category": "news_events",
            "data_types": [
              "events",
              "calendar",
              "announcements"
            ],
            "free_tier": {
              "rate_limit": "3 requests/second",
              "monthly_limit": "unlimited",
              "daily_limit": "unlimited",
              "restrictions": "free tier available"
            },
            "authentication": "api_key_required",
            "reliability": "medium",
            "data_quality": "good",
            "latency": "2-5 seconds"
          }
        ]
      },
      "macro_economic": {
        "description": "Federal Reserve data, economic indicators, macro trends",
        "sources": [
          {
            "name": "FRED API (Federal Reserve)",
            "url": "https://fred.stlouisfed.org/docs/api/",
            "category": "macro_economic",
            "data_types": [
              "interest_rates",
              "inflation",
              "economic_indicators"
            ],
            "free_tier": {
              "rate_limit": "120 requests/minute",
              "monthly_limit": "unlimited",
              "daily_limit": "unlimited",
              "restrictions": "none"
            },
            "authentication": "api_key_required",
            "reliability": "excellent",
            "data_quality": "excellent",
            "latency": "1-2 seconds"
          },
          {
            "name": "Economic Calendar API",
            "url": "https://tradingeconomics.com/api",
            "category": "macro_economic",
            "data_types": [
              "economic_events",
              "forecasts",
              "historical"
            ],
            "free_tier": {
              "rate_limit": "1000 requests/day",
              "monthly_limit": "30000",
              "daily_limit": "1000",
              "restrictions": "free tier"
            },
            "authentication": "api_key_required",
            "reliability": "high",
            "data_quality": "excellent",
            "latency": "2-4 seconds"
          }
        ]
      }
    },
    "implementation_guidance": {
      "rate_limiting": {
        "strategy": "Implement exponential backoff",
        "retry_logic": "3 attempts with 2^n second delays",
        "error_handling": "Graceful degradation with fallback sources"
      },
      "data_validation": {
        "cross_reference": "Always validate critical data against 2+ sources",
        "outlier_detection": "Flag data points >2 standard deviations from mean",
        "freshness_check": "Reject data older than defined thresholds"
      },
      "caching": {
        "strategy": "Cache stable data (prices: 5min, news: 15min, on-chain: 1hr)",
        "storage": "Redis recommended for real-time systems",
        "invalidation": "Time-based with manual refresh capability"
      },
      "prioritization": {
        "critical": [
          "price_data",
          "major_news",
          "whale_movements"
        ],
        "important": [
          "sentiment",
          "technical_indicators",
          "derivatives"
        ],
        "supplementary": [
          "social_media",
          "events",
          "macro_data"
        ]
      }
    }
  }
}  