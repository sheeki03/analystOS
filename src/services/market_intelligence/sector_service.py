"""
Sector Service

Provides sector-based views and classifications.
Maps assets to sectors (similar to CoinGecko categories).
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


@dataclass
class SectorInfo:
    """Information about a sector."""
    key: str
    name: str
    description: str
    stocks: List[str]
    crypto: List[str]


@dataclass
class SectorData:
    """Aggregated data for a sector."""
    sector: SectorInfo
    total_market_cap: float
    stock_market_cap: float
    crypto_market_cap: float
    asset_count: int
    top_performers: List[Dict[str, Any]]
    worst_performers: List[Dict[str, Any]]
    avg_change_24h: float


class SectorService:
    """
    Service for sector-based analysis.

    Loads sector classifications from YAML config and provides
    aggregated views across stocks and crypto.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize with sector config.

        Args:
            config_path: Path to sector_classifications.yaml
        """
        if config_path is None:
            # Default to config directory
            config_path = Path(__file__).parent.parent.parent.parent / "config" / "sector_classifications.yaml"

        self.config_path = Path(config_path)
        self._sectors: Optional[Dict[str, SectorInfo]] = None
        self._cross_asset_service = None

    def _load_sectors(self) -> Dict[str, SectorInfo]:
        """Load sector definitions from YAML."""
        if self._sectors is not None:
            return self._sectors

        if not self.config_path.exists():
            logger.warning(f"Sector config not found at {self.config_path}")
            self._sectors = {}
            return self._sectors

        with open(self.config_path) as f:
            config = yaml.safe_load(f)

        self._sectors = {}
        for key, data in config.items():
            if key == "default_watchlist":
                continue  # Skip watchlist, not a sector

            if isinstance(data, dict) and "name" in data:
                self._sectors[key] = SectorInfo(
                    key=key,
                    name=data.get("name", key),
                    description=data.get("description", ""),
                    stocks=data.get("stocks", []),
                    crypto=data.get("crypto", [])
                )

        return self._sectors

    async def _get_cross_asset_service(self):
        """Get cross asset service."""
        if self._cross_asset_service is None:
            from .cross_asset_service import CrossAssetService
            self._cross_asset_service = CrossAssetService()
        return self._cross_asset_service

    def get_sectors(self) -> List[SectorInfo]:
        """Get all sector definitions."""
        sectors = self._load_sectors()
        return list(sectors.values())

    def get_sector(self, sector_key: str) -> Optional[SectorInfo]:
        """Get a specific sector by key."""
        sectors = self._load_sectors()
        return sectors.get(sector_key)

    def get_sector_for_asset(self, symbol: str) -> Optional[SectorInfo]:
        """Find which sector an asset belongs to."""
        sectors = self._load_sectors()
        symbol_upper = symbol.upper()

        for sector in sectors.values():
            if symbol_upper in sector.stocks or symbol_upper in sector.crypto:
                return sector

        return None

    async def get_sector_data(self, sector_key: str) -> Optional[SectorData]:
        """
        Get aggregated data for a sector.

        Args:
            sector_key: Sector key (e.g., "tech_ai")

        Returns:
            SectorData with aggregated metrics
        """
        sector = self.get_sector(sector_key)
        if not sector:
            return None

        service = await self._get_cross_asset_service()

        # Get all assets in sector
        all_symbols = sector.stocks + sector.crypto
        snapshots = []

        for symbol in all_symbols:
            try:
                snapshot = await service.get_asset_snapshot(symbol)
                snapshots.append(snapshot)
            except Exception as e:
                logger.debug(f"Failed to get snapshot for {symbol}: {e}")

        if not snapshots:
            return None

        # Compute aggregates
        total_market_cap = sum(s.market_cap or 0 for s in snapshots)
        stock_market_cap = sum(s.market_cap or 0 for s in snapshots if s.asset_type == "stock")
        crypto_market_cap = sum(s.market_cap or 0 for s in snapshots if s.asset_type == "crypto")

        # Performance ranking
        sorted_by_change = sorted(
            [s for s in snapshots if s.change_24h_percent is not None],
            key=lambda s: s.change_24h_percent,
            reverse=True
        )

        top_performers = [
            {"symbol": s.symbol, "change_24h_percent": s.change_24h_percent, "asset_type": s.asset_type}
            for s in sorted_by_change[:3]
        ]

        worst_performers = [
            {"symbol": s.symbol, "change_24h_percent": s.change_24h_percent, "asset_type": s.asset_type}
            for s in sorted_by_change[-3:]
        ]

        # Average change
        changes = [s.change_24h_percent for s in snapshots if s.change_24h_percent is not None]
        avg_change = sum(changes) / len(changes) if changes else 0

        return SectorData(
            sector=sector,
            total_market_cap=total_market_cap,
            stock_market_cap=stock_market_cap,
            crypto_market_cap=crypto_market_cap,
            asset_count=len(snapshots),
            top_performers=top_performers,
            worst_performers=worst_performers,
            avg_change_24h=avg_change
        )

    async def get_all_sectors_data(self) -> List[SectorData]:
        """Get data for all sectors."""
        sectors = self.get_sectors()
        results = []

        for sector in sectors:
            try:
                data = await self.get_sector_data(sector.key)
                if data:
                    results.append(data)
            except Exception as e:
                logger.error(f"Failed to get data for sector {sector.key}: {e}")

        # Sort by total market cap
        results.sort(key=lambda x: x.total_market_cap, reverse=True)
        return results

    def get_default_watchlist(self) -> Dict[str, List[str]]:
        """Get the default watchlist from config."""
        if not self.config_path.exists():
            return {
                "crypto": ["BTC", "ETH", "SOL"],
                "stocks": ["V", "MA", "NVDA", "INTC", "MSFT", "GOOGL", "JPM", "COIN", "SOFI"]
            }

        with open(self.config_path) as f:
            config = yaml.safe_load(f)

        return config.get("default_watchlist", {})

    async def get_sector_treemap_data(self) -> Dict[str, Any]:
        """
        Get data formatted for treemap visualization.

        Returns:
            Dict with hierarchical data for treemap chart
        """
        sectors_data = await self.get_all_sectors_data()

        treemap_data = {
            "name": "Market",
            "children": []
        }

        for sector_data in sectors_data:
            sector_node = {
                "name": sector_data.sector.name,
                "children": []
            }

            # Add stock assets
            for symbol in sector_data.sector.stocks:
                sector_node["children"].append({
                    "name": symbol,
                    "type": "stock",
                    "value": 0  # Would need individual market caps
                })

            # Add crypto assets
            for symbol in sector_data.sector.crypto:
                sector_node["children"].append({
                    "name": symbol,
                    "type": "crypto",
                    "value": 0  # Would need individual market caps
                })

            sector_node["total_market_cap"] = sector_data.total_market_cap
            treemap_data["children"].append(sector_node)

        return treemap_data
