"""
Financial Tools Service

Migrated from Dexter TypeScript financial tools to Python.
Provides 19 financial data tools with OpenBB (equities) and CoinGecko (crypto) backends.
"""

from .types import format_tool_result
from .constants import ITEMS_10K_MAP, ITEMS_10Q_MAP, format_items_description
from .tools import (
    # Price tools
    get_price_snapshot,
    get_prices,
    get_crypto_price_snapshot,
    get_crypto_prices,
    get_available_crypto_tickers,
    # Fundamentals
    get_income_statements,
    get_balance_sheets,
    get_cash_flow_statements,
    get_all_financial_statements,
    # Metrics & Estimates
    get_financial_metrics_snapshot,
    get_financial_metrics,
    get_analyst_estimates,
    # Filings
    get_filings,
    get_10k_filing_items,
    get_10q_filing_items,
    get_8k_filing_items,
    # Other
    get_news,
    get_insider_trades,
    get_segmented_revenues,
    # Tool collections
    FINANCIAL_TOOLS,
    FINANCIAL_TOOL_MAP,
)
from .schemas import build_tool_schemas
from .router import FinancialSearchRouter, financial_search
from .crypto_resolver import (
    resolve_ticker_to_coin_id,
    parse_ticker,
    validate_date_range,
    calculate_fetch_days,
    slice_historical_data,
    resample_to_interval,
    TICKER_TO_COIN_ID,
    MAX_DAYS,
)

__all__ = [
    # Types
    'format_tool_result',
    # Constants
    'ITEMS_10K_MAP',
    'ITEMS_10Q_MAP',
    'format_items_description',
    # Price tools
    'get_price_snapshot',
    'get_prices',
    'get_crypto_price_snapshot',
    'get_crypto_prices',
    'get_available_crypto_tickers',
    # Fundamentals
    'get_income_statements',
    'get_balance_sheets',
    'get_cash_flow_statements',
    'get_all_financial_statements',
    # Metrics & Estimates
    'get_financial_metrics_snapshot',
    'get_financial_metrics',
    'get_analyst_estimates',
    # Filings
    'get_filings',
    'get_10k_filing_items',
    'get_10q_filing_items',
    'get_8k_filing_items',
    # Other
    'get_news',
    'get_insider_trades',
    'get_segmented_revenues',
    # Tool collections
    'FINANCIAL_TOOLS',
    'FINANCIAL_TOOL_MAP',
    # Schemas
    'build_tool_schemas',
    # Router
    'FinancialSearchRouter',
    'financial_search',
    # Crypto resolver
    'resolve_ticker_to_coin_id',
    'parse_ticker',
    'validate_date_range',
    'calculate_fetch_days',
    'slice_historical_data',
    'resample_to_interval',
    'TICKER_TO_COIN_ID',
    'MAX_DAYS',
]
