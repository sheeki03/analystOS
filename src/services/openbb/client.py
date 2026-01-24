"""
OpenBB Platform Client

Wraps OpenBB Platform SDK for equity data access with yfinance fallback.
Handles initialization, provider configuration, and data retrieval.

Note: OpenBB has compatibility issues with Python 3.13+. This client
uses yfinance directly as a fallback when OpenBB fails.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from dataclasses import dataclass

from .config import OpenBBConfig

logger = logging.getLogger(__name__)


@dataclass
class PriceBar:
    """Single price bar data."""
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None


@dataclass
class PriceSnapshot:
    """Current price snapshot."""
    ticker: str
    price: float
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    vwap: Optional[float] = None
    timestamp: Optional[datetime] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None


class OpenBBClient:
    """
    Client for OpenBB Platform SDK with yfinance fallback.

    Provides methods for equity data retrieval.
    Uses yfinance directly when OpenBB has Python version issues.
    """

    def __init__(self, config: Optional[OpenBBConfig] = None):
        """
        Initialize OpenBB client.

        Args:
            config: OpenBB configuration (loads from env if not provided)
        """
        self.config = config or OpenBBConfig.from_env()
        self._obb = None
        self._initialized = False
        self._use_yfinance_fallback = False

    def _ensure_initialized(self) -> None:
        """Ensure OpenBB is initialized with API keys, or use yfinance fallback."""
        if self._initialized:
            return

        try:
            from openbb import obb

            # Configure API keys
            if self.config.fmp_api_key:
                obb.user.credentials.fmp_api_key = self.config.fmp_api_key

            if self.config.finnhub_api_key:
                obb.user.credentials.finnhub_api_key = self.config.finnhub_api_key

            if self.config.openbb_pat:
                obb.user.credentials.openbb_api_key = self.config.openbb_pat

            # Test if equity module works (Python 3.13+ compatibility issue)
            try:
                _ = obb.equity
                self._obb = obb
                logger.info("OpenBB Platform initialized successfully")
            except ImportError as e:
                logger.warning(f"OpenBB equity module has issues, using yfinance fallback: {e}")
                self._use_yfinance_fallback = True

            self._initialized = True

        except ImportError:
            logger.warning("OpenBB not installed, using yfinance fallback")
            self._use_yfinance_fallback = True
            self._initialized = True
        except Exception as e:
            logger.warning(f"OpenBB init failed, using yfinance fallback: {e}")
            self._use_yfinance_fallback = True
            self._initialized = True

    def _to_dict_list(self, result: Any) -> List[Dict[str, Any]]:
        """Convert OpenBB result to list of dictionaries."""
        if hasattr(result, 'to_df'):
            df = result.to_df()
            return df.to_dict('records')
        elif hasattr(result, 'results') and result.results:
            return [r.model_dump() if hasattr(r, 'model_dump') else dict(r) for r in result.results]
        return []

    # ==================== YFINANCE FALLBACK ====================

    def _yf_get_price_snapshot(self, ticker: str) -> Dict[str, Any]:
        """Get price snapshot via yfinance."""
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "ticker": ticker,
            "open": info.get('open') or info.get('regularMarketOpen'),
            "high": info.get('dayHigh') or info.get('regularMarketDayHigh'),
            "low": info.get('dayLow') or info.get('regularMarketDayLow'),
            "close": info.get('currentPrice') or info.get('regularMarketPrice'),
            "volume": info.get('volume') or info.get('regularMarketVolume'),
            "vwap": None,
            "timestamp": datetime.now().isoformat(),
            "change": info.get('regularMarketChange'),
            "change_percent": info.get('regularMarketChangePercent'),
            "market_cap": info.get('marketCap'),
            "pe_ratio": info.get('trailingPE'),
            "52_week_high": info.get('fiftyTwoWeekHigh'),
            "52_week_low": info.get('fiftyTwoWeekLow'),
        }

    def _yf_get_prices(self, ticker: str, start_date: str, end_date: str,
                       interval: str = "day") -> List[Dict[str, Any]]:
        """Get historical prices via yfinance."""
        import yfinance as yf

        # Map interval to yfinance format
        interval_map = {
            "minute": "1m",
            "day": "1d",
            "week": "1wk",
            "month": "1mo",
        }
        yf_interval = interval_map.get(interval, "1d")

        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date, interval=yf_interval)

        prices = []
        for idx, row in hist.iterrows():
            prices.append({
                "date": idx.strftime("%Y-%m-%d") if hasattr(idx, 'strftime') else str(idx)[:10],
                "open": row.get('Open'),
                "high": row.get('High'),
                "low": row.get('Low'),
                "close": row.get('Close'),
                "volume": int(row.get('Volume', 0)),
                "vwap": None,
            })
        return prices

    def _yf_get_income_statements(self, ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get income statements via yfinance."""
        import yfinance as yf
        stock = yf.Ticker(ticker)
        financials = stock.income_stmt

        if financials is None or financials.empty:
            return []

        statements = []
        for col in financials.columns[:limit]:
            stmt = {"period_ending": col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col)}
            for idx, val in financials[col].items():
                key = str(idx).lower().replace(' ', '_')
                stmt[key] = val if not (hasattr(val, '__float__') and str(val) == 'nan') else None
            statements.append(stmt)
        return statements

    def _yf_get_balance_sheets(self, ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get balance sheets via yfinance."""
        import yfinance as yf
        stock = yf.Ticker(ticker)
        balance = stock.balance_sheet

        if balance is None or balance.empty:
            return []

        sheets = []
        for col in balance.columns[:limit]:
            sheet = {"period_ending": col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col)}
            for idx, val in balance[col].items():
                key = str(idx).lower().replace(' ', '_')
                sheet[key] = val if not (hasattr(val, '__float__') and str(val) == 'nan') else None
            sheets.append(sheet)
        return sheets

    def _yf_get_cash_flow_statements(self, ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get cash flow statements via yfinance."""
        import yfinance as yf
        stock = yf.Ticker(ticker)
        cashflow = stock.cashflow

        if cashflow is None or cashflow.empty:
            return []

        statements = []
        for col in cashflow.columns[:limit]:
            stmt = {"period_ending": col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col)}
            for idx, val in cashflow[col].items():
                key = str(idx).lower().replace(' ', '_')
                stmt[key] = val if not (hasattr(val, '__float__') and str(val) == 'nan') else None
            statements.append(stmt)
        return statements

    def _yf_get_financial_metrics_snapshot(self, ticker: str) -> Dict[str, Any]:
        """Get financial metrics via yfinance."""
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "ticker": ticker,
            "market_cap": info.get('marketCap'),
            "enterprise_value": info.get('enterpriseValue'),
            "pe_ratio": info.get('trailingPE'),
            "forward_pe": info.get('forwardPE'),
            "peg_ratio": info.get('pegRatio'),
            "price_to_book": info.get('priceToBook'),
            "price_to_sales": info.get('priceToSalesTrailing12Months'),
            "ev_to_revenue": info.get('enterpriseToRevenue'),
            "ev_to_ebitda": info.get('enterpriseToEbitda'),
            "profit_margin": info.get('profitMargins'),
            "operating_margin": info.get('operatingMargins'),
            "return_on_assets": info.get('returnOnAssets'),
            "return_on_equity": info.get('returnOnEquity'),
            "revenue": info.get('totalRevenue'),
            "revenue_per_share": info.get('revenuePerShare'),
            "quarterly_revenue_growth": info.get('revenueGrowth'),
            "gross_profit": info.get('grossProfits'),
            "ebitda": info.get('ebitda'),
            "net_income": info.get('netIncomeToCommon'),
            "eps": info.get('trailingEps'),
            "forward_eps": info.get('forwardEps'),
            "book_value": info.get('bookValue'),
            "dividend_rate": info.get('dividendRate'),
            "dividend_yield": info.get('dividendYield'),
            "payout_ratio": info.get('payoutRatio'),
            "beta": info.get('beta'),
            "52_week_high": info.get('fiftyTwoWeekHigh'),
            "52_week_low": info.get('fiftyTwoWeekLow'),
            "50_day_average": info.get('fiftyDayAverage'),
            "200_day_average": info.get('twoHundredDayAverage'),
            "shares_outstanding": info.get('sharesOutstanding'),
            "float_shares": info.get('floatShares'),
            "short_ratio": info.get('shortRatio'),
            "short_percent_of_float": info.get('shortPercentOfFloat'),
        }

    def _yf_get_news(self, ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get company news via yfinance."""
        import yfinance as yf
        stock = yf.Ticker(ticker)
        news = stock.news

        if not news:
            return []

        articles = []
        for article in news[:limit]:
            articles.append({
                "title": article.get('title'),
                "publisher": article.get('publisher'),
                "link": article.get('link'),
                "published_utc": article.get('providerPublishTime'),
                "type": article.get('type'),
                "thumbnail": article.get('thumbnail', {}).get('resolutions', [{}])[0].get('url') if article.get('thumbnail') else None,
                "related_tickers": article.get('relatedTickers', []),
            })
        return articles

    def _yf_get_analyst_estimates(self, ticker: str) -> List[Dict[str, Any]]:
        """Get analyst estimates via yfinance."""
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info

        # yfinance doesn't have detailed analyst estimates like FMP
        # Return summary data available in info
        return [{
            "ticker": ticker,
            "target_high_price": info.get('targetHighPrice'),
            "target_low_price": info.get('targetLowPrice'),
            "target_mean_price": info.get('targetMeanPrice'),
            "target_median_price": info.get('targetMedianPrice'),
            "recommendation_mean": info.get('recommendationMean'),
            "recommendation_key": info.get('recommendationKey'),
            "number_of_analyst_opinions": info.get('numberOfAnalystOpinions'),
            "current_price": info.get('currentPrice'),
        }]

    # ==================== PRICE DATA ====================

    def get_price_snapshot(self, ticker: str) -> Dict[str, Any]:
        """
        Get current price snapshot for a stock.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")

        Returns:
            Dictionary with price snapshot data
        """
        self._ensure_initialized()

        # Use yfinance fallback if needed
        if self._use_yfinance_fallback:
            return self._yf_get_price_snapshot(ticker)

        try:
            result = self._obb.equity.price.quote(
                symbol=ticker,
                provider=self.config.default_equity_provider
            )

            if result.results:
                data = result.results[0]
                return {
                    "ticker": ticker,
                    "open": getattr(data, 'open', None),
                    "high": getattr(data, 'high', None),
                    "low": getattr(data, 'low', None),
                    "close": getattr(data, 'price', None) or getattr(data, 'last_price', None),
                    "volume": getattr(data, 'volume', None),
                    "vwap": getattr(data, 'vwap', None),
                    "timestamp": getattr(data, 'timestamp', None) or datetime.now().isoformat(),
                    "change": getattr(data, 'change', None),
                    "change_percent": getattr(data, 'change_percent', None),
                    "market_cap": getattr(data, 'market_cap', None),
                    "pe_ratio": getattr(data, 'pe', None),
                    "52_week_high": getattr(data, 'year_high', None),
                    "52_week_low": getattr(data, 'year_low', None),
                }
            return {}

        except Exception as e:
            logger.error(f"Failed to get price snapshot for {ticker}: {e}")
            raise

    def get_prices(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        interval: str = "day",
        interval_multiplier: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data for a stock.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Time interval (day, week, month)
            interval_multiplier: Multiplier for interval

        Returns:
            List of price bar dictionaries
        """
        self._ensure_initialized()

        # Use yfinance fallback if needed
        if self._use_yfinance_fallback:
            return self._yf_get_prices(ticker, start_date, end_date, interval)

        # Map interval to OpenBB interval string
        interval_map = {
            "minute": "1m",
            "day": "1d",
            "week": "1wk",
            "month": "1mo",
            "year": "1y",
        }
        obb_interval = interval_map.get(interval, "1d")

        # Handle multiplier (e.g., 5-minute bars)
        if interval_multiplier > 1 and interval == "minute":
            obb_interval = f"{interval_multiplier}m"

        try:
            result = self._obb.equity.price.historical(
                symbol=ticker,
                start_date=start_date,
                end_date=end_date,
                interval=obb_interval,
                provider=self.config.default_equity_provider
            )

            prices = []
            for row in self._to_dict_list(result):
                prices.append({
                    "date": row.get("date"),
                    "open": row.get("open"),
                    "high": row.get("high"),
                    "low": row.get("low"),
                    "close": row.get("close"),
                    "volume": row.get("volume"),
                    "vwap": row.get("vwap"),
                })

            return prices

        except Exception as e:
            logger.error(f"Failed to get prices for {ticker}: {e}")
            raise

    # ==================== FUNDAMENTALS ====================

    def get_income_statements(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 10,
        **filters
    ) -> List[Dict[str, Any]]:
        """
        Get income statements for a company.

        Args:
            ticker: Stock ticker symbol
            period: "annual", "quarterly", or "ttm"
            limit: Number of periods to return
            **filters: Optional date filters (report_period_gte, etc.)

        Returns:
            List of income statement dictionaries
        """
        self._ensure_initialized()

        # Use yfinance fallback if needed
        if self._use_yfinance_fallback:
            statements = self._yf_get_income_statements(ticker, limit)
            return self._apply_report_period_filters(statements, filters)

        try:
            result = self._obb.equity.fundamental.income(
                symbol=ticker,
                period=period,
                limit=limit,
                provider=self.config.default_equity_provider
            )
            statements = self._to_dict_list(result)
            return self._apply_report_period_filters(statements, filters)

        except Exception as e:
            logger.error(f"Failed to get income statements for {ticker}: {e}")
            raise

    def get_balance_sheets(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 10,
        **filters
    ) -> List[Dict[str, Any]]:
        """Get balance sheets for a company."""
        self._ensure_initialized()

        # Use yfinance fallback if needed
        if self._use_yfinance_fallback:
            sheets = self._yf_get_balance_sheets(ticker, limit)
            return self._apply_report_period_filters(sheets, filters)

        try:
            result = self._obb.equity.fundamental.balance(
                symbol=ticker,
                period=period,
                limit=limit,
                provider=self.config.default_equity_provider
            )
            statements = self._to_dict_list(result)
            return self._apply_report_period_filters(statements, filters)

        except Exception as e:
            logger.error(f"Failed to get balance sheets for {ticker}: {e}")
            raise

    def get_cash_flow_statements(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 10,
        **filters
    ) -> List[Dict[str, Any]]:
        """Get cash flow statements for a company."""
        self._ensure_initialized()

        # Use yfinance fallback if needed
        if self._use_yfinance_fallback:
            statements = self._yf_get_cash_flow_statements(ticker, limit)
            return self._apply_report_period_filters(statements, filters)

        try:
            result = self._obb.equity.fundamental.cash(
                symbol=ticker,
                period=period,
                limit=limit,
                provider=self.config.default_equity_provider
            )
            statements = self._to_dict_list(result)
            return self._apply_report_period_filters(statements, filters)

        except Exception as e:
            logger.error(f"Failed to get cash flow statements for {ticker}: {e}")
            raise

    def get_all_financial_statements(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 10,
        **filters
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get all financial statements (income, balance, cash flow) for a company."""
        return {
            "income_statements": self.get_income_statements(ticker, period, limit, **filters),
            "balance_sheets": self.get_balance_sheets(ticker, period, limit, **filters),
            "cash_flow_statements": self.get_cash_flow_statements(ticker, period, limit, **filters),
        }

    def _apply_report_period_filters(
        self,
        statements: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply report_period filters to statements."""
        if not filters:
            return statements

        filtered = statements
        for stmt in filtered[:]:
            report_date = stmt.get("period_ending") or stmt.get("date") or stmt.get("fiscal_period")
            if not report_date:
                continue

            # Convert to date string if datetime
            if hasattr(report_date, "strftime"):
                report_date = report_date.strftime("%Y-%m-%d")

            if filters.get("report_period_gt") and report_date <= filters["report_period_gt"]:
                filtered.remove(stmt)
            elif filters.get("report_period_gte") and report_date < filters["report_period_gte"]:
                filtered.remove(stmt)
            elif filters.get("report_period_lt") and report_date >= filters["report_period_lt"]:
                filtered.remove(stmt)
            elif filters.get("report_period_lte") and report_date > filters["report_period_lte"]:
                filtered.remove(stmt)

        return filtered

    # ==================== METRICS ====================

    def get_financial_metrics_snapshot(self, ticker: str) -> Dict[str, Any]:
        """Get current financial metrics snapshot."""
        self._ensure_initialized()

        # Use yfinance fallback if needed
        if self._use_yfinance_fallback:
            return self._yf_get_financial_metrics_snapshot(ticker)

        try:
            result = self._obb.equity.fundamental.metrics(
                symbol=ticker,
                provider=self.config.default_equity_provider
            )

            if result.results:
                data = result.results[0]
                return data.model_dump() if hasattr(data, 'model_dump') else dict(data)
            return {}

        except Exception as e:
            logger.error(f"Failed to get metrics snapshot for {ticker}: {e}")
            raise

    def get_financial_metrics(
        self,
        ticker: str,
        period: str = "ttm",
        limit: int = 4,
        **filters
    ) -> List[Dict[str, Any]]:
        """Get historical financial metrics."""
        self._ensure_initialized()

        # Use yfinance fallback if needed (only returns current snapshot)
        if self._use_yfinance_fallback:
            return [self._yf_get_financial_metrics_snapshot(ticker)]

        try:
            result = self._obb.equity.fundamental.metrics(
                symbol=ticker,
                period=period,
                limit=limit,
                provider=self.config.default_equity_provider
            )
            metrics = self._to_dict_list(result)
            return self._apply_report_period_filters(metrics, filters)

        except Exception as e:
            logger.error(f"Failed to get metrics for {ticker}: {e}")
            raise

    # ==================== FILINGS ====================

    def get_filings(
        self,
        ticker: str,
        filing_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get SEC filings metadata for a company."""
        self._ensure_initialized()

        # yfinance doesn't provide SEC filings - return empty list with note
        if self._use_yfinance_fallback:
            logger.warning(f"SEC filings not available via yfinance for {ticker}")
            return []

        try:
            kwargs = {
                "symbol": ticker,
                "limit": limit,
                "provider": self.config.default_filings_provider,
            }
            if filing_type:
                kwargs["form_type"] = filing_type

            result = self._obb.equity.fundamental.filings(**kwargs)
            return self._to_dict_list(result)

        except Exception as e:
            logger.error(f"Failed to get filings for {ticker}: {e}")
            raise

    def get_10k_filing_items(
        self,
        ticker: str,
        year: int,
        item: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get specific items from 10-K filing."""
        self._ensure_initialized()

        # yfinance doesn't provide SEC filing content
        if self._use_yfinance_fallback:
            logger.warning(f"SEC filing content not available via yfinance for {ticker}")
            return {"error": "SEC filings not available via yfinance fallback", "ticker": ticker, "year": year}

        try:
            # Use SEC EDGAR directly for filing content
            result = self._obb.equity.fundamental.filings(
                symbol=ticker,
                form_type="10-K",
                limit=5,
                provider="sec"
            )

            filings = self._to_dict_list(result)

            # Find the filing for the requested year
            target_filing = None
            for f in filings:
                filing_date = f.get("filing_date") or f.get("accepted_date")
                if filing_date:
                    if hasattr(filing_date, "year"):
                        filing_year = filing_date.year
                    else:
                        filing_year = int(str(filing_date)[:4])
                    if filing_year == year:
                        target_filing = f
                        break

            if not target_filing:
                return {"error": f"No 10-K filing found for {ticker} in {year}"}

            return {
                "ticker": ticker,
                "year": year,
                "filing": target_filing,
                "items_requested": item,
                # Note: Full item extraction requires additional SEC EDGAR parsing
            }

        except Exception as e:
            logger.error(f"Failed to get 10-K items for {ticker}: {e}")
            raise

    def get_10q_filing_items(
        self,
        ticker: str,
        year: int,
        quarter: int,
        item: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get specific items from 10-Q filing."""
        self._ensure_initialized()

        # yfinance doesn't provide SEC filing content
        if self._use_yfinance_fallback:
            logger.warning(f"SEC filing content not available via yfinance for {ticker}")
            return {"error": "SEC filings not available via yfinance fallback", "ticker": ticker, "year": year, "quarter": quarter}

        try:
            result = self._obb.equity.fundamental.filings(
                symbol=ticker,
                form_type="10-Q",
                limit=10,
                provider="sec"
            )

            filings = self._to_dict_list(result)

            # Find the filing for the requested year and quarter
            target_filing = None
            for f in filings:
                filing_date = f.get("filing_date") or f.get("accepted_date")
                if filing_date:
                    if hasattr(filing_date, "year"):
                        filing_year = filing_date.year
                        filing_month = filing_date.month
                    else:
                        filing_year = int(str(filing_date)[:4])
                        filing_month = int(str(filing_date)[5:7])

                    # Map month to quarter
                    filing_quarter = (filing_month - 1) // 3 + 1

                    if filing_year == year and filing_quarter == quarter:
                        target_filing = f
                        break

            if not target_filing:
                return {"error": f"No 10-Q filing found for {ticker} in Q{quarter} {year}"}

            return {
                "ticker": ticker,
                "year": year,
                "quarter": quarter,
                "filing": target_filing,
                "items_requested": item,
            }

        except Exception as e:
            logger.error(f"Failed to get 10-Q items for {ticker}: {e}")
            raise

    def get_8k_filing_items(
        self,
        ticker: str,
        accession_number: str,
    ) -> Dict[str, Any]:
        """Get specific items from 8-K filing by accession number."""
        self._ensure_initialized()

        # yfinance doesn't provide SEC filing content
        if self._use_yfinance_fallback:
            logger.warning(f"SEC filing content not available via yfinance for {ticker}")
            return {"error": "SEC filings not available via yfinance fallback", "ticker": ticker, "accession_number": accession_number}

        try:
            result = self._obb.equity.fundamental.filings(
                symbol=ticker,
                form_type="8-K",
                limit=50,
                provider="sec"
            )

            filings = self._to_dict_list(result)

            # Find the filing by accession number
            target_filing = None
            for f in filings:
                if f.get("accession_number") == accession_number:
                    target_filing = f
                    break

            if not target_filing:
                return {"error": f"No 8-K filing found with accession number {accession_number}"}

            return {
                "ticker": ticker,
                "accession_number": accession_number,
                "filing": target_filing,
            }

        except Exception as e:
            logger.error(f"Failed to get 8-K items for {ticker}: {e}")
            raise

    # ==================== NEWS ====================

    def get_news(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get company news articles."""
        self._ensure_initialized()

        # Use yfinance fallback if needed
        if self._use_yfinance_fallback:
            return self._yf_get_news(ticker, limit)

        try:
            kwargs = {
                "symbol": ticker,
                "limit": min(limit, 100),
                "provider": self.config.default_news_provider,
            }
            if start_date:
                kwargs["start_date"] = start_date
            if end_date:
                kwargs["end_date"] = end_date

            result = self._obb.equity.news(
                **kwargs
            )
            return self._to_dict_list(result)

        except Exception as e:
            logger.error(f"Failed to get news for {ticker}: {e}")
            raise

    # ==================== ESTIMATES ====================

    def get_analyst_estimates(
        self,
        ticker: str,
        period: str = "annual",
    ) -> List[Dict[str, Any]]:
        """Get analyst estimates."""
        self._ensure_initialized()

        # Use yfinance fallback if needed
        if self._use_yfinance_fallback:
            return self._yf_get_analyst_estimates(ticker)

        try:
            result = self._obb.equity.estimates.consensus(
                symbol=ticker,
                provider=self.config.default_equity_provider
            )
            return self._to_dict_list(result)

        except Exception as e:
            logger.error(f"Failed to get analyst estimates for {ticker}: {e}")
            raise

    # ==================== INSIDER TRADES ====================

    def get_insider_trades(
        self,
        ticker: str,
        limit: int = 100,
        **filters
    ) -> List[Dict[str, Any]]:
        """Get insider trading transactions."""
        self._ensure_initialized()

        # yfinance doesn't provide insider trades data
        if self._use_yfinance_fallback:
            logger.warning(f"Insider trades not available via yfinance for {ticker}")
            return []

        try:
            result = self._obb.equity.ownership.insider_trading(
                symbol=ticker,
                limit=min(limit, 1000),
                provider=self.config.default_equity_provider
            )
            trades = self._to_dict_list(result)

            # Apply filing_date filters
            if filters:
                filtered = []
                for trade in trades:
                    filing_date = trade.get("filing_date")
                    if not filing_date:
                        filtered.append(trade)
                        continue

                    if hasattr(filing_date, "strftime"):
                        filing_date = filing_date.strftime("%Y-%m-%d")

                    include = True
                    if filters.get("filing_date") and filing_date != filters["filing_date"]:
                        include = False
                    if filters.get("filing_date_gte") and filing_date < filters["filing_date_gte"]:
                        include = False
                    if filters.get("filing_date_lte") and filing_date > filters["filing_date_lte"]:
                        include = False
                    if filters.get("filing_date_gt") and filing_date <= filters["filing_date_gt"]:
                        include = False
                    if filters.get("filing_date_lt") and filing_date >= filters["filing_date_lt"]:
                        include = False

                    if include:
                        filtered.append(trade)
                return filtered

            return trades

        except Exception as e:
            logger.error(f"Failed to get insider trades for {ticker}: {e}")
            raise

    # ==================== SEGMENTED REVENUES ====================

    def get_segmented_revenues(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Get revenue breakdown by segment."""
        self._ensure_initialized()

        # yfinance doesn't provide segmented revenue data
        if self._use_yfinance_fallback:
            logger.warning(f"Segmented revenues not available via yfinance for {ticker}")
            return {"ticker": ticker, "segments": []}

        try:
            result = self._obb.equity.fundamental.revenue_per_segment(
                symbol=ticker,
                period=period,
                provider=self.config.default_equity_provider
            )
            segments = self._to_dict_list(result)
            return {
                "ticker": ticker,
                "segments": segments,
            }

        except Exception as e:
            logger.error(f"Failed to get segmented revenues for {ticker}: {e}")
            raise
