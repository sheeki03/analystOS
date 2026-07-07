"""
Tests for the optional private market-data warehouse integration.

Three concerns, mirroring the existing flat tests/ layout:

1. Schema validation for the new warehouse tools (like the other function
   schemas the router binds).
2. The client's graceful "not configured" path (no crash when the warehouse
   is absent).
3. The tools end-to-end against a tiny SYNTHETIC .duckdb fixture built in this
   test. Every value below is fabricated for testing — it is NOT market data.
"""

import json

import pytest

duckdb = pytest.importorskip("duckdb")

from src.services.financial_tools import schemas as schemas_mod
from src.services.financial_tools import tools as tools_mod
from src.services.marketdata_client import MarketDataWarehouse
from src.services.marketdata_client.client import ENV_WAREHOUSE_PATH, ENV_RELEASE


NEW_TOOLS = [
    "get_commodity_prices",
    "get_futures_voi",
    "get_cot_positioning",
    "get_warehouse_stocks",
    "get_arb_window",
    "get_market_cap",
]


# --------------------------------------------------------------------------
# Synthetic warehouse fixture (fabricated data — NOT real market data)
# --------------------------------------------------------------------------

def _build_synthetic_warehouse(path: str) -> None:
    """Create the handful of tables/views the warehouse tools query, each with
    a few clearly SYNTHETIC rows. Table/column names match the real warehouse
    schema so the tools exercise the same SQL."""
    con = duckdb.connect(path)
    try:
        # Futures (CME + SHFE/INE harmonized) — commodity prices + VOI.
        con.execute(
            "CREATE TABLE futures_daily_all ("
            "trade_date DATE, exchange VARCHAR, product_root VARCHAR, "
            "contract_id VARCHAR, settle DOUBLE, close DOUBLE, volume BIGINT, "
            "open_interest BIGINT, revision VARCHAR, source VARCHAR)"
        )
        con.execute(
            "INSERT INTO futures_daily_all VALUES "
            "(DATE '2024-01-02','SHFE','cu','cu2402', 68000.0, 68000.0, 1000, 5000, 'final','SYNTHETIC'),"
            "(DATE '2024-01-02','SHFE','cu','cu2403', 68100.0, 68100.0,  500, 3000, 'final','SYNTHETIC'),"
            "(DATE '2024-01-03','SHFE','cu','cu2402', 68200.0, 68200.0, 1200, 5200, 'final','SYNTHETIC')"
        )

        # COT weekly + percentiles.
        con.execute(
            "CREATE TABLE cot_weekly ("
            "dataset VARCHAR, market_code VARCHAR, report_date DATE, "
            "commodity_name VARCHAR, market_and_exchange_names VARCHAR, "
            "open_interest_all BIGINT, noncomm_positions_long_all BIGINT, "
            "noncomm_positions_short_all BIGINT, comm_positions_long_all BIGINT, "
            "comm_positions_short_all BIGINT, m_money_positions_long_all BIGINT, "
            "m_money_positions_short_all BIGINT)"
        )
        con.execute(
            "INSERT INTO cot_weekly VALUES "
            "('legacy_fut','085692',DATE '2024-01-02','COPPER','COPPER-CMX',"
            "200000, 60000, 40000, 90000, 95000, 30000, 20000),"
            "('legacy_fut','085692',DATE '2024-01-09','COPPER','COPPER-CMX',"
            "210000, 62000, 39000, 91000, 96000, 31000, 21000)"
        )
        con.execute(
            "CREATE TABLE cot_percentiles ("
            "dataset VARCHAR, market_code VARCHAR, commodity_name VARCHAR, "
            "market_and_exchange_names VARCHAR, report_date DATE, metric VARCHAR, "
            "value DOUBLE, percentile DOUBLE, n_obs BIGINT)"
        )
        con.execute(
            "INSERT INTO cot_percentiles VALUES "
            "('legacy_fut','085692','COPPER','COPPER-CMX',DATE '2024-01-02','noncomm_net',20000.0,0.5,1),"
            "('legacy_fut','085692','COPPER','COPPER-CMX',DATE '2024-01-09','noncomm_net',23000.0,1.0,2)"
        )

        # Warehouse stocks + copper history.
        con.execute(
            "CREATE TABLE warehouse_stocks ("
            "exchange VARCHAR, metal VARCHAR, stock_date DATE, stock_tonnes DOUBLE, "
            "change_tonnes DOUBLE, unit VARCHAR, mirror VARCHAR, captured_date DATE)"
        )
        con.execute(
            "INSERT INTO warehouse_stocks VALUES "
            "('LME','copper',DATE '2024-01-02',150000.0,-500.0,'tonnes','mirror_a',DATE '2024-01-02'),"
            "('SHFE','copper',DATE '2024-01-02', 40000.0, 200.0,'tonnes','shfe',DATE '2024-01-02')"
        )
        con.execute(
            "CREATE TABLE warehouse_stocks_copper_history ("
            "stock_date DATE, mirror VARCHAR, cash_settlement_usd_per_t DOUBLE, "
            "stock_tonnes DOUBLE)"
        )
        con.execute(
            "INSERT INTO warehouse_stocks_copper_history VALUES "
            "(DATE '2024-01-02','mirror_a',8400.0,150000.0),"
            "(DATE '2024-01-03','mirror_a',8425.0,149500.0)"
        )

        # Import-arb window (indicative; param_status labels missing inputs).
        con.execute(
            "CREATE TABLE import_arb ("
            "date DATE, import_parity_cny_per_t DOUBLE, shfe_cny_per_t DOUBLE, "
            "arb_cny_per_t DOUBLE, param_status VARCHAR, label VARCHAR)"
        )
        con.execute(
            "INSERT INTO import_arb VALUES "
            "(DATE '2024-01-02', 68500.0, 68000.0, -500.0, 'ok', 'indicative'),"
            "(DATE '2024-01-03', NULL, 68200.0, NULL, 'missing:yangshan_premium', 'indicative')"
        )

        # Equities: security master + market cap + EOD + corporate actions.
        con.execute(
            "CREATE TABLE security_master ("
            "security_id VARCHAR, cik VARCHAR, share_class VARCHAR, ticker VARCHAR, "
            "issuer_name VARCHAR, class_source VARCHAR, class_unresolved BOOLEAN)"
        )
        con.execute(
            "INSERT INTO security_master VALUES "
            "('0001045810::common','0001045810','common','NVDA','NVIDIA CORP','snapshot',FALSE)"
        )
        con.execute(
            "CREATE TABLE issuer_market_cap ("
            "cik VARCHAR, date DATE, market_cap DOUBLE, n_classes BIGINT, n_proxied BIGINT)"
        )
        con.execute(
            "INSERT INTO issuer_market_cap VALUES "
            "('0001045810',DATE '2024-01-02', 1.2e12, 1, 0),"
            "('0001045810',DATE '2024-01-03', 1.23e12, 1, 0)"
        )
        con.execute(
            "CREATE TABLE equities_eod ("
            "symbol VARCHAR, trade_date DATE, open DOUBLE, high DOUBLE, low DOUBLE, "
            "close DOUBLE, volume BIGINT, source VARCHAR, source_price_basis VARCHAR)"
        )
        con.execute(
            "INSERT INTO equities_eod VALUES "
            "('NVDA',DATE '2024-01-02', 48.0, 49.0, 47.5, 48.5, 400000000,'SYNTHETIC','raw'),"
            "('NVDA',DATE '2024-01-03', 48.5, 50.0, 48.0, 49.8, 420000000,'SYNTHETIC','raw')"
        )
        con.execute(
            "CREATE TABLE corporate_actions ("
            "symbol VARCHAR, action_date DATE, action_type VARCHAR, value DOUBLE, source VARCHAR)"
        )
        # No split rows: adjusted == raw for this fixture.
    finally:
        con.close()


@pytest.fixture(scope="module")
def synthetic_warehouse_path(tmp_path_factory) -> str:
    path = str(tmp_path_factory.mktemp("marketdata") / "synthetic_warehouse.duckdb")
    _build_synthetic_warehouse(path)
    return path


@pytest.fixture
def configured_tools(synthetic_warehouse_path, monkeypatch):
    """Point the tools' warehouse singleton at the synthetic fixture."""
    monkeypatch.setenv(ENV_WAREHOUSE_PATH, synthetic_warehouse_path)
    monkeypatch.delenv(ENV_RELEASE, raising=False)
    tools_mod._marketdata_warehouse = None  # reset singleton to pick up env
    yield tools_mod
    if tools_mod._marketdata_warehouse is not None:
        tools_mod._marketdata_warehouse.close()
    tools_mod._marketdata_warehouse = None


def _data(result_json: str):
    """Parse the tool result envelope and return its data payload."""
    return json.loads(result_json)["data"]


# --------------------------------------------------------------------------
# 1. Schema validation
# --------------------------------------------------------------------------

def test_new_tool_schemas_present_and_wellformed():
    schemas = schemas_mod.build_tool_schemas()
    by_name = {s["function"]["name"]: s for s in schemas}
    for name in NEW_TOOLS:
        assert name in by_name, f"missing schema for {name}"
        fn = by_name[name]
        assert fn["type"] == "function"
        assert fn["function"]["description"]
        params = fn["function"]["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert isinstance(params.get("required", []), list)


def test_schemas_and_tool_map_stay_in_sync():
    schema_names = {s["function"]["name"] for s in schemas_mod.build_tool_schemas()}
    # Every new tool is both schema-defined and routable.
    for name in NEW_TOOLS:
        assert name in schema_names
        assert name in tools_mod.FINANCIAL_TOOL_MAP


def test_get_prices_schema_gains_basis_param():
    schemas = schemas_mod.build_tool_schemas()
    gp = next(s for s in schemas if s["function"]["name"] == "get_prices")
    props = gp["function"]["parameters"]["properties"]
    assert "basis" in props
    assert props["basis"]["enum"] == ["raw", "adjusted"]


# --------------------------------------------------------------------------
# 2. Graceful "not configured" path
# --------------------------------------------------------------------------

def test_warehouse_not_configured(monkeypatch):
    monkeypatch.delenv(ENV_WAREHOUSE_PATH, raising=False)
    monkeypatch.delenv(ENV_RELEASE, raising=False)
    wh = MarketDataWarehouse()
    assert wh.configured is False
    status = wh.status()
    assert status["status"] == "unavailable"
    assert status["configured"] is False


def test_tools_return_unavailable_payload_when_not_configured(monkeypatch):
    monkeypatch.delenv(ENV_WAREHOUSE_PATH, raising=False)
    monkeypatch.delenv(ENV_RELEASE, raising=False)
    tools_mod._marketdata_warehouse = None
    try:
        for name in NEW_TOOLS:
            result = _data(tools_mod.FINANCIAL_TOOL_MAP[name]())
            assert result["status"] == "unavailable"
            assert "not configured" in result["reason"].lower()
    finally:
        tools_mod._marketdata_warehouse = None


# --------------------------------------------------------------------------
# 3. Tools against the synthetic warehouse
# --------------------------------------------------------------------------

def test_status_ok_when_configured(configured_tools):
    status = configured_tools._get_warehouse().status()
    assert status["status"] == "ok"
    assert status["mode"] == "duckdb_file"


def test_get_commodity_prices(configured_tools):
    rows = _data(configured_tools.get_commodity_prices(product_root="cu", exchange="SHFE"))
    assert len(rows) == 3
    first = rows[0]
    assert first["product_root"] == "cu"
    assert first["exchange"] == "SHFE"
    assert first["trade_date"] == "2024-01-02"
    assert first["settle"] == 68000.0


def test_get_futures_voi_aggregates_across_contracts(configured_tools):
    rows = _data(configured_tools.get_futures_voi(product_root="cu", exchange="SHFE"))
    # Two trade dates; 2024-01-02 sums two contracts (1000+500 vol, 5000+3000 OI).
    by_date = {r["trade_date"]: r for r in rows}
    assert by_date["2024-01-02"]["total_volume"] == 1500
    assert by_date["2024-01-02"]["total_open_interest"] == 8000
    assert by_date["2024-01-02"]["n_contracts"] == 2


def test_get_cot_positioning(configured_tools):
    payload = _data(configured_tools.get_cot_positioning(market_code="085692"))
    assert len(payload["weekly"]) == 2
    assert len(payload["percentiles"]) == 2
    assert payload["weekly"][0]["market_code"] == "085692"
    assert payload["percentiles"][-1]["metric"] == "noncomm_net"


def test_get_warehouse_stocks_includes_copper_history(configured_tools):
    payload = _data(configured_tools.get_warehouse_stocks(metal="copper"))
    assert len(payload["stocks"]) >= 1
    assert all(r["metal"] == "copper" for r in payload["stocks"])
    assert len(payload["copper_history"]) == 2
    assert payload["copper_history"][0]["cash_settlement_usd_per_t"] == 8400.0


def test_get_arb_window_carries_param_status(configured_tools):
    rows = _data(configured_tools.get_arb_window())
    assert len(rows) == 2
    assert rows[0]["param_status"] == "ok"
    # Missing input greys the parity: NULL becomes None, param_status explains.
    assert rows[1]["import_parity_cny_per_t"] is None
    assert rows[1]["param_status"].startswith("missing:")
    assert rows[1]["label"] == "indicative"


def test_get_market_cap_by_ticker(configured_tools):
    payload = _data(configured_tools.get_market_cap(ticker="NVDA"))
    assert payload["cik"] == "0001045810"
    assert payload["series"] == "economic"
    assert len(payload["rows"]) == 2
    assert payload["rows"][0]["market_cap"] == pytest.approx(1.2e12)


def test_get_market_cap_unknown_ticker_returns_empty(configured_tools):
    payload = _data(configured_tools.get_market_cap(ticker="NOPE"))
    assert payload["rows"] == []


def test_get_prices_prefers_warehouse(configured_tools):
    result = json.loads(
        configured_tools.get_prices("NVDA", "2024-01-01", "2024-01-31")
    )
    bars = result["data"]
    assert len(bars) == 2
    assert bars[0]["date"] == "2024-01-02"
    assert bars[0]["close"] == 48.5
    assert bars[0]["vwap"] is None
    # Sourced from the warehouse, not the external provider.
    assert result["sourceUrls"] == ["marketdata://warehouse/equities_eod"]


def test_get_prices_falls_back_for_symbol_not_in_warehouse(configured_tools, monkeypatch):
    # A symbol absent from the warehouse should fall through to the OpenBB path,
    # which we stub to avoid any network call.
    captured = {}

    class _StubClient:
        def get_prices(self, **kwargs):
            captured.update(kwargs)
            return [{"date": "2024-01-02", "close": 1.23, "vwap": None}]

    monkeypatch.setattr(configured_tools, "_get_openbb_client", lambda: _StubClient())
    result = json.loads(
        configured_tools.get_prices("ZZZZ", "2024-01-01", "2024-01-31")
    )
    assert captured["ticker"] == "ZZZZ"  # fell back to OpenBB
    assert result["data"][0]["close"] == 1.23
