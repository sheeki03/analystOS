"""
Financial Tools - All 19 migrated from Dexter TypeScript.

Tools are grouped by category:
1. Price Data (5 tools)
2. Fundamentals (4 tools)
3. Metrics & Estimates (3 tools)
4. Filings (4 tools)
5. Other Data (3 tools)

Each tool returns JSON string matching Dexter's formatToolResult format.
"""

import logging
from typing import Optional, List
from datetime import datetime

from .types import format_tool_result
from .constants import ITEMS_10K_MAP, ITEMS_10Q_MAP, format_items_description
from .crypto_resolver import (
    resolve_ticker_to_coin_id,
    calculate_fetch_days,
    slice_historical_data,
    resample_to_interval,
    get_available_crypto_tickers as _get_available_crypto_tickers,
)
from ..openbb import OpenBBClient
from ..marketdata_client import MarketDataWarehouse, MarketDataUnavailable

logger = logging.getLogger(__name__)

# Singleton OpenBB client
_openbb_client: Optional[OpenBBClient] = None


def _get_openbb_client() -> OpenBBClient:
    """Get or create OpenBB client singleton."""
    global _openbb_client
    if _openbb_client is None:
        _openbb_client = OpenBBClient()
    return _openbb_client


# Singleton client for the optional private market-data warehouse.
_marketdata_warehouse: Optional[MarketDataWarehouse] = None


def _get_warehouse() -> MarketDataWarehouse:
    """Get or create the market-data warehouse client singleton."""
    global _marketdata_warehouse
    if _marketdata_warehouse is None:
        _marketdata_warehouse = MarketDataWarehouse()
    return _marketdata_warehouse


def _warehouse_source(table: str) -> str:
    """A provenance label for warehouse-sourced rows (no external URL)."""
    return f"marketdata://warehouse/{table}"


def _warehouse_result(query_fn, table: str) -> str:
    """Run ``query_fn(warehouse)`` and format it as a tool result.

    Degrades gracefully (per analystOS's optional-provider style): if the
    warehouse is not configured or is unavailable, returns a clear payload
    instead of raising, so the app never crashes when the warehouse is absent.
    """
    warehouse = _get_warehouse()
    if not warehouse.configured:
        return format_tool_result(warehouse.not_configured_payload(), [])
    try:
        data = query_fn(warehouse)
    except MarketDataUnavailable as exc:
        return format_tool_result({"status": "unavailable", "reason": str(exc), "rows": []}, [])
    except Exception as exc:  # noqa: BLE001 - surface the query error, do not crash
        logger.error(f"marketdata warehouse query failed for {table}: {exc}")
        return format_tool_result({"status": "error", "reason": str(exc), "rows": []}, [])
    return format_tool_result(data, [_warehouse_source(table)])


# ==================== PRICE DATA ====================

def get_price_snapshot(ticker: str) -> str:
    """
    Fetches the most recent price snapshot for a specific stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")

    Returns:
        JSON string with price snapshot data and source URLs
    """
    client = _get_openbb_client()
    data = client.get_price_snapshot(ticker)
    url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}"
    return format_tool_result(data, [url])


def get_prices(
    ticker: str,
    start_date: str,
    end_date: str,
    interval: str = "day",
    interval_multiplier: int = 1,
    basis: str = "raw",
) -> str:
    """
    Retrieves historical price data for a stock over a specified date range.

    When the private market-data warehouse is configured it is preferred for
    daily bars (unadjusted EOD by default, or split-adjusted with
    basis="adjusted"); otherwise (or for non-daily intervals, or symbols not in
    the warehouse) this falls back to the existing OpenBB/yfinance path.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        start_date: Start date in YYYY-MM-DD format (required)
        end_date: End date in YYYY-MM-DD format (required)
        interval: Time interval - "minute", "day", "week", "month", "year" (default: "day")
        interval_multiplier: Multiplier for interval (default: 1)
        basis: "raw" (unadjusted, default) or "adjusted" (split-adjusted).
            Only applies to the warehouse path; ignored by the fallback.

    Returns:
        JSON string with list of price bars and source URLs
    """
    # Prefer the private warehouse for plain daily bars when it is configured.
    warehouse = _get_warehouse()
    if warehouse.configured and interval == "day" and interval_multiplier == 1:
        try:
            bars = warehouse.price_bars(ticker, start_date, end_date, basis=basis)
        except Exception as exc:  # noqa: BLE001 - warehouse hiccup -> fall back
            logger.warning(
                f"marketdata warehouse get_prices failed for {ticker}, "
                f"falling back to OpenBB: {exc}"
            )
            bars = None
        if bars:
            return format_tool_result(bars, [_warehouse_source("equities_eod")])
        # Configured but no rows (symbol not in the warehouse universe): fall back.

    client = _get_openbb_client()
    data = client.get_prices(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        interval_multiplier=interval_multiplier,
    )
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}"
    return format_tool_result(data, [url])


async def get_crypto_price_snapshot(ticker: str) -> str:
    """
    Fetches the most recent price snapshot for a specific cryptocurrency.

    LIMITATIONS:
    - Only USD pairs supported (BTC-USD, not BTC-ETH)
    - Returns close price only (no OHLC)
    - open and vwap fields return None

    Args:
        ticker: Crypto ticker symbol (e.g., "BTC-USD")

    Returns:
        JSON string with price snapshot data and source URLs
    """
    # Resolve ticker to CoinGecko coin_id (validates USD quote)
    coin_id = await resolve_ticker_to_coin_id(ticker)

    # Get price from CoinGecko
    from ..mcp.coingecko_client import CoinGeckoMCPClient
    client = CoinGeckoMCPClient()
    await client.connect()

    price_data = await client.get_coin_price(coin_id)

    # Normalize timestamp - can be datetime or string depending on code path
    timestamp = price_data.last_updated
    if hasattr(timestamp, 'isoformat'):
        timestamp = timestamp.isoformat()

    # Map to Dexter snapshot format
    snapshot = {
        "ticker": ticker,
        "open": None,   # CoinGecko doesn't provide OHLC in snapshot
        "high": price_data.high_24h,
        "low": price_data.low_24h,
        "close": price_data.current_price,  # Use current as "close"
        "volume": price_data.total_volume,
        "vwap": None,   # CoinGecko doesn't provide VWAP
        "timestamp": timestamp,
        # Additional CoinGecko fields (for enrichment)
        "market_cap": price_data.market_cap,
        "price_change_24h": price_data.price_change_24h,
        "price_change_percentage_24h": price_data.price_change_percentage_24h,
    }

    return format_tool_result(snapshot, [f"https://www.coingecko.com/en/coins/{coin_id}"])


async def get_crypto_prices(
    ticker: str,
    start_date: str,
    end_date: str,
    interval: str = "day",
    interval_multiplier: int = 1,
) -> str:
    """
    Retrieves historical price data for a cryptocurrency over a specified date range.

    LIMITATIONS:
    - Only USD pairs supported (BTC-ETH not supported)
    - minute interval raises ValueError (CoinGecko doesn't support it for long ranges)
    - Max 365 days from today (older data is impossible to retrieve)
    - Returns close price + volume only, NOT OHLC
    - Future end_date is silently clamped to today

    Args:
        ticker: Crypto ticker symbol (e.g., "BTC-USD")
        start_date: Start date in YYYY-MM-DD format (required)
        end_date: End date in YYYY-MM-DD format (required)
        interval: Time interval - "day", "week", "month", "year" (NOT minute)
        interval_multiplier: Multiplier for interval (default: 1)

    Returns:
        JSON string with list of price bars and source URLs
    """
    # Minute interval not supported
    if interval == "minute":
        raise ValueError(
            "minute interval not supported for crypto prices. "
            "Use 'day', 'week', 'month', or 'year'."
        )

    # Resolve ticker to CoinGecko coin_id (validates USD quote)
    coin_id = await resolve_ticker_to_coin_id(ticker)

    # Calculate how many days to fetch
    days_to_fetch, start_dt, end_dt = calculate_fetch_days(start_date, end_date)

    # Get historical data from CoinGecko
    from ..mcp.coingecko_client import CoinGeckoMCPClient
    client = CoinGeckoMCPClient()
    await client.connect()

    historical = await client.get_historical_data(coin_id, days_to_fetch)

    # Slice to requested date range
    sliced = slice_historical_data(historical, start_dt, end_dt)

    # ALWAYS resample - CoinGecko returns hourly for <=90 days even with interval="day"
    resampled = resample_to_interval(sliced, interval, interval_multiplier)

    # Convert to Dexter format
    prices = []
    for price in resampled.prices:
        price_entry = {
            "date": price.timestamp.strftime("%Y-%m-%d"),
            "close": price.price,
            # NOTE: CoinGecko doesn't provide OHLC, only close
            "open": None,
            "high": None,
            "low": None,
        }
        prices.append(price_entry)

    # Add volumes if available
    volume_map = {v.timestamp.strftime("%Y-%m-%d"): v.price for v in resampled.total_volumes}
    for price in prices:
        price["volume"] = volume_map.get(price["date"])

    return format_tool_result(prices, [f"https://www.coingecko.com/en/coins/{coin_id}"])


async def get_available_crypto_tickers() -> str:
    """
    Retrieves the list of available cryptocurrency tickers.

    Returns top 250 coins by market cap in Dexter format (SYMBOL-USD).
    De-duplicates symbols (keeps highest market cap coin for each symbol).

    Returns:
        JSON string with list of ticker strings
    """
    tickers = await _get_available_crypto_tickers()
    return format_tool_result(tickers, ["https://www.coingecko.com/en"])


# ==================== FUNDAMENTALS ====================

def get_income_statements(
    ticker: str,
    period: str = "annual",
    limit: int = 10,
    report_period_gte: Optional[str] = None,
    report_period_lte: Optional[str] = None,
    report_period_gt: Optional[str] = None,
    report_period_lt: Optional[str] = None,
) -> str:
    """
    Fetches a company's income statements.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        period: "annual", "quarterly", or "ttm" (default: "annual")
        limit: Number of periods to return (default: 10)
        report_period_gte: Filter for periods on or after this date (YYYY-MM-DD)
        report_period_lte: Filter for periods on or before this date (YYYY-MM-DD)
        report_period_gt: Filter for periods after this date (YYYY-MM-DD)
        report_period_lt: Filter for periods before this date (YYYY-MM-DD)

    Returns:
        JSON string with income statements and source URLs
    """
    client = _get_openbb_client()
    filters = {
        k: v for k, v in {
            "report_period_gte": report_period_gte,
            "report_period_lte": report_period_lte,
            "report_period_gt": report_period_gt,
            "report_period_lt": report_period_lt,
        }.items() if v is not None
    }
    data = client.get_income_statements(ticker, period, limit, **filters)
    url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}"
    return format_tool_result(data, [url])


def get_balance_sheets(
    ticker: str,
    period: str = "annual",
    limit: int = 10,
    report_period_gte: Optional[str] = None,
    report_period_lte: Optional[str] = None,
    report_period_gt: Optional[str] = None,
    report_period_lt: Optional[str] = None,
) -> str:
    """
    Retrieves a company's balance sheets.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        period: "annual", "quarterly", or "ttm" (default: "annual")
        limit: Number of periods to return (default: 10)
        report_period_gte: Filter for periods on or after this date (YYYY-MM-DD)
        report_period_lte: Filter for periods on or before this date (YYYY-MM-DD)
        report_period_gt: Filter for periods after this date (YYYY-MM-DD)
        report_period_lt: Filter for periods before this date (YYYY-MM-DD)

    Returns:
        JSON string with balance sheets and source URLs
    """
    client = _get_openbb_client()
    filters = {
        k: v for k, v in {
            "report_period_gte": report_period_gte,
            "report_period_lte": report_period_lte,
            "report_period_gt": report_period_gt,
            "report_period_lt": report_period_lt,
        }.items() if v is not None
    }
    data = client.get_balance_sheets(ticker, period, limit, **filters)
    url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}"
    return format_tool_result(data, [url])


def get_cash_flow_statements(
    ticker: str,
    period: str = "annual",
    limit: int = 10,
    report_period_gte: Optional[str] = None,
    report_period_lte: Optional[str] = None,
    report_period_gt: Optional[str] = None,
    report_period_lt: Optional[str] = None,
) -> str:
    """
    Retrieves a company's cash flow statements.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        period: "annual", "quarterly", or "ttm" (default: "annual")
        limit: Number of periods to return (default: 10)
        report_period_gte: Filter for periods on or after this date (YYYY-MM-DD)
        report_period_lte: Filter for periods on or before this date (YYYY-MM-DD)
        report_period_gt: Filter for periods after this date (YYYY-MM-DD)
        report_period_lt: Filter for periods before this date (YYYY-MM-DD)

    Returns:
        JSON string with cash flow statements and source URLs
    """
    client = _get_openbb_client()
    filters = {
        k: v for k, v in {
            "report_period_gte": report_period_gte,
            "report_period_lte": report_period_lte,
            "report_period_gt": report_period_gt,
            "report_period_lt": report_period_lt,
        }.items() if v is not None
    }
    data = client.get_cash_flow_statements(ticker, period, limit, **filters)
    url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}"
    return format_tool_result(data, [url])


def get_all_financial_statements(
    ticker: str,
    period: str = "annual",
    limit: int = 10,
    report_period_gte: Optional[str] = None,
    report_period_lte: Optional[str] = None,
    report_period_gt: Optional[str] = None,
    report_period_lt: Optional[str] = None,
) -> str:
    """
    Retrieves all three financial statements (income, balance, cash flow) in one call.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        period: "annual", "quarterly", or "ttm" (default: "annual")
        limit: Number of periods to return (default: 10)
        report_period_gte: Filter for periods on or after this date (YYYY-MM-DD)
        report_period_lte: Filter for periods on or before this date (YYYY-MM-DD)
        report_period_gt: Filter for periods after this date (YYYY-MM-DD)
        report_period_lt: Filter for periods before this date (YYYY-MM-DD)

    Returns:
        JSON string with all financial statements and source URLs
    """
    client = _get_openbb_client()
    filters = {
        k: v for k, v in {
            "report_period_gte": report_period_gte,
            "report_period_lte": report_period_lte,
            "report_period_gt": report_period_gt,
            "report_period_lt": report_period_lt,
        }.items() if v is not None
    }
    data = client.get_all_financial_statements(ticker, period, limit, **filters)
    url = f"https://financialmodelingprep.com/api/v3/financial-statements/{ticker}"
    return format_tool_result(data, [url])


# ==================== METRICS & ESTIMATES ====================

def get_financial_metrics_snapshot(ticker: str) -> str:
    """
    Fetches a snapshot of the most current financial metrics for a company.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")

    Returns:
        JSON string with metrics snapshot and source URLs
    """
    client = _get_openbb_client()
    data = client.get_financial_metrics_snapshot(ticker)
    url = f"https://financialmodelingprep.com/api/v3/key-metrics/{ticker}"
    return format_tool_result(data, [url])


def get_financial_metrics(
    ticker: str,
    period: str = "ttm",
    limit: int = 4,
    report_period: Optional[str] = None,
    report_period_gte: Optional[str] = None,
    report_period_lte: Optional[str] = None,
    report_period_gt: Optional[str] = None,
    report_period_lt: Optional[str] = None,
) -> str:
    """
    Retrieves historical financial metrics for a company.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        period: "annual", "quarterly", or "ttm" (default: "ttm")
        limit: Number of periods to return (default: 4)
        report_period: Filter for exact report period date (YYYY-MM-DD)
        report_period_gte: Filter for periods on or after this date
        report_period_lte: Filter for periods on or before this date
        report_period_gt: Filter for periods after this date
        report_period_lt: Filter for periods before this date

    Returns:
        JSON string with financial metrics and source URLs
    """
    client = _get_openbb_client()
    filters = {
        k: v for k, v in {
            "report_period": report_period,
            "report_period_gte": report_period_gte,
            "report_period_lte": report_period_lte,
            "report_period_gt": report_period_gt,
            "report_period_lt": report_period_lt,
        }.items() if v is not None
    }
    data = client.get_financial_metrics(ticker, period, limit, **filters)
    url = f"https://financialmodelingprep.com/api/v3/key-metrics/{ticker}"
    return format_tool_result(data, [url])


def get_analyst_estimates(
    ticker: str,
    period: str = "annual",
) -> str:
    """
    Retrieves analyst estimates for a given company ticker.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        period: "annual" or "quarterly" (default: "annual")

    Returns:
        JSON string with analyst estimates and source URLs
    """
    client = _get_openbb_client()
    data = client.get_analyst_estimates(ticker, period)
    url = f"https://financialmodelingprep.com/api/v3/analyst-estimates/{ticker}"
    return format_tool_result(data, [url])


# ==================== FILINGS ====================

def get_filings(
    ticker: str,
    filing_type: Optional[str] = None,
    limit: int = 10,
) -> str:
    """
    Retrieves metadata for SEC filings for a company.

    NOTE: This returns metadata only, not full content. Use get_10K_filing_items,
    get_10Q_filing_items, or get_8K_filing_items for actual content.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        filing_type: Optional - "10-K", "10-Q", or "8-K"
        limit: Number of filings to return (default: 10)

    Returns:
        JSON string with filing metadata and source URLs
    """
    client = _get_openbb_client()
    data = client.get_filings(ticker, filing_type, limit)
    url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type={filing_type or ''}"
    return format_tool_result(data, [url])


def get_10k_filing_items(
    ticker: str,
    year: int,
    item: Optional[List[str]] = None,
) -> str:
    """
    Retrieves specific sections (items) from a company's 10-K annual report.

    Valid items: Item-1 (Business), Item-1A (Risk Factors), Item-7 (MD&A),
    Item-8 (Financial Statements), etc.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        year: Year of the 10-K filing (e.g., 2023)
        item: Optional list of specific items to retrieve

    Returns:
        JSON string with filing items and source URLs
    """
    client = _get_openbb_client()
    data = client.get_10k_filing_items(ticker, year, item)
    url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K"
    return format_tool_result(data, [url])


def get_10q_filing_items(
    ticker: str,
    year: int,
    quarter: int,
    item: Optional[List[str]] = None,
) -> str:
    """
    Retrieves specific sections (items) from a company's 10-Q quarterly report.

    Valid items: Item-1 (Financial Statements), Item-2 (MD&A),
    Item-3 (Market Risk), Item-4 (Controls and Procedures).

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        year: Year of the 10-Q filing (e.g., 2023)
        quarter: Quarter (1, 2, 3, or 4)
        item: Optional list of specific items to retrieve

    Returns:
        JSON string with filing items and source URLs
    """
    client = _get_openbb_client()
    data = client.get_10q_filing_items(ticker, year, quarter, item)
    url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-Q"
    return format_tool_result(data, [url])


def get_8k_filing_items(
    ticker: str,
    accession_number: str,
) -> str:
    """
    Retrieves specific sections (items) from a company's 8-K current report.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        accession_number: SEC accession number (e.g., "0000320193-24-000123")

    Returns:
        JSON string with filing items and source URLs
    """
    client = _get_openbb_client()
    data = client.get_8k_filing_items(ticker, accession_number)
    url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=8-K"
    return format_tool_result(data, [url])


# ==================== OTHER DATA ====================

def get_news(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 10,
) -> str:
    """
    Retrieves recent news articles for a given company ticker.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        limit: Number of articles to return (default: 10, max: 100)

    Returns:
        JSON string with news articles and source URLs
    """
    client = _get_openbb_client()
    data = client.get_news(ticker, start_date, end_date, limit)
    url = f"https://financialmodelingprep.com/api/v3/stock_news?tickers={ticker}"
    return format_tool_result(data, [url])


def get_insider_trades(
    ticker: str,
    limit: int = 100,
    filing_date: Optional[str] = None,
    filing_date_gte: Optional[str] = None,
    filing_date_lte: Optional[str] = None,
    filing_date_gt: Optional[str] = None,
    filing_date_lt: Optional[str] = None,
) -> str:
    """
    Retrieves insider trading transactions for a given company ticker.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        limit: Number of trades to return (default: 100, max: 1000)
        filing_date: Exact filing date filter (YYYY-MM-DD)
        filing_date_gte: Filing date >= this date
        filing_date_lte: Filing date <= this date
        filing_date_gt: Filing date > this date
        filing_date_lt: Filing date < this date

    Returns:
        JSON string with insider trades and source URLs
    """
    client = _get_openbb_client()
    filters = {
        k: v for k, v in {
            "filing_date": filing_date,
            "filing_date_gte": filing_date_gte,
            "filing_date_lte": filing_date_lte,
            "filing_date_gt": filing_date_gt,
            "filing_date_lt": filing_date_lt,
        }.items() if v is not None
    }
    data = client.get_insider_trades(ticker, limit, **filters)
    url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=4"
    return format_tool_result(data, [url])


def get_segmented_revenues(
    ticker: str,
    period: str = "annual",
    limit: int = 10,
) -> str:
    """
    Provides a detailed breakdown of a company's revenue by operating segments.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        period: "annual" or "quarterly" (default: "annual")
        limit: Number of periods to return (default: 10)

    Returns:
        JSON string with segmented revenues and source URLs
    """
    client = _get_openbb_client()
    data = client.get_segmented_revenues(ticker, period, limit)
    url = f"https://financialmodelingprep.com/api/v4/revenue-product-segmentation/{ticker}"
    return format_tool_result(data, [url])


# ==================== MARKET-DATA WAREHOUSE ====================
# These tools read from an optional, separately-maintained private market-data
# warehouse (commodities, COT positioning, warehouse stocks, copper import-arb,
# issuer market caps). When it is not configured they return a clear
# "unavailable" payload rather than raising.

def get_commodity_prices(
    product_root: Optional[str] = None,
    exchange: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 500,
) -> str:
    """
    Retrieves historical daily futures prices from the private market-data warehouse.

    Args:
        product_root: Product root, e.g. "cu" (SHFE copper), "HG" (COMEX copper)
        exchange: Exchange code, e.g. "SHFE", "INE", "CME"
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Max rows to return (default: 500)

    Returns:
        JSON string with per-contract daily rows (settle/close, volume, open interest)
    """
    return _warehouse_result(
        lambda w: w.commodity_prices(product_root, exchange, start_date, end_date, limit),
        "futures_daily_all",
    )


def get_futures_voi(
    product_root: Optional[str] = None,
    exchange: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 500,
) -> str:
    """
    Retrieves a per-product futures volume and open-interest (VOI) series.

    Volume and open interest are summed across contracts per trade date, giving
    an open-interest / volume trend for a product (e.g. SHFE copper OI over time).

    Args:
        product_root: Product root, e.g. "cu" for SHFE copper
        exchange: Exchange code, e.g. "SHFE"
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Max rows to return (default: 500)

    Returns:
        JSON string with total volume and open interest per product per date
    """
    return _warehouse_result(
        lambda w: w.futures_voi(product_root, exchange, start_date, end_date, limit),
        "futures_daily_all",
    )


def get_cot_positioning(
    market_code: Optional[str] = None,
    dataset: Optional[str] = None,
    limit: int = 300,
) -> str:
    """
    Retrieves CFTC Commitments of Traders (COT) positioning for a market.

    Returns weekly long/short positions plus positioning percentiles computed
    over each series' own history.

    Args:
        market_code: CFTC market code for the commodity
        dataset: Optional dataset family (e.g. legacy vs disaggregated)
        limit: Max rows to return per section (default: 300)

    Returns:
        JSON string with "weekly" positions and "percentiles"
    """
    return _warehouse_result(
        lambda w: w.cot_positioning(market_code, dataset, limit),
        "cot_weekly",
    )


def get_warehouse_stocks(
    metal: Optional[str] = "copper",
    exchange: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 500,
) -> str:
    """
    Retrieves exchange warehouse metal-stock levels (tonnes), incl. copper history.

    Args:
        metal: Metal name (default: "copper")
        exchange: Optional exchange filter (e.g. "LME", "SHFE")
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Max rows to return per section (default: 500)

    Returns:
        JSON string with "stocks" rows and "copper_history" rows
    """
    return _warehouse_result(
        lambda w: w.warehouse_stocks(metal, exchange, start_date, end_date, limit),
        "warehouse_stocks",
    )


def get_arb_window(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 500,
) -> str:
    """
    Retrieves the China copper import-arbitrage window (import parity vs SHFE).

    Rows are indicative and carry a `param_status` field describing any missing
    or stale inputs (the panel is greyed out rather than fabricated when inputs
    are absent).

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Max rows to return (default: 500)

    Returns:
        JSON string with import-arb rows (CNY/tonne) and param_status
    """
    return _warehouse_result(
        lambda w: w.arb_window(start_date, end_date, limit),
        "import_arb",
    )


def get_market_cap(
    ticker: Optional[str] = None,
    cik: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 5000,
) -> str:
    """
    Retrieves issuer-level market-capitalization history (price x shares outstanding).

    Args:
        ticker: Stock ticker symbol (e.g. "NVDA"); resolved to an issuer
        cik: SEC CIK (alternative to ticker)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Max rows to return (default: 5000)

    Returns:
        JSON string with the issuer market-cap series (economic series)
    """
    return _warehouse_result(
        lambda w: w.market_cap(cik, ticker, start_date, end_date, limit),
        "issuer_market_cap",
    )


# ==================== TOOL MAP ====================

# All finance tools as a list (matching Dexter's FINANCE_TOOLS array)
FINANCIAL_TOOLS = [
    # Price Data
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
    # Other Data
    get_news,
    get_insider_trades,
    get_segmented_revenues,
    # Market-Data Warehouse (optional private source)
    get_commodity_prices,
    get_futures_voi,
    get_cot_positioning,
    get_warehouse_stocks,
    get_arb_window,
    get_market_cap,
]

# Tool name to function map (for router)
FINANCIAL_TOOL_MAP = {
    "get_price_snapshot": get_price_snapshot,
    "get_prices": get_prices,
    "get_crypto_price_snapshot": get_crypto_price_snapshot,
    "get_crypto_prices": get_crypto_prices,
    "get_available_crypto_tickers": get_available_crypto_tickers,
    "get_income_statements": get_income_statements,
    "get_balance_sheets": get_balance_sheets,
    "get_cash_flow_statements": get_cash_flow_statements,
    "get_all_financial_statements": get_all_financial_statements,
    "get_financial_metrics_snapshot": get_financial_metrics_snapshot,
    "get_financial_metrics": get_financial_metrics,
    "get_analyst_estimates": get_analyst_estimates,
    "get_filings": get_filings,
    "get_10K_filing_items": get_10k_filing_items,  # Note: Dexter uses 10K not 10k
    "get_10Q_filing_items": get_10q_filing_items,  # Note: Dexter uses 10Q not 10q
    "get_8K_filing_items": get_8k_filing_items,    # Note: Dexter uses 8K not 8k
    "get_news": get_news,
    "get_insider_trades": get_insider_trades,
    "get_segmented_revenues": get_segmented_revenues,
    # Market-Data Warehouse (optional private source)
    "get_commodity_prices": get_commodity_prices,
    "get_futures_voi": get_futures_voi,
    "get_cot_positioning": get_cot_positioning,
    "get_warehouse_stocks": get_warehouse_stocks,
    "get_arb_window": get_arb_window,
    "get_market_cap": get_market_cap,
}
