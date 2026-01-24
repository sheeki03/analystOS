"""
Volatility Service

Computes and normalizes volatility metrics across crypto and stocks.
Handles the 24/7 vs market hours difference.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


@dataclass
class VolatilityMetrics:
    """Volatility metrics for an asset."""
    symbol: str
    asset_type: str
    # Raw volatility (standard deviation of returns)
    volatility_daily: float  # Based on daily returns
    volatility_annualized: float
    # Normalized volatility (adjusted for trading hours)
    volatility_normalized: float
    # Additional metrics
    average_true_range: Optional[float]
    beta: Optional[float]  # vs BTC for crypto, vs SPY for stocks
    # Time period
    period_days: int
    calculation_date: datetime


class VolatilityService:
    """
    Service for computing volatility metrics.

    Normalizes crypto 24/7 volatility to be comparable with
    stock market hours (6.5 hours/day, 252 days/year).
    """

    # Trading hours constants
    STOCK_TRADING_HOURS_PER_DAY = 6.5
    STOCK_TRADING_DAYS_PER_YEAR = 252
    CRYPTO_TRADING_HOURS_PER_DAY = 24
    CRYPTO_TRADING_DAYS_PER_YEAR = 365

    def __init__(self):
        self._openbb_client = None
        self._coingecko_client = None

    async def _get_coingecko_client(self):
        """Get or create CoinGecko client."""
        if self._coingecko_client is None:
            from ..mcp.coingecko_client import CoinGeckoMCPClient
            self._coingecko_client = CoinGeckoMCPClient()
            await self._coingecko_client.connect()
        return self._coingecko_client

    def _get_openbb_client(self):
        """Get or create OpenBB client."""
        if self._openbb_client is None:
            from ..openbb import OpenBBClient
            self._openbb_client = OpenBBClient()
        return self._openbb_client

    async def compute_volatility(
        self,
        symbol: str,
        period_days: int = 30,
        asset_type: Optional[str] = None
    ) -> VolatilityMetrics:
        """
        Compute volatility metrics for an asset.

        Args:
            symbol: Asset symbol
            period_days: Number of days to compute volatility over
            asset_type: "crypto" or "stock" (auto-detected if not provided)

        Returns:
            VolatilityMetrics with raw and normalized volatility
        """
        # Auto-detect asset type
        if asset_type is None:
            from .cross_asset_service import CrossAssetService
            service = CrossAssetService()
            asset_type = service._detect_asset_type(symbol)

        if asset_type == "crypto":
            return await self._compute_crypto_volatility(symbol, period_days)
        else:
            return self._compute_stock_volatility(symbol, period_days)

    async def _compute_crypto_volatility(
        self,
        symbol: str,
        period_days: int
    ) -> VolatilityMetrics:
        """Compute volatility for crypto asset."""
        from ..financial_tools.crypto_resolver import (
            resolve_ticker_to_coin_id,
            calculate_fetch_days,
            slice_historical_data,
        )

        # Normalize symbol
        if "-" not in symbol:
            symbol = f"{symbol}-USD"

        coin_id = await resolve_ticker_to_coin_id(symbol)
        client = await self._get_coingecko_client()

        # Get historical data
        historical = await client.get_historical_data(coin_id, period_days)

        # Extract prices
        prices = [p.price for p in historical.prices]

        if len(prices) < 2:
            raise ValueError(f"Insufficient data for volatility calculation")

        # Compute daily returns
        returns = []
        for i in range(1, len(prices)):
            if prices[i - 1] > 0:
                daily_return = (prices[i] - prices[i - 1]) / prices[i - 1]
                returns.append(daily_return)

        # Compute raw volatility
        volatility_daily = self._std_dev(returns)
        volatility_annualized = volatility_daily * math.sqrt(self.CRYPTO_TRADING_DAYS_PER_YEAR)

        # Normalize to stock-equivalent trading hours
        # Crypto trades 24/7/365, stocks trade 6.5h/day for 252 days
        # Adjustment factor: sqrt(252 * 6.5 / (365 * 24))
        normalization_factor = math.sqrt(
            (self.STOCK_TRADING_DAYS_PER_YEAR * self.STOCK_TRADING_HOURS_PER_DAY) /
            (self.CRYPTO_TRADING_DAYS_PER_YEAR * self.CRYPTO_TRADING_HOURS_PER_DAY)
        )
        volatility_normalized = volatility_annualized * normalization_factor

        return VolatilityMetrics(
            symbol=symbol.split("-")[0].upper(),
            asset_type="crypto",
            volatility_daily=volatility_daily,
            volatility_annualized=volatility_annualized,
            volatility_normalized=volatility_normalized,
            average_true_range=None,  # Would need OHLC data
            beta=None,  # Would need BTC data for comparison
            period_days=period_days,
            calculation_date=datetime.now()
        )

    def _compute_stock_volatility(
        self,
        symbol: str,
        period_days: int
    ) -> VolatilityMetrics:
        """Compute volatility for stock."""
        client = self._get_openbb_client()

        # Get historical prices
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=period_days + 10)).strftime("%Y-%m-%d")

        prices_data = client.get_prices(
            ticker=symbol,
            start_date=start_date,
            end_date=end_date,
            interval="day"
        )

        # Extract closing prices
        prices = [p.get("close", 0) for p in prices_data if p.get("close")]

        if len(prices) < 2:
            raise ValueError(f"Insufficient data for volatility calculation")

        # Compute daily returns
        returns = []
        for i in range(1, len(prices)):
            if prices[i - 1] > 0:
                daily_return = (prices[i] - prices[i - 1]) / prices[i - 1]
                returns.append(daily_return)

        # Compute raw volatility
        volatility_daily = self._std_dev(returns)
        volatility_annualized = volatility_daily * math.sqrt(self.STOCK_TRADING_DAYS_PER_YEAR)

        # For stocks, normalized = annualized (already in stock trading terms)
        volatility_normalized = volatility_annualized

        return VolatilityMetrics(
            symbol=symbol.upper(),
            asset_type="stock",
            volatility_daily=volatility_daily,
            volatility_annualized=volatility_annualized,
            volatility_normalized=volatility_normalized,
            average_true_range=None,
            beta=None,
            period_days=period_days,
            calculation_date=datetime.now()
        )

    def _std_dev(self, values: List[float]) -> float:
        """Compute standard deviation."""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    async def compare_volatility(
        self,
        symbols: List[str],
        period_days: int = 30
    ) -> Dict[str, VolatilityMetrics]:
        """
        Compare volatility across multiple assets.

        Args:
            symbols: List of asset symbols
            period_days: Period for volatility calculation

        Returns:
            Dict mapping symbol to VolatilityMetrics
        """
        results = {}

        for symbol in symbols:
            try:
                metrics = await self.compute_volatility(symbol, period_days)
                results[metrics.symbol] = metrics
            except Exception as e:
                logger.error(f"Failed to compute volatility for {symbol}: {e}")

        return results

    async def get_volatility_chart_data(
        self,
        symbols: List[str],
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get volatility data formatted for charts.

        Returns:
            Dict with chart-ready data including normalized volatility comparison
        """
        volatility_data = await self.compare_volatility(symbols, period_days)

        # Sort by normalized volatility
        sorted_symbols = sorted(
            volatility_data.keys(),
            key=lambda s: volatility_data[s].volatility_normalized,
            reverse=True
        )

        return {
            "labels": sorted_symbols,
            "volatility_raw": [volatility_data[s].volatility_annualized for s in sorted_symbols],
            "volatility_normalized": [volatility_data[s].volatility_normalized for s in sorted_symbols],
            "asset_types": [volatility_data[s].asset_type for s in sorted_symbols],
            "period_days": period_days,
        }
