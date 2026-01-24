"""
OpenAI-compatible tool schemas for financial tools.

These schemas are used by the router to bind tools to the LLM for native tool calling.
"""

from typing import List, Dict, Any
from .constants import ITEMS_10K_MAP, ITEMS_10Q_MAP, format_items_description


def build_tool_schemas() -> List[Dict[str, Any]]:
    """
    Build OpenAI-compatible tool schemas for all financial tools.

    Returns:
        List of tool definitions in OpenAI format
    """
    return [
        # ==================== PRICE DATA ====================
        {
            "type": "function",
            "function": {
                "name": "get_price_snapshot",
                "description": "Fetches the most recent price snapshot for a specific stock ticker, including the latest price, trading volume, and other open, high, low, and close price data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol to fetch the price snapshot for. For example, 'AAPL' for Apple."
                        }
                    },
                    "required": ["ticker"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_prices",
                "description": "Retrieves historical price data for a stock over a specified date range, including open, high, low, close prices, and volume.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol to fetch aggregated prices for. For example, 'AAPL' for Apple."
                        },
                        "interval": {
                            "type": "string",
                            "enum": ["minute", "day", "week", "month", "year"],
                            "default": "day",
                            "description": "The time interval for price data. Defaults to 'day'."
                        },
                        "interval_multiplier": {
                            "type": "integer",
                            "default": 1,
                            "description": "Multiplier for the interval. Defaults to 1."
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format. Must be in past. Required."
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format. Must be today or in the past. Required."
                        }
                    },
                    "required": ["ticker", "start_date", "end_date"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_crypto_price_snapshot",
                "description": "Fetches the most recent price snapshot for a specific cryptocurrency, including the latest price, trading volume, and 24h high/low. Ticker format: use 'CRYPTO-USD' for USD prices (e.g., 'BTC-USD'). Note: Only USD pairs are supported.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The crypto ticker symbol to fetch the price snapshot for. For example, 'BTC-USD' for Bitcoin."
                        }
                    },
                    "required": ["ticker"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_crypto_prices",
                "description": "Retrieves historical price data for a cryptocurrency over a specified date range. Returns close prices and volume (not OHLC). Ticker format: use 'CRYPTO-USD' for USD prices. Note: Only USD pairs supported, minute interval not available, max 365 days.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The crypto ticker symbol to fetch aggregated prices for. For example, 'BTC-USD' for Bitcoin."
                        },
                        "interval": {
                            "type": "string",
                            "enum": ["day", "week", "month", "year"],
                            "default": "day",
                            "description": "The time interval for price data. Defaults to 'day'. Note: 'minute' is not supported."
                        },
                        "interval_multiplier": {
                            "type": "integer",
                            "default": 1,
                            "description": "Multiplier for the interval. Defaults to 1."
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format. Required."
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format. Required."
                        }
                    },
                    "required": ["ticker", "start_date", "end_date"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_available_crypto_tickers",
                "description": "Retrieves the list of available cryptocurrency tickers that can be used with the crypto price tools.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },

        # ==================== FUNDAMENTALS ====================
        {
            "type": "function",
            "function": {
                "name": "get_income_statements",
                "description": "Fetches a company's income statements, detailing its revenues, expenses, net income, etc. over a reporting period. Useful for evaluating a company's profitability and operational efficiency.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol to fetch financial statements for. For example, 'AAPL' for Apple."
                        },
                        "period": {
                            "type": "string",
                            "enum": ["annual", "quarterly", "ttm"],
                            "description": "The reporting period for the financial statements. 'annual' for yearly, 'quarterly' for quarterly, and 'ttm' for trailing twelve months."
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "Maximum number of report periods to return (default: 10). Returns the most recent N periods based on the period type."
                        },
                        "report_period_gt": {
                            "type": "string",
                            "description": "Filter for financial statements with report periods after this date (YYYY-MM-DD)."
                        },
                        "report_period_gte": {
                            "type": "string",
                            "description": "Filter for financial statements with report periods on or after this date (YYYY-MM-DD)."
                        },
                        "report_period_lt": {
                            "type": "string",
                            "description": "Filter for financial statements with report periods before this date (YYYY-MM-DD)."
                        },
                        "report_period_lte": {
                            "type": "string",
                            "description": "Filter for financial statements with report periods on or before this date (YYYY-MM-DD)."
                        }
                    },
                    "required": ["ticker", "period"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_balance_sheets",
                "description": "Retrieves a company's balance sheets, providing a snapshot of its assets, liabilities, shareholders' equity, etc. at a specific point in time. Useful for assessing a company's financial position.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol to fetch financial statements for. For example, 'AAPL' for Apple."
                        },
                        "period": {
                            "type": "string",
                            "enum": ["annual", "quarterly", "ttm"],
                            "description": "The reporting period for the financial statements."
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "Maximum number of report periods to return (default: 10)."
                        },
                        "report_period_gt": {"type": "string"},
                        "report_period_gte": {"type": "string"},
                        "report_period_lt": {"type": "string"},
                        "report_period_lte": {"type": "string"}
                    },
                    "required": ["ticker", "period"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_cash_flow_statements",
                "description": "Retrieves a company's cash flow statements, showing how cash is generated and used across operating, investing, and financing activities. Useful for understanding a company's liquidity and solvency.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol to fetch financial statements for. For example, 'AAPL' for Apple."
                        },
                        "period": {
                            "type": "string",
                            "enum": ["annual", "quarterly", "ttm"],
                            "description": "The reporting period for the financial statements."
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "Maximum number of report periods to return (default: 10)."
                        },
                        "report_period_gt": {"type": "string"},
                        "report_period_gte": {"type": "string"},
                        "report_period_lt": {"type": "string"},
                        "report_period_lte": {"type": "string"}
                    },
                    "required": ["ticker", "period"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_all_financial_statements",
                "description": "Retrieves all three financial statements (income statements, balance sheets, and cash flow statements) for a company in a single API call. This is more efficient than calling each statement type separately when you need all three for comprehensive financial analysis.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol to fetch financial statements for. For example, 'AAPL' for Apple."
                        },
                        "period": {
                            "type": "string",
                            "enum": ["annual", "quarterly", "ttm"],
                            "description": "The reporting period for the financial statements."
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "Maximum number of report periods to return (default: 10)."
                        },
                        "report_period_gt": {"type": "string"},
                        "report_period_gte": {"type": "string"},
                        "report_period_lt": {"type": "string"},
                        "report_period_lte": {"type": "string"}
                    },
                    "required": ["ticker", "period"]
                }
            }
        },

        # ==================== METRICS & ESTIMATES ====================
        {
            "type": "function",
            "function": {
                "name": "get_financial_metrics_snapshot",
                "description": "Fetches a snapshot of the most current financial metrics for a company, including key indicators like market capitalization, P/E ratio, and dividend yield. Useful for a quick overview of a company's financial health.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol to fetch financial metrics snapshot for. For example, 'AAPL' for Apple."
                        }
                    },
                    "required": ["ticker"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_financial_metrics",
                "description": "Retrieves historical financial metrics for a company, such as P/E ratio, revenue per share, and enterprise value, over a specified period. Useful for trend analysis and historical performance evaluation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol to fetch financial metrics for. For example, 'AAPL' for Apple."
                        },
                        "period": {
                            "type": "string",
                            "enum": ["annual", "quarterly", "ttm"],
                            "default": "ttm",
                            "description": "The reporting period. 'annual' for yearly, 'quarterly' for quarterly, and 'ttm' for trailing twelve months."
                        },
                        "limit": {
                            "type": "integer",
                            "default": 4,
                            "description": "The number of past financial statements to retrieve."
                        },
                        "report_period": {
                            "type": "string",
                            "description": "Filter for financial metrics with an exact report period date (YYYY-MM-DD)."
                        },
                        "report_period_gt": {"type": "string"},
                        "report_period_gte": {"type": "string"},
                        "report_period_lt": {"type": "string"},
                        "report_period_lte": {"type": "string"}
                    },
                    "required": ["ticker"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_analyst_estimates",
                "description": "Retrieves analyst estimates for a given company ticker, including metrics like estimated EPS. Useful for understanding consensus expectations, assessing future growth prospects, and performing valuation analysis.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol to fetch analyst estimates for. For example, 'AAPL' for Apple."
                        },
                        "period": {
                            "type": "string",
                            "enum": ["annual", "quarterly"],
                            "default": "annual",
                            "description": "The period for the estimates, either 'annual' or 'quarterly'."
                        }
                    },
                    "required": ["ticker"]
                }
            }
        },

        # ==================== FILINGS ====================
        {
            "type": "function",
            "function": {
                "name": "get_filings",
                "description": "Retrieves metadata for SEC filings for a company. Returns accession numbers, filing types, and document URLs. This tool ONLY returns metadata - it does NOT return the actual text content from filings. To retrieve text content, use get_10K_filing_items, get_10Q_filing_items, or get_8K_filing_items.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol to fetch filings for. For example, 'AAPL' for Apple."
                        },
                        "filing_type": {
                            "type": "string",
                            "enum": ["10-K", "10-Q", "8-K"],
                            "description": "REQUIRED when searching for a specific filing type. Use '10-K' for annual reports, '10-Q' for quarterly reports, or '8-K' for current reports. If omitted, returns most recent filings of ANY type."
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "Maximum number of filings to return (default: 10). Returns the most recent N filings matching the criteria."
                        }
                    },
                    "required": ["ticker"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_10K_filing_items",
                "description": f"Retrieves specific sections (items) from a company's 10-K annual report. Use this to extract detailed information from specific sections of a 10-K filing, such as: Item-1: Business, Item-1A: Risk Factors, Item-7: Management's Discussion and Analysis, Item-8: Financial Statements and Supplementary Data. The optional 'item' parameter allows you to filter for specific sections.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol. For example, 'AAPL' for Apple."
                        },
                        "year": {
                            "type": "integer",
                            "description": "The year of the 10-K filing. For example, 2023."
                        },
                        "item": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": f"Optional list of specific items to retrieve from the 10-K. Valid items are:\n{format_items_description(ITEMS_10K_MAP)}\nIf not specified, all available items will be returned."
                        }
                    },
                    "required": ["ticker", "year"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_10Q_filing_items",
                "description": "Retrieves specific sections (items) from a company's 10-Q quarterly report. Use this to extract detailed information from specific sections of a 10-Q filing, such as: Item-1: Financial Statements, Item-2: Management's Discussion and Analysis, Item-3: Quantitative and Qualitative Disclosures About Market Risk, Item-4: Controls and Procedures.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol. For example, 'AAPL' for Apple."
                        },
                        "year": {
                            "type": "integer",
                            "description": "The year of the 10-Q filing. For example, 2023."
                        },
                        "quarter": {
                            "type": "integer",
                            "description": "The quarter of the 10-Q filing (1, 2, 3, or 4)."
                        },
                        "item": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": f"Optional list of specific items to retrieve from the 10-Q. Valid items are:\n{format_items_description(ITEMS_10Q_MAP)}\nIf not specified, all available items will be returned."
                        }
                    },
                    "required": ["ticker", "year", "quarter"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_8K_filing_items",
                "description": "Retrieves specific sections (items) from a company's 8-K current report. 8-K filings report material events such as acquisitions, financial results, management changes, and other significant corporate events. The accession_number parameter can be retrieved using the get_filings tool by filtering for 8-K filings.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol. For example, 'AAPL' for Apple."
                        },
                        "accession_number": {
                            "type": "string",
                            "description": "The SEC accession number for the 8-K filing. For example, '0000320193-24-000123'. This can be retrieved from the get_filings tool."
                        }
                    },
                    "required": ["ticker", "accession_number"]
                }
            }
        },

        # ==================== OTHER DATA ====================
        {
            "type": "function",
            "function": {
                "name": "get_news",
                "description": "Retrieves recent news articles for a given company ticker, covering financial announcements, market trends, and other significant events. Useful for staying up-to-date with market-moving information and investor sentiment.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol to fetch news for. For example, 'AAPL' for Apple."
                        },
                        "start_date": {
                            "type": "string",
                            "description": "The start date to fetch news from (YYYY-MM-DD)."
                        },
                        "end_date": {
                            "type": "string",
                            "description": "The end date to fetch news to (YYYY-MM-DD)."
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "The number of news articles to retrieve. Max is 100."
                        }
                    },
                    "required": ["ticker"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_insider_trades",
                "description": "Retrieves insider trading transactions for a given company ticker. Insider trades include purchases and sales of company stock by executives, directors, and other insiders. This data is sourced from SEC Form 4 filings. Use filing_date filters to narrow down results by date range.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol to fetch insider trades for. For example, 'AAPL' for Apple."
                        },
                        "limit": {
                            "type": "integer",
                            "default": 100,
                            "description": "Maximum number of insider trades to return (default: 100, max: 1000)."
                        },
                        "filing_date": {
                            "type": "string",
                            "description": "Exact filing date to filter by (YYYY-MM-DD)."
                        },
                        "filing_date_gte": {
                            "type": "string",
                            "description": "Filter for trades with filing date greater than or equal to this date (YYYY-MM-DD)."
                        },
                        "filing_date_lte": {
                            "type": "string",
                            "description": "Filter for trades with filing date less than or equal to this date (YYYY-MM-DD)."
                        },
                        "filing_date_gt": {
                            "type": "string",
                            "description": "Filter for trades with filing date greater than this date (YYYY-MM-DD)."
                        },
                        "filing_date_lt": {
                            "type": "string",
                            "description": "Filter for trades with filing date less than this date (YYYY-MM-DD)."
                        }
                    },
                    "required": ["ticker"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_segmented_revenues",
                "description": "Provides a detailed breakdown of a company's revenue by operating segments, such as products, services, or geographic regions. Useful for analyzing the composition of a company's revenue.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "The stock ticker symbol to fetch segmented revenues for. For example, 'AAPL' for Apple."
                        },
                        "period": {
                            "type": "string",
                            "enum": ["annual", "quarterly"],
                            "description": "The reporting period for the segmented revenues. 'annual' for yearly, 'quarterly' for quarterly."
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "The number of past periods to retrieve."
                        }
                    },
                    "required": ["ticker", "period"]
                }
            }
        }
    ]
