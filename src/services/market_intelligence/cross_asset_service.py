"""
Cross-Asset Comparison Service

Enables comparison between crypto and traditional equities.
Example: Compare Bitcoin vs Visa market cap, returns, etc.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class AssetSnapshot:
    """Unified snapshot for any asset type."""
    symbol: str
    name: str
    asset_type: str  # "crypto" or "stock"
    price: float
    market_cap: Optional[float]
    volume_24h: Optional[float]
    change_24h: Optional[float]
    change_24h_percent: Optional[float]
    high_24h: Optional[float]
    low_24h: Optional[float]
    timestamp: datetime
    # Additional metadata
    sector: Optional[str] = None
    pe_ratio: Optional[float] = None  # stocks only
    dividend_yield: Optional[float] = None  # stocks only
    circulating_supply: Optional[float] = None  # crypto only
    max_supply: Optional[float] = None  # crypto only


@dataclass
class ComparisonResult:
    """Result of comparing multiple assets."""
    assets: List[AssetSnapshot]
    comparison_date: datetime
    metrics: Dict[str, Dict[str, Any]]  # metric_name -> {asset_symbol: value}


class CrossAssetService:
    """
    Service for comparing assets across crypto and traditional markets.

    Normalizes data from different sources to enable meaningful comparisons.
    """

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

    async def get_asset_snapshot(
        self,
        symbol: str,
        asset_type: Optional[str] = None
    ) -> AssetSnapshot:
        """
        Get unified snapshot for any asset.

        Args:
            symbol: Asset symbol (e.g., "BTC", "AAPL")
            asset_type: Optional - "crypto" or "stock". Auto-detected if not provided.

        Returns:
            AssetSnapshot with normalized data
        """
        # Auto-detect asset type if not provided
        if asset_type is None:
            asset_type = self._detect_asset_type(symbol)

        if asset_type == "crypto":
            return await self._get_crypto_snapshot(symbol)
        else:
            return self._get_stock_snapshot(symbol)

    def _detect_asset_type(self, symbol: str) -> str:
        """Detect if symbol is crypto or stock."""
        # Known crypto symbols
        crypto_symbols = {
            "BTC", "ETH", "SOL", "XRP", "ADA", "AVAX", "DOT", "MATIC",
            "LINK", "UNI", "AAVE", "MKR", "DOGE", "SHIB", "PEPE", "WIF",
            "BONK", "LTC", "BCH", "ATOM", "FIL", "NEAR", "APT", "ARB",
            "OP", "IMX", "INJ", "TIA", "SUI", "SEI", "RNDR", "TAO", "AKT"
        }

        # Check for crypto format (SYMBOL-USD)
        if "-" in symbol:
            base = symbol.split("-")[0].upper()
            return "crypto" if base in crypto_symbols else "stock"

        # Check against known crypto symbols
        if symbol.upper() in crypto_symbols:
            return "crypto"

        # Default to stock
        return "stock"

    async def _get_crypto_snapshot(self, symbol: str) -> AssetSnapshot:
        """Get snapshot for crypto asset."""
        from ..financial_tools.crypto_resolver import resolve_ticker_to_coin_id

        # Normalize symbol to include USD if not present
        if "-" not in symbol:
            symbol = f"{symbol}-USD"

        coin_id = await resolve_ticker_to_coin_id(symbol)
        client = await self._get_coingecko_client()
        price_data = await client.get_coin_price(coin_id)

        # Normalize timestamp
        timestamp = price_data.last_updated
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif timestamp is None:
            timestamp = datetime.now()

        return AssetSnapshot(
            symbol=symbol.split("-")[0].upper(),
            name=price_data.name,
            asset_type="crypto",
            price=price_data.current_price,
            market_cap=price_data.market_cap,
            volume_24h=price_data.total_volume,
            change_24h=price_data.price_change_24h,
            change_24h_percent=price_data.price_change_percentage_24h,
            high_24h=price_data.high_24h,
            low_24h=price_data.low_24h,
            timestamp=timestamp,
            circulating_supply=price_data.circulating_supply,
            max_supply=price_data.max_supply,
        )

    def _get_stock_snapshot(self, symbol: str) -> AssetSnapshot:
        """Get snapshot for stock."""
        client = self._get_openbb_client()
        data = client.get_price_snapshot(symbol)

        return AssetSnapshot(
            symbol=symbol.upper(),
            name=symbol.upper(),  # Would need company name lookup
            asset_type="stock",
            price=data.get("close") or data.get("price", 0),
            market_cap=data.get("market_cap"),
            volume_24h=data.get("volume"),
            change_24h=data.get("change"),
            change_24h_percent=data.get("change_percent"),
            high_24h=data.get("high"),
            low_24h=data.get("low"),
            timestamp=datetime.now(),
            pe_ratio=data.get("pe_ratio"),
        )

    async def compare_assets(
        self,
        symbols: List[str],
        asset_types: Optional[List[str]] = None
    ) -> ComparisonResult:
        """
        Compare multiple assets side by side.

        Args:
            symbols: List of asset symbols
            asset_types: Optional list of asset types (same length as symbols)

        Returns:
            ComparisonResult with all assets and computed metrics
        """
        snapshots = []

        for i, symbol in enumerate(symbols):
            asset_type = asset_types[i] if asset_types else None
            try:
                snapshot = await self.get_asset_snapshot(symbol, asset_type)
                snapshots.append(snapshot)
            except Exception as e:
                logger.error(f"Failed to get snapshot for {symbol}: {e}")

        # Compute comparison metrics
        metrics = self._compute_comparison_metrics(snapshots)

        return ComparisonResult(
            assets=snapshots,
            comparison_date=datetime.now(),
            metrics=metrics
        )

    def _compute_comparison_metrics(
        self,
        snapshots: List[AssetSnapshot]
    ) -> Dict[str, Dict[str, Any]]:
        """Compute comparison metrics across assets."""
        metrics = {
            "market_cap": {},
            "price": {},
            "change_24h_percent": {},
            "volume_24h": {},
            "market_cap_rank": {},
        }

        # Collect values
        market_caps = []
        for s in snapshots:
            metrics["market_cap"][s.symbol] = s.market_cap
            metrics["price"][s.symbol] = s.price
            metrics["change_24h_percent"][s.symbol] = s.change_24h_percent
            metrics["volume_24h"][s.symbol] = s.volume_24h
            if s.market_cap:
                market_caps.append((s.symbol, s.market_cap))

        # Rank by market cap
        market_caps.sort(key=lambda x: x[1], reverse=True)
        for rank, (symbol, _) in enumerate(market_caps, 1):
            metrics["market_cap_rank"][symbol] = rank

        return metrics

    async def get_market_cap_comparison(
        self,
        symbols: List[str]
    ) -> Dict[str, Any]:
        """
        Get market cap comparison data formatted for visualization.

        Args:
            symbols: List of asset symbols

        Returns:
            Dict with comparison data for charts
        """
        result = await self.compare_assets(symbols)

        # Format for chart
        chart_data = {
            "labels": [a.symbol for a in result.assets],
            "market_caps": [a.market_cap or 0 for a in result.assets],
            "asset_types": [a.asset_type for a in result.assets],
            "changes_24h": [a.change_24h_percent or 0 for a in result.assets],
        }

        return chart_data
