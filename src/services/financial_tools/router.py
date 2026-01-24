"""
Financial Search Router

Uses OpenRouter LLM with native tool calling to route natural language queries
to appropriate financial data tools.

Output format matches Dexter's financial-search.ts exactly:
- Uses tool-name as key, or tool_ticker for multiple calls to same tool
- Includes _errors array for failed tool calls
"""

import json
import asyncio
import inspect
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from .types import format_tool_result
from .tools import FINANCIAL_TOOL_MAP
from .schemas import build_tool_schemas

logger = logging.getLogger(__name__)


def _get_current_date() -> str:
    """Get current date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")


def _build_router_prompt() -> str:
    """Build the system prompt for the financial search router."""
    return f"""You are a financial data routing assistant.
Current date: {_get_current_date()}

Given a user's natural language query about financial data, call the appropriate financial tool(s).

## Guidelines

1. **Ticker Resolution**: Convert company names to ticker symbols:
   - Apple → AAPL, Tesla → TSLA, Microsoft → MSFT, Amazon → AMZN
   - Google/Alphabet → GOOGL, Meta/Facebook → META, Nvidia → NVDA

2. **Date Inference**: Convert relative dates to YYYY-MM-DD format:
   - "last year" → start_date 1 year ago, end_date today
   - "last quarter" → start_date 3 months ago, end_date today
   - "past 5 years" → start_date 5 years ago, end_date today
   - "YTD" → start_date Jan 1 of current year, end_date today

3. **Tool Selection**:
   - For "current" or "latest" data, use snapshot tools (get_price_snapshot, get_financial_metrics_snapshot)
   - For "historical" or "over time" data, use date-range tools
   - For P/E ratio, market cap, valuation metrics → get_financial_metrics_snapshot
   - For revenue, earnings, profitability → get_income_statements
   - For debt, assets, equity → get_balance_sheets
   - For cash flow, free cash flow → get_cash_flow_statements
   - For comprehensive analysis → get_all_financial_statements

4. **Crypto Tools**:
   - For cryptocurrency prices, use get_crypto_price_snapshot or get_crypto_prices
   - Crypto tickers must use format "SYMBOL-USD" (e.g., "BTC-USD", "ETH-USD")
   - Only USD pairs are supported (not BTC-ETH)

5. **Efficiency**:
   - Prefer specific tools over general ones when possible
   - Use get_all_financial_statements only when multiple statement types needed
   - For comparisons between companies, call the same tool for each ticker

Call the appropriate tool(s) now."""


class FinancialSearchRouter:
    """
    Routes natural language financial queries to appropriate tools using LLM.

    Uses OpenRouter's chat completion with tool calling to intelligently
    select and execute financial data tools.
    """

    def __init__(self, model: Optional[str] = None):
        """
        Initialize the router.

        Args:
            model: Optional model override (uses primary_model if not specified)
        """
        from src.openrouter import OpenRouterClient
        self.client = OpenRouterClient()
        self.model = model
        self.tool_schemas = build_tool_schemas()

    async def search(self, query: str) -> str:
        """
        Execute a natural language financial search query.

        Args:
            query: Natural language query about financial data

        Returns:
            JSON string matching Dexter's formatToolResult format with combined data
        """
        # Build messages for LLM
        messages = [
            {"role": "system", "content": _build_router_prompt()},
            {"role": "user", "content": query}
        ]

        # Call LLM with tools
        response = await self.client.chat_completion_with_tools(
            messages=messages,
            tools=self.tool_schemas,
            model=self.model,
            tool_choice="auto"
        )

        # Check for tool calls
        tool_calls = response.get("tool_calls", [])
        if not tool_calls:
            # No tools selected - return error
            return format_tool_result({"error": "No tools selected for query"}, [])

        # Execute tool calls in parallel
        results = await self._execute_tool_calls(tool_calls)

        # Build combined data matching Dexter format (financial-search.ts:160-176)
        combined_data: Dict[str, Any] = {}
        all_urls: List[str] = []
        errors: List[Dict[str, Any]] = []

        for result in results:
            if result["error"] is None:
                # Use tool name as key, or tool_ticker for multiple calls
                ticker = result["args"].get("ticker")
                key = f"{result['tool']}_{ticker}" if ticker else result["tool"]
                combined_data[key] = result["data"]
                all_urls.extend(result["source_urls"])
            else:
                errors.append({
                    "tool": result["tool"],
                    "args": result["args"],
                    "error": result["error"]
                })

        # Add _errors block if any failures (matches Dexter:170-176)
        if errors:
            combined_data["_errors"] = errors

        return format_tool_result(combined_data, all_urls)

    async def _execute_tool_calls(self, tool_calls: List[dict]) -> List[dict]:
        """
        Execute tool calls and return results.

        Args:
            tool_calls: List of tool call objects from LLM response

        Returns:
            List of result dictionaries with tool, args, data, source_urls, error
        """
        async def execute_one(tc: dict) -> dict:
            func_name = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"])

            try:
                tool_func = FINANCIAL_TOOL_MAP.get(func_name)
                if not tool_func:
                    raise ValueError(f"Tool '{func_name}' not found")

                # Use **args to unpack as keyword arguments (matches Dexter's tool.invoke(tc.args))
                # Handle both sync and async functions
                if inspect.iscoroutinefunction(tool_func):
                    raw_result = await tool_func(**args)
                else:
                    raw_result = tool_func(**args)

                parsed = json.loads(raw_result)

                return {
                    "tool": func_name,
                    "args": args,
                    "data": parsed["data"],
                    "source_urls": parsed.get("sourceUrls", []),
                    "error": None
                }
            except Exception as e:
                logger.error(f"Tool {func_name} failed: {e}")
                return {
                    "tool": func_name,
                    "args": args,
                    "data": None,
                    "source_urls": [],
                    "error": str(e)
                }

        return await asyncio.gather(*[execute_one(tc) for tc in tool_calls])


async def financial_search(query: str, model: Optional[str] = None) -> str:
    """
    Convenience function for single financial search queries.

    Args:
        query: Natural language query about financial data
        model: Optional model override

    Returns:
        JSON string with search results
    """
    router = FinancialSearchRouter(model=model)
    return await router.search(query)
