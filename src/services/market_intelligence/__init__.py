"""
Market Intelligence Services

Provides cross-asset comparison, volatility analysis, and sector-based views.
Combines data from OpenBB (equities) and CoinGecko (crypto) for unified analysis.
"""

from .cross_asset_service import CrossAssetService
from .volatility_service import VolatilityService
from .sector_service import SectorService

__all__ = [
    'CrossAssetService',
    'VolatilityService',
    'SectorService',
]
