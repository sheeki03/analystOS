"""
Resolves Dexter crypto ticker format to CoinGecko coin_id.
BTC-USD -> bitcoin, ETH-USD -> ethereum, etc.

LIMITATION: Only USD pairs supported. BTC-ETH and similar crypto-to-crypto
pairs are not supported by this implementation since CoinGecko returns USD prices only.
"""

from datetime import datetime, timedelta
from typing import Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)

# Static map for common tickers (from Dexter crypto.ts)
TICKER_TO_COIN_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "XRP": "ripple",
    "ADA": "cardano",
    "AVAX": "avalanche-2",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "AAVE": "aave",
    "MKR": "maker",
    "COMP": "compound-governance-token",
    "RNDR": "render-token",
    "TAO": "bittensor",
    "AKT": "akash-network",
    "DOGE": "dogecoin",
    "SHIB": "shiba-inu",
    "LTC": "litecoin",
    "BCH": "bitcoin-cash",
    "ATOM": "cosmos",
    "FIL": "filecoin",
    "NEAR": "near",
    "APT": "aptos",
    "ARB": "arbitrum",
    "OP": "optimism",
    "IMX": "immutable-x",
    "INJ": "injective-protocol",
    "TIA": "celestia",
    "SUI": "sui",
    "SEI": "sei-network",
    "PEPE": "pepe",
    "WIF": "dogwifcoin",
    "BONK": "bonk",
    "JUP": "jupiter-exchange-solana",
    "PYTH": "pyth-network",
    "JTO": "jito-governance-token",
    "HBAR": "hedera-hashgraph",
    "ICP": "internet-computer",
    "VET": "vechain",
    "ALGO": "algorand",
    "XLM": "stellar",
    "XMR": "monero",
    "ETC": "ethereum-classic",
    "SAND": "the-sandbox",
    "MANA": "decentraland",
    "CRV": "curve-dao-token",
    "SUSHI": "sushi",
    "YFI": "yearn-finance",
    "CAKE": "pancakeswap-token",
    "RUNE": "thorchain",
    "BNB": "binancecoin",
    "USDT": "tether",
    "USDC": "usd-coin",
    "DAI": "dai",
    "TRX": "tron",
    "TON": "the-open-network",
}

# Top 250 tickers cache for get_available_crypto_tickers
_AVAILABLE_TICKERS_CACHE: Optional[List[str]] = None
_CACHE_TIMESTAMP: Optional[datetime] = None

# CoinGecko practical limit for daily data
MAX_DAYS = 365


def parse_ticker(ticker: str) -> Tuple[str, str]:
    """
    Parse Dexter ticker format into (base, quote).
    BTC-USD -> (BTC, USD), BTC-ETH -> (BTC, ETH), BTC -> (BTC, USD)

    Args:
        ticker: Ticker string like "BTC-USD" or "BTC"

    Returns:
        Tuple of (base_currency, quote_currency)
    """
    ticker = ticker.upper()
    if "-" in ticker:
        parts = ticker.split("-")
        return parts[0], parts[1]
    return ticker, "USD"


async def resolve_ticker_to_coin_id(ticker: str) -> str:
    """
    Resolve Dexter ticker format to CoinGecko coin_id.

    Resolution priority:
    1. Static TICKER_TO_COIN_ID map (fast, accurate)
    2. Exact symbol match from markets list (avoids ambiguity)
    3. search_coins fallback (last resort, may pick wrong asset)

    Args:
        ticker: Ticker string like "BTC-USD" or "BTC"

    Returns:
        CoinGecko coin_id (e.g., "bitcoin")

    Raises:
        ValueError: For non-USD quote currencies or unknown tickers
    """
    base, quote = parse_ticker(ticker)

    # Only USD pairs supported
    if quote != "USD":
        raise ValueError(
            f"Only USD-quoted pairs supported. Got {ticker}. "
            f"Crypto-to-crypto pairs like BTC-ETH are not supported."
        )

    # 1. Check static map first (most reliable)
    if base in TICKER_TO_COIN_ID:
        return TICKER_TO_COIN_ID[base]

    # Import here to avoid circular dependency
    from ..mcp.coingecko_client import CoinGeckoMCPClient
    client = CoinGeckoMCPClient()
    await client.connect()

    # 2. Try exact symbol match from markets list (avoids symbol collisions)
    try:
        coins = await client.get_coins_markets(per_page=250)
        for coin in coins:
            if coin.symbol.upper() == base:
                return coin.id
    except Exception as e:
        logger.warning(f"Failed to fetch markets list: {e}")
        pass  # Fall through to search

    # 3. Last resort: search_coins (may pick wrong asset on symbol collision)
    try:
        results = await client.search_coins(base)
        if results:
            # Prefer exact symbol match in search results
            for r in results:
                if r.symbol.upper() == base:
                    return r.id
            # Fall back to first result
            return results[0].id
    except Exception as e:
        logger.warning(f"Search failed: {e}")

    raise ValueError(f"Unknown crypto ticker: {ticker}")


def validate_date_range(start_date: str, end_date: str) -> Tuple[datetime, datetime]:
    """
    Validate and parse date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Tuple of (start_datetime, end_datetime)

    Raises:
        ValueError: For invalid date ranges:
        - start_date > end_date
        - future start_date
        - ranges exceeding MAX_DAYS
        - fetch distance (now - start_date) exceeding MAX_DAYS
    """
    now = datetime.now()
    today = now.date()

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    # Use end-of-day for end_date to include all data on that day
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

    # Validate: start_date <= end_date
    if start_dt > end_dt:
        raise ValueError(f"start_date ({start_date}) cannot be after end_date ({end_date})")

    # Validate: no future start dates (allow up to today)
    if start_dt.date() > today:
        raise ValueError(f"start_date ({start_date}) cannot be in the future")

    # Clamp end_date to today if in the future (silent, not an error)
    if end_dt.date() > today:
        end_dt = now

    # Validate: range within MAX_DAYS
    days_in_range = (end_dt - start_dt).days + 1
    if days_in_range > MAX_DAYS:
        raise ValueError(
            f"Date range ({days_in_range} days) exceeds maximum of {MAX_DAYS} days. "
            f"Please use a shorter range."
        )

    # CRITICAL: Also validate fetch distance (now - start_date)
    # CoinGecko's `days` parameter is "days from now", not a date range.
    # Even if the requested range is <=365 days, if start_date is far in the past,
    # we'd need to fetch more than MAX_DAYS.
    days_from_now = (now - start_dt).days + 1
    if days_from_now > MAX_DAYS:
        raise ValueError(
            f"start_date ({start_date}) is too far in the past. "
            f"CoinGecko only supports fetching up to {MAX_DAYS} days from now. "
            f"Please use a more recent start_date."
        )

    return start_dt, end_dt


def calculate_fetch_days(start_date: str, end_date: str) -> Tuple[int, datetime, datetime]:
    """
    Calculate how many days to fetch from CoinGecko and the slice range.

    CoinGecko's historical API returns data from (now - days) to now.
    If end_date is in the past, we need to fetch more data and slice.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Tuple of (days_to_fetch, slice_start, slice_end)

    Raises:
        ValueError: If range exceeds MAX_DAYS or start_date is too old
    """
    # Validate first (raises if invalid - includes fetch distance check)
    start_dt, end_dt = validate_date_range(start_date, end_date)

    now = datetime.now()

    # Calculate days from now to start_date (fetch this much)
    # This is guaranteed to be <= MAX_DAYS due to validation above
    days_to_fetch = (now - start_dt).days + 1

    return days_to_fetch, start_dt, end_dt


def slice_historical_data(
    historical_data,
    start_dt: datetime,
    end_dt: datetime
):
    """
    Slice CoinGecko HistoricalData to requested date range.

    NOTE: CoinGeckoMCPClient.get_historical_data() returns HistoricalData objects
    containing HistoricalPrice objects (with .timestamp and .price attributes),
    NOT raw [timestamp_ms, price] arrays.

    Uses date-only comparisons (not datetime) to include all data points
    on start_date and end_date regardless of time.

    Args:
        historical_data: HistoricalData object from CoinGecko client
        start_dt: Start datetime (inclusive)
        end_dt: End datetime (inclusive)

    Returns:
        New HistoricalData object with filtered data
    """
    from ..mcp.models import HistoricalData, HistoricalPrice

    # Use date-only comparisons to include all data on boundary dates
    start_date = start_dt.date()
    end_date = end_dt.date()

    # Filter prices to date range (inclusive on both ends)
    filtered_prices = [
        p for p in historical_data.prices
        if start_date <= p.timestamp.date() <= end_date
    ]

    filtered_market_caps = [
        m for m in historical_data.market_caps
        if start_date <= m.timestamp.date() <= end_date
    ]

    filtered_volumes = [
        v for v in historical_data.total_volumes
        if start_date <= v.timestamp.date() <= end_date
    ]

    return HistoricalData(
        coin_id=historical_data.coin_id,
        prices=filtered_prices,
        market_caps=filtered_market_caps,
        total_volumes=filtered_volumes
    )


def resample_to_interval(
    historical_data,
    interval: str,
    interval_multiplier: int = 1
):
    """
    ALWAYS resample HistoricalData to specified interval.

    IMPORTANT: CoinGecko returns hourly data for ranges <=90 days even when
    requesting daily. This function MUST be called even for interval="day"
    to ensure consistent daily aggregation matching Dexter's behavior.

    Supported intervals: day, week, month, year
    (minute NOT supported - raises error before this is called)

    For each bucket, returns:
    - price: last close price in bucket
    - volume: sum of volumes in bucket

    NOTE: Returns CLOSE prices only, NOT OHLC.

    Args:
        historical_data: HistoricalData object from CoinGecko client
        interval: One of 'day', 'week', 'month', 'year'
        interval_multiplier: Multiplier for interval (e.g., 2 for 2-day)

    Returns:
        New HistoricalData object with resampled data
    """
    from ..mcp.models import HistoricalData, HistoricalPrice
    import pandas as pd

    if not historical_data.prices:
        return historical_data

    # Convert to pandas for resampling
    df = pd.DataFrame([
        {'timestamp': p.timestamp, 'price': p.price}
        for p in historical_data.prices
    ])
    df.set_index('timestamp', inplace=True)

    # Map interval to pandas resample rule
    # Use 'M' and 'A' for broader pandas compatibility (not ME/YE)
    interval_map = {
        'day': 'D',
        'week': 'W',
        'month': 'M',   # Month end (works in older pandas)
        'year': 'A',    # Year end (alias, works in older pandas)
    }

    rule = interval_map.get(interval, 'D')

    # Apply multiplier (e.g., 2D for 2-day intervals)
    if interval_multiplier > 1:
        rule = f"{interval_multiplier}{rule}"

    # Resample: last price for close, sum of volumes
    resampled = df.resample(rule).last().dropna()

    # Convert back to HistoricalPrice objects
    resampled_prices = [
        HistoricalPrice(timestamp=ts.to_pydatetime(), price=row['price'])
        for ts, row in resampled.iterrows()
    ]

    # Similarly resample volumes if present
    resampled_volumes = []
    if historical_data.total_volumes:
        vol_df = pd.DataFrame([
            {'timestamp': v.timestamp, 'volume': v.price}  # price field holds volume
            for v in historical_data.total_volumes
        ])
        vol_df.set_index('timestamp', inplace=True)
        vol_resampled = vol_df.resample(rule).sum().dropna()
        resampled_volumes = [
            HistoricalPrice(timestamp=ts.to_pydatetime(), price=row['volume'])
            for ts, row in vol_resampled.iterrows()
        ]

    # NOTE: market_caps is intentionally left empty after resampling.
    # Market cap resampling is complex (not additive like volume, not a close like price)
    # and Dexter's crypto.ts doesn't return market caps anyway.
    # If needed later, resample as last value per bucket like prices.
    return HistoricalData(
        coin_id=historical_data.coin_id,
        prices=resampled_prices,
        market_caps=[],  # Intentionally empty - see note above
        total_volumes=resampled_volumes
    )


async def get_available_crypto_tickers() -> List[str]:
    """
    Return list of available crypto tickers in Dexter format (SYMBOL-USD).

    Since CoinGecko doesn't have a tickers endpoint like Financial Datasets,
    we fetch top 250 coins by market cap and cache the result.

    NOTE: De-duplicates symbols (keeps highest market cap coin for each symbol).
    Some symbols like "ETH" may appear multiple times for different coins.

    Returns:
        List of ticker strings like ["BTC-USD", "ETH-USD", ...]
    """
    global _AVAILABLE_TICKERS_CACHE, _CACHE_TIMESTAMP

    # Cache for 1 hour
    if _AVAILABLE_TICKERS_CACHE and _CACHE_TIMESTAMP:
        if (datetime.now() - _CACHE_TIMESTAMP).seconds < 3600:
            return _AVAILABLE_TICKERS_CACHE

    from ..mcp.coingecko_client import CoinGeckoMCPClient
    client = CoinGeckoMCPClient()
    await client.connect()

    # Fetch top 250 coins
    coins = await client.get_coins_markets(per_page=250, page=1)

    # De-duplicate: keep first occurrence of each symbol (highest market cap)
    # since coins are sorted by market_cap_desc
    seen_symbols = set()
    tickers = []
    for coin in coins:
        symbol = coin.symbol.upper()
        if symbol not in seen_symbols:
            seen_symbols.add(symbol)
            tickers.append(f"{symbol}-USD")

    _AVAILABLE_TICKERS_CACHE = tickers
    _CACHE_TIMESTAMP = datetime.now()

    return tickers
