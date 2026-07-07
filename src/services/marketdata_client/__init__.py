"""
Optional client for a private market-data warehouse.

Exposes commodities, COT positioning, warehouse stocks, the copper import-arb
window, and issuer market-cap history to the financial tools. Fully optional:
if the warehouse is not configured, callers degrade gracefully (see
``MarketDataWarehouse.configured`` / ``not_configured_payload``).
"""

from .client import (
    MarketDataUnavailable,
    MarketDataWarehouse,
    NOT_CONFIGURED_MESSAGE,
)

__all__ = ["MarketDataWarehouse", "MarketDataUnavailable", "NOT_CONFIGURED_MESSAGE"]
