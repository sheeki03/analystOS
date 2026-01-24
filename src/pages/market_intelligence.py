"""
Market Intelligence Page

Cross-asset comparison, volatility analysis, and sector-based views.
Combines data from OpenBB (equities) and CoinGecko (crypto) for unified analysis.
"""

import streamlit as st
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.pages.base_page import BasePage
from src.audit_logger import get_audit_logger

logger = logging.getLogger(__name__)


class MarketIntelligencePage(BasePage):
    """Market Intelligence page for cross-asset analysis."""

    def __init__(self):
        super().__init__("Market Intelligence", "Market Intelligence")
        self.title = "📊 Market Intelligence"

    async def render(self):
        """Render the market intelligence page."""
        self._render_header()

        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔀 Cross-Asset Compare",
            "📈 Volatility Analysis",
            "🏷️ Sector View",
            "👀 Watchlist"
        ])

        with tab1:
            await self._render_cross_asset_tab()

        with tab2:
            await self._render_volatility_tab()

        with tab3:
            await self._render_sector_tab()

        with tab4:
            await self._render_watchlist_tab()

    def _render_header(self):
        """Render page header."""
        st.markdown("""
        <div style="text-align: center; padding: 10px;">
            <h1>📊 Market Intelligence</h1>
            <p style="font-size: 16px; color: #666;">
                Cross-asset comparison between crypto and traditional equities
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

    async def _render_cross_asset_tab(self):
        """Render cross-asset comparison tab."""
        st.markdown("### 🔀 Cross-Asset Comparison")
        st.markdown("Compare market caps, returns, and metrics across crypto and stocks.")

        # Input for assets to compare
        col1, col2 = st.columns([3, 1])

        with col1:
            default_assets = "BTC, ETH, V, MA, NVDA"
            assets_input = st.text_input(
                "Enter assets to compare (comma-separated)",
                value=default_assets,
                placeholder="BTC, ETH, AAPL, MSFT",
                help="Mix crypto (BTC, ETH, SOL) and stocks (AAPL, MSFT, NVDA)"
            )

        with col2:
            compare_btn = st.button("Compare", type="primary", use_container_width=True)

        if compare_btn and assets_input:
            symbols = [s.strip().upper() for s in assets_input.split(",")]

            with st.spinner("Fetching cross-asset data..."):
                try:
                    from src.services.market_intelligence import CrossAssetService
                    service = CrossAssetService()

                    result = await service.compare_assets(symbols)

                    if result and result.assets:
                        self._render_comparison_results(result)
                    else:
                        st.warning("No data returned for the specified assets.")

                except Exception as e:
                    logger.error(f"Cross-asset comparison error: {e}")
                    st.error(f"Error comparing assets: {str(e)}")

        # Quick comparison presets
        st.markdown("---")
        st.markdown("#### Quick Comparisons")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("BTC vs Payments", use_container_width=True):
                st.session_state.mi_quick_compare = "BTC, V, MA, PYPL"
                st.rerun()

        with col2:
            if st.button("Tech vs Crypto", use_container_width=True):
                st.session_state.mi_quick_compare = "BTC, ETH, NVDA, MSFT, GOOGL"
                st.rerun()

        with col3:
            if st.button("DeFi vs Banks", use_container_width=True):
                st.session_state.mi_quick_compare = "ETH, AAVE, UNI, JPM, GS"
                st.rerun()

        with col4:
            if st.button("L1 Chains", use_container_width=True):
                st.session_state.mi_quick_compare = "BTC, ETH, SOL, AVAX, ADA"
                st.rerun()

    def _render_comparison_results(self, result):
        """Render comparison results."""
        st.markdown("#### Comparison Results")

        # Market cap comparison
        st.markdown("##### Market Cap Comparison")

        chart_data = {
            "Asset": [],
            "Market Cap ($B)": [],
            "Type": []
        }

        for asset in result.assets:
            chart_data["Asset"].append(asset.symbol)
            market_cap_b = (asset.market_cap or 0) / 1e9
            chart_data["Market Cap ($B)"].append(market_cap_b)
            chart_data["Type"].append(asset.asset_type.upper())

        import pandas as pd
        df = pd.DataFrame(chart_data)

        if not df.empty:
            st.bar_chart(df.set_index("Asset")["Market Cap ($B)"])

        # Detailed table
        st.markdown("##### Detailed Metrics")

        table_data = []
        for asset in result.assets:
            table_data.append({
                "Symbol": asset.symbol,
                "Name": asset.name,
                "Type": asset.asset_type.upper(),
                "Price": f"${asset.price:,.2f}" if asset.price else "N/A",
                "Market Cap": f"${asset.market_cap / 1e9:.1f}B" if asset.market_cap else "N/A",
                "24h Change": f"{asset.change_24h_percent:+.2f}%" if asset.change_24h_percent else "N/A",
                "24h Volume": f"${asset.volume_24h / 1e9:.2f}B" if asset.volume_24h else "N/A"
            })

        st.dataframe(pd.DataFrame(table_data), use_container_width=True)

        # 24h Performance comparison
        st.markdown("##### 24h Performance")
        perf_data = {
            "Asset": [a.symbol for a in result.assets if a.change_24h_percent is not None],
            "Change (%)": [a.change_24h_percent for a in result.assets if a.change_24h_percent is not None]
        }
        if perf_data["Asset"]:
            perf_df = pd.DataFrame(perf_data)
            st.bar_chart(perf_df.set_index("Asset"))

    async def _render_volatility_tab(self):
        """Render volatility analysis tab."""
        st.markdown("### 📈 Volatility Analysis")
        st.markdown("Compare normalized volatility across crypto and stocks (adjusted for trading hours).")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            vol_assets = st.text_input(
                "Assets to analyze",
                value="BTC, ETH, SOL, NVDA, AAPL, V",
                key="vol_assets"
            )

        with col2:
            period_days = st.selectbox(
                "Period (days)",
                options=[7, 14, 30, 60, 90],
                index=2,
                key="vol_period"
            )

        with col3:
            vol_btn = st.button("Analyze Volatility", type="primary", use_container_width=True)

        if vol_btn and vol_assets:
            symbols = [s.strip().upper() for s in vol_assets.split(",")]

            with st.spinner("Computing volatility metrics..."):
                try:
                    from src.services.market_intelligence import VolatilityService
                    service = VolatilityService()

                    chart_data = await service.get_volatility_chart_data(symbols, period_days)

                    if chart_data and chart_data.get("labels"):
                        self._render_volatility_results(chart_data)
                    else:
                        st.warning("No volatility data returned.")

                except Exception as e:
                    logger.error(f"Volatility analysis error: {e}")
                    st.error(f"Error computing volatility: {str(e)}")

        # Explanation
        with st.expander("ℹ️ About Volatility Normalization"):
            st.markdown("""
            **Why Normalize?**

            Crypto markets trade 24/7 (8,760 hours/year), while stock markets trade ~6.5 hours/day
            for ~252 days/year (1,638 hours/year).

            Raw annualized volatility makes crypto appear ~2.3x more volatile than it would be
            under equivalent trading conditions.

            **Normalized volatility** adjusts for this difference, enabling fair comparison:
            - `Normalization Factor = sqrt(252 × 6.5 / 365 × 24) ≈ 0.43`
            - Normalized crypto volatility = Raw × 0.43
            """)

    def _render_volatility_results(self, chart_data: Dict[str, Any]):
        """Render volatility analysis results."""
        import pandas as pd

        labels = chart_data.get("labels", [])
        raw_vol = chart_data.get("volatility_raw", [])
        norm_vol = chart_data.get("volatility_normalized", [])
        asset_types = chart_data.get("asset_types", [])

        # Chart: Raw vs Normalized
        st.markdown("#### Volatility Comparison")

        df = pd.DataFrame({
            "Asset": labels,
            "Raw (Annualized)": [v * 100 for v in raw_vol],
            "Normalized": [v * 100 for v in norm_vol],
            "Type": [t.upper() for t in asset_types]
        })

        # Display as grouped bar chart data
        chart_df = df.set_index("Asset")[["Raw (Annualized)", "Normalized"]]
        st.bar_chart(chart_df)

        # Table
        st.markdown("#### Volatility Metrics (%)")
        display_df = df.copy()
        display_df["Raw (Annualized)"] = display_df["Raw (Annualized)"].apply(lambda x: f"{x:.1f}%")
        display_df["Normalized"] = display_df["Normalized"].apply(lambda x: f"{x:.1f}%")
        st.dataframe(display_df, use_container_width=True)

    async def _render_sector_tab(self):
        """Render sector view tab."""
        st.markdown("### 🏷️ Sector View")
        st.markdown("View assets grouped by sector (similar to CoinGecko categories).")

        with st.spinner("Loading sector data..."):
            try:
                from src.services.market_intelligence import SectorService
                service = SectorService()

                # Get all sectors
                sectors = service.get_sectors()

                if not sectors:
                    st.warning("No sector classifications found. Check config/sector_classifications.yaml")
                    return

                # Sector selector
                sector_names = {s.key: s.name for s in sectors}
                selected_key = st.selectbox(
                    "Select Sector",
                    options=list(sector_names.keys()),
                    format_func=lambda x: sector_names[x]
                )

                if selected_key:
                    sector_data = await service.get_sector_data(selected_key)

                    if sector_data:
                        self._render_sector_details(sector_data)
                    else:
                        st.warning("No data available for this sector.")

            except Exception as e:
                logger.error(f"Sector view error: {e}")
                st.error(f"Error loading sector data: {str(e)}")

    def _render_sector_details(self, sector_data):
        """Render sector details."""
        import pandas as pd

        sector = sector_data.sector

        st.markdown(f"#### {sector.name}")
        if sector.description:
            st.caption(sector.description)

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Market Cap",
                f"${sector_data.total_market_cap / 1e9:.1f}B" if sector_data.total_market_cap else "N/A"
            )

        with col2:
            st.metric(
                "Stock Market Cap",
                f"${sector_data.stock_market_cap / 1e9:.1f}B" if sector_data.stock_market_cap else "N/A"
            )

        with col3:
            st.metric(
                "Crypto Market Cap",
                f"${sector_data.crypto_market_cap / 1e9:.1f}B" if sector_data.crypto_market_cap else "N/A"
            )

        with col4:
            st.metric(
                "Avg 24h Change",
                f"{sector_data.avg_change_24h:+.2f}%"
            )

        # Assets in sector
        st.markdown("##### Assets in Sector")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Stocks**")
            if sector.stocks:
                for symbol in sector.stocks:
                    st.write(f"• {symbol}")
            else:
                st.caption("No stocks in this sector")

        with col2:
            st.markdown("**Crypto**")
            if sector.crypto:
                for symbol in sector.crypto:
                    st.write(f"• {symbol}")
            else:
                st.caption("No crypto in this sector")

        # Top and worst performers
        if sector_data.top_performers:
            st.markdown("##### Top Performers (24h)")
            for p in sector_data.top_performers:
                st.write(f"🟢 **{p['symbol']}** ({p['asset_type']}): {p['change_24h_percent']:+.2f}%")

        if sector_data.worst_performers:
            st.markdown("##### Worst Performers (24h)")
            for p in sector_data.worst_performers:
                st.write(f"🔴 **{p['symbol']}** ({p['asset_type']}): {p['change_24h_percent']:+.2f}%")

    async def _render_watchlist_tab(self):
        """Render watchlist tab."""
        st.markdown("### 👀 Default Watchlist")
        st.markdown("Quick view of your default assets.")

        try:
            from src.services.market_intelligence import SectorService, CrossAssetService
            sector_service = SectorService()
            cross_service = CrossAssetService()

            watchlist = sector_service.get_default_watchlist()

            crypto_symbols = watchlist.get("crypto", [])
            stock_symbols = watchlist.get("stocks", [])

            # Crypto section
            if crypto_symbols:
                st.markdown("#### 🪙 Crypto")
                with st.spinner("Loading crypto prices..."):
                    crypto_snapshots = []
                    for symbol in crypto_symbols:
                        try:
                            snapshot = await cross_service.get_asset_snapshot(symbol, "crypto")
                            crypto_snapshots.append(snapshot)
                        except Exception as e:
                            logger.debug(f"Failed to get {symbol}: {e}")

                    if crypto_snapshots:
                        self._render_watchlist_table(crypto_snapshots)

            # Stocks section
            if stock_symbols:
                st.markdown("#### 📈 Stocks")
                with st.spinner("Loading stock prices..."):
                    stock_snapshots = []
                    for symbol in stock_symbols:
                        try:
                            snapshot = await cross_service.get_asset_snapshot(symbol, "stock")
                            stock_snapshots.append(snapshot)
                        except Exception as e:
                            logger.debug(f"Failed to get {symbol}: {e}")

                    if stock_snapshots:
                        self._render_watchlist_table(stock_snapshots)

        except Exception as e:
            logger.error(f"Watchlist error: {e}")
            st.error(f"Error loading watchlist: {str(e)}")

    def _render_watchlist_table(self, snapshots: List):
        """Render watchlist as a table."""
        import pandas as pd

        data = []
        for s in snapshots:
            change_str = f"{s.change_24h_percent:+.2f}%" if s.change_24h_percent is not None else "N/A"
            data.append({
                "Symbol": s.symbol,
                "Name": s.name,
                "Price": f"${s.price:,.2f}" if s.price else "N/A",
                "24h Change": change_str,
                "Market Cap": f"${s.market_cap / 1e9:.1f}B" if s.market_cap else "N/A"
            })

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)


def main():
    """Main function to run the market intelligence page."""
    page = MarketIntelligencePage()
    asyncio.run(page.render())


if __name__ == "__main__":
    main()
