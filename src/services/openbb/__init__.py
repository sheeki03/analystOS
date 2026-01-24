"""
OpenBB Platform Integration

Provides unified access to equity data via OpenBB Platform:
- Prices (FMP)
- Fundamentals (FMP)
- Filings (SEC EDGAR)
- News (Finnhub)
- Metrics and Estimates
"""

from .client import OpenBBClient
from .config import OpenBBConfig

__all__ = ['OpenBBClient', 'OpenBBConfig']
