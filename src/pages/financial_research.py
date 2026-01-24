"""
Financial Research Page

AI-powered financial research using the migrated Dexter tools.
Supports natural language queries routed to appropriate financial data tools.
"""

import streamlit as st
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from src.pages.base_page import BasePage
from src.audit_logger import get_audit_logger

logger = logging.getLogger(__name__)


class FinancialResearchPage(BasePage):
    """Financial Research page with AI-powered tool routing."""

    def __init__(self):
        super().__init__("Financial Research", "Financial Research")
        self.title = "🔬 Financial Research"

    async def render(self):
        """Render the financial research page."""
        self._render_header()

        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🤖 AI Research",
            "📊 Quick Tools",
            "📈 Price Charts",
            "📁 Filings"
        ])

        with tab1:
            await self._render_ai_research_tab()

        with tab2:
            await self._render_quick_tools_tab()

        with tab3:
            await self._render_price_charts_tab()

        with tab4:
            await self._render_filings_tab()

    def _render_header(self):
        """Render page header."""
        st.markdown("""
        <div style="text-align: center; padding: 10px;">
            <h1>🔬 Financial Research</h1>
            <p style="font-size: 16px; color: #666;">
                AI-powered research across equities and crypto markets
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

    async def _render_ai_research_tab(self):
        """Render AI research tab with natural language queries."""
        st.markdown("### 🤖 AI-Powered Research")
        st.markdown("Ask questions in natural language. The AI will route to the appropriate data tools.")

        # Initialize chat history
        if "fr_chat_history" not in st.session_state:
            st.session_state.fr_chat_history = []

        # Example queries
        with st.expander("💡 Example Queries", expanded=False):
            st.markdown("""
            **Equity Research:**
            - "Show me AAPL's revenue for the last 3 years"
            - "What's NVDA's current P/E ratio and market cap?"
            - "Get the latest 10-K filing for MSFT"
            - "Show analyst estimates for GOOGL"
            - "What are the insider trades for TSLA?"

            **Crypto Research:**
            - "What's the current price of Bitcoin?"
            - "Show me ETH price history for the last 30 days"
            - "List available crypto tickers"

            **Comparisons:**
            - "Compare AAPL and MSFT revenue"
            - "Show me BTC and ETH prices"
            """)

        # Chat interface
        chat_container = st.container()

        with chat_container:
            for msg in st.session_state.fr_chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    if "data" in msg and msg["data"]:
                        self._render_research_data(msg["data"])

        # Query input
        if query := st.chat_input("Ask a financial research question..."):
            # Add user message
            st.session_state.fr_chat_history.append({
                "role": "user",
                "content": query,
                "timestamp": datetime.now()
            })

            with st.chat_message("user"):
                st.markdown(query)

            # Process query
            with st.chat_message("assistant"):
                with st.spinner("Researching..."):
                    response = await self._process_research_query(query)
                    st.markdown(response["content"])
                    if "data" in response and response["data"]:
                        self._render_research_data(response["data"])

            # Add assistant response
            st.session_state.fr_chat_history.append(response)
            st.rerun()

        # Clear chat button
        if st.session_state.fr_chat_history:
            if st.button("🗑️ Clear Chat", key="fr_clear_chat"):
                st.session_state.fr_chat_history = []
                st.rerun()

    async def _process_research_query(self, query: str) -> Dict[str, Any]:
        """Process a research query using the financial tools router."""
        try:
            from src.services.financial_tools import FinancialSearchRouter

            router = FinancialSearchRouter()
            result_json = await router.search(query)
            result = json.loads(result_json)

            data = result.get("data", {})
            source_urls = result.get("sourceUrls", [])

            # Check for errors
            if "_errors" in data:
                errors = data["_errors"]
                error_msgs = [f"• {e.get('tool', 'Unknown')}: {e.get('error', 'Unknown error')}" for e in errors]
                content = "⚠️ **Some tools encountered errors:**\n\n" + "\n".join(error_msgs)

                # Remove errors from data for display
                data_without_errors = {k: v for k, v in data.items() if k != "_errors"}
                if data_without_errors:
                    content += "\n\n**Successful Results:**"

                return {
                    "role": "assistant",
                    "content": content,
                    "data": data_without_errors if data_without_errors else None,
                    "timestamp": datetime.now()
                }

            # Format successful response
            content = "✅ **Research Complete**"
            if source_urls:
                content += f"\n\n*Sources: {len(source_urls)} data source(s)*"

            return {
                "role": "assistant",
                "content": content,
                "data": data,
                "timestamp": datetime.now()
            }

        except Exception as e:
            logger.error(f"Research query error: {e}")
            return {
                "role": "assistant",
                "content": f"⚠️ **Error processing query:** {str(e)}",
                "data": None,
                "timestamp": datetime.now()
            }

    def _render_research_data(self, data: Dict[str, Any]):
        """Render research data in appropriate format."""
        import pandas as pd

        if not data:
            return

        for key, value in data.items():
            if key.startswith("_"):
                continue

            st.markdown(f"##### {key.replace('_', ' ').title()}")

            if isinstance(value, list):
                if value and isinstance(value[0], dict):
                    # Table of records
                    df = pd.DataFrame(value)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    # Simple list
                    for item in value[:20]:  # Limit display
                        st.write(f"• {item}")
            elif isinstance(value, dict):
                # Single record or nested data
                if any(isinstance(v, (list, dict)) for v in value.values()):
                    # Complex nested data
                    st.json(value)
                else:
                    # Simple key-value
                    for k, v in value.items():
                        st.write(f"**{k}:** {v}")
            else:
                st.write(value)

    async def _render_quick_tools_tab(self):
        """Render quick tools for direct data access."""
        st.markdown("### 📊 Quick Tools")
        st.markdown("Direct access to financial data tools.")

        tool_type = st.selectbox(
            "Select Tool",
            options=[
                "Price Snapshot (Stock)",
                "Price Snapshot (Crypto)",
                "Income Statements",
                "Balance Sheets",
                "Cash Flow Statements",
                "Financial Metrics",
                "Analyst Estimates",
                "Insider Trades",
                "News"
            ],
            key="quick_tool_select"
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            ticker = st.text_input(
                "Ticker Symbol",
                placeholder="AAPL, BTC-USD, etc.",
                key="quick_tool_ticker"
            )

        with col2:
            run_btn = st.button("Run", type="primary", use_container_width=True, key="quick_tool_run")

        if run_btn and ticker:
            await self._run_quick_tool(tool_type, ticker.upper())

    async def _run_quick_tool(self, tool_type: str, ticker: str):
        """Run a quick tool and display results."""
        import pandas as pd

        with st.spinner(f"Fetching {tool_type}..."):
            try:
                from src.services.financial_tools import tools

                result_json = None

                if tool_type == "Price Snapshot (Stock)":
                    result_json = tools.get_price_snapshot(ticker)
                elif tool_type == "Price Snapshot (Crypto)":
                    result_json = await tools.get_crypto_price_snapshot(ticker)
                elif tool_type == "Income Statements":
                    result_json = tools.get_income_statements(ticker)
                elif tool_type == "Balance Sheets":
                    result_json = tools.get_balance_sheets(ticker)
                elif tool_type == "Cash Flow Statements":
                    result_json = tools.get_cash_flow_statements(ticker)
                elif tool_type == "Financial Metrics":
                    result_json = tools.get_financial_metrics_snapshot(ticker)
                elif tool_type == "Analyst Estimates":
                    result_json = tools.get_analyst_estimates(ticker)
                elif tool_type == "Insider Trades":
                    result_json = tools.get_insider_trades(ticker)
                elif tool_type == "News":
                    result_json = tools.get_news(ticker)

                if result_json:
                    result = json.loads(result_json)
                    data = result.get("data")

                    if data:
                        st.success(f"✅ {tool_type} for {ticker}")
                        self._render_research_data({tool_type: data})
                    else:
                        st.warning("No data returned.")

            except Exception as e:
                logger.error(f"Quick tool error: {e}")
                st.error(f"Error: {str(e)}")

    async def _render_price_charts_tab(self):
        """Render price charts tab."""
        st.markdown("### 📈 Price Charts")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            chart_ticker = st.text_input(
                "Ticker",
                value="AAPL",
                key="chart_ticker"
            )

        with col2:
            asset_type = st.selectbox(
                "Type",
                options=["Stock", "Crypto"],
                key="chart_asset_type"
            )

        with col3:
            period = st.selectbox(
                "Period",
                options=["7 days", "30 days", "90 days", "1 year"],
                index=1,
                key="chart_period"
            )

        chart_btn = st.button("Load Chart", type="primary", key="chart_load")

        if chart_btn and chart_ticker:
            await self._render_price_chart(chart_ticker.upper(), asset_type, period)

    async def _render_price_chart(self, ticker: str, asset_type: str, period: str):
        """Render a price chart."""
        import pandas as pd

        period_days = {
            "7 days": 7,
            "30 days": 30,
            "90 days": 90,
            "1 year": 365
        }[period]

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=period_days)).strftime("%Y-%m-%d")

        with st.spinner(f"Loading {ticker} price data..."):
            try:
                from src.services.financial_tools import tools

                if asset_type == "Crypto":
                    # Ensure crypto format
                    if "-" not in ticker:
                        ticker = f"{ticker}-USD"
                    result_json = await tools.get_crypto_prices(
                        ticker=ticker,
                        start_date=start_date,
                        end_date=end_date,
                        interval="day"
                    )
                else:
                    result_json = tools.get_prices(
                        ticker=ticker,
                        start_date=start_date,
                        end_date=end_date,
                        interval="day"
                    )

                result = json.loads(result_json)
                data = result.get("data", [])

                if data:
                    # Convert to DataFrame
                    df = pd.DataFrame(data)

                    # Identify date and price columns
                    date_col = None
                    price_col = None

                    for col in df.columns:
                        col_lower = col.lower()
                        if "date" in col_lower or "time" in col_lower or "timestamp" in col_lower:
                            date_col = col
                        if "close" in col_lower or "price" in col_lower:
                            price_col = col

                    if date_col and price_col:
                        df[date_col] = pd.to_datetime(df[date_col])
                        df = df.sort_values(date_col)

                        st.line_chart(df.set_index(date_col)[price_col])

                        # Key stats
                        col1, col2, col3, col4 = st.columns(4)
                        prices = df[price_col].values

                        with col1:
                            st.metric("Current", f"${prices[-1]:,.2f}")
                        with col2:
                            st.metric("High", f"${max(prices):,.2f}")
                        with col3:
                            st.metric("Low", f"${min(prices):,.2f}")
                        with col4:
                            change = ((prices[-1] - prices[0]) / prices[0]) * 100
                            st.metric("Change", f"{change:+.2f}%")
                    else:
                        st.warning("Could not identify date/price columns in the data.")
                        st.dataframe(df)
                else:
                    st.warning("No price data returned.")

            except Exception as e:
                logger.error(f"Price chart error: {e}")
                st.error(f"Error loading price data: {str(e)}")

    async def _render_filings_tab(self):
        """Render SEC filings tab."""
        st.markdown("### 📁 SEC Filings")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            filing_ticker = st.text_input(
                "Ticker",
                value="AAPL",
                key="filing_ticker"
            )

        with col2:
            filing_type = st.selectbox(
                "Filing Type",
                options=["All", "10-K", "10-Q", "8-K"],
                key="filing_type"
            )

        with col3:
            filing_limit = st.number_input(
                "Limit",
                min_value=1,
                max_value=50,
                value=10,
                key="filing_limit"
            )

        filing_btn = st.button("Search Filings", type="primary", key="filing_search")

        if filing_btn and filing_ticker:
            await self._search_filings(filing_ticker.upper(), filing_type, filing_limit)

        # Specific filing content
        st.markdown("---")
        st.markdown("#### Extract Filing Content")

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            content_ticker = st.text_input(
                "Ticker",
                value="AAPL",
                key="content_ticker"
            )

        with col2:
            content_year = st.number_input(
                "Year",
                min_value=2015,
                max_value=datetime.now().year,
                value=datetime.now().year - 1,
                key="content_year"
            )

        with col3:
            content_type = st.selectbox(
                "Filing",
                options=["10-K", "10-Q"],
                key="content_type"
            )

        if content_type == "10-Q":
            content_quarter = st.selectbox(
                "Quarter",
                options=[1, 2, 3],
                key="content_quarter"
            )

        content_btn = st.button("Extract Content", type="primary", key="content_extract")

        if content_btn and content_ticker:
            if content_type == "10-K":
                await self._extract_10k_content(content_ticker.upper(), content_year)
            else:
                await self._extract_10q_content(content_ticker.upper(), content_year, content_quarter)

    async def _search_filings(self, ticker: str, filing_type: str, limit: int):
        """Search for SEC filings."""
        import pandas as pd

        with st.spinner(f"Searching {filing_type} filings for {ticker}..."):
            try:
                from src.services.financial_tools import tools

                type_filter = None if filing_type == "All" else filing_type
                result_json = tools.get_filings(ticker, filing_type=type_filter, limit=limit)

                result = json.loads(result_json)
                data = result.get("data", [])

                if data:
                    st.success(f"Found {len(data)} filings for {ticker}")
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.warning("No filings found.")

            except Exception as e:
                logger.error(f"Filings search error: {e}")
                st.error(f"Error searching filings: {str(e)}")

    async def _extract_10k_content(self, ticker: str, year: int):
        """Extract 10-K filing content."""
        with st.spinner(f"Extracting 10-K content for {ticker} ({year})..."):
            try:
                from src.services.financial_tools import tools

                result_json = tools.get_10k_filing_items(ticker, year)
                result = json.loads(result_json)
                data = result.get("data", {})

                if data:
                    st.success(f"10-K Content for {ticker} ({year})")

                    for item_key, content in data.items():
                        with st.expander(f"📄 {item_key}", expanded=False):
                            if isinstance(content, str):
                                st.markdown(content[:5000] + "..." if len(content) > 5000 else content)
                            else:
                                st.json(content)
                else:
                    st.warning("No 10-K content found.")

            except Exception as e:
                logger.error(f"10-K extraction error: {e}")
                st.error(f"Error extracting 10-K: {str(e)}")

    async def _extract_10q_content(self, ticker: str, year: int, quarter: int):
        """Extract 10-Q filing content."""
        with st.spinner(f"Extracting 10-Q content for {ticker} ({year} Q{quarter})..."):
            try:
                from src.services.financial_tools import tools

                result_json = tools.get_10q_filing_items(ticker, year, quarter)
                result = json.loads(result_json)
                data = result.get("data", {})

                if data:
                    st.success(f"10-Q Content for {ticker} ({year} Q{quarter})")

                    for item_key, content in data.items():
                        with st.expander(f"📄 {item_key}", expanded=False):
                            if isinstance(content, str):
                                st.markdown(content[:5000] + "..." if len(content) > 5000 else content)
                            else:
                                st.json(content)
                else:
                    st.warning("No 10-Q content found.")

            except Exception as e:
                logger.error(f"10-Q extraction error: {e}")
                st.error(f"Error extracting 10-Q: {str(e)}")


def main():
    """Main function to run the financial research page."""
    page = FinancialResearchPage()
    asyncio.run(page.render())


if __name__ == "__main__":
    main()
