"""
Configuration for OpenBB Platform integration.

Supported Providers:
- yfinance: Yahoo Finance (free, no API key required) - prices, fundamentals
- fmp: Financial Modeling Prep (paid, requires legacy subscription as of Aug 2025)
- sec: SEC EDGAR (free, no API key required) - filings only
- finnhub: Finnhub (free tier available) - news
- intrinio: Intrinio (paid) - comprehensive data
- polygon: Polygon.io (paid) - real-time data
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class OpenBBConfig:
    """Configuration for OpenBB Platform."""

    # OpenBB Personal Access Token (optional, for higher rate limits)
    openbb_pat: Optional[str] = None

    # Provider API keys (used by OpenBB internally)
    fmp_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None

    # Data provider preferences
    # NOTE: FMP free tier restricted as of Aug 2025 for new accounts
    # Using yfinance (Yahoo Finance) as default - free, no key required
    default_equity_provider: str = "yfinance"  # Changed from "fmp" - free alternative
    default_news_provider: str = "yfinance"    # yfinance has basic news
    default_filings_provider: str = "sec"       # SEC EDGAR - always free

    # Fallback providers if primary fails
    fallback_equity_provider: str = "fmp"  # Try FMP if yfinance fails

    @classmethod
    def from_env(cls) -> 'OpenBBConfig':
        """Load configuration from environment variables."""
        # Allow provider override via environment
        default_provider = os.getenv("OPENBB_DEFAULT_PROVIDER", "yfinance")

        return cls(
            openbb_pat=os.getenv("OPENBB_PAT"),
            fmp_api_key=os.getenv("FMP_API_KEY"),
            finnhub_api_key=os.getenv("FINNHUB_API_KEY"),
            default_equity_provider=default_provider,
        )

    def validate(self) -> bool:
        """
        Validate configuration.

        Note: FMP key is no longer strictly required since we default to yfinance.
        If using FMP provider, the key is required.
        """
        if self.default_equity_provider == "fmp" and not self.fmp_api_key:
            raise ValueError(
                "FMP_API_KEY is required when using 'fmp' provider. "
                "Set OPENBB_DEFAULT_PROVIDER=yfinance to use free Yahoo Finance instead."
            )
        return True

    def get_provider_for_function(self, function_type: str) -> str:
        """Get the appropriate provider for a function type."""
        provider_map = {
            "price": self.default_equity_provider,
            "fundamental": self.default_equity_provider,
            "news": self.default_news_provider,
            "filings": self.default_filings_provider,
        }
        return provider_map.get(function_type, self.default_equity_provider)
