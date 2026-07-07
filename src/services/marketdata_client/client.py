"""
Thin, optional client over a private market-data warehouse.

analystOS can read commodities, COT positioning, warehouse stocks, the China
copper import-arbitrage window, and issuer market-cap history from a
separately-maintained private market-data warehouse. That warehouse is a
read-only DuckDB database (silver views + gold tables) whose table/view names
are stable regardless of how the database was produced, so everything here is
just SQL against a handful of named tables.

Configuration (all optional — absence degrades gracefully and NEVER raises at
import, matching analystOS's optional-provider style, e.g. the OpenBB client's
yfinance fallback):

* ``MARKETDATA_WAREHOUSE_PATH`` — filesystem path to a prebuilt read-only
  ``.duckdb`` file (a synced warehouse snapshot). Preferred: it needs only
  ``duckdb`` installed and no other package.
* ``MARKETDATA_RELEASE`` — a release identifier (or a local release-store
  directory) used together with the optional ``marketdata`` package. When that
  package is installed it builds the warehouse itself, reading any remote-store
  credentials from its own environment configuration; analystOS never handles
  those secrets.

If neither is configured — or the required optional dependency is missing —
callers get a clear "unavailable" signal (``configured`` is ``False`` or a
:class:`MarketDataUnavailable` is raised from a query) instead of a crash.

Heavy dependencies (``duckdb``, the ``marketdata`` package, ``pandas``) are
imported lazily inside methods so importing this module is always cheap.
"""

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ENV_WAREHOUSE_PATH = "MARKETDATA_WAREHOUSE_PATH"
ENV_RELEASE = "MARKETDATA_RELEASE"

NOT_CONFIGURED_MESSAGE = (
    "marketdata warehouse not configured; set MARKETDATA_WAREHOUSE_PATH to a "
    "prebuilt read-only .duckdb file, or install the optional 'marketdata' "
    "package and set MARKETDATA_RELEASE"
)


class MarketDataUnavailable(Exception):
    """The warehouse is configured but cannot be reached right now.

    Raised when an optional dependency is missing, the configured file does
    not exist, or a configured remote store is not reachable. Callers should
    treat this as a soft/unavailable condition, not an application error.
    """


def _coerce(value: Any) -> Any:
    """Return a JSON-serializable version of one cell value.

    Handles the types warehouse rows carry across both backends: python
    ``date``/``datetime`` (DuckDB file backend) and pandas ``Timestamp`` /
    numpy scalars / ``Decimal`` / ``NaN`` / ``NaT`` (marketdata-package
    backend). ``NaN``/``NaT``/``inf`` become ``None`` (not valid JSON).
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    # NaN and NaT are the only values not equal to themselves.
    try:
        if value != value:  # noqa: PLR0124 - intentional NaN/NaT probe
            return None
    except Exception:  # noqa: BLE001 - odd objects: fall through to normal handling
        pass
    if isinstance(value, (int, str)):
        return value
    # date / datetime / pandas Timestamp
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        try:
            return isoformat()
        except Exception:  # noqa: BLE001
            return str(value)
    from decimal import Decimal

    if isinstance(value, Decimal):
        return float(value)
    # numpy scalar -> python scalar
    item = getattr(value, "item", None)
    if callable(item):
        try:
            value = value.item()
        except Exception:  # noqa: BLE001
            pass
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            return None
        return value
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).decode("utf-8", "replace")
    if isinstance(value, (bool, int, str)) or value is None:
        return value
    return str(value)


def _records(columns: List[str], rows: List[tuple]) -> List[Dict[str, Any]]:
    return [{col: _coerce(val) for col, val in zip(columns, row)} for row in rows]


class MarketDataWarehouse:
    """Read-only accessor over the pinned warehouse (lazy, env-configured)."""

    def __init__(self) -> None:
        self._warehouse_path = os.environ.get(ENV_WAREHOUSE_PATH) or None
        self._release = os.environ.get(ENV_RELEASE) or None
        # Cached backend: (kind, handle). kind in {"duckdb_file", "marketdata_client"}.
        self._backend: Optional[tuple] = None
        self._backend_error: Optional[str] = None

    # -- configuration / status ------------------------------------------

    @property
    def configured(self) -> bool:
        """True if either configuration path is present in the environment."""
        return bool(self._warehouse_path or self._release)

    def not_configured_payload(self) -> Dict[str, Any]:
        """The standard payload returned by tools when nothing is configured."""
        return {"status": "unavailable", "reason": NOT_CONFIGURED_MESSAGE, "rows": []}

    def status(self) -> Dict[str, Any]:
        """A small, public-safe description of whether the warehouse is usable."""
        if not self.configured:
            return {"status": "unavailable", "configured": False, "reason": NOT_CONFIGURED_MESSAGE}
        try:
            kind, _ = self._ensure_backend()
        except MarketDataUnavailable as exc:
            return {"status": "unavailable", "configured": True, "reason": str(exc)}
        source = "prebuilt_warehouse_file" if kind == "duckdb_file" else "marketdata_package_release"
        return {"status": "ok", "configured": True, "mode": kind, "source": source}

    # -- backend resolution ----------------------------------------------

    def _ensure_backend(self) -> tuple:
        if self._backend is not None:
            return self._backend
        if self._backend_error is not None:
            raise MarketDataUnavailable(self._backend_error)
        try:
            self._backend = self._build_backend()
        except MarketDataUnavailable as exc:
            self._backend_error = str(exc)
            raise
        return self._backend

    def _build_backend(self) -> tuple:
        # Prefer a prebuilt DuckDB file: zero extra deps beyond duckdb, and no
        # storage credentials handled by analystOS.
        if self._warehouse_path:
            if not os.path.exists(self._warehouse_path):
                raise MarketDataUnavailable(
                    f"{ENV_WAREHOUSE_PATH} is set but the warehouse file does not exist"
                )
            try:
                import duckdb  # lazy, optional
            except ImportError as exc:
                raise MarketDataUnavailable(
                    "duckdb is not installed (pip install 'duckdb>=1.0')"
                ) from exc
            try:
                con = duckdb.connect(self._warehouse_path, read_only=True)
            except Exception as exc:  # noqa: BLE001 - corrupt/locked file -> unavailable
                raise MarketDataUnavailable(f"could not open warehouse file: {exc}") from exc
            return ("duckdb_file", con)
        if self._release:
            return ("marketdata_client", self._build_marketdata_client())
        raise MarketDataUnavailable(NOT_CONFIGURED_MESSAGE)

    def _build_marketdata_client(self):
        try:
            from marketdata import MarketData  # optional private package
        except ImportError as exc:
            raise MarketDataUnavailable(
                "the optional 'marketdata' package is not installed"
            ) from exc
        release = self._release
        # A release given as an existing local directory -> a local release store.
        if os.path.isdir(release):
            return MarketData(release_path=release)
        # Otherwise pin the release id and let the package resolve its own
        # remote store from its own environment configuration. analystOS holds
        # no storage credentials of its own.
        try:
            from marketdata.storage import R2Backend, Storage

            storage = Storage(R2Backend())
        except Exception as exc:  # noqa: BLE001 - package reports its own config gaps
            logger.debug("remote warehouse store unavailable: %s", exc)
            raise MarketDataUnavailable(
                "remote warehouse store is not configured for the marketdata package"
            ) from exc
        return MarketData(storage=storage, release_id=release)

    # -- query ------------------------------------------------------------

    def query(self, sql: str, params: Optional[list] = None) -> List[Dict[str, Any]]:
        """Run ``sql`` against the pinned warehouse and return JSON-safe rows."""
        kind, backend = self._ensure_backend()
        if kind == "duckdb_file":
            cur = backend.execute(sql, params) if params is not None else backend.execute(sql)
            columns = [d[0] for d in cur.description]
            return _records(columns, cur.fetchall())
        # marketdata_client backend: MarketData.query returns a pandas DataFrame.
        df = backend.query(sql, params)
        return [{k: _coerce(v) for k, v in rec.items()} for rec in df.to_dict("records")]

    def _query_optional(self, sql: str, params: Optional[list] = None) -> List[Dict[str, Any]]:
        """Like :meth:`query`, but a missing table/view yields ``[]``.

        Some tables (e.g. the copper stock history) are not guaranteed to be
        present in every warehouse build; their absence should not error.
        """
        try:
            return self.query(sql, params)
        except MarketDataUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001
            message = str(exc).lower()
            if "does not exist" in message or "not found" in message or "catalog" in message:
                return []
            raise

    # -- typed accessors (SQL over the stable warehouse table/view names) --

    @staticmethod
    def _where(clauses: List[str]) -> str:
        return ("WHERE " + " AND ".join(clauses)) if clauses else ""

    def commodity_prices(
        self,
        product_root: Optional[str] = None,
        exchange: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """Per-contract daily futures rows (``futures_daily_all``: CME + SHFE/INE)."""
        clauses: List[str] = []
        params: List[Any] = []
        if product_root:
            clauses.append("product_root = ?")
            params.append(product_root)
        if exchange:
            clauses.append("exchange = ?")
            params.append(exchange)
        if start_date:
            clauses.append("trade_date >= ?")
            params.append(start_date)
        if end_date:
            clauses.append("trade_date <= ?")
            params.append(end_date)
        sql = (
            "SELECT trade_date, exchange, product_root, contract_id, settle, close, "
            "volume, open_interest, revision, source "
            f"FROM futures_daily_all {self._where(clauses)} "
            f"ORDER BY trade_date, contract_id LIMIT {int(limit)}"
        )
        return self.query(sql, params or None)

    def futures_voi(
        self,
        product_root: Optional[str] = None,
        exchange: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """Per-product volume and open-interest series, summed across contracts."""
        clauses: List[str] = []
        params: List[Any] = []
        if product_root:
            clauses.append("product_root = ?")
            params.append(product_root)
        if exchange:
            clauses.append("exchange = ?")
            params.append(exchange)
        if start_date:
            clauses.append("trade_date >= ?")
            params.append(start_date)
        if end_date:
            clauses.append("trade_date <= ?")
            params.append(end_date)
        sql = (
            "SELECT trade_date, exchange, product_root, "
            "SUM(volume) AS total_volume, SUM(open_interest) AS total_open_interest, "
            "COUNT(*) AS n_contracts "
            f"FROM futures_daily_all {self._where(clauses)} "
            "GROUP BY trade_date, exchange, product_root "
            f"ORDER BY trade_date, exchange, product_root LIMIT {int(limit)}"
        )
        return self.query(sql, params or None)

    def cot_positioning(
        self,
        market_code: Optional[str] = None,
        dataset: Optional[str] = None,
        limit: int = 300,
    ) -> Dict[str, Any]:
        """COT weekly rows plus positioning percentiles for a market."""
        clauses: List[str] = []
        params: List[Any] = []
        if market_code:
            clauses.append("market_code = ?")
            params.append(market_code)
        if dataset:
            clauses.append("dataset = ?")
            params.append(dataset)
        where = self._where(clauses)
        weekly = self.query(
            "SELECT dataset, market_code, report_date, commodity_name, "
            "market_and_exchange_names, open_interest_all, noncomm_positions_long_all, "
            "noncomm_positions_short_all, comm_positions_long_all, "
            "comm_positions_short_all, m_money_positions_long_all, "
            "m_money_positions_short_all "
            f"FROM cot_weekly {where} ORDER BY report_date, dataset LIMIT {int(limit)}",
            params or None,
        )
        percentiles = self.query(
            "SELECT dataset, market_code, commodity_name, report_date, metric, value, "
            "percentile, n_obs "
            f"FROM cot_percentiles {where} ORDER BY report_date, metric LIMIT {int(limit)}",
            params or None,
        )
        return {"weekly": weekly, "percentiles": percentiles}

    def warehouse_stocks(
        self,
        metal: Optional[str] = "copper",
        exchange: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 500,
    ) -> Dict[str, Any]:
        """Exchange warehouse metal-stock levels, plus copper stock history."""
        clauses: List[str] = []
        params: List[Any] = []
        if metal:
            clauses.append("metal = ?")
            params.append(metal)
        if exchange:
            clauses.append("exchange = ?")
            params.append(exchange)
        if start_date:
            clauses.append("stock_date >= ?")
            params.append(start_date)
        if end_date:
            clauses.append("stock_date <= ?")
            params.append(end_date)
        stocks = self.query(
            "SELECT exchange, metal, stock_date, stock_tonnes, change_tonnes, unit, "
            "mirror, captured_date "
            f"FROM warehouse_stocks {self._where(clauses)} "
            f"ORDER BY stock_date, exchange LIMIT {int(limit)}",
            params or None,
        )
        copper_history: List[Dict[str, Any]] = []
        if metal is None or str(metal).lower() in ("cu", "copper"):
            hist_clauses: List[str] = []
            hist_params: List[Any] = []
            if start_date:
                hist_clauses.append("stock_date >= ?")
                hist_params.append(start_date)
            if end_date:
                hist_clauses.append("stock_date <= ?")
                hist_params.append(end_date)
            copper_history = self._query_optional(
                "SELECT * FROM warehouse_stocks_copper_history "
                f"{self._where(hist_clauses)} ORDER BY stock_date LIMIT {int(limit)}",
                hist_params or None,
            )
        return {"stocks": stocks, "copper_history": copper_history}

    def arb_window(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """China copper import-arbitrage window rows (indicative; see param_status)."""
        clauses: List[str] = []
        params: List[Any] = []
        if start_date:
            clauses.append("date >= ?")
            params.append(start_date)
        if end_date:
            clauses.append("date <= ?")
            params.append(end_date)
        sql = (
            f"SELECT * FROM import_arb {self._where(clauses)} "
            f"ORDER BY date LIMIT {int(limit)}"
        )
        return self.query(sql, params or None)

    def market_cap(
        self,
        cik: Optional[str] = None,
        ticker: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 5000,
    ) -> Dict[str, Any]:
        """Issuer-level market-cap history (economic series)."""
        resolved_cik = cik
        if resolved_cik is None and ticker:
            rows = self.query(
                "SELECT cik FROM security_master WHERE ticker = ? LIMIT 1", [ticker]
            )
            if not rows:
                return {"cik": None, "ticker": ticker, "series": "economic", "rows": []}
            resolved_cik = rows[0].get("cik")
        clauses: List[str] = []
        params: List[Any] = []
        if resolved_cik is not None:
            clauses.append("cik = ?")
            params.append(resolved_cik)
        if start_date:
            clauses.append("date >= ?")
            params.append(start_date)
        if end_date:
            clauses.append("date <= ?")
            params.append(end_date)
        rows = self.query(
            "SELECT cik, date, market_cap, n_classes, n_proxied "
            f"FROM issuer_market_cap {self._where(clauses)} "
            f"ORDER BY cik, date LIMIT {int(limit)}",
            params or None,
        )
        return {"cik": resolved_cik, "ticker": ticker, "series": "economic", "rows": rows}

    def equity_eod(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        basis: str = "raw",
    ) -> List[Dict[str, Any]]:
        """Unadjusted EOD rows for ``symbol``; ``basis='adjusted'`` computes the
        split-adjusted close on read from the corporate-actions chain."""
        if basis not in ("raw", "adjusted"):
            raise ValueError(f"basis must be 'raw' or 'adjusted', got {basis!r}")
        clauses = ["symbol = ?"]
        params: List[Any] = [symbol]
        if start_date:
            clauses.append("trade_date >= ?")
            params.append(start_date)
        if end_date:
            clauses.append("trade_date <= ?")
            params.append(end_date)
        rows = self.query(
            "SELECT symbol, trade_date, open, high, low, close, volume, source, "
            "source_price_basis "
            f"FROM equities_eod {self._where(clauses)} ORDER BY trade_date",
            params,
        )
        if basis == "adjusted" and rows:
            rows = self._apply_split_adjustment(symbol, rows)
        return rows

    def _apply_split_adjustment(
        self, symbol: str, rows: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Divide pre-split closes by each split ratio (matches the warehouse
        client's on-read adjustment). Dates are ISO strings on both backends,
        so lexicographic comparison is chronological."""
        for row in rows:
            close = row.get("close")
            row["close_adjusted"] = float(close) if close is not None else None
        actions = self._query_optional(
            "SELECT action_date, value FROM corporate_actions "
            "WHERE symbol = ? AND action_type = 'split' ORDER BY action_date",
            [symbol],
        )
        for action in actions:
            ratio = action.get("value")
            action_date = action.get("action_date")
            if not ratio or float(ratio) <= 0 or action_date is None:
                continue
            for row in rows:
                trade_date = row.get("trade_date")
                if (
                    trade_date is not None
                    and str(trade_date) < str(action_date)
                    and row["close_adjusted"] is not None
                ):
                    row["close_adjusted"] = row["close_adjusted"] / float(ratio)
        return rows

    def price_bars(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        basis: str = "raw",
    ) -> List[Dict[str, Any]]:
        """EOD rows shaped as OpenBB-style price bars (date/open/high/low/close/
        volume/vwap) so they can transparently replace the OpenBB price path."""
        rows = self.equity_eod(symbol, start_date, end_date, basis)
        bars: List[Dict[str, Any]] = []
        for row in rows:
            if basis == "adjusted" and "close_adjusted" in row:
                close = row.get("close_adjusted")
            else:
                close = row.get("close")
            bars.append(
                {
                    "date": row.get("trade_date"),
                    "open": row.get("open"),
                    "high": row.get("high"),
                    "low": row.get("low"),
                    "close": close,
                    "volume": row.get("volume"),
                    "vwap": None,
                }
            )
        return bars

    def close(self) -> None:
        if self._backend is not None and self._backend[0] == "duckdb_file":
            try:
                self._backend[1].close()
            except Exception:  # noqa: BLE001
                pass
        self._backend = None


__all__ = ["MarketDataWarehouse", "MarketDataUnavailable", "NOT_CONFIGURED_MESSAGE"]
