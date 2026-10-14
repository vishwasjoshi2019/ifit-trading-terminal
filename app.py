from dotenv import load_dotenv
load_dotenv()

from engines.ifit_signal_engine import build_signal
from engines.event_engine import detect_events, monitored_conditions
from engines.alert_engine import update_memory, alert_snapshot
from engines.decision_matrix_engine import build_decision_matrix, decision_table
from engines.scenario_engine import build_scenario_matrix, scenario_summary
from engines.risk_engine import build_risk_engine, risk_summary
from engines.portfolio_risk_engine import build_portfolio_risk
from engines.liquidity_execution_engine import build_liquidity_execution
from engines.microstructure_engine import build_microstructure
from engines.consolidated_engine import build_consolidated_intelligence
from engines.ifit_regime_engine import classify_regime
from engines.live_market_intelligence_engine import build_market_intelligence
from engines.live_vol_signal_engine import build_vol_signal
from engines.live_model_dislocation_engine import analyze_live_dislocation
from engines.live_heston_engine import calibrate_live_heston
from engines.live_vol_surface_engine import build_surface, surface_summary, term_structure
from engines.live_greeks_engine import chain_greek_rows, bsm_greeks
from engines.workspace_engine import workspace_names, subviews_for, workspace_code, workspace_description, build_context, context_payload
from engines.charts_engine import build_ohlcv, build_option_ohlcv, build_volume_profile, profile_levels, chart_snapshot
from engines.interactive_chart_engine import build_interactive_figure, chart_capabilities
from engines.cht_live_component import render_live_chart

import streamlit as st
import pandas as pd
import numpy as np
import math
import time
from datetime import date, timedelta, timezone, datetime

from engines.options_engine import build_option_chain, calculate_metrics
from engines.volatility_engine import expected_move_table, volatility_snapshot, gamma_exposure
from engines.orderflow_engine import build_orderflow, orderflow_metrics, classify_levels
from engines.time_footprint_engine import build_time_footprint, time_footprint_metrics
from engines.absorption_engine import detect_absorption_exhaustion
from engines.greeks_engine import calculate_higher_order_greeks, greek_snapshot_dataframe, greek_risk_interpretation, build_greek_surface, greek_surface_summary
from engines.greek_regime_engine import analyze_greek_regime, regime_component_table
from engines.portfolio_greeks_engine import portfolio_greeks, portfolio_regime, scenario_matrix, scenario_pnl, portfolio_exposure_summary
from engines.model_dislocation_engine import model_dislocation, heston_to_bsm_iv_surface
from engines.heston_calibration_engine import calibrate_heston, calibrated_iv_surface, dislocation_rank
from engines.dislocation_engine import build_dislocation_rank, dislocation_summary
from engines.data_adapter import IFITDataAdapter, health_from_snapshot
from engines.live_data.adapters.dhan import DhanAdapter
from engines.live_data.dhan_live_service import DhanLiveService
from engines.live_data.live_candles import build_live_ohlcv, build_dhan_historical_ohlcv
from engines.screener_engine import build_equity_universe, apply_filters, rank_equities, sector_summary
from engines.derivatives_screener_engine import build_derivatives_universe, apply_derivatives_filters, rank_derivatives, signal_summary
from engines.market_screener_engine import build_market_universe, apply_market_filters, rank_market, sector_summary as market_sector_summary, market_summary, available_sectors, available_signals
from engines.cross_asset_intelligence_engine import build_cross_asset_intelligence_snapshot, cross_asset_summary
from engines.global_markets_intelligence_engine import build_global_markets_intelligence_snapshot, global_markets_summary
from engines.forex_crypto_ui import _ifit_forex_page, _ifit_crypto_page

from engines.data_health_engine import health_frame, health_label, data_quality
from engines.cvd_engine import analyze_cvd_divergence
from engines.flow_confluence_engine import build_flow_confluence
from engines.mcx_commodities_engine import (
    build_commodities_universe,
    apply_commodity_filters,
    rank_commodities,
    commodity_summary,
    available_commodities,
    available_commodity_signals,
    available_term_structures,
    available_roll_behaviours,
)

from engines.mcx_intelligence_engine import (
    build_mcx_intelligence,
    apply_mcx_intelligence_filters,
    rank_mcx_intelligence,
    mcx_intelligence_summary,
    available_mcx_intelligence_commodities,
    available_mcx_intelligence_signals,
    available_positioning_states,
    available_volatility_regimes,
    available_mcx_term_structures,
    available_mcx_roll_behaviours,
)

from engines.gsec_intelligence_engine import (
    build_gsec_intelligence,
    apply_gsec_intelligence_filters,
    rank_gsec_intelligence,
    gsec_intelligence_summary,
    available_gsec_signals,
)

from engines.bond_screener_engine import (
    build_bond_screener,
    apply_bond_screener_filters,
    rank_bond_screener,
    bond_screener_summary,
    available_bond_screener_asset_types,
    available_bond_screener_signals,
    available_bond_screener_ratings,
)

from engines.footprint_intelligence_engine import (
    classify_footprint_intelligence,
    footprint_intelligence_summary,
)
from engines.footprint_auction_intelligence_engine import (
    build_advanced_auction_snapshot,
    auction_intelligence_summary,
)
from engines.footprint_decision_intelligence_engine import (
    build_footprint_decision_intelligence,
    decision_intelligence_summary,
)

from engines.footprint_cluster_renderer import (
    build_cluster_footprint_figure,
    build_delta_intensity_figure,
    footprint_event_counts,
)

from engines.order_flow_footprint_engine import (
    build_footprint_data,
    build_bar_footprint,
    aggregate_footprint,
    footprint_summary,
    available_footprint_timeframes,
)

from engines.live_tick_footprint_engine import build_live_tick_footprint

from engines.motion_charts_engine import (
    build_motion_data,
    build_momentum_motion,
    build_volatility_motion,
    build_liquidity_flow_motion,
    motion_summary,
    available_motion_views,
)

from engines.tbill_intelligence_engine import (
    build_tbill_intelligence,
    apply_tbill_intelligence_filters,
    rank_tbill_intelligence,
    tbill_intelligence_summary,
    available_tbill_tenors,
    available_tbill_signals,
)

from engines.corporate_bond_intelligence_engine import (
    build_corporate_bond_intelligence,
    apply_corporate_bond_intelligence_filters,
    rank_corporate_bond_intelligence,
    corporate_bond_intelligence_summary,
    available_corporate_bond_ratings,
    available_corporate_issuer_types,
    available_corporate_bond_signals,
)

from engines.sdl_intelligence_engine import (
    build_sdl_intelligence,
    apply_sdl_intelligence_filters,
    rank_sdl_intelligence,
    sdl_intelligence_summary,
    available_sdl_states,
    available_sdl_signals,
)

from engines.yield_curve_engine import (
    build_yield_curve,
    apply_yield_curve_filters,
    rank_yield_curve,
    yield_curve_summary,
    available_yield_curve_tenors,
)

from engines.bond_intelligence_engine import (
    build_bond_intelligence,
    apply_bond_intelligence_filters,
    rank_bond_intelligence,
    bond_intelligence_summary,
    available_bond_asset_types,
    available_bond_ratings,
    available_bond_signals,
)

from engines.payoff_ui import render_payoff_charts
from engines.mutual_funds_ui import render_mutual_funds_intelligence
from engines.live_hedge_universe import build_live_hedge_universe
from engines.hedging_engine import (
    PortfolioExposure,
    build_demo_hedge_universe,
    optimize_single_hedges,
    optimize_single_hedges_v023,
    optimize_combined_hedges,
    hedge_summary,
    hedge_recommendation,
)

st.set_page_config(
    page_title="IFIT — Indian Financial Intelligence Terminal",
    page_icon="🇮🇳",
    layout="wide",
)

st.markdown("""
<style>
/* =====================================================================
   IFIT Master Fintech Design Tokens (Bloomberg / Institutional Terminal)
   ===================================================================== */
:root {
    --bg-primary: #080B10;
    --bg-surface: #0E131F;
    --bg-card: #121826;
    --border-subtle: #1E293B;
    --border-active: #38BDF8;
    --text-primary: #F1F5F9;
    --text-muted: #94A3B8;
    --emerald-alpha: #10B981;
    --crimson-risk: #EF4444;
    --amber-warning: #F59E0B;
    --cyan-accent: #38BDF8;
}

.block-container {
    padding-top: 0.4rem;
    padding-bottom: 2rem;
    max-width: 1600px;
}

/* Tabular numbers for financial metrics and tickers */
body, [data-testid="stMetricValue"], [data-testid="stDataFrame"], table {
    font-variant-numeric: tabular-nums;
}

/* Metric card containers */
[data-testid="stMetric"] {
    background: #0E131F;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 0.65rem 0.85rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.35);
    transition: border-color 0.15s ease, transform 0.15s ease;
}
[data-testid="stMetric"]:hover {
    border-color: #334155;
}
[data-testid="stMetricLabel"] {
    font-size: 0.72rem;
    font-weight: 700;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
[data-testid="stMetricValue"] {
    font-size: 1.32rem;
    font-weight: 800;
    font-family: -apple-system, BlinkMacSystemFont, "SF Mono", "JetBrains Mono", monospace;
    letter-spacing: -0.02em;
    color: #F8FAFC;
}

/* Modern terminal command bar */
.ifit-terminal-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1.1rem;
    margin: 0.2rem 0 0.4rem;
    border: 1px solid #1E293B;
    border-radius: 8px;
    background: #0B0F17;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.45);
    position: sticky;
    top: 0;
    z-index: 99;
}
.ifit-logo {
    font-size: 1.35rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    color: #F8FAFC;
}
.ifit-logo-badge {
    background: linear-gradient(135deg, #FF9933 0%, #FFFFFF 50%, #138808 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 900;
}
.ifit-terminal-name {
    font-size: 1.05rem;
    font-weight: 700;
    color: #64748B;
    margin-left: 0.35rem;
}
.ifit-active-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    background: rgba(56, 189, 248, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.35);
    padding: 0.3rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 800;
    color: #38BDF8;
    letter-spacing: 0.06em;
}
.ifit-live-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: #10B981;
    box-shadow: 0 0 8px #10B981;
    animation: pulse-dot 1.8s infinite ease-in-out;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.85); }
}
.ifit-nav-note {
    font-size: 0.78rem;
    color: #94A3B8;
    margin: 0.2rem 0 0.85rem;
    padding: 0.35rem 0.65rem;
    background: #0E131F;
    border-left: 3px solid #38BDF8;
    border-radius: 0 6px 6px 0;
}

/* Radio buttons / Segments */
div[role="radiogroup"] {
    gap: 0.3rem;
}
div[role="radiogroup"] label {
    padding: 0.45rem 0.85rem;
    border-radius: 6px;
    border: 1px solid #1E293B;
    background: #0E131F;
    transition: all 0.15s ease;
}
div[role="radiogroup"] label:hover {
    border-color: #38BDF8;
}

/* Buttons */
.stButton button {
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.78rem;
    letter-spacing: 0.02em;
    transition: all 0.15s ease;
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def _get_dhan_live_service():
    service = DhanLiveService()
    service.start()
    return service

@st.fragment(run_every=1)
def _ifit_live_spot_fragment():
    if st.session_state.get("ifit_data_mode", "SIMULATION") != "DHAN LIVE":
        return
    try:
        service = _get_dhan_live_service()
        snapshot = service.live_tick_snapshot()
        live = float(snapshot.get("spot") or 0)
        if live > 0:
            st.session_state["ifit_live_spot"] = live
            with st.sidebar:
                st.metric("NIFTY Spot • LIVE", f"₹{live:,.2f}")
    except Exception:
        pass


_ifit_live_spot_fragment()

# ---------- Controls ----------
# ---------- Controls ----------
with st.sidebar:
    st.header("🇮🇳 IFIT")
    st.caption("Indian Financial Intelligence Terminal")
    st.divider()
    _sidebar_data_mode = st.session_state.get("ifit_data_mode", "SIMULATION")
    if _sidebar_data_mode == "DHAN LIVE":
        try:
            _sidebar_dhan_service = _get_dhan_live_service()
            _sidebar_dhan_snapshot = _sidebar_dhan_service.snapshot()
            _sidebar_live_spot = float(_sidebar_dhan_snapshot.get("spot") or 0)
            if _sidebar_live_spot > 0:
                st.session_state["ifit_nifty_spot"] = _sidebar_live_spot
        except Exception:
            pass
    if _sidebar_data_mode == "DHAN LIVE":
        _live_spot_box = st.empty()
        try:
            _live_spot_value = float(_sidebar_dhan_snapshot.get("spot") or 0)
        except Exception:
            _live_spot_value = 0.0
        if _live_spot_value > 0:
            _live_spot_box.metric("NIFTY Spot • LIVE", f"₹{_live_spot_value:,.2f}")
            spot = _live_spot_value
        else:
            _live_spot_box.metric("NIFTY Spot • LIVE", "—")
            spot = float(st.session_state.get("ifit_nifty_spot", 24782.35))
    else:
        spot = st.number_input("NIFTY Spot", value=24782.35, step=25.0, key="ifit_nifty_spot")

    # NIFTY expiry selector — automatically converts selected expiry to DTE
    _today = date.today()

    _expiry_dates = [
        _today + timedelta(days=d)
        for d in range(1, 91)
        if (_today + timedelta(days=d)).weekday() == 3
    ]

    _expiry_labels = [d.strftime("%d %b %Y") for d in _expiry_dates]

    _selected_expiry_label = st.selectbox(
        "NIFTY Expiry",
        _expiry_labels,
        index=0,
        key="ifit_expiry_date",
    )

    _selected_expiry = _expiry_dates[_expiry_labels.index(_selected_expiry_label)]
    days = max((_selected_expiry - _today).days, 1)

    st.caption(f"DTE: {days} days")

    atm_iv = st.slider("ATM IV (%)", 5.0, 60.0, 14.5, 0.1)
    hv30 = st.slider("30D Realized Vol (%)", 5.0, 60.0, 12.8, 0.1)
    flow_levels = st.slider("Footprint levels", 20, 100, 50, 5)
    imbalance_ratio = st.slider("Imbalance ratio", 1.2, 3.0, 1.5, 0.1)
    st.divider()
    st.subheader("Live Data")
    data_mode = st.selectbox(
        "Data source",
        ["SIMULATION", "AUTHORIZED API / BROKER", "DHAN LIVE"],
        index=0,
        key="ifit_data_mode"
    )
    api_endpoint = ""
    if data_mode == "AUTHORIZED API / BROKER":
        api_endpoint = st.text_input(
            "JSON endpoint",
            value="",
            placeholder="https://your-authorized-provider/api/market",
            type="default",
            key="ifit_data_endpoint"
        )
        st.caption("Use an authorized broker/vendor endpoint. Do not scrape NSE webpages.")
    refresh_data = st.button("↻ Refresh Market Data", use_container_width=True)
    st.caption("V0.8.4.1 • Professional Drawing Engine")

# ---------- Live Data Adapter ----------
if data_mode == "DHAN LIVE":
    _dhan_service = _get_dhan_live_service()
    _dhan_snapshot = _dhan_service.snapshot()
    _dhan_health = _dhan_service.health()
    _option_chain = _dhan_snapshot.get("option_chain")
    if _option_chain is None:
        _option_chain = pd.DataFrame()
    _snapshot = {
        "timestamp": _dhan_snapshot.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        "spot": float(_dhan_snapshot.get("spot") or 0),
        "futures": 0.0,
        "option_chain": _option_chain,
        "source": "Dhan WebSocket + REST Option Chain",
    }
    _tick_count = int(_dhan_snapshot.get("tick_count", 0))
    if float(_dhan_snapshot.get("spot") or 0) > 0:
        spot = float(_dhan_snapshot["spot"])
    _health = type("LiveHealth", (), {})()
    _health.source = "Dhan WebSocket"
    _dhan_status = _dhan_health.get("status", "CONNECTING"); _health.status = "LIVE" if _dhan_status == "LIVE" else ("CONNECTING" if _dhan_status == "CONNECTING" else "ERROR")
    _health.last_update = str(_snapshot["timestamp"])
    _health.age_seconds = 0.0
    _health.records = _tick_count
    _health.latency_ms = 0.0
    _health.message = f"Dhan WebSocket • {_tick_count} live ticks received"
    _health.mode = "DHAN LIVE"
    st.session_state["ifit_market_snapshot"] = _snapshot
    st.session_state["ifit_data_health"] = _health
else:
    _adapter_mode = "API" if data_mode == "AUTHORIZED API / BROKER" else "SIMULATION"
    _adapter = IFITDataAdapter(mode=_adapter_mode, endpoint=api_endpoint, api_key=None, timeout=8, symbol="NIFTY")
    if refresh_data or "ifit_market_snapshot" not in st.session_state:
        _snapshot, _health = _adapter.fetch()
        if _snapshot is not None:
            st.session_state["ifit_market_snapshot"] = _snapshot
        st.session_state["ifit_data_health"] = _health
    else:
        _snapshot = st.session_state.get("ifit_market_snapshot")
        _health = st.session_state.get("ifit_data_health")

if _snapshot is not None and _health is not None:
    if data_mode != "DHAN LIVE":
        _health = health_from_snapshot(_snapshot, _health)
        st.session_state["ifit_data_health"] = _health
    if _health.status == "LIVE" and float(_snapshot.get("spot", 0)) > 0:
        spot = float(_snapshot["spot"])

st.markdown(
    '<div style="padding-top:1.25rem;padding-bottom:0.35rem;">'
    '<div style="font-size:2.15rem;font-weight:800;letter-spacing:-0.03em;">IN <span style="font-weight:900;">IFIT</span></div>'
    '<div style="color:#9aa0a6;font-size:0.9rem;margin-top:0.25rem;">Indian Financial Intelligence Terminal • V0.8.2 • Terminal Navigation & Workspace Engine</div>'
    '</div>',
    unsafe_allow_html=True,
)
st.divider()

# ---------- Data Health Monitor ----------
if _health is not None:
    _quality = data_quality(_snapshot)
    dh1,dh2,dh3,dh4,dh5,dh6 = st.columns(6)
    dh1.metric("DATA", health_label(_health.status))
    dh2.metric("SOURCE", _health.source)
    dh3.metric("AGE", f"{_health.age_seconds:.1f}s" if _health.age_seconds != float("inf") else "∞")
    dh4.metric("LATENCY", f"{_health.latency_ms:.0f} ms")
    dh5.metric("RECORDS", str(_health.records))
    dh6.metric("QUALITY", f'{_quality["score"]}/100')
    if _health.status == "ERROR":
        st.error(f"Data adapter error: {_health.message}")
    elif _health.status == "STALE":
        st.warning(f"Data health warning: {_health.message}")
    elif _health.mode == "SIMULATION":
        st.info("IFIT is running on the local market-data simulator. Select AUTHORIZED API / BROKER to connect a real feed.")
else:
    st.warning("Data adapter has not produced a snapshot yet.")


@st.fragment(run_every=1)
def _ifit_futures_depth_render():
    if st.session_state.get("ifit_data_mode", "SIMULATION") != "DHAN LIVE":
        return
    st.markdown("### Live NIFTY Futures Depth")
    try:
        service = _get_dhan_live_service()
        service.start_futures_feed()
        snap = service.futures_depth_snapshot()
        c1, c2, c3 = st.columns(3)
        ltp = snap.get("ltp")
        c1.metric("Futures LTP", f"{ltp:,.2f}" if ltp is not None else "—")
        c2.metric("Feed Status", snap.get("status", "UNKNOWN"))
        c3.metric("Received Ticks", str(snap.get("tick_count", 0)))
        levels = snap.get("depth", [])
        if levels:
            rows = []
            for i, level in enumerate(levels, start=1):
                rows.append({
                    "Level": i,
                    "Bid Price": level.get("bid_price"),
                    "Bid Qty": level.get("bid_quantity"),
                    "Ask Price": level.get("ask_price"),
                    "Ask Qty": level.get("ask_quantity"),
                })
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
            st.caption("Displayed NIFTY futures order-book liquidity from Dhan. Quantities are not executed volume, CVD, or trade-level footprint.")
        else:
            st.info("Waiting for live futures depth from Dhan...")
    except Exception as exc:
        st.warning(f"Futures depth unavailable: {exc}")

_ifit_futures_depth_render()

# IFIT V0.6.2 LIVE GREEKS
def _ifit_v062_render(chain_df, live_spot, live_days, live_iv):
    """Render V0.6.2 Greeks directly from the active Options Intelligence chain."""
    if chain_df is None or len(chain_df) == 0:
        st.info("V0.6.2 Live Greeks is waiting for option-chain data.")
        return

    st.markdown("### ⚡ IFIT V0.6.2 — LIVE GREEKS ENGINE")
    st.caption(
        "Primary and higher-order BSM Greeks calculated from the active IFIT "
        "option chain. Greeks are analytical model outputs, not exchange-published values."
    )

    rate = st.sidebar.number_input(
        "Risk-free rate (%)",
        min_value=-5.0, max_value=25.0, value=6.0, step=0.25,
        key="ifit_v062_rate",
    )

    from engines.live_greeks_engine import bsm_greeks
    import pandas as pd

    rows = []
    T = max(float(live_days), 1.0) / 365.0
    for _, r in chain_df.iterrows():
        for side in ("CE", "PE"):
            iv = float(r[f"{side} IV"])
            g = bsm_greeks(
                float(live_spot), float(r["Strike"]), T,
                rate / 100.0, iv, side
            ).as_dict()
            rows.append({
                "Strike": float(r["Strike"]),
                "Option": side,
                "LTP": float(r[f"{side} LTP"]),
                "OI": float(r[f"{side} OI"]),
                "IV": iv,
                **g,
            })

    df = pd.DataFrame(rows)
    strikes = df["Strike"].dropna().unique()
    atm_strike = min(strikes, key=lambda x: abs(float(x)-float(live_spot)))
    atm = df[df["Strike"] == atm_strike]
    ce = atm[atm["Option"] == "CE"]
    pe = atm[atm["Option"] == "PE"]

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Live NIFTY Spot", f"{live_spot:,.2f}")
    c2.metric("ATM Strike", f"{atm_strike:,.0f}")
    c3.metric("CE Delta", f"{float(ce.iloc[0]['delta']):.4f}")
    c4.metric("PE Delta", f"{float(pe.iloc[0]['delta']):.4f}")
    c5.metric("ATM Gamma", f"{float(ce.iloc[0]['gamma']):.6f}")

    cols = [
        "Strike","Option","LTP","OI","IV","delta","gamma","theta","vega","rho",
        "vanna","vomma","charm","zomma","speed","color","ultima","veta"
    ]
    st.dataframe(
        df[cols].round(6),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("**ATM Greek Snapshot**")
    atm_cols = [
        "Option","delta","gamma","theta","vega","rho",
        "vanna","vomma","charm","zomma","speed","color","ultima","veta"
    ]
    st.dataframe(atm[atm_cols].round(8), width="stretch", hide_index=True)
    st.caption(
        f"BSM horizon: {float(live_days):.0f} days • Risk-free rate: {rate:.2f}%"
    )


# IFIT V0.6.3 LIVE VOLATILITY SURFACE
def _ifit_v063_render(chain_df, live_spot):
    if chain_df is None or len(chain_df) == 0 or live_spot <= 0:
        st.info("V0.6.3 Live Volatility Surface is waiting for option-chain data.")
        return

    import pandas as pd

    rows = build_surface(chain_df, live_spot)
    if not rows:
        st.warning("No valid IV observations available for the volatility surface.")
        return

    df = pd.DataFrame(rows)
    summary = surface_summary(rows, live_spot)
    ts = pd.DataFrame(term_structure(rows))

    st.markdown("---")
    st.markdown("### ⚡ IFIT V0.6.3 — LIVE VOLATILITY SURFACE")
    st.caption(
        "Live implied-volatility structure derived from the active IFIT option chain. "
        "Surface values are market-data inputs, not model estimates."
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Live ATM IV", f"{summary['atm_iv']:.2f}%")
    c2.metric("Put Skew", f"{summary['put_skew']:+.2f} vol pts")
    c3.metric("Call Skew", f"{summary['call_skew']:+.2f} vol pts")
    c4.metric("Smile", f"{summary['smile']:+.2f} vol pts")
    c5.metric("Expiries / Strikes", f"{summary['expiries']} / {summary['strikes']}")

    left, right = st.columns(2)

    with left:
        st.markdown("**Live IV Smile**")
        smile = df.copy()
        smile["moneyness"] = smile["moneyness_pct"]
        pivot = smile.pivot_table(
            index="moneyness", columns="option", values="iv", aggfunc="mean"
        ).sort_index()
        st.line_chart(pivot, use_container_width=True)

    with right:
        st.markdown("**IV Term Structure**")
        if len(ts):
            st.dataframe(ts.round(4), width="stretch", hide_index=True)
            if len(ts) > 1:
                st.line_chart(ts.set_index("expiry")["mean_iv"], use_container_width=True)
            else:
                st.info("One expiry is currently available; term-structure slope will appear when additional expiries are connected.")
        else:
            st.info("No expiry structure available.")

    st.markdown("**Strike × Expiry IV Surface**")
    surface = df.pivot_table(
        index="strike", columns="expiry", values="iv", aggfunc="mean"
    ).sort_index()

    if surface.shape[1] == 1:
        st.dataframe(surface.round(4), width="stretch")
    else:
        st.dataframe(surface.round(4), width="stretch")
        st.line_chart(surface, use_container_width=True)

    st.markdown("**Live IV Surface Data**")
    st.dataframe(
        df[["expiry", "strike", "option", "iv", "moneyness_pct"]].sort_values(
            ["expiry", "strike", "option"]
        ).round(4),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Skew is measured versus the nearest available strike around ATM. "
        "IV is displayed in volatility percentage points."
    )



# IFIT V0.6.4 LIVE HESTON INTELLIGENCE
@st.cache_data(ttl=30, show_spinner=False)
def _ifit_v064_calibrate_cached(spot_value, chain_df, days_value, rate_value):
    return calibrate_live_heston(
        float(spot_value),
        chain_df,
        int(days_value),
        float(rate_value),
        max_nfev=12,
    )


def _ifit_v064_render(chain_df, live_spot, live_days):
    if chain_df is None or len(chain_df) < 5 or live_spot <= 0:
        st.info("V0.6.4 Live Heston Intelligence is waiting for sufficient option-chain data.")
        return

    st.markdown("---")
    st.markdown("### ⚡ IFIT V0.6.4 — LIVE HESTON MODEL INTELLIGENCE")
    st.caption(
        "Heston stochastic-volatility calibration against the active IFIT IV smile, "
        "with model-vs-market dislocation diagnostics. This is research/model intelligence, "
        "not an automatic arbitrage or trading signal."
    )

    rate = st.sidebar.number_input(
        "Heston risk-free rate (%)",
        min_value=-5.0,
        max_value=25.0,
        value=6.0,
        step=0.25,
        key="ifit_v064_rate",
    )

    try:
        params, fit, stats, h_surface, ranked, summary = _ifit_v064_calibrate_cached(
            float(live_spot), chain_df, int(live_days), float(rate)
        )
    except Exception as exc:
        st.warning(f"Heston calibration unavailable: {exc}")
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Calibration Points", str(stats["points"]))
    c2.metric("IV RMSE", f'{stats["iv_rmse"]:.3f} vol pts')
    c3.metric("Price RMSE", f'{stats["price_rmse"]:,.2f}')
    c4.metric("Iterations", str(stats["iterations"]))
    c5.metric("Top Dislocation", f'{summary["top_score"]:.1f}/100')

    bounds_hit = (
        abs(params["kappa"] - 0.10) < 1e-4 or
        abs(params["theta"] - 0.005) < 1e-4 or
        abs(params["sigma_v"] - 2.0) < 1e-4 or
        abs(params["rho"] + 0.95) < 1e-4
    )
    if bounds_hit or int(stats.get("points", 0)) <= 15:
        st.warning("Single-expiry Heston calibration: parameters are at/near bounds. Treat fitted parameters as unstable and use dislocation ranking cautiously.")

    st.markdown("**Calibrated Heston Parameters**")
    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("v0", f'{params["v0"]:.5f}')
    p2.metric("κ Kappa", f'{params["kappa"]:.4f}')
    p3.metric("θ Theta", f'{params["theta"]:.5f}')
    p4.metric("σv Vol-of-Vol", f'{params["sigma_v"]:.4f}')
    p5.metric("ρ Rho", f'{params["rho"]:.4f}')

    left, right = st.columns(2)
    with left:
        st.markdown("**Market IV vs Heston IV**")
        compare = fit[["Strike", "Market IV", "Heston IV"]].copy().set_index("Strike")
        st.line_chart(compare, use_container_width=True)
    with right:
        st.markdown("**Heston IV Surface / Calibration Fit**")
        surface_display = h_surface.copy()
        st.dataframe(surface_display.round(4), width="stretch")
        st.caption("The current simulator supplies one expiry; additional live expiries will expand this into a full term surface.")

    st.markdown("**Model Dislocation Ranking**")
    if len(ranked):
        display_cols = [
            "Strike", "DTE", "Market IV", "Heston IV", "IV Gap",
            "Price Gap", "Dislocation Score", "Regime",
        ]
        display_cols = [c for c in display_cols if c in ranked.columns]
        st.dataframe(
            ranked[display_cols].round(4),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No model-dislocation observations available.")

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Mean Dislocation", f'{summary["mean_score"]:.1f}/100')
    d2.metric("High Dislocations", str(summary["high_count"]))
    d3.metric("Largest IV Gap", f'{summary["max_gap"]:.3f} vol pts')
    d4.metric(
        "Top Contract",
        f'{summary["top_strike"]:.0f}' if summary["top_strike"] is not None else "—",
    )

    st.caption(
        "Interpretation: higher dislocation means a larger model-vs-market difference "
        "under the calibrated Heston specification. Calibration quality should be checked "
        "before using the ranking for research decisions."
    )



# IFIT V0.6.5 LIVE MODEL DISLOCATION INTELLIGENCE
@st.cache_data(ttl=30, show_spinner=False)
def _ifit_v065_analyze_cached(spot_value, chain_df, days_value, rate_value):
    return analyze_live_dislocation(
        float(spot_value),
        chain_df,
        int(days_value),
        float(rate_value),
    )


def _ifit_v065_render(chain_df, live_spot, live_days):
    if chain_df is None or len(chain_df) < 5 or live_spot <= 0:
        st.info("V0.6.5 Live Model Dislocation Intelligence is waiting for sufficient option-chain data.")
        return

    st.markdown("---")
    st.markdown("### ⚡ IFIT V0.6.5 — LIVE MODEL DISLOCATION INTELLIGENCE")
    st.caption(
        "Explainable market-vs-Heston residual analysis across the active option chain. "
        "The score identifies model dislocation; it is not an automatic arbitrage or trade signal."
    )

    rate = st.sidebar.number_input(
        "Dislocation risk-free rate (%)",
        min_value=-5.0, max_value=25.0, value=6.0, step=0.25,
        key="ifit_v065_rate",
    )

    try:
        result = _ifit_v065_analyze_cached(
            float(live_spot), chain_df, int(live_days), float(rate)
        )
    except Exception as exc:
        st.warning(f"Model dislocation analysis unavailable: {exc}")
        return

    ranked = result["ranked"]
    stats = result["stats"]
    confidence = result["confidence"]

    top = ranked.iloc[0] if len(ranked) else None
    high = int((ranked["Dislocation Score"] >= 75).sum()) if len(ranked) else 0
    elevated = int((ranked["Dislocation Score"] >= 50).sum()) if len(ranked) else 0
    mean_score = float(ranked["Dislocation Score"].mean()) if len(ranked) else 0.0
    max_gap = float(ranked["IV Gap"].abs().max()) if len(ranked) else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Top Dislocation", f'{float(top["Dislocation Score"]):.1f}/100' if top is not None else "—")
    c2.metric("Mean Score", f"{mean_score:.1f}/100")
    c3.metric("Extreme", str(high))
    c4.metric("Elevated+", str(elevated))
    c5.metric("Calibration Confidence", f"{confidence:.1f}/100")

    if confidence >= 75:
        st.success("🟢 **CALIBRATION QUALITY: GOOD**")
    elif confidence >= 50:
        st.warning("🟡 **CALIBRATION QUALITY: MODERATE**")
    else:
        st.error("🔴 **CALIBRATION QUALITY: LOW**")

    if top is not None:
        st.markdown("**Top Model Dislocation**")
        t1, t2, t3, t4, t5 = st.columns(5)
        t1.metric("Strike", f'{float(top["Strike"]):,.0f}')
        t2.metric("Market IV", f'{float(top["Market IV"]):.2f}%')
        t3.metric("Heston IV", f'{float(top["Heston IV"]):.2f}%')
        t4.metric("IV Gap", f'{float(top["IV Gap"]):+.2f} vol pts')
        t5.metric("Regime", str(top["Regime"]))

        st.info(
            f'**Primary driver:** {top["Primary Driver"]}  •  '
            f'**Secondary driver:** {top["Secondary Driver"]}  •  '
            f'**Model relation:** {top["Direction"]}'
        )

    st.markdown("**Explainable Dislocation Ranking**")
    display_cols = [
        "Strike", "DTE", "Market IV", "Heston IV", "IV Gap", "Price Gap",
        "Greek Sensitivity", "Calibration Quality", "Dislocation Score",
        "Regime", "Direction", "Primary Driver", "Secondary Driver",
    ]
    st.dataframe(
        ranked[display_cols].round(4),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("**Dislocation Drivers**")
    if len(ranked):
        driver_counts = ranked["Primary Driver"].value_counts().rename_axis("Driver").reset_index(name="Contracts")
        st.bar_chart(driver_counts.set_index("Driver"), use_container_width=True)

    with st.expander("How the V0.6.5 score works"):
        st.write(
            "The score combines absolute IV residual, normalized price residual, "
            "expiry sensitivity, higher-order Greek sensitivity, and calibration quality. "
            "All components are transparent and capped to 0–100. Calibration confidence "
            "is a model-fit quality indicator—not a probability of profit."
        )

    st.caption(
        f'Calibration: {int(stats["points"])} points • '
        f'IV RMSE: {float(stats["iv_rmse"]):.3f} vol pts • '
        f'Price RMSE: {float(stats["price_rmse"]):,.2f} • '
        f'Largest |IV gap|: {max_gap:.3f} vol pts'
    )



# IFIT V0.6.6 LIVE VOLATILITY SIGNAL ENGINE
@st.cache_data(ttl=15, show_spinner=False)
def _ifit_v066_signal_cached(spot_value, chain_df, atm_iv_value, hv_value, days_value, rate_value):
    return build_vol_signal(
        float(spot_value),
        chain_df,
        float(atm_iv_value),
        float(hv_value),
        int(days_value),
        float(rate_value),
    )


def _ifit_v066_render(chain_df, live_spot, atm_iv_value, hv_value, live_days):
    if chain_df is None or len(chain_df) < 5 or live_spot <= 0:
        st.info("V0.6.6 Live Volatility Signal Engine is waiting for sufficient option-chain data.")
        return

    st.markdown("---")
    st.markdown("### ⚡ IFIT V0.6.6 — LIVE VOLATILITY SIGNAL ENGINE")
    st.caption(
        "Transparent volatility-regime synthesis using IV premium, skew, smile, "
        "Heston residuals and gamma structure. This is a research signal, not an automatic trade recommendation."
    )

    rate = st.sidebar.number_input(
        "Volatility signal risk-free rate (%)",
        min_value=-5.0, max_value=25.0, value=6.0, step=0.25,
        key="ifit_v066_rate",
    )

    try:
        sig = _ifit_v066_signal_cached(
            float(live_spot), chain_df, float(atm_iv_value),
            float(hv_value), int(live_days), float(rate)
        )
    except Exception as exc:
        st.warning(f"Volatility signal unavailable: {exc}")
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("VOL SIGNAL", f'{sig["score"]:.1f}/100')
    c2.metric("REGIME", sig["regime"])
    c3.metric("SIGNAL STRENGTH", f'{sig["strength"]:.1f}/100')
    c4.metric("IV − HV", f'{sig["iv_premium"]:+.2f} pts')
    c5.metric("Heston Gap", f'{sig["mean_heston_gap"]:+.2f} pts')

    if sig["regime"] == "VOL EXPANSION":
        st.error("🔴 **VOLATILITY EXPANSION REGIME**")
    elif sig["regime"] == "EXPANSION WATCH":
        st.warning("🟠 **EXPANSION WATCH**")
    elif sig["regime"] == "VOL COMPRESSION":
        st.success("🟢 **VOLATILITY COMPRESSION REGIME**")
    elif sig["regime"] == "COMPRESSION WATCH":
        st.info("🔵 **COMPRESSION WATCH**")
    else:
        st.info("⚪ **NEUTRAL VOLATILITY REGIME**")

    st.info(sig["interpretation"])

    st.markdown("**Current Volatility State**")
    a,b,c,d,e = st.columns(5)
    a.metric("Put Skew", f'{sig["put_skew"]:+.2f}')
    b.metric("Call Skew", f'{sig["call_skew"]:+.2f}')
    c.metric("Smile", f'{sig["smile"]:+.2f}')
    d.metric("Net Gamma", f'{sig["net_gamma"]:+,.0f}')
    e.metric("Mean Dislocation", f'{sig["mean_dislocation"]:.1f}/100')

    st.markdown("**Volatility Signal Components**")
    comp = pd.DataFrame(sig["components"], columns=["Factor", "Impact", "Reading"])
    comp["Impact"] = comp["Impact"].map(lambda x: f"{x:+.2f}")
    st.dataframe(comp, width="stretch", hide_index=True)

    st.markdown("**Strongest Volatility Drivers**")
    if sig["drivers"]:
        cols = st.columns(len(sig["drivers"]))
        for col, driver in zip(cols, sig["drivers"]):
            col.metric(
                driver["name"],
                f'{driver["impact"]:+.2f}',
                driver["reading"]
            )

    with st.expander("How the V0.6.6 signal is calculated"):
        st.write(
            "The score starts at 50. IV premium, downside skew, smile curvature, "
            "the sign of the Heston market-model residual, and gamma structure add "
            "or subtract transparent directional contributions. Mean model-dislocation "
            "raises conviction modestly but does not determine direction. The score is "
            "capped to 0–100. 70+ is VOL EXPANSION, 55–69 EXPANSION WATCH, "
            "46–54 NEUTRAL, 31–45 COMPRESSION WATCH, and 30 or below VOL COMPRESSION."
        )

    st.caption(
        f'Calibration confidence: {sig["calibration_confidence"]:.1f}/100 • '
        "Signal refresh cache: 15 seconds"
    )


# IFIT V0.6.7 REAL-TIME MARKET INTELLIGENCE
@st.cache_data(ttl=10, show_spinner=False)
def _ifit_v067_market_cached(spot_value, days_value, atm_iv_value, hv_value,
                              flow_levels_value, imbalance_value):
    return build_market_intelligence(
        float(spot_value), int(days_value), float(atm_iv_value), float(hv_value),
        int(flow_levels_value), float(imbalance_value), r_percent=6.0
    )


def _ifit_v067_render():
    st.markdown("---")
    st.markdown("### ⚡ IFIT V0.6.7 — REAL-TIME MARKET INTELLIGENCE")
    st.caption(
        "Cross-module synthesis of options structure, order flow, volatility, "
        "gamma and model risk. The intelligence score is a research classification, "
        "not a probability of profit or an automatic trade signal."
    )

    try:
        mi = _ifit_v067_market_cached(
            spot, days, atm_iv, hv30, flow_levels, imbalance_ratio
        )
    except Exception as exc:
        st.warning(f"Market intelligence unavailable: {exc}")
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("IFIT MARKET STATE", f'{mi["score"]:.1f}/100')
    c2.metric("REGIME", mi["regime"])
    c3.metric("CONFIDENCE", f'{mi["confidence"]:.1f}/100')
    c4.metric("RISK STATE", mi["risk_state"])
    c5.metric("FLOW", f'{mi["flow_score"]}/100')

    if mi["regime"] == "BULLISH":
        st.success("🟢 **IFIT MARKET STATE: BULLISH**")
    elif mi["regime"] == "BEARISH":
        st.error("🔴 **IFIT MARKET STATE: BEARISH**")
    else:
        st.info("⚪ **IFIT MARKET STATE: NEUTRAL**")

    st.info(mi["summary"])

    st.markdown("**Cross-Module State**")
    a,b,c,d,e,f = st.columns(6)
    a.metric("Flow Confluence", f'{mi["flow_score"]}/100', mi["flow_regime"])
    b.metric("Volatility Signal", f'{mi["vol_score"]:.1f}/100', mi["vol_regime"])
    c.metric("PCR", f'{mi["pcr"]:.2f}')
    d.metric("IV − HV", f'{mi["iv_premium"]:+.2f} pts')
    e.metric("Gamma Risk", f'{mi["gamma_risk"]:.0f}/100')
    f.metric("Model Dislocation", f'{mi["mean_dislocation"]:.0f}/100')

    left, right = st.columns(2)
    with left:
        st.markdown("**Strongest Market Drivers**")
        if mi["drivers"]:
            driver_df = pd.DataFrame(mi["drivers"])
            driver_df["Impact"] = driver_df["impact"].map(lambda x: f"{x:+.1f}")
            driver_df = driver_df.rename(columns={"name":"Driver","reading":"Reading"})
            st.dataframe(
                driver_df[["Driver","Impact","Reading"]],
                width="stretch", hide_index=True
            )
    with right:
        st.markdown("**Current Risk Flags**")
        for risk in mi["risks"]:
            st.warning(risk)

    with st.expander("Why IFIT reached this market state"):
        st.markdown(
            f"""
            **Directional layer:** Flow Confluence = **{mi["flow_score"]}/100** and
            PCR = **{mi["pcr"]:.2f}** provide the primary directional inputs.

            **Volatility layer:** V0.6.6 = **{mi["vol_score"]:.1f}/100
            ({mi["vol_regime"]}). Volatility changes risk intensity and is not
            automatically treated as bullish or bearish.

            **Risk layer:** Gamma Risk = **{mi["gamma_risk"]:.0f}/100**,
            Model Dislocation = **{mi["mean_dislocation"]:.0f}/100**, and
            Heston calibration confidence = **{mi["calibration_confidence"]:.0f}/100**.

            **Important:** Confidence is an alignment/model-quality metric,
            **not a probability of profit**.
            """
        )

    st.caption(
        "V0.6.7 combines the active IFIT analytics stack. Production deployment "
        "should use synchronized authorized market data; simulation mode remains illustrative."
    )


# IFIT V0.6.8 REGIME ENGINE
@st.cache_data(ttl=10, show_spinner=False)
def _ifit_v068_regime_cached(market_score, market_confidence, flow_score,
                              vol_score, vol_regime, gamma_risk,
                              model_dislocation, pcr, iv_premium):
    return classify_regime(
        market_score, market_confidence, flow_score, vol_score, vol_regime,
        gamma_risk, model_dislocation, pcr, iv_premium
    )


def _ifit_v068_render():
    st.markdown("---")
    st.markdown("### ⚡ IFIT V0.6.8 — REGIME ENGINE")

    # V0.6.8 owns its dependency boundary: build the V0.6.7 market-intelligence
    # snapshot here instead of relying on a local variable created by another
    # renderer. This prevents Streamlit execution-order/name-scope failures.
    try:
        mi = _ifit_v067_market_cached(
            spot, days, atm_iv, hv30, flow_levels, imbalance_ratio
        )
    except Exception as exc:
        st.warning(f"Market intelligence dependency unavailable: {exc}")
        return
    st.caption(
        "Market-environment classification using directional state, flow alignment, "
        "volatility, gamma risk and model dislocation. Regime confidence is not a probability of profit."
    )
    try:
        regime = _ifit_v068_regime_cached(
            mi["score"], mi["confidence"], mi["flow_score"], mi["vol_score"],
            mi["vol_regime"], mi["gamma_risk"], mi["mean_dislocation"],
            mi["pcr"], mi["iv_premium"]
        )
    except Exception as exc:
        st.warning(f"Regime engine unavailable: {exc}")
        return

    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("MARKET REGIME", regime["regime"])
    c2.metric("REGIME CONFIDENCE", f'{regime["confidence"]:.1f}/100')
    c3.metric("DIRECTIONAL STRENGTH", f'{regime["directional_strength"]:.1f}/100')
    c4.metric("TRANSITION RISK", f'{regime["transition_risk"]:.1f}/100')
    c5.metric("FLOW ALIGNMENT", f'{regime["directional_alignment"]:.1f}/100')

    if regime["regime"] in ("TRENDING BULL", "BULLISH BIAS / MIXED"):
        st.success(f'🟢 **{regime["regime"]}**')
    elif regime["regime"] in ("TRENDING BEAR", "BEARISH BIAS / MIXED"):
        st.error(f'🔴 **{regime["regime"]}**')
    elif regime["regime"] == "VOLATILITY EXPANSION":
        st.warning("🔥 **VOLATILITY EXPANSION**")
    elif regime["regime"] == "HIGH-RISK TRANSITION":
        st.warning("⚠️ **HIGH-RISK TRANSITION**")
    elif regime["regime"] == "RANGE / MEAN REVERSION":
        st.info("🟡 **RANGE / MEAN REVERSION**")
    else:
        st.info("⚪ **NO EDGE / MIXED REGIME**")

    a,b,c,d,e=st.columns(5)
    a.metric("Market State", f'{mi["score"]:.1f}/100', mi["regime"])
    b.metric("Flow", f'{mi["flow_score"]}/100', mi["flow_regime"])
    c.metric("Volatility", f'{mi["vol_score"]:.1f}/100', mi["vol_regime"])
    d.metric("Gamma Risk", f'{mi["gamma_risk"]:.0f}/100')
    e.metric("Model Dislocation", f'{mi["mean_dislocation"]:.0f}/100')

    left,right=st.columns(2)
    with left:
        st.markdown("**Regime Drivers**")
        df=pd.DataFrame(regime["drivers"]).rename(columns={"name":"Driver","score":"Score"})
        st.dataframe(df, width="stretch", hide_index=True)
    with right:
        st.markdown("**Regime Diagnostics**")
        st.metric("Range / Mean-Reversion Score", f'{regime["range_score"]:.1f}/100')
        st.metric("Transition State", regime["transition_label"])
        st.metric("PCR", f'{mi["pcr"]:.2f}')
        st.metric("IV − HV", f'{mi["iv_premium"]:+.2f} pts')

    with st.expander("How IFIT classifies the regime"):
        st.write(
            "IFIT separates directional state from volatility and risk. Trending "
            "regimes require directional strength plus flow alignment. Range/mean "
            "reversion requires weak direction and supportive compression/neutral "
            "positioning. Volatility expansion is triggered by the V0.6.6 regime. "
            "High-risk transition is triggered by elevated gamma/model risk when "
            "direction is not decisive. Confidence measures cross-module agreement "
            "and model quality; it is not a probability of profit."
        )


# IFIT V0.6.9 SIGNAL ENGINE
@st.cache_data(ttl=10, show_spinner=False)
def _ifit_v069_signal_cached(market_score, market_confidence, market_regime,
                             regime_confidence, directional_strength, flow_score,
                             vol_score, vol_regime, gamma_risk, model_dislocation,
                             spot_value, atm_value, expected_low_value,
                             expected_high_value, pcr_value, max_pain_value):
    return build_signal(
        market_score, market_confidence, market_regime, regime_confidence,
        directional_strength, flow_score, vol_score, vol_regime, gamma_risk,
        model_dislocation, spot_value, atm_value, expected_low_value,
        expected_high_value, pcr_value, max_pain_value
    )


def _ifit_v069_render():
    st.markdown("---")
    st.markdown("### ⚡ IFIT V0.6.9 — SIGNAL ENGINE")
    st.caption(
        "Decision-intelligence layer combining IFIT Market State, Regime, Flow, "
        "Volatility and risk diagnostics. This is a research signal, not an automatic order."
    )
    try:
        # Rebuild the upstream snapshots locally to keep this renderer independent
        # of Streamlit execution order.
        mi_local = _ifit_v067_market_cached(
            spot, days, atm_iv, hv30, flow_levels, imbalance_ratio
        )
        rg_local = _ifit_v068_regime_cached(
            mi_local["score"], mi_local["confidence"], mi_local["flow_score"],
            mi_local["vol_score"], mi_local["vol_regime"], mi_local["gamma_risk"],
            mi_local["mean_dislocation"], mi_local["pcr"], mi_local["iv_premium"]
        )
        om = mi_local["option_metrics"]
        # options_engine.calculate_metrics exposes the expected move as "move";
        # derive the actual upper/lower boundaries here for the signal layer.
        expected_move = float(om.get("move", 0.0))
        exp_low = float(spot - expected_move)
        exp_high = float(spot + expected_move)
        atm_value = round(float(spot) / 100.0) * 100.0
        pcr_value = float(mi_local.get("pcr", 1.0))
        max_pain_value = atm_value
        sig = _ifit_v069_signal_cached(
            mi_local["score"], mi_local["confidence"], rg_local["regime"],
            rg_local["confidence"], rg_local["directional_strength"],
            mi_local["flow_score"], mi_local["vol_score"], mi_local["vol_regime"],
            mi_local["gamma_risk"], mi_local["mean_dislocation"], spot,
            atm_value, exp_low, exp_high, pcr_value, max_pain_value
        )
    except Exception as exc:
        st.warning(f"Signal engine unavailable: {exc}")
        return

    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("IFIT SIGNAL", sig["direction"])
    c2.metric("DIRECTION SCORE", f'{sig["direction_score"]:.1f}/100')
    c3.metric("CONVICTION", f'{sig["conviction"]:.1f}/100')
    c4.metric("RISK", sig["risk"])
    c5.metric("REGIME", sig["market_regime"])

    if sig["direction"]=="BULLISH":
        st.success(f'🟢 **IFIT SIGNAL: BULLISH — {sig["conviction_label"]} CONVICTION**')
    elif sig["direction"]=="BEARISH":
        st.error(f'🔴 **IFIT SIGNAL: BEARISH — {sig["conviction_label"]} CONVICTION**')
    else:
        st.info(f'⚪ **IFIT SIGNAL: NEUTRAL — {sig["conviction_label"]} CONVICTION**')

    st.info(sig["summary"])

    a,b,c,d,e,f=st.columns(6)
    a.metric("Market State",f'{mi_local["score"]:.1f}/100',mi_local["regime"])
    b.metric("Regime Confidence",f'{rg_local["confidence"]:.1f}/100')
    c.metric("Flow",f'{mi_local["flow_score"]}/100',mi_local["flow_regime"])
    d.metric("Volatility",f'{mi_local["vol_score"]:.1f}/100',mi_local["vol_regime"])
    e.metric("Support",f'{sig["support"]:,.0f}',sig["support_name"])
    f.metric("Resistance",f'{sig["resistance"]:,.0f}',sig["resistance_name"])

    st.markdown("**Signal Framework**")
    left,right=st.columns(2)
    with left:
        df=pd.DataFrame(sig["drivers"]).rename(columns={"name":"Driver","strength":"Strength","reading":"Reading"})
        st.dataframe(df,width="stretch",hide_index=True)
    with right:
        st.metric("Invalidation",sig["invalidation_rule"])
        st.metric("Expected Move",f'{exp_low:,.0f} – {exp_high:,.0f}')
        st.metric("PCR",f'{mi_local["pcr"]:.2f}')
        st.metric("Model Dislocation",f'{mi_local["mean_dislocation"]:.0f}/100')

    with st.expander("IFIT Signal Methodology"):
        st.write(
            "Direction is primarily driven by Market State and Flow, with PCR as a "
            "low-weight options-positioning input. Conviction rewards cross-module "
            "agreement and confidence while penalizing high-risk transition, gamma, "
            "model-dislocation and volatility-expansion conditions. Support and "
            "resistance are selected from expected-move and available structural "
            "levels. Invalidation is a conservative research boundary. None of these "
            "outputs is a probability of profit or a guaranteed forecast."
        )


# IFIT V0.7.1 EVENT MEMORY & ALERT ENGINE
def _ifit_v071_render():
    st.markdown("---")
    st.markdown("### ⚡ IFIT V0.7.1 — EVENT MEMORY & ALERT ENGINE")
    st.caption(
        "Persistent event intelligence: ranks new, ongoing and resolved conditions "
        "across IFIT's signal, regime, flow, volatility, gamma, model and structure layers."
    )
    try:
        mi = _ifit_v067_market_cached(spot, days, atm_iv, hv30, flow_levels, imbalance_ratio)
        rg = _ifit_v068_regime_cached(
            mi["score"], mi["confidence"], mi["flow_score"], mi["vol_score"],
            mi["vol_regime"], mi["gamma_risk"], mi["mean_dislocation"],
            mi["pcr"], mi["iv_premium"]
        )
        om=mi["option_metrics"]
        move=float(om.get("move",0.0))
        atm_value=round(float(spot)/100.0)*100.0
        current={
            "timestamp":pd.Timestamp.now().isoformat(),
            "signal":"NEUTRAL","direction_score":0.0,"conviction":0.0,
            "regime":rg["regime"],"regime_confidence":rg["confidence"],
            "transition_risk":rg["transition_risk"],
            "flow_score":mi["flow_score"],"flow_regime":mi["flow_regime"],
            "vol_score":mi["vol_score"],"vol_regime":mi["vol_regime"],
            "gamma_risk":mi["gamma_risk"],"model_dislocation":mi["mean_dislocation"],
            "spot":float(spot),"expected_low":float(spot-move),"expected_high":float(spot+move),
            "support":float(spot-move),"resistance":float(atm_value),
            "health":health_label(_health.status) if _health is not None else "UNKNOWN",
        }
        sig=build_signal(
            mi["score"],mi["confidence"],rg["regime"],rg["confidence"],
            rg["directional_strength"],mi["flow_score"],mi["vol_score"],mi["vol_regime"],
            mi["gamma_risk"],mi["mean_dislocation"],float(spot),atm_value,
            float(spot-move),float(spot+move),mi["pcr"],atm_value
        )
        current.update({
            "signal":sig["direction"],"direction_score":sig["direction_score"],
            "conviction":sig["conviction"],"support":sig["support"],"resistance":sig["resistance"]
        })
    except Exception as exc:
        st.warning(f"Event memory engine unavailable: {exc}")
        return

    previous=st.session_state.get("ifit_v070_previous_state")
    new_events=detect_events(previous,current)
    flags=monitored_conditions(current)

    memory=st.session_state.get("ifit_v071_event_memory",{"records":{},"active_keys":[]})
    memory=update_memory(memory,new_events,flags)
    st.session_state["ifit_v071_event_memory"]=memory
    st.session_state["ifit_v070_previous_state"]=current

    snap=alert_snapshot(memory)
    counts=snap["counts"]

    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("ACTIVE ALERTS",counts["active"])
    c2.metric("NEW",counts["new"])
    c3.metric("ONGOING",counts["ongoing"])
    c4.metric("RESOLVED",counts["resolved"])
    c5.metric("TOP SCORE",f'{snap["top"].get("priority_score",0):.1f}' if snap["top"] else "—")

    top=snap["top"]
    if top:
        st.warning(f'🚨 IFIT MARKET ALERT — {top["severity"]}: {top["title"]}')
        st.info(f'{top.get("detail","")}  |  Priority {top.get("priority_score",0):.1f}/100')
    else:
        st.success("IFIT MARKET ALERT — No high-priority active alert.")

    st.markdown("**Alert Summary**")
    st.write(snap["summary"])

    st.markdown("**Active Alert Ranking**")
    if snap["active"]:
        rows=[]
        for r in snap["active"]:
            rows.append({
                "Status":r.get("status"),"Severity":r.get("severity"),
                "Type":r.get("kind"),"Alert":r.get("title"),
                "Priority":r.get("priority_score",0),"Occurrences":r.get("occurrences",0),
                "Details":r.get("detail","")
            })
        st.dataframe(pd.DataFrame(rows),width="stretch",hide_index=True)
    else:
        st.info("No active alerts.")

    with st.expander("Resolved Event Memory"):
        if snap["resolved"]:
            rows=[{
                "Status":"RESOLVED","Severity":r.get("severity"),"Type":r.get("kind"),
                "Alert":r.get("title"),"Priority":r.get("priority_score",0),
                "Occurrences":r.get("occurrences",0)
            } for r in snap["resolved"][:20]]
            st.dataframe(pd.DataFrame(rows),width="stretch",hide_index=True)
        else:
            st.caption("No resolved events in the current session.")

    with st.expander("IFIT Event Memory Methodology"):
        st.write(
            "Events are persisted in the Streamlit session and classified as NEW, "
            "ONGOING or RESOLVED. Active alerts are ranked using severity plus event "
            "score. Persistent watchlist conditions remain active until the condition "
            "disappears. Resolved history is retained for the current session. "
            "No external notification or order is sent by this engine."
        )


# IFIT V0.7.5 PORTFOLIO RISK ENGINE
def _ifit_v075_render():
    st.markdown("---")
    st.markdown("### ⚡ IFIT V0.7.5 — PORTFOLIO RISK ENGINE")
    st.caption(
        "Portfolio-level risk diagnostics combining higher-order Greeks, concentration and multi-dimensional stress. "
        "Normalized research output — not statistical VaR, margin or an automatic trading instruction."
    )

    default_positions = [
        {"Instrument":"NIFTY 25000 CE","Side":"BUY","Qty":1,"Multiplier":50,"Strike":25000,"DTE":14,"IV":atm_iv},
        {"Instrument":"NIFTY 24700 PE","Side":"BUY","Qty":1,"Multiplier":50,"Strike":24700,"DTE":14,"IV":atm_iv+0.3},
        {"Instrument":"NIFTY 24900 CE","Side":"SELL","Qty":1,"Multiplier":50,"Strike":24900,"DTE":14,"IV":atm_iv+0.1},
    ]
    st.markdown("**Portfolio Positions**")
    pos_df=pd.DataFrame(default_positions)
    edited=st.data_editor(
        pos_df,
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        column_config={
            "Side":st.column_config.SelectboxColumn("Side",options=["BUY","SELL"]),
            "Qty":st.column_config.NumberColumn("Qty",min_value=1,step=1),
            "Multiplier":st.column_config.NumberColumn("Multiplier",min_value=1,step=1),
            "Strike":st.column_config.NumberColumn("Strike",min_value=1,step=50),
            "DTE":st.column_config.NumberColumn("DTE",min_value=1,step=1),
            "IV":st.column_config.NumberColumn("IV %",min_value=0.1,step=0.1),
        },
        key="ifit_v075_positions"
    )

    try:
        pos_rows=[]
        for p in edited.to_dict("records"):
            if not p.get("Instrument"):
                continue
            instrument=str(p["Instrument"])
            opt="PE" if instrument.upper().endswith("PE") or " PE" in instrument.upper() else "CE"
            pos_rows.append({
                "Instrument":instrument,
                "Side":str(p.get("Side","BUY")),
                "Qty":float(p.get("Qty",1)),
                "Multiplier":float(p.get("Multiplier",50)),
                "Strike":float(p.get("Strike",spot)),
                "DTE":float(p.get("DTE",days)),
                "IV":float(p.get("IV",atm_iv)),
                "Option":opt,
            })
        pg_df,totals=portfolio_greeks(pos_rows,float(spot),r_percent=6.5,q_percent=0.0)
        st.session_state["ifit_portfolio_totals"] = totals

        if not totals:
            st.info("Add at least one valid portfolio position to calculate risk.")
            return

        result=build_portfolio_risk(positions_df=pg_df,totals=totals,spot=float(spot))

        a,b,c,d,e,f=st.columns(6)
        a.metric("PORTFOLIO RISK",f'{result["score"]:.1f}/100')
        b.metric("RISK REGIME",result["regime"])
        c.metric("TAIL BIAS",result["tail_bias"])
        d.metric("CONCENTRATION",f'{result["concentration_risk"]:.1f}')
        e.metric("STRESS SCORE",f'{result["stress_score"]:.1f}')
        f.metric("LOSS SCENARIOS",f'{result["loss_rate"]:.1f}%')

        if result["regime"] in ("EXTREME","HIGH"):
            st.warning(f'⚠️ {result["alert"]}')
        elif result["regime"] in ("ELEVATED","MODERATE"):
            st.info(result["alert"])
        else:
            st.success(result["alert"])

        st.markdown("**Portfolio Risk Drivers**")
        left,right=st.columns(2)
        with left:
            st.dataframe(result["components"],width="stretch",hide_index=True)
        with right:
            st.markdown("**Strongest Risk Drivers**")
            st.dataframe(result["drivers"],width="stretch",hide_index=True)

        st.markdown("**Net Portfolio Risk Snapshot**")
        x1,x2,x3,x4,x5=st.columns(5)
        x1.metric("Net Delta",f'{result["net_delta"]:.4f}')
        x2.metric("Net Gamma",f'{result["net_gamma"]:.7f}')
        x3.metric("Net Theta / day",f'{result["net_theta"]:.4f}')
        x4.metric("Net Vega / vol pt",f'{result["net_vega"]:.4f}')
        x5.metric("Delta Notional",f'₹{result["net_delta_notional"]:,.0f}')

        st.markdown("**Position-Level Risk Attribution**")
        attr=result["attribution"]
        if not attr.empty:
            st.dataframe(
                attr.style.format({
                    "Delta Risk":"{:.4f}","Gamma Risk":"{:.7f}","Vega Risk":"{:.4f}",
                    "Vol Convexity":"{:.4f}","Total Risk Contribution":"{:.4f}","Risk Share %":"{:.1f}%"
                }),
                use_container_width=True,hide_index=True
            )

        st.markdown("**Portfolio Stress Map — Spot × IV × Time**")
        sv=result["scenarios"].copy()
        h=st.selectbox("Stress horizon",sorted(sv["Days"].unique().tolist()),key="ifit_v075_horizon")
        hv=sv[sv["Days"]==h]
        pivot=hv.pivot(index="Spot Shock %",columns="IV Shock pt",values="Approx P&L")
        st.dataframe(pivot.style.format("₹{:,.2f}"),width="stretch")

        w=result["worst"]; best=result["best"]
        q1,q2=st.columns(2)
        with q1:
            st.markdown("**Worst Modeled Scenario**")
            st.write({"Days":int(w["Days"]),"Spot Shock":f'{w["Spot Shock %"]:+g}%',"IV Shock":f'{w["IV Shock pt"]:+g} pt',"Approx P&L":round(w["Approx P&L"],2)})
        with q2:
            st.markdown("**Best Modeled Scenario**")
            st.write({"Days":int(best["Days"]),"Spot Shock":f'{best["Spot Shock %"]:+g}%',"IV Shock":f'{best["IV Shock pt"]:+g} pt',"Approx P&L":round(best["Approx P&L"],2)})

        with st.expander("IFIT Portfolio Risk Engine Methodology"):
            st.markdown(
                "The portfolio risk score combines normalized Delta, convexity, volatility, theta/carry, "
                "third-order, concentration and scenario-tail diagnostics. The stress cube uses the existing "
                "local Taylor approximation from the portfolio Greek engine across spot, IV and time shocks. "
                "Risk-share is based on modeled position contribution. These scales are screening diagnostics, "
                "not probabilities, statistical VaR, margin requirements or forecasts."
            )
    except Exception as exc:
        st.error(f"Portfolio risk engine unavailable: {type(exc).__name__}: {exc}")



# IFIT V0.7.6 LIQUIDITY & EXECUTION ENGINE
def _ifit_v076_render():
    st.markdown("---")
    st.markdown("### ⚡ IFIT V0.7.6 — LIQUIDITY & EXECUTION ENGINE")
    st.caption(
        "Liquidity and execution diagnostics across the active option chain: spread, depth, order-size impact and execution risk. "
        "Provider bid/ask/depth fields are used when available; otherwise IFIT uses clearly labelled simulation proxies. "
        "Not a guaranteed fill estimate or automatic order engine."
    )
    try:
        chain = build_option_chain(float(spot), float(days), float(atm_iv))
        result = build_liquidity_execution(chain_df=chain, spot=float(spot), multiplier=50)
        a,b,c,d,e = st.columns(5)
        a.metric("LIQUIDITY SCORE", f'{result["score"]:.1f}/100')
        b.metric("EXECUTION REGIME", result["regime"])
        c.metric("EXECUTION RISK", f'{result["execution_risk"]:.1f}')
        d.metric("MEDIAN SPREAD", f'{result["summary"].get("median_spread_bps", 0):.1f} bps')
        e.metric("P90 SPREAD", f'{result["summary"].get("p90_spread_bps", 0):.1f} bps')

        if result["regime"] in ("THIN", "FRAGILE"):
            st.warning("⚠️ " + result["alert"])
        else:
            st.info(result["alert"])

        st.markdown("**Liquidity Map — Highest Quality Contracts**")
        top = result["top_liquid"][[
            "Strike","Option","LTP","OI","Bid","Ask","Spread (bps)","5-Level Depth","Liquidity Score","Quote Source","Depth Source"
        ]].copy()
        st.dataframe(top.style.format({
            "LTP":"{:,.2f}","OI":"{:,.0f}","Bid":"{:,.2f}","Ask":"{:,.2f}",
            "Spread (bps)":"{:.1f}","5-Level Depth":"{:,.0f}","Liquidity Score":"{:.1f}"
        }), use_container_width=True, hide_index=True)

        left,right = st.columns(2)
        with left:
            st.markdown("**Execution Risk — Lowest Quality Contracts**")
            low = result["risk_contracts"][[
                "Strike","Option","LTP","OI","Spread (bps)","5-Level Depth","Liquidity Score"
            ]].copy()
            st.dataframe(low.style.format({
                "LTP":"{:,.2f}","OI":"{:,.0f}","Spread (bps)":"{:.1f}",
                "5-Level Depth":"{:,.0f}","Liquidity Score":"{:.1f}"
            }), use_container_width=True, hide_index=True)
        with right:
            st.markdown("**ATM Execution Ladder**")
            ladder = result["atm_ladder"].copy()
            st.dataframe(ladder.style.format({
                "Strike":"{:,.0f}","Order Qty":"{:,.0f}","Est. Slippage / pt":"{:,.4f}",
                "Est. Slippage ₹":"₹{:,.2f}","Top-Depth Utilization":"{:.1f}%","5-Level Utilization":"{:.1f}%"
            }), width="stretch", hide_index=True)

        st.markdown("**Execution Intelligence**")
        x1,x2,x3,x4 = st.columns(4)
        x1.metric("Contracts Analysed", result["summary"].get("contracts", 0))
        x2.metric("Median 5-Level Depth", f'{result["summary"].get("median_5level_depth", 0):,.0f}')
        x3.metric("ATM Strike", f'{result["summary"].get("atm_strike", 0):,.0f}')
        x4.metric("Depth Model", "PROVIDER / PROXY")

        with st.expander("IFIT Liquidity & Execution Methodology"):
            st.write(
                "Liquidity Score is a normalized 0–100 diagnostic combining quoted spread, modeled/observed depth, open-interest scale and quote quality. "
                "Execution slippage is a local impact approximation for 1, 5 and 10 lots at the ATM-nearest contracts. "
                "If the connected provider supplies bid/ask and depth, those fields are preferred; in simulation mode, IFIT derives conservative proxies from LTP and OI. "
                "OI is not order-book depth and should never be interpreted as guaranteed executable liquidity."
            )
    except Exception as exc:
        st.error(f"Liquidity & execution engine unavailable: {type(exc).__name__}: {exc}")


# IFIT V0.7.7 MARKET MICROSTRUCTURE / EXECUTION INTELLIGENCE ENGINE
def _ifit_v077_render():
    st.markdown("---")
    st.markdown("### ⚡ IFIT V0.7.7 — MARKET MICROSTRUCTURE / EXECUTION INTELLIGENCE ENGINE")
    st.caption(
        "Microstructure diagnostics combining quote quality, spread efficiency, depth, queue concentration, "
        "OI concentration and order-size impact. Provider fields are preferred; simulation mode uses clearly labelled proxies. "
        "Research diagnostics only — not automatic execution or guaranteed fills."
    )
    try:
        chain = build_option_chain(float(spot), float(days), float(atm_iv))
        result = build_microstructure(chain_df=chain, spot=float(spot), multiplier=50)
        s = result["summary"]
        a,b,c,d,e,f = st.columns(6)
        a.metric("MICROSTRUCTURE SCORE", f'{result["score"]:.1f}/100')
        b.metric("REGIME", result["regime"])
        c.metric("EXECUTION FRICTION", f'{s.get("friction", 0):.1f}')
        d.metric("MEDIAN SPREAD", f'{s.get("median_spread_bps", 0):.1f} bps')
        e.metric("P90 SPREAD", f'{s.get("p90_spread_bps", 0):.1f} bps')
        f.metric("ATM PRESSURE", f'{s.get("atm_pressure", 0):+.1f}')

        if result["regime"] in ("THIN", "FRAGILE"):
            st.warning("⚠️ " + result["alert"])
        else:
            st.info(result["alert"])

        st.markdown("**Microstructure Map — Highest Quality Contracts**")
        top = result["top_contracts"][[
            "Strike","Option","LTP","OI","Bid","Ask","Spread (bps)",
            "Top Depth","5-Level Depth","Queue Concentration","Microstructure Score",
            "Quote Source","Depth Source"
        ]].copy()
        st.dataframe(top.style.format({
            "Strike":"{:,.0f}","LTP":"{:,.2f}","OI":"{:,.0f}","Bid":"{:,.2f}","Ask":"{:,.2f}",
            "Spread (bps)":"{:.1f}","Top Depth":"{:,.0f}","5-Level Depth":"{:,.0f}",
            "Queue Concentration":"{:.1f}%","Microstructure Score":"{:.1f}"
        }), use_container_width=True, hide_index=True)

        left,right = st.columns(2)
        with left:
            st.markdown("**Execution Friction — Highest Risk Contracts**")
            low = result["risk_contracts"][[
                "Strike","Option","LTP","Spread (bps)","5-Level Depth",
                "Execution Friction","Microstructure Score","Quote Source"
            ]].copy()
            st.dataframe(low.style.format({
                "Strike":"{:,.0f}","LTP":"{:,.2f}","Spread (bps)":"{:.1f}",
                "5-Level Depth":"{:,.0f}","Execution Friction":"{:.1f}","Microstructure Score":"{:.1f}"
            }), use_container_width=True, hide_index=True)
        with right:
            st.markdown("**ATM Execution Impact Ladder**")
            ladder = result["ladder"].copy()
            st.dataframe(ladder.style.format({
                "Strike":"{:,.0f}","Order Qty":"{:,.0f}","Spread Cost ₹":"₹{:,.2f}",
                "Impact / pt":"{:,.4f}","Est. Slippage ₹":"₹{:,.2f}",
                "5-Level Utilization":"{:.1f}%","Execution Friction":"{:.1f}"
            }), width="stretch", hide_index=True)

        st.markdown("**Execution Intelligence**")
        x1,x2,x3,x4 = st.columns(4)
        x1.metric("Contracts Analysed", s.get("contracts", 0))
        x2.metric("Median 5-Level Depth", f'{s.get("median_depth", 0):,.0f}')
        x3.metric("Top-5 OI Concentration", f'{s.get("top5_oi_concentration", 0):.1f}%')
        x4.metric("ATM Strike", f'{s.get("atm_strike", 0):,.0f}')

        with st.expander("IFIT Market Microstructure Methodology"):
            st.write(
                "Microstructure Score is a normalized diagnostic combining spread efficiency, depth score, "
                "OI scale, quote quality and queue concentration. Execution Friction increases with wider spreads, "
                "lower five-level depth and concentrated top-of-book liquidity. ATM Pressure is the CE-versus-PE "
                "difference in microstructure score and is not a directional trading signal. Top-5 OI concentration "
                "describes positioning concentration, not executable liquidity. Provider quote/depth fields are used "
                "when supplied; otherwise IFIT uses V0.7.6 simulation proxies."
            )
    except Exception as exc:
        st.error(f"Market microstructure engine unavailable: {type(exc).__name__}: {exc}")


# IFIT V0.7.2 DECISION MATRIX ENGINE
def _ifit_v072_render():
    st.markdown("---")
    st.markdown("### ⚡ IFIT V0.7.2 — DECISION MATRIX ENGINE")
    st.caption(
        "Cross-module decision-support layer combining market state, regime, signal, "
        "flow, volatility, gamma, model dislocation and event alerts. Research output only; "
        "not an automatic trading signal or order."
    )
    try:
        mi=_ifit_v067_market_cached(spot, days, atm_iv, hv30, flow_levels, imbalance_ratio)
        rg=_ifit_v068_regime_cached(
            mi["score"],mi["confidence"],mi["flow_score"],mi["vol_score"],
            mi["vol_regime"],mi["gamma_risk"],mi["mean_dislocation"],
            mi["pcr"],mi["iv_premium"]
        )
        om=mi["option_metrics"]
        move=float(om.get("move",0.0))
        atm_value=round(float(spot)/100.0)*100.0
        sig=build_signal(
            mi["score"],mi["confidence"],rg["regime"],rg["confidence"],
            rg["directional_strength"],mi["flow_score"],mi["vol_score"],mi["vol_regime"],
            mi["gamma_risk"],mi["mean_dislocation"],float(spot),atm_value,
            float(spot-move),float(spot+move),mi["pcr"],atm_value
        )
        memory=st.session_state.get("ifit_v071_event_memory",{"records":{},"active_keys":[]})
        active=len([r for r in memory.get("records",{}).values()
                    if r.get("status") in ("NEW","ONGOING")])
        dm=build_decision_matrix(
            market_score=mi["score"],regime_confidence=rg["confidence"],
            directional_strength=rg["directional_strength"],flow_score=mi["flow_score"],
            vol_score=mi["vol_score"],gamma_risk=mi["gamma_risk"],
            model_dislocation=mi["mean_dislocation"],signal_direction=sig["direction"],
            conviction=sig["conviction"],transition_risk=rg["transition_risk"],
            spot=float(spot),support=float(sig["support"]),resistance=float(sig["resistance"]),
            expected_low=float(spot-move),expected_high=float(spot+move),
            pcr=mi["pcr"],iv_premium=mi["iv_premium"],active_alerts=active
        )
    except Exception as exc:
        st.warning(f"Decision matrix unavailable: {exc}")
        return

    a,b,c,d,e=st.columns(5)
    a.metric("SETUP",dm["setup"])
    b.metric("DIRECTION",dm["direction_bias"],f'{dm["directional_score"]:.1f}/100')
    c.metric("CONFIRMATION",f'{dm["confirmation_score"]:.1f}/100')
    d.metric("RISK",dm["risk_level"],f'{dm["risk_score"]:.1f}/100')
    e.metric("AGREEMENT",f'{dm["agreement_score"]:.1f}/100')

    if dm["risk_level"] in ("HIGH","EXTREME"):
        st.warning(f'⚠️ IFIT RISK STATE: {dm["risk_level"]} — risk controls dominate directional conviction.')
    elif dm["setup"]=="HIGH-QUALITY SETUP":
        st.success(f'IFIT SETUP: {dm["setup"]} — cross-module confirmation is strong.')
    else:
        st.info(f'IFIT SETUP: {dm["setup"]} — wait for stronger cross-module confirmation.')

    left,right=st.columns(2)
    with left:
        st.markdown("**Decision Matrix**")
        st.dataframe(
            pd.DataFrame(decision_table(dm),columns=["Dimension","IFIT Reading"]),
            use_container_width=True,hide_index=True
        )
    with right:
        st.markdown("**Decision Framework**")
        st.metric("Support",f'{sig["support"]:,.0f}',sig["support_name"])
        st.metric("Resistance",f'{sig["resistance"]:,.0f}',sig["resistance_name"])
        st.metric("Expected Move",dm["expected_move"])
        st.metric("Active Alerts",dm["active_alerts"])

    st.markdown("**Strongest Decision Drivers**")
    st.dataframe(
        pd.DataFrame(dm["strongest_drivers"],columns=["Driver","Strength","Interpretation"]),
        use_container_width=True,hide_index=True
    )

    with st.expander("IFIT Decision Matrix Methodology"):
        st.write(
            "Directional score combines Market State, Flow and the existing IFIT Signal. "
            "Confirmation combines regime confidence, conviction and transition-risk control. "
            "Risk combines gamma risk, model dislocation, transition risk and active alerts. "
            "The setup label is deliberately conservative and is not a probability of profit. "
            "Expected move and support/resistance are research boundaries, not guarantees. "
            "This engine does not place orders."
        )


# Normalize the simulator/DataFrame option chain into the schema expected by
# the live-Greeks engine. This prevents DataFrame rows (strings/scalars) from
# being treated as option dictionaries.
def _ifit_scenario_option_records(chain_df, live_days):
    if chain_df is None or len(chain_df) == 0:
        return []
    expiry = (date.today() + timedelta(days=max(1, int(live_days)))).isoformat()
    records = []
    for _, r in chain_df.iterrows():
        records.append({
            "symbol": "NIFTY",
            "expiryDate": expiry,
            "strikePrice": float(r["Strike"]),
            "CE": {
                "lastPrice": float(r["CE LTP"]),
                "openInterest": float(r["CE OI"]),
                "impliedVolatility": float(r["CE IV"]),
            },
            "PE": {
                "lastPrice": float(r["PE LTP"]),
                "openInterest": float(r["PE OI"]),
                "impliedVolatility": float(r["PE IV"]),
            },
        })
    return records


# IFIT V0.7.3 SCENARIO ENGINE
def _ifit_v073_render():
    st.markdown("---")
    st.markdown("### ⚡ IFIT V0.7.3 — SCENARIO ENGINE")
    st.caption("BUILD: V0.7.4 HOTFIX7 — SCENARIO PATH REPAIRED")
    st.caption(
        "Multi-dimensional stress engine combining spot, implied-volatility and time shocks "
        "with current IFIT risk inputs. Approximate research scenarios, not forecasts or orders."
    )
    try:
        # Build the upstream state first.
        mi = _ifit_v067_market_cached(
            spot, days, atm_iv, hv30, flow_levels, imbalance_ratio
        )
        rg = _ifit_v068_regime_cached(
            mi["score"], mi["confidence"], mi["flow_score"], mi["vol_score"],
            mi["vol_regime"], mi["gamma_risk"], mi["mean_dislocation"],
            mi["pcr"], mi["iv_premium"]
        )

        # Do NOT depend on mi["option_metrics"] at all.
        # Rebuild the active option chain and calculate the expected move locally.
        # This removes the legacy/cached-string .get() failure path completely.
        scenario_chain = build_option_chain(float(spot), float(days), float(atm_iv))
        scenario_metrics = calculate_metrics(
            scenario_chain, float(spot), int(days), float(atm_iv)
        )
        move = float(scenario_metrics["move"])
        atm = round(float(spot) / 100.0) * 100.0

        sig = build_signal(
            mi["score"], mi["confidence"], rg["regime"], rg["confidence"],
            rg["directional_strength"], mi["flow_score"], mi["vol_score"],
            mi["vol_regime"], mi["gamma_risk"], mi["mean_dislocation"],
            float(spot), atm, float(spot - move), float(spot + move),
            mi["pcr"], atm
        )

        # Pull ATM CE Greeks directly from the active option-chain DataFrame.
        # chain_greek_rows() expects normalized list records, whereas
        # build_option_chain() returns a DataFrame. Direct BSM calculation is
        # both safer and avoids the legacy "str has no attribute get" path.
        atm_row = scenario_chain.iloc[
            (scenario_chain["Strike"].astype(float) - atm).abs().argsort()[0]
        ]
        ce_iv_decimal = float(atm_row["CE IV"]) / 100.0
        greek = bsm_greeks(
            float(spot), atm, max(float(days) / 365.0, 1e-8),
            0.06, ce_iv_decimal, "CE"
        )
        delta = float(greek.delta)
        gamma = float(greek.gamma)
        vega = float(greek.vega)
        theta = float(greek.theta) / 365.0
        vanna = float(greek.vanna)
        vomma = float(greek.vomma)

        result = build_scenario_matrix(
            spot=float(spot),
            expected_low=float(spot - move),
            expected_high=float(spot + move),
            direction_bias=sig["direction"],
            directional_score=rg["directional_strength"],
            confirmation_score=rg["confidence"],
            risk_score=mi["gamma_risk"],
            vol_score=mi["vol_score"],
            gamma_risk=mi["gamma_risk"],
            model_dislocation=mi["mean_dislocation"],
            base_iv=float(atm_iv),
            delta=delta,
            gamma=gamma,
            vega=vega,
            theta_per_day=theta,
            vanna=vanna,
            vomma=vomma,
        )
    except Exception as exc:
        st.warning(f"Scenario engine unavailable: {type(exc).__name__}: {exc}")
        return

    a, b, c, d, e, f = st.columns(6)
    for col, (label, value) in zip((a, b, c, d, e, f), scenario_summary(result)):
        col.metric(label, value)

    best = result["best"]
    worst = result["worst"]

    if float(worst["Stress"]) >= 70:
        st.warning(
            f'⚠️ STRESS ALERT: worst-case scenario is {worst["Approx P&L"]:,.2f} '
            f'at {worst["Spot Shock"]} spot / {worst["IV Shock"]} IV '
            f'over {int(worst["Horizon (D)"])}D.'
        )
    else:
        st.info(
            "Scenario map indicates manageable modeled stress under the current parameter set."
        )

    left, right = st.columns(2)
    with left:
        st.markdown("**Best Modeled Scenario**")
        st.write(best)
    with right:
        st.markdown("**Worst Modeled Scenario**")
        st.write(worst)

    st.markdown("**Spot × IV × Time Scenario Matrix**")
    view = result["rows"].copy()
    horizon = st.selectbox(
        "Scenario horizon",
        sorted(view["Horizon (D)"].unique().tolist()),
        key="ifit_v073_horizon",
    )
    view = view[view["Horizon (D)"] == horizon]
    pivot = view.pivot(index="Spot Shock", columns="IV Shock", values="Approx P&L")
    st.dataframe(pivot, width="stretch")

    st.markdown("**Detailed Scenario Map**")
    st.dataframe(view, width="stretch", hide_index=True)

    with st.expander("IFIT Scenario Engine Methodology"):
        st.write(
            "P&L is a local second-order approximation using Delta, Gamma, Vega, Vanna, "
            "Vomma and daily Theta. Spot shocks are applied to the live simulated/current "
            "spot; IV shocks are additive volatility-point changes. Scenario confidence is "
            "a diagnostic score, not a statistical probability. Expected-range breaches "
            "flag stress, not future direction. No scenario places or recommends an automatic order."
        )


# IFIT V0.7.4 RISK ENGINE
def _ifit_v074_render():
    st.markdown("---")
    st.markdown("### ⚡ IFIT V0.7.4 — RISK ENGINE")
    st.caption(
        "Cross-engine market-risk diagnostics combining volatility, convexity, model dislocation, "
        "signal uncertainty, regime confidence, flow and event pressure. Diagnostic research output — "
        "not VaR, a capital requirement or an automatic trading instruction."
    )
    try:
        mi=_ifit_v067_market_cached(spot, days, atm_iv, hv30, flow_levels, imbalance_ratio)
        rg=_ifit_v068_regime_cached(
            mi["score"],mi["confidence"],mi["flow_score"],mi["vol_score"],
            mi["vol_regime"],mi["gamma_risk"],mi["mean_dislocation"],
            mi["pcr"],mi["iv_premium"]
        )
        move=float(mi["option_metrics"].get("move",0.0))
        atm=round(float(spot)/100.0)*100.0
        sig=build_signal(
            mi["score"],mi["confidence"],rg["regime"],rg["confidence"],
            rg["directional_strength"],mi["flow_score"],mi["vol_score"],mi["vol_regime"],
            mi["gamma_risk"],mi["mean_dislocation"],float(spot),atm,
            float(spot-move),float(spot+move),mi["pcr"],atm
        )
        # Re-use the scenario engine as a stress context when available.
        scenario=None
        try:
            scenario_records=_ifit_scenario_option_records(
                build_option_chain(float(spot), float(days), float(atm_iv)), days
            )
            greeks=chain_greek_rows(scenario_records,float(spot),0.06)
            gdf=pd.DataFrame(greeks)
            atm_row=gdf.iloc[(gdf["strike"].astype(float)-atm).abs().argsort()[0]] if not gdf.empty else None
            gd = {k: float(atm_row.get(k,0.0)) for k in ["delta","gamma","vega","theta","vanna","vomma"]} if atm_row is not None else {}
            scenario=build_scenario_matrix(
                spot=float(spot),expected_low=float(spot-move),expected_high=float(spot+move),
                direction_bias=sig["direction"],directional_score=rg["directional_strength"],
                confirmation_score=rg["confidence"],risk_score=mi["gamma_risk"],
                vol_score=mi["vol_score"],gamma_risk=mi["gamma_risk"],
                model_dislocation=mi["mean_dislocation"],base_iv=float(atm_iv),
                delta=gd.get("delta",0),gamma=gd.get("gamma",0),vega=gd.get("vega",0),
                theta_per_day=gd.get("theta",0)/365.0,vanna=gd.get("vanna",0),vomma=gd.get("vomma",0)
            )
        except Exception:
            scenario=None

        # Event engine is used defensively; if its output shape changes, risk still renders.
        event_count=0
        alert_count=0
        try:
            ev=detect_events()
            if isinstance(ev,(list,tuple,pd.DataFrame)):
                event_count=len(ev)
        except Exception:
            pass
        try:
            al=alert_snapshot()
            if isinstance(al,(list,tuple,pd.DataFrame)):
                alert_count=len(al)
            elif isinstance(al,dict):
                alert_count=len(al.get("alerts",[])) if isinstance(al.get("alerts",[]),(list,tuple)) else 0
        except Exception:
            pass

        result=build_risk_engine(
            market_score=mi["score"],regime_confidence=rg["confidence"],
            flow_score=mi["flow_score"],vol_score=mi["vol_score"],
            gamma_risk=mi["gamma_risk"],model_dislocation=mi["mean_dislocation"],
            signal_confirmation=sig["conviction"],direction_score=sig["direction"],
            event_count=event_count,alert_count=alert_count,
            expected_low=float(spot-move),expected_high=float(spot+move),spot=float(spot),
            scenario_result=scenario
        )
    except Exception as exc:
        st.warning(f"Risk engine unavailable: {exc}")
        return

    cols=st.columns(6)
    for col,(label,value) in zip(cols,risk_summary(result)):
        col.metric(label,value)

    if result["regime"] in ("EXTREME","HIGH"):
        st.warning(
            f'⚠️ RISK ALERT — {result["regime"]} risk. '
            f'Tail bias: {result["tail_bias"]}. Highest driver: '
            f'{result["drivers"].iloc[0]["Risk Driver"]}.'
        )
    elif result["regime"]=="ELEVATED":
        st.info("Risk is elevated; directional conviction should be evaluated alongside the stress map.")
    else:
        st.success("Risk diagnostics are currently in the controlled zone.")

    left,right=st.columns(2)
    with left:
        st.markdown("**Risk Driver Map**")
        st.dataframe(result["components"],width="stretch",hide_index=True)
    with right:
        st.markdown("**Strongest Risk Drivers**")
        st.dataframe(result["drivers"],width="stretch",hide_index=True)

    stats=result["scenario_stats"]
    if stats:
        st.markdown("**Scenario Stress Context**")
        a,b,c,d=st.columns(4)
        a.metric("Scenarios",stats["scenario_count"])
        b.metric("Loss Scenarios",f'{stats["loss_rate"]:.1f}%')
        c.metric("Worst P&L Proxy",f'{stats["worst_pnl"]:,.2f}')
        d.metric("Range Breaches",stats["outside_range"])

    with st.expander("IFIT Risk Engine Methodology"):
        st.write(
            "Risk Score is a normalized 0–100 diagnostic built from volatility/convexity, model "
            "dislocation, signal uncertainty, regime risk, flow risk, event/alert pressure and "
            "expected-range asymmetry. It is deliberately explainable and does not claim to be "
            "statistical VaR or a forecast. Scenario figures are local model approximations and "
            "should be scaled to an actual position before any portfolio-level use."
        )


# ---------- V0.8.0 Consolidated Intelligence ----------
@st.cache_data(ttl=8, show_spinner=False)
def _ifit_v080_cached(spot_value, days_value, atm_iv_value, hv_value,
                      flow_levels_value, imbalance_value):
    return build_consolidated_intelligence(
        spot=float(spot_value),
        days=int(days_value),
        atm_iv=float(atm_iv_value),
        hv30=float(hv_value),
        flow_levels=int(flow_levels_value),
        imbalance_ratio=float(imbalance_value),
        active_alerts=0,
    )


def _ifit_v080_render():
    st.markdown("## ⚡ IFIT V0.8.0 — CONSOLIDATED INTELLIGENCE TERMINAL")
    st.caption(
        "The IFIT command center. One synchronized research snapshot across market state, "
        "regime, signal, volatility, model risk, scenarios, portfolio risk and execution. "
        "This is decision support, not an automatic trading system."
    )

    try:
        x = _ifit_v080_cached(
            spot, days, atm_iv, hv30, flow_levels, imbalance_ratio
        )
    except Exception as exc:
        st.error(f"V0.8.0 consolidation unavailable: {type(exc).__name__}: {exc}")
        return

    # Executive header
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("IFIT SCORE", f'{x["overall_score"]:.1f}/100')
    c2.metric("OPERATING STATE", x["operating_state"])
    c3.metric("DIRECTION", x["signal"]["direction"])
    c4.metric("CONVICTION", f'{x["signal"]["conviction"]:.1f}/100')
    c5.metric("RISK", x["risk"]["regime"])
    c6.metric("CONFIDENCE", f'{x["executive_confidence"]:.1f}/100')

    state = x["operating_state"]
    if state == "RISK CONTROL":
        st.error("🛑 **IFIT OPERATING STATE: RISK CONTROL** — risk layers dominate directional conviction.")
    elif state == "HIGH-CONVICTION":
        st.success("🟢 **IFIT OPERATING STATE: HIGH-CONVICTION** — multiple research layers are aligned.")
    elif state == "WATCHLIST":
        st.warning("🟠 **IFIT OPERATING STATE: WATCHLIST** — evidence is useful, but confirmation is incomplete.")
    elif state == "EXECUTION CONSTRAINED":
        st.warning("🟡 **IFIT OPERATING STATE: EXECUTION CONSTRAINED** — market may be analyzable but execution quality is limiting.")
    else:
        st.info("⚪ **IFIT OPERATING STATE: NO CLEAR EDGE** — preserve optionality and monitor for confirmation.")

    # The six-panel market map
    st.markdown("### Executive Market Map")
    a,b,c,d,e,f = st.columns(6)
    a.metric("Market State", f'{x["market"]["score"]:.1f}/100', x["market"]["regime"])
    b.metric("Regime", x["regime"]["regime"], f'{x["regime"]["confidence"]:.1f}/100')
    c.metric("Flow", f'{x["market"]["flow_score"]}/100', x["market"]["flow_regime"])
    d.metric("Volatility", f'{x["market"]["vol_score"]:.1f}/100', x["market"]["vol_regime"])
    e.metric("Model Dislocation", f'{x["market"]["mean_dislocation"]:.1f}/100')
    f.metric("Execution", f'{x["liquidity"]["score"]:.1f}/100', x["liquidity"]["regime"])

    st.info(
        f'NIFTY {x["spot"]:,.2f} • ATM {x["atm"]:,.0f} • '
        f'Expected move {x["expected_low"]:,.0f} → {x["expected_high"]:,.0f} • '
        f'PCR {x["market"]["pcr"]:.2f} • IV−HV {x["market"]["iv_premium"]:+.2f} pts'
    )

    # Decision + risk
    left, right = st.columns(2)
    with left:
        st.markdown("### Decision Matrix")
        st.dataframe(
            pd.DataFrame([
                ["Setup", x["decision"]["setup"]],
                ["Direction Bias", x["decision"]["direction_bias"]],
                ["Directional Score", f'{x["decision"]["directional_score"]:.1f}/100'],
                ["Confirmation", f'{x["decision"]["confirmation_score"]:.1f}/100'],
                ["Risk", f'{x["decision"]["risk_level"]} ({x["decision"]["risk_score"]:.1f}/100)'],
                ["Location", x["decision"]["location"]],
                ["Confirmation Rule", x["decision"]["confirmation_rule"]],
                ["Invalidation", x["decision"]["invalidation"]],
            ], columns=["Dimension","IFIT Reading"]),
            use_container_width=True, hide_index=True
        )
    with right:
        st.markdown("### Risk & Execution")
        r1,r2,r3,r4 = st.columns(4)
        r1.metric("Risk Score", f'{x["risk"]["overall_score"]:.1f}')
        r2.metric("Portfolio Risk", f'{x["portfolio"]["score"]:.1f}')
        r3.metric("Liquidity", f'{x["liquidity"]["score"]:.1f}')
        r4.metric("Microstructure", f'{x["microstructure"]["score"]:.1f}')
        st.markdown(
            f'**Tail Bias:** {x["risk"]["tail_bias"]}  \n'
            f'**Portfolio Tail:** {x["portfolio"]["tail_bias"]}  \n'
            f'**Execution:** {x["liquidity"]["regime"]} / {x["microstructure"]["regime"]}'
        )
        st.warning(x["risk"]["drivers"].iloc[0]["Risk Driver"] + " is the strongest cross-market risk driver.")

    # Evidence ladder
    st.markdown("### Evidence Ladder")
    evidence = pd.DataFrame([
        ["Direction", x["signal"]["direction"], x["signal"]["direction_score"], "Market + flow + PCR"],
        ["Conviction", x["signal"]["conviction_label"], x["signal"]["conviction"], "Cross-module agreement"],
        ["Regime", x["regime"]["regime"], x["regime"]["confidence"], "Market + flow + volatility + risk"],
        ["Volatility", x["market"]["vol_regime"], x["market"]["vol_score"], "IV premium / skew / model"],
        ["Risk", x["risk"]["regime"], x["risk"]["overall_score"], "Vol / model / signal / regime / flow"],
        ["Execution", x["liquidity"]["regime"], x["liquidity"]["score"], "Spread + depth + size impact"],
        ["Microstructure", x["microstructure"]["regime"], x["microstructure"]["score"], "Quote + depth + queue"],
        ["Portfolio", x["portfolio"]["regime"], x["portfolio"]["score"], "Greeks + concentration + stress"],
    ], columns=["Layer","Reading","Score","Method"])
    st.dataframe(evidence, width="stretch", hide_index=True)

    # Scenario extremes
    st.markdown("### Stress & Tail Map")
    s1,s2,s3,s4 = st.columns(4)
    s1.metric("Scenarios", f'{x["scenario"]["total"]:,}')
    s2.metric("Outside Expected Range", f'{x["scenario"]["outside_count"]:,}')
    s3.metric("Best P&L Proxy", f'{x["scenario"]["best"]["Approx P&L"]:,.2f}')
    s4.metric("Worst P&L Proxy", f'{x["scenario"]["worst"]["Approx P&L"]:,.2f}')

    scenario_df = x["scenario"]["rows"].copy()
    # Compact heat-style summary without adding another chart dependency.
    pivot = scenario_df.pivot_table(
        index="Spot Shock", columns="IV Shock", values="Approx P&L", aggfunc="mean"
    )
    st.dataframe(pivot.round(2), width="stretch")

    # Key levels + execution
    l1,l2 = st.columns(2)
    with l1:
        st.markdown("### Key Levels")
        levels = pd.DataFrame(x["signal"]["levels"])
        levels.columns = ["Level","Price"]
        st.dataframe(levels.round(2), width="stretch", hide_index=True)
    with l2:
        st.markdown("### Execution Impact")
        ladder = x["microstructure"]["ladder"].copy()
        if not ladder.empty:
            
            
            if len(ladder.columns) < 8:
                st.error(
                    f"Unexpected execution ladder schema: {list(ladder.columns)}"
                )
            else:
                display_ladder = ladder.iloc[:, [0, 1, 2, 3, 4, 6, 7]].copy()
                display_ladder.columns = [
                    "Strike",
                    "Option",
                    "Lots",
                    "Order Qty",
                    "Spread Cost (INR)",
                    "Est. Slippage (INR)",
                    "5-Level Utilization",
                ]
                st.dataframe(
                    display_ladder.round(2),
                    use_container_width=True,
                    hide_index=True,
                )



    # Portfolio attribution
    st.markdown("### Portfolio Risk Snapshot")
    p = x["portfolio"]
    if isinstance(p.get("attribution"), pd.DataFrame) and not p["attribution"].empty:
        st.dataframe(p["attribution"].round(4), width="stretch", hide_index=True)
    else:
        st.info("Portfolio attribution is unavailable for the current snapshot.")

    with st.expander("IFIT V0.8.0 — Architecture & Methodology"):
        st.markdown(
            """
            **V0.8.0 is an orchestration layer, not a replacement for the underlying engines.**

            1. **Market state** synthesizes options, flow, volatility, gamma and model diagnostics.
            2. **Regime** classifies the environment and transition risk.
            3. **Signal** converts the state into directional bias and conviction.
            4. **Decision Matrix** checks directional agreement against risk and location.
            5. **Scenario Engine** stress-tests spot, IV and time.
            6. **Risk Engine** separates risk intensity from direction.
            7. **Portfolio Risk** evaluates concentration, Greeks and stress tails.
            8. **Liquidity + Microstructure** determine whether the market is executable at size.
            9. **IFIT Score** is a normalized research-quality index — **not a probability of profit**.
            10. Simulation/proxy data remains explicitly illustrative until authorized live feeds are connected.
            """
        )

    st.caption(
        "V0.8.0 consolidates V0.6.7–V0.7.7 into one command-center view. "
        "Production deployment requires synchronized authorized market-data and depth feeds."
    )


# ---------- V0.8.1 Terminal Architecture ----------

def _ifit_v081_header(active_module):
    st.markdown(
        '<div class="ifit-terminal-bar">'
        '<div><span class="ifit-logo">IN IFIT</span><span class="ifit-terminal-name"> TERMINAL</span></div>'
        f'<div class="ifit-active">WORKSPACE: {active_module.upper()}</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ifit-nav-note">'
        'V0.8.2 • Navigation & Workspace Engine • persistent module + subview + market context'
        '</div>',
        unsafe_allow_html=True,
    )


def _ifit_v081_market_page():
    _ifit_v081_header("Markets")
    st.markdown("## Markets")
    st.caption("Market command layer. Detailed engines remain available underneath the terminal shell.")
    mi = _ifit_v067_market_cached(spot, days, atm_iv, hv30, flow_levels, imbalance_ratio)
    om = mi["option_metrics"]
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("NIFTY 50", f"{spot:,.2f}")
    c2.metric("MARKET STATE", f'{mi["score"]:.1f}/100', mi["regime"])
    c3.metric("PCR", f'{mi["pcr"]:.2f}')
    c4.metric("IV − HV", f'{mi["iv_premium"]:+.2f} pts')
    c5.metric("FLOW", f'{mi["flow_score"]:.0f}/100', mi["flow_regime"])
    c6.metric("VOLATILITY", f'{mi["vol_score"]:.0f}/100', mi["vol_regime"])
    st.info(f'Expected range: {spot-om["move"]:,.0f} → {spot+om["move"]:,.0f} • Max Pain: {om["max_pain"]:,.0f} • Gamma risk: {mi["gamma_risk"]:.1f}/100')
    a,b = st.columns([2.2,1])
    with a:
        p = spot*np.exp(np.cumsum(np.random.default_rng(7).normal(0,.0025,180)))
        st.line_chart(pd.DataFrame({"NIFTY":p}), height=320)
    with b:
        st.markdown("### Market Map")
        st.metric("Trend", mi["regime"])
        st.metric("Flow", mi["flow_regime"])
        st.metric("Volatility", mi["vol_regime"])
        st.metric("Model Dislocation", f'{mi["mean_dislocation"]:.1f}/100')
    with st.expander("Open legacy Market Intelligence engines"):
        _ifit_v067_render()
        _ifit_v068_render()
        _ifit_v069_render()
        _ifit_v071_render()


def _ifit_v081_options_page():
    _ifit_v081_header("Options")
    subview = st.session_state.get("ifit_v082_subview", "Option Chain")

    chain = build_option_chain(spot, days, atm_iv)
    om = calculate_metrics(chain, spot, days, atm_iv)

    if subview == "Greeks":
        _ifit_v062_render(chain, spot, days, atm_iv)
        return

    if subview == "Volatility":
        _ifit_v063_render(chain, spot)
        _ifit_v066_render(chain, spot, atm_iv, hv30, days)
        return

    if subview == "OI & Gamma":
        _ifit_v062_render(chain, spot, days, atm_iv)
        st.markdown("### Open Interest & Gamma")
        gdf = gamma_exposure(chain)
        st.bar_chart(gdf.set_index("Strike"), height=420)
        return

    if subview == "Heston":
        _ifit_v064_render(chain, spot, days)
        _ifit_v065_render(chain, spot, days)
        return

    if subview == "Execution":
        _ifit_v076_render()
        return

    st.markdown("## Options")
    st.caption(
        "Options workspace built around the existing live Greeks, volatility, "
        "model and execution engines."
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("SPOT", f"{spot:,.2f}")
    c2.metric("ATM", f'{om["atm"]:,.0f}')
    c3.metric("PCR", f'{om["pcr"]:.2f}')
    c4.metric("ATM IV", f'{atm_iv:.2f}%')
    c5.metric("IV / HV", f'{atm_iv/max(hv30,0.01):.2f}x')
    c6.metric("MAX PAIN", f'{om["max_pain"]:,.0f}')

    st.info(f'1σ expected range: {spot-om["move"]:,.0f} → {spot+om["move"]:,.0f}')

    near = chain.iloc[(chain["Strike"] - spot).abs().argsort()[:15]].sort_values("Strike")
    display_positions = [1, 2, 3, 4, 5, 6, 17, 0, 10, 11, 12, 9, 15, 16]

    if len(near.columns) <= max(display_positions):
        raise ValueError(
            f"Unexpected option-chain schema: {list(near.columns)}"
        )

    display = near.iloc[:, display_positions].copy()
    display.columns = [
        "CE OI",
        "CE Change OI",
        "CE LTP",
        "CE IV",
        "CE Delta",
        "CE Gamma",
        "Moneyness",
        "Strike",
        "PE IV",
        "PE Delta",
        "PE Gamma",
        "PE LTP",
        "PE Change OI",
        "PE OI",
    ]

    st.markdown("### Professional Option Chain")
    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
        height=430
    )

    a, b, c = st.columns(3)

    with a:
        st.markdown("### IV Smile")
        st.line_chart(
            chain[["Strike", "CE IV", "PE IV"]].set_index("Strike"),
            height=260
        )

    with b:
        st.markdown("### Gamma")
        gdf = gamma_exposure(chain)
        st.bar_chart(gdf.set_index("Strike"), height=260)

    with c:
        st.markdown("### Expected Move")
        st.dataframe(
            expected_move_table(spot, atm_iv, days),
            use_container_width=True,
            hide_index=True
        )

    with st.expander("Open full Options Intelligence stack"):
        _ifit_v062_render(chain, spot, days, atm_iv)
        _ifit_v063_render(chain, spot)
        _ifit_v064_render(chain, spot, days)
        _ifit_v065_render(chain, spot, days)
        _ifit_v066_render(chain, spot, atm_iv, hv30, days)

def _ifit_v086_motion_charts_page(ctx):
    st.markdown("## CHT MOTION CHARTS V0.1")
    st.caption("Dynamic momentum, volatility and liquidity / flow motion inside the existing CHT architecture.")

    df = build_motion_data()
    summary = motion_summary(df)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Price", f'{summary["Last Price"]:,.2f}')
    c2.metric("Momentum", f'{summary["Momentum"]:.3f}%')
    c3.metric("IV", f'{summary["IV"]:.2f}%')
    c4.metric("RV", f'{summary["RV"]:.2f}%')
    c5.metric("Motion Score", f'{summary["Motion Score"]:.1f}')

    motion_view = st.radio(
        "Motion View",
        available_motion_views(),
        horizontal=True,
        key="ifit_motion_view",
    )

    if motion_view == "Motion Overview":
        st.markdown("### Motion Overview")
        c1, c2, c3 = st.columns(3)
        c1.metric("Momentum Regime", summary["Momentum Regime"])
        c2.metric("Volatility Regime", summary["Volatility Regime"])
        c3.metric("Flow Regime", summary["Flow Regime"])
        st.markdown("### Price Motion")
        st.line_chart(df.set_index("Timestamp")[["Price"]], height=300)
        st.markdown("### Motion Score")
        st.line_chart(df.set_index("Timestamp")[["Motion Score"]], height=240)

    elif motion_view == "Momentum Motion":
        mom = build_momentum_motion(df)
        st.markdown("### Momentum Motion")
        st.caption("Momentum, acceleration, velocity and regime transitions.")
        st.line_chart(mom.set_index("Timestamp")[["Momentum %", "Momentum Acceleration"]], height=320)
        st.dataframe(mom.tail(30), width="stretch", hide_index=True)

    elif motion_view == "Volatility Motion":
        vol = build_volatility_motion(df)
        st.markdown("### Volatility Motion")
        st.caption("Realized volatility, implied volatility and IV-RV regime transitions.")
        st.line_chart(vol.set_index("Timestamp")[["RV %", "IV %"]], height=320)
        st.markdown("### IV - RV Spread")
        st.line_chart(vol.set_index("Timestamp")[["IV-RV Spread"]], height=240)
        st.dataframe(vol.tail(30), width="stretch", hide_index=True)

    elif motion_view == "Liquidity / Flow Motion":
        flow = build_liquidity_flow_motion(df)
        latest = flow.iloc[-1]
        st.markdown("### Liquidity / Flow Motion")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Delta", f'{latest["Delta"]:,.0f}')
        c2.metric("CVD", f'{latest["CVD"]:,.0f}')
        c3.metric("Imbalance", f'{latest["Imbalance"]:.2f}x')
        c4.metric("Absorption", f'{latest["Absorption"]:.1f}')
        st.markdown("### CVD Motion")
        st.line_chart(flow.set_index("Timestamp")[["CVD"]], height=280)
        st.markdown("### Liquidity Pressure")
        st.line_chart(flow.set_index("Timestamp")[["Liquidity Pressure"]], height=280)
        st.dataframe(flow.tail(30), width="stretch", hide_index=True)

    st.info(
        f'CHT MOTION • {ctx.instrument} • DATA {ctx.data_mode} • '
        'Simulation/proxy data until an authorized live market/order-flow feed is connected.'
    )


def _ifit_v087_order_flow_footprint_page(ctx):
    st.markdown("## CHT ORDER FLOW FOOTPRINT V0.1")
    st.caption(
        "Per-candle bid/ask order-flow intelligence with price-level clusters, "
        "delta, imbalance, absorption, exhaustion, POC and multi-timeframe aggregation."
    )

    timeframe = st.selectbox(
        "Footprint Timeframe",
        available_footprint_timeframes(),
        index=0,
        key="ifit_footprint_timeframe",
    )
    periods = st.slider(
        "Developing Bars", 30, 120, 60, 15,
        key="ifit_footprint_periods",
    )
    levels = st.slider(
        "Price Levels / Bar", 12, 36, 24, 4,
        key="ifit_footprint_levels",
    )

    df = build_footprint_data(periods=periods, levels=levels)
    bars = build_bar_footprint(periods=periods, levels=levels)
    view = aggregate_footprint(df, timeframe)
    summary = footprint_summary(df)
    latest = bars.iloc[-1]

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Bid Volume", f'{int(latest["Bid_Volume"]):,}')
    c2.metric("Ask Volume", f'{int(latest["Ask_Volume"]):,}')
    c3.metric("Delta", f'{int(latest["Delta"]):+,}')
    c4.metric("CVD", f'{summary["CVD"]:+,.0f}')
    c5.metric("POC", f'{summary["POC"]:,.2f}')
    c6.metric("OF Score", f'{summary["Order Flow Score"]:.1f}')

    st.markdown("### Order Flow State")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Absorption", summary["Absorption Events"])
    c2.metric("Exhaustion", summary["Exhaustion Events"])
    c3.metric("Stacked Imbalance", summary["Stacked Imbalances"])
    c4.metric("Large Prints", summary["Large Prints"])
    c5.metric("Buy / Sell", f'{summary["Buy/Sell Ratio"]:.2f}x')


    # V0.3 Institutional Footprint Intelligence
    intelligence_df = classify_footprint_intelligence(df)
    intelligence_summary = footprint_intelligence_summary(intelligence_df)

    st.markdown("### Footprint Intelligence")
    i1, i2, i3, i4, i5 = st.columns(5)
    i1.metric("Intelligence Score", f'{intelligence_summary["Score"]:.1f}')
    i2.metric("State", intelligence_summary["State"])
    i3.metric("Dominant Side", intelligence_summary["Dominant Side"])
    i4.metric("Aggression", intelligence_summary["Aggression"])
    i5.metric("Imbalance", intelligence_summary["Imbalance"])

    st.markdown("### Institutional Order-Flow Events")
    e1, e2, e3, e4, e5, e6 = st.columns(6)
    e1.metric("Absorption", intelligence_summary["Absorption"])
    e2.metric("Exhaustion", intelligence_summary["Exhaustion"])
    e3.metric("Failed Auctions", intelligence_summary["Failed Auctions"])
    e4.metric("Delta Flips", intelligence_summary["Delta Flips"])
    e5.metric("CVD Divergence", intelligence_summary["CVD Divergences"])
    e6.metric("Large Prints", intelligence_summary["Large Prints"])

    latest_intel = intelligence_df[
        intelligence_df["Bar"] == intelligence_df["Bar"].max()
    ].copy()

    st.markdown("### Price-Level Intelligence")
    intel_cols = [
        "Price", "Delta", "Delta %", "Bid/Ask Imbalance",
        "Imbalance Signal", "Dominant Side", "Aggression State",
        "Absorption Signal", "Exhaustion Signal",
        "Auction Signal", "Large Print Signal",
        "Footprint Intelligence Score", "Intelligence State",
    ]
    intel_cols = [c for c in intel_cols if c in latest_intel.columns]
    st.dataframe(
        latest_intel[intel_cols].sort_values("Price", ascending=False),
        width="stretch",
        hide_index=True,
    )

    st.markdown("### Cluster Footprint")

    latest_bar = df[df["Bar"] == df["Bar"].max()].copy()

    # V0.4 Advanced Auction Intelligence
    previous_bar = bars.iloc[-2].to_dict() if len(bars) >= 2 else {}
    current_bar_dict = bars.iloc[-1].to_dict() if len(bars) >= 1 else {}

    current_poc = float(summary.get("POC", current_bar_dict.get("POC", 0.0)))
    previous_poc = float(
        bars.iloc[-2]["POC"]
        if len(bars) >= 2 and "POC" in bars.columns
        else current_poc
    )

    current_price = float(current_bar_dict.get("Price", 0.0))
    previous_price = float(
        bars.iloc[-2]["Price"]
        if len(bars) >= 2 and "Price" in bars.columns
        else current_price
    )

    current_cvd = float(current_bar_dict.get("CVD", 0.0))
    previous_cvd = float(
        bars.iloc[-2]["CVD"]
        if len(bars) >= 2 and "CVD" in bars.columns
        else current_cvd
    )

    auction_snapshot = build_advanced_auction_snapshot(
        latest_bar,
        current_bar=current_bar_dict,
        previous_bar=previous_bar,
        previous_poc=previous_poc,
        current_poc=current_poc,
        price_change=current_price - previous_price,
        cvd_change=current_cvd - previous_cvd,
    )
    auction_summary = auction_intelligence_summary(auction_snapshot)

    st.markdown("### Advanced Auction Intelligence")
    a1, a2, a3, a4, a5 = st.columns(5)
    a1.metric("Auction State", auction_summary.get("Auction State", "N/A"))
    a2.metric("Confidence", f'{auction_summary.get("Auction Confidence", 0):.0f}')
    a3.metric("POC Migration", auction_summary.get("POC Migration", "N/A"))
    a4.metric("Failed Auction", auction_summary.get("Failed Auction", "NONE"))
    a5.metric("Delta Flip", auction_summary.get("Delta Flip", "NONE"))

    a6, a7, a8, a9, a10 = st.columns(5)
    a6.metric("HVN Count", auction_summary.get("HVN Count", 0))
    a7.metric("LVN Count", auction_summary.get("LVN Count", 0))
    a8.metric("Absorption Zones", auction_summary.get("Absorption Zones", 0))
    a9.metric("Exhaustion Zones", auction_summary.get("Exhaustion Zones", 0))
    a10.metric("Stacked Imbalance", auction_summary.get("Stacked Imbalance Zones", 0))

    st.markdown("### Auction Intelligence Detail")
    auction_detail = {
        "Metric": [
            "Auction State", "Auction Confidence", "POC Migration",
            "HVN Count", "LVN Count", "Absorption Zones",
            "Exhaustion Zones", "Stacked Imbalance Zones",
            "Failed Auction", "Delta Flip", "CVD Divergence",
        ],
        "Value": [
            auction_summary.get("Auction State", "N/A"),
            auction_summary.get("Auction Confidence", 0),
            auction_summary.get("POC Migration", "N/A"),
            auction_summary.get("HVN Count", 0),
            auction_summary.get("LVN Count", 0),
            auction_summary.get("Absorption Zones", 0),
            auction_summary.get("Exhaustion Zones", 0),
            auction_summary.get("Stacked Imbalance Zones", 0),
            auction_summary.get("Failed Auction", "NONE"),
            auction_summary.get("Delta Flip", "NONE"),
            auction_summary.get("CVD Divergence", "NONE"),
        ],
    }
    st.dataframe(auction_detail, width="stretch", hide_index=True)

    # V0.4 -> Decision Intelligence bridge.
    st.markdown("### Decision Intelligence • Footprint Auction Input")
    d1, d2, d3 = st.columns(3)
    d1.metric("Auction State", auction_summary.get("Auction State", "N/A"))
    d2.metric("Auction Confidence", f'{auction_summary.get("Auction Confidence", 0):.0f}')
    d3.metric("CVD Divergence", auction_summary.get("CVD Divergence", "NONE"))

    # V0.5 Native Footprint Decision Intelligence
    decision = build_footprint_decision_intelligence(auction_summary, footprint_summary=summary, footprint_intelligence=intelligence_summary)
    decision_summary = decision_intelligence_summary(decision)
    st.session_state['ifit_footprint_decision_intelligence'] = decision

    st.markdown('### Decision Intelligence • Native Footprint Signal')
    q1, q2, q3, q4 = st.columns(4)
    q1.metric('Market State', decision_summary['Market State'])
    q2.metric('Signal', decision_summary['Signal'])
    q3.metric('Confidence', f"{decision_summary['Confidence']:.1f}")
    q4.metric('Auction State', decision['Auction State'])
    st.markdown('### Decision Thesis')
    st.info(decision_summary['Thesis'])
    q5, q6 = st.columns(2)
    with q5:
        st.markdown('**Confirmation**')
        st.write(decision_summary['Confirmation'])
    with q6:
        st.markdown('**Strategy Context**')
        st.write(decision_summary['Strategy Context'])
    st.markdown('### Risk / Invalidation')
    st.warning(decision_summary['Risk / Invalidation'])
    decision_table = {'Decision Field': ['Market State','Auction State','Decision Signal','Decision Confidence','Thesis','Confirmation','Strategy Context','Risk / Invalidation','POC Migration','Delta Flip','CVD Divergence','Failed Auction','Source'], 'Value': [decision['Market State'],decision['Auction State'],decision['Decision Signal'],decision['Decision Confidence'],decision['Thesis'],decision['Confirmation'],decision['Strategy Context'],decision['Risk / Invalidation'],decision['POC Migration'],decision['Delta Flip'],decision['CVD Divergence'],decision['Failed Auction'],decision['Source']]}
    st.dataframe(decision_table, width='stretch', hide_index=True)

    st.info(
        "Decision Intelligence input: Footprint Auction State, confidence, "
        "POC migration, liquidity zones, imbalance, auction failure, delta flip "
        "and CVD divergence."
    )

    cluster_fig = build_cluster_footprint_figure(
        latest_bar,
        title=f"Developing Footprint • {timeframe} • Latest Bar",
    )
    st.plotly_chart(
        cluster_fig,
        use_container_width=True,
        key="ifit_v087_cluster_footprint",
    )

    st.markdown("### Delta Intensity")
    delta_fig = build_delta_intensity_figure(
        latest_bar,
        title="Price-Level Delta Intensity",
    )
    st.plotly_chart(
        delta_fig,
        use_container_width=True,
        key="ifit_v087_delta_intensity",
    )

    events = footprint_event_counts(latest_bar)
    st.markdown("### Footprint Events")
    e1, e2, e3, e4, e5, e6 = st.columns(6)
    e1.metric("Absorption", events["Absorption"])
    e2.metric("Exhaustion", events["Exhaustion"])
    e3.metric("Stacked Imbalance", events["Stacked Imbalance"])
    e4.metric("Delta Flip", events["Delta Flip"])
    e5.metric("Failed Auction", events["Failed Auction"])
    e6.metric("Large Print", events["Large Print"])

    st.markdown("### Developing Footprint — Exact Values")
    exact_cols = [
        "Price", "Bid Volume", "Ask Volume", "Total Volume", "Delta",
        "Delta %", "Trade Count", "Buy/Sell Ratio", "POC",
        "Bid/Ask Imbalance", "Stacked Imbalance", "Absorption",
        "Exhaustion", "Delta Flip", "Failed Auction", "HVN", "LVN",
        "Large Print", "Aggression Pressure",
    ]
    exact_cols = [c for c in exact_cols if c in latest_bar.columns]
    st.dataframe(
        latest_bar[exact_cols].sort_values("Price", ascending=False),
        width="stretch",
        hide_index=True,
    )

    st.markdown(f"### {timeframe} Footprint Summary")
    display_cols = [
        "Timestamp", "Price", "Bid_Volume", "Ask_Volume",
        "Total_Volume", "Delta", "Delta %", "Buy/Sell Ratio",
        "POC", "POC Migration", "Absorption", "Exhaustion",
        "Stacked_Imbalance", "Large_Print", "Relative_Volume",
        "Aggression_Pressure",
    ]
    display_cols = [c for c in display_cols if c in view.columns]
    st.dataframe(view[display_cols].tail(30), width="stretch", hide_index=True)

    st.info(
        f'CHT FOOTPRINT • {ctx.instrument} • {timeframe} • DATA {ctx.data_mode} • '
        "Simulation/proxy order-flow data until an authorized tick/depth feed is connected."
    )


def _ifit_cht_asset_reference(ctx):
    """Resolve a chart reference price without changing the global NIFTY spot."""
    instrument = str(ctx.instrument).upper().strip()
    references = {
        "NIFTY 50": 24782.35,
        "BANK NIFTY": 54250.00,
        "SENSEX": 81000.00,
        "EURUSD": 1.1750,
        "GBPUSD": 1.3500,
        "USDJPY": 147.50,
        "USDINR": 88.00,
        "EURINR": 103.50,
        "BTCUSDT": 117500.00,
        "ETHUSDT": 4600.00,
        "SOLUSDT": 245.00,
        "BNBUSDT": 950.00,
        "XRPUSDT": 3.05,
    }
    return float(references.get(instrument, spot))



# ============================================================
# CHT FOOTPRINT INTELLIGENCE V0.4
# ============================================================

def _render_cht_footprint_intelligence(
    footprint_df,
    ohlcv,
):
    """
    CHT Footprint Intelligence V0.4.2.

    Native Streamlit terminal-style decision panel.
    Uses the existing frozen footprint engine.
    """

    if footprint_df is None or footprint_df.empty:
        st.info("Footprint intelligence unavailable.")
        return

    data = footprint_df.copy()

    latest_bar_no = data["Bar"].max()

    latest = data[
        data["Bar"] == latest_bar_no
    ].copy()

    if latest.empty:
        st.info("Latest footprint bar unavailable.")
        return

    # --------------------------------------------------------
    # NUMERIC DATA
    # --------------------------------------------------------
    for column in [
        "Bid Volume",
        "Ask Volume",
        "Total Volume",
        "Delta",
    ]:
        if column in latest.columns:
            latest[column] = pd.to_numeric(
                latest[column],
                errors="coerce",
            ).fillna(0.0)

    bid_volume = float(
        latest["Bid Volume"].sum()
        if "Bid Volume" in latest.columns
        else 0.0
    )

    ask_volume = float(
        latest["Ask Volume"].sum()
        if "Ask Volume" in latest.columns
        else 0.0
    )

    total_volume = max(
        bid_volume + ask_volume,
        1.0,
    )

    delta = float(
        latest["Delta"].sum()
        if "Delta" in latest.columns
        else ask_volume - bid_volume
    )

    buyer_pressure = (
        ask_volume / total_volume * 100.0
    )

    seller_pressure = (
        bid_volume / total_volume * 100.0
    )

    # --------------------------------------------------------
    # CVD
    # --------------------------------------------------------
    if "Delta" in data.columns:
        all_delta = pd.to_numeric(
            data["Delta"],
            errors="coerce",
        ).fillna(0.0)

        cvd = float(all_delta.sum())
    else:
        cvd = delta

    # --------------------------------------------------------
    # OFI
    # --------------------------------------------------------
    aggression = None

    if "Aggression Pressure" in latest.columns:
        ag = pd.to_numeric(
            latest["Aggression Pressure"],
            errors="coerce",
        ).dropna()

        if not ag.empty:
            aggression = float(ag.mean())

    if aggression is None:
        aggression = (
            (ask_volume - bid_volume)
            / total_volume
        ) * 100.0

    ofi_score = float(
        np.clip(
            50.0 + aggression / 2.0,
            0.0,
            100.0,
        )
    )

    # --------------------------------------------------------
    # MARKET STATE
    # --------------------------------------------------------
    if (
        delta > 0
        and buyer_pressure >= 52
    ):
        market_state = "BUYER CONTROL"
        structure = "BULLISH FLOW"

    elif (
        delta < 0
        and seller_pressure >= 52
    ):
        market_state = "SELLER CONTROL"
        structure = "BEARISH FLOW"

    else:
        market_state = "BALANCED / MIXED"
        structure = "MIXED FLOW"

    # --------------------------------------------------------
    # POC
    # --------------------------------------------------------
    poc = None

    if "POC" in latest.columns:
        values = pd.to_numeric(
            latest["POC"],
            errors="coerce",
        ).dropna()

        if not values.empty:
            poc = float(values.iloc[-1])

    if (
        poc is None
        and "Total Volume" in latest.columns
    ):
        idx = latest["Total Volume"].idxmax()

        poc = float(
            latest.loc[idx, "Price"]
        )

    # --------------------------------------------------------
    # POC MIGRATION
    # --------------------------------------------------------
    poc_migration = "N/A"

    if "POC Migration" in latest.columns:
        values = latest[
            "POC Migration"
        ].dropna()

        if not values.empty:
            poc_migration = str(
                values.iloc[-1]
            )

    # --------------------------------------------------------
    # EVENT COUNTS
    # --------------------------------------------------------
    def event_count(column):
        if column not in latest.columns:
            return 0

        count = 0

        for value in latest[column]:

            if value is None:
                continue

            try:
                if pd.isna(value):
                    continue
            except Exception:
                pass

            if isinstance(
                value,
                (bool, np.bool_),
            ):
                count += int(bool(value))
                continue

            if isinstance(
                value,
                (int, float, np.integer, np.floating),
            ):
                count += int(
                    float(value) != 0
                )
                continue

            text = str(
                value
            ).strip().upper()

            if text not in {
                "",
                "0",
                "0.0",
                "FALSE",
                "NO",
                "NONE",
                "NAN",
                "NEUTRAL",
            }:
                count += 1

        return count

    stacked = event_count(
        "Stacked Imbalance"
    )

    absorption = event_count(
        "Absorption"
    )

    exhaustion = event_count(
        "Exhaustion"
    )

    delta_flip = event_count(
        "Delta Flip"
    )

    failed_auction = event_count(
        "Failed Auction"
    )

    large_print = event_count(
        "Large Print"
    )

    hvn = event_count("HVN")
    lvn = event_count("LVN")

    # --------------------------------------------------------
    # PANEL
    # --------------------------------------------------------
    st.markdown(
        "### CHT Footprint Intelligence"
    )

    # Market state
    if market_state == "BUYER CONTROL":
        st.success(
            f"▲ {market_state}"
        )
    elif market_state == "SELLER CONTROL":
        st.error(
            f"▼ {market_state}"
        )
    else:
        st.warning(
            f"◆ {market_state}"
        )

    st.caption(
        f"Structure: {structure}"
    )

    # --------------------------------------------------------
    # OFI / AGGRESSION
    # --------------------------------------------------------
    c1, c2 = st.columns(2)

    with c1:
        st.metric(
            "OFI Score",
            f"{ofi_score:.1f}",
        )

    with c2:
        st.metric(
            "Aggression",
            f"{aggression:+.1f}",
        )

    # --------------------------------------------------------
    # PRESSURE
    # --------------------------------------------------------
    st.markdown(
        "**Buyer / Seller Pressure**"
    )

    p1, p2 = st.columns(2)

    with p1:
        st.metric(
            "Buyers",
            f"{buyer_pressure:.1f}%",
        )

    with p2:
        st.metric(
            "Sellers",
            f"{seller_pressure:.1f}%",
        )

    st.progress(
        int(
            np.clip(
                buyer_pressure,
                0,
                100,
            )
        ),
        text=(
            f"Buyer pressure {buyer_pressure:.1f}%"
        ),
    )

    # --------------------------------------------------------
    # DELTA / CVD / POC
    # --------------------------------------------------------
    d1, d2, d3 = st.columns(3)

    with d1:
        st.metric(
            "Delta",
            f"{delta:+,.0f}",
        )

    with d2:
        st.metric(
            "CVD",
            f"{cvd:+,.0f}",
        )

    with d3:
        st.metric(
            "POC",
            (
                f"{poc:,.2f}"
                if poc is not None
                else "N/A"
            ),
        )

    # --------------------------------------------------------
    # FLOW EVENTS
    # --------------------------------------------------------
    st.markdown(
        "**Flow Events**"
    )

    event_items = [
        ("SI", stacked),
        ("ABS", absorption),
        ("EXH", exhaustion),
        ("DF", delta_flip),
        ("FA", failed_auction),
        ("LP", large_print),
    ]

    e1, e2, e3 = st.columns(3)

    event_columns = [
        e1, e2, e3,
        e1, e2, e3,
    ]

    for index, (
        label,
        count,
    ) in enumerate(event_items):

        with event_columns[index]:
            st.metric(
                label,
                str(count),
            )

    # --------------------------------------------------------
    # STRUCTURE
    # --------------------------------------------------------
    st.markdown(
        "**Structure**"
    )

    structure_df = pd.DataFrame(
        [
            [
                "POC Migration",
                poc_migration,
            ],
            [
                "HVN",
                hvn,
            ],
            [
                "LVN",
                lvn,
            ],
            [
                "Flow Structure",
                structure,
            ],
        ],
        columns=[
            "Metric",
            "Value",
        ],
    )

    st.dataframe(
        structure_df,
        width="stretch",
        hide_index=True,
        height=150,
    )

    # --------------------------------------------------------
    # KEY LEVELS
    # --------------------------------------------------------
    st.markdown(
        "**Key Levels**"
    )

    levels = []

    if poc is not None:
        levels.append(
            [
                "POC",
                f"{poc:,.2f}",
            ]
        )

    if (
        "Price" in latest.columns
        and not latest.empty
    ):
        levels.extend(
            [
                [
                    "Footprint High",
                    f"{float(latest['Price'].max()):,.2f}",
                ],
                [
                    "Footprint Low",
                    f"{float(latest['Price'].min()):,.2f}",
                ],
            ]
        )

    if levels:
        levels_df = pd.DataFrame(
            levels,
            columns=[
                "Level",
                "Price",
            ],
        )

        st.dataframe(
            levels_df,
            width="stretch",
            hide_index=True,
            height=125,
        )

    # ========================================================
    # CHT FOOTPRINT DECISION INTELLIGENCE V0.5
    # ========================================================

    # --------------------------------------------------------
    # FLOW DIAGNOSIS
    # --------------------------------------------------------
    positive_events = (
        stacked
        + delta_flip
        + large_print
    )

    negative_events = (
        absorption
        + exhaustion
        + failed_auction
    )

    if (
        delta < 0
        and seller_pressure >= 55
        and cvd < 0
    ):
        decision_state = "SELLER CONTROL"
        flow_diagnosis = "INITIATIVE SELLING"

    elif (
        delta > 0
        and buyer_pressure >= 55
        and cvd > 0
    ):
        decision_state = "BUYER CONTROL"
        flow_diagnosis = "INITIATIVE BUYING"

    elif absorption > exhaustion:
        decision_state = "ABSORPTION"
        flow_diagnosis = "ABSORPTION / DEFENSE"

    elif exhaustion > absorption:
        decision_state = "EXHAUSTION"
        flow_diagnosis = "EXHAUSTION / FAILED FOLLOW-THROUGH"

    elif (
        delta_flip > 0
        and abs(delta) < total_volume * 0.15
    ):
        decision_state = "TRANSITION"
        flow_diagnosis = "DELTA FLIP / TRANSITION"

    else:
        decision_state = "BALANCED"
        flow_diagnosis = "MIXED ORDER FLOW"

    # --------------------------------------------------------
    # CONFIRMATION
    # --------------------------------------------------------
    confirmations = []

    if delta > 0:
        confirmations.append(
            "Positive Delta"
        )
    elif delta < 0:
        confirmations.append(
            "Negative Delta"
        )

    if cvd > 0:
        confirmations.append(
            "Positive CVD"
        )
    elif cvd < 0:
        confirmations.append(
            "Negative CVD"
        )

    if buyer_pressure >= 55:
        confirmations.append(
            "Buyer Pressure"
        )

    if seller_pressure >= 55:
        confirmations.append(
            "Seller Pressure"
        )

    if stacked > 0:
        confirmations.append(
            "Stacked Imbalance"
        )

    if large_print > 0:
        confirmations.append(
            "Large Print"
        )

    if not confirmations:
        confirmations.append(
            "No dominant flow confirmation"
        )

    confirmation_text = " • ".join(
        confirmations[:4]
    )

    # --------------------------------------------------------
    # WARNING
    # --------------------------------------------------------
    warnings = []

    if absorption > 0:
        warnings.append(
            "Absorption detected"
        )

    if exhaustion > 0:
        warnings.append(
            "Exhaustion detected"
        )

    if failed_auction > 0:
        warnings.append(
            "Failed auction detected"
        )

    if delta_flip > 0:
        warnings.append(
            "Delta flip detected"
        )

    if (
        buyer_pressure < 48
        and seller_pressure < 48
    ):
        warnings.append(
            "No dominant pressure"
        )

    if not warnings:
        warnings.append(
            "No major footprint warning"
        )

    warning_text = " • ".join(
        warnings[:3]
    )

    # --------------------------------------------------------
    # INVALIDATION
    # --------------------------------------------------------
    invalidation_text = "Acceptance through opposing flow level"

    if poc is not None:

        if decision_state == "SELLER CONTROL":
            invalidation_text = (
                f"Sustained acceptance above POC "
                f"{poc:,.2f}"
            )

        elif decision_state == "BUYER CONTROL":
            invalidation_text = (
                f"Sustained acceptance below POC "
                f"{poc:,.2f}"
            )

        elif decision_state == "ABSORPTION":
            invalidation_text = (
                f"Absorption failure around POC "
                f"{poc:,.2f}"
            )

        else:
            invalidation_text = (
                f"Clear acceptance away from POC "
                f"{poc:,.2f}"
            )

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------
    confidence = 50.0

    if abs(
        buyer_pressure
        - seller_pressure
    ) >= 15:
        confidence += 10

    if abs(delta) >= total_volume * 0.15:
        confidence += 10

    if cvd != 0:
        confidence += 8

    if stacked > 0:
        confidence += 7

    if large_print > 0:
        confidence += 5

    if (
        absorption > 0
        or exhaustion > 0
        or failed_auction > 0
    ):
        confidence -= 5

    confidence = float(
        np.clip(
            confidence,
            0,
            100,
        )
    )

    # --------------------------------------------------------
    # DECISION CONTEXT
    # --------------------------------------------------------
    if decision_state == "BUYER CONTROL":
        context = (
            "Order flow currently shows buyer dominance. "
            "Monitor continuation and acceptance above key levels."
        )

    elif decision_state == "SELLER CONTROL":
        context = (
            "Order flow currently shows seller dominance. "
            "Monitor continuation and acceptance below key levels."
        )

    elif decision_state == "ABSORPTION":
        context = (
            "Aggressive flow is being absorbed. "
            "Watch for either rejection or eventual acceptance."
        )

    elif decision_state == "EXHAUSTION":
        context = (
            "Aggressive flow is losing follow-through. "
            "Watch for reversal or failed continuation."
        )

    elif decision_state == "TRANSITION":
        context = (
            "Order flow is transitioning. "
            "Wait for confirmation from delta, CVD and pressure."
        )

    else:
        context = (
            "Order flow is mixed. "
            "No dominant participant control is currently established."
        )

    # --------------------------------------------------------
    # RENDER DECISION INTELLIGENCE
    # --------------------------------------------------------
    st.markdown(
        "---"
    )

    st.markdown(
        "### Decision Intelligence"
    )

    st.caption(
        "Native footprint interpretation • "
        "Prototype decision context"
    )

    # --------------------------------------------------------
    # STATE / CONFIDENCE
    # --------------------------------------------------------
    d1, d2 = st.columns(2)

    with d1:
        st.metric(
            "Decision State",
            decision_state,
        )

    with d2:
        st.metric(
            "Confidence",
            f"{confidence:.0f}/100",
        )

    # --------------------------------------------------------
    # FLOW DIAGNOSIS
    # --------------------------------------------------------
    st.info(
        f"**Flow Diagnosis:** {flow_diagnosis}"
    )

    # --------------------------------------------------------
    # CONFIRMATION
    # --------------------------------------------------------
    st.markdown(
        "**Confirmation**"
    )

    st.success(
        confirmation_text
    )

    # --------------------------------------------------------
    # WARNING
    # --------------------------------------------------------
    st.markdown(
        "**Warning**"
    )

    if (
        len(warnings) == 1
        and warnings[0]
        == "No major footprint warning"
    ):
        st.info(
            warning_text
        )
    else:
        st.warning(
            warning_text
        )

    # --------------------------------------------------------
    # INVALIDATION
    # --------------------------------------------------------
    st.markdown(
        "**Invalidation**"
    )

    st.error(
        invalidation_text
    )

    # --------------------------------------------------------
    # DECISION CONTEXT
    # --------------------------------------------------------
    st.markdown(
        "**Decision Context**"
    )

    st.write(
        context
    )

    # --------------------------------------------------------
    # DECISION EVIDENCE
    # --------------------------------------------------------
    evidence_df = pd.DataFrame(
        [
            [
                "Market State",
                market_state,
            ],
            [
                "Flow Diagnosis",
                flow_diagnosis,
            ],
            [
                "Delta",
                f"{delta:+,.0f}",
            ],
            [
                "CVD",
                f"{cvd:+,.0f}",
            ],
            [
                "Buyer Pressure",
                f"{buyer_pressure:.1f}%",
            ],
            [
                "Seller Pressure",
                f"{seller_pressure:.1f}%",
            ],
            [
                "POC",
                (
                    f"{poc:,.2f}"
                    if poc is not None
                    else "N/A"
                ),
            ],
            [
                "POC Migration",
                poc_migration,
            ],
        ],
        columns=[
            "Evidence",
            "Value",
        ],
    )

    st.dataframe(
        evidence_df,
        width="stretch",
        hide_index=True,
        height=245,
    )

    st.caption(
        "V0.5 • Decision Intelligence is derived from "
        "existing footprint fields • SIMULATED / PROXY"
    )


    # ========================================================
    # CHT DECISION FUSION V0.6
    # ========================================================
    #
    # Combines existing:
    #   Price Structure
    #   VWAP
    #   POC
    #   Delta
    #   CVD
    #   Buyer/Seller Pressure
    #   Footprint Events
    #
    # No new market-data or footprint engine is created.
    # ========================================================

    # --------------------------------------------------------
    # PRICE / VWAP STRUCTURE
    # --------------------------------------------------------

    price_vs_vwap = "N/A"
    vwap_value = None
    last_price = None
    price_direction = "FLAT"

    if (
        ohlcv is not None
        and not ohlcv.empty
    ):

        last_price = float(
            ohlcv["Close"].iloc[-1]
        )

        first_price = float(
            ohlcv["Open"].iloc[0]
        )

        if last_price > first_price:
            price_direction = "UP"
        elif last_price < first_price:
            price_direction = "DOWN"

        if "VWAP" in ohlcv.columns:

            vwap_values = pd.to_numeric(
                ohlcv["VWAP"],
                errors="coerce",
            ).dropna()

            if not vwap_values.empty:

                vwap_value = float(
                    vwap_values.iloc[-1]
                )

                if last_price > vwap_value:
                    price_vs_vwap = "ABOVE VWAP"
                elif last_price < vwap_value:
                    price_vs_vwap = "BELOW VWAP"
                else:
                    price_vs_vwap = "AT VWAP"

    # --------------------------------------------------------
    # PRICE VS POC
    # --------------------------------------------------------

    price_vs_poc = "N/A"

    if (
        last_price is not None
        and poc is not None
    ):

        if last_price > poc:
            price_vs_poc = "ABOVE POC"
        elif last_price < poc:
            price_vs_poc = "BELOW POC"
        else:
            price_vs_poc = "AT POC"

    # --------------------------------------------------------
    # PRICE / FLOW ALIGNMENT
    # --------------------------------------------------------

    alignment_points = 0
    alignment_reasons = []
    conflict_reasons = []

    # Price direction + delta
    if (
        price_direction == "UP"
        and delta > 0
    ):
        alignment_points += 1
        alignment_reasons.append(
            "Price ↑ + positive Delta"
        )

    elif (
        price_direction == "DOWN"
        and delta < 0
    ):
        alignment_points += 1
        alignment_reasons.append(
            "Price ↓ + negative Delta"
        )

    elif (
        price_direction == "UP"
        and delta < 0
    ):
        conflict_reasons.append(
            "Price ↑ vs negative Delta"
        )

    elif (
        price_direction == "DOWN"
        and delta > 0
    ):
        conflict_reasons.append(
            "Price ↓ vs positive Delta"
        )

    # CVD confirmation
    if (
        price_direction == "UP"
        and cvd > 0
    ):
        alignment_points += 1
        alignment_reasons.append(
            "Price ↑ + positive CVD"
        )

    elif (
        price_direction == "DOWN"
        and cvd < 0
    ):
        alignment_points += 1
        alignment_reasons.append(
            "Price ↓ + negative CVD"
        )

    elif (
        price_direction == "UP"
        and cvd < 0
    ):
        conflict_reasons.append(
            "Price ↑ vs negative CVD"
        )

    elif (
        price_direction == "DOWN"
        and cvd > 0
    ):
        conflict_reasons.append(
            "Price ↓ vs positive CVD"
        )

    # VWAP confirmation
    if price_direction == "UP":
        if price_vs_vwap == "ABOVE VWAP":
            alignment_points += 1
            alignment_reasons.append(
                "Price above VWAP"
            )
        elif price_vs_vwap == "BELOW VWAP":
            conflict_reasons.append(
                "Price below VWAP"
            )

    elif price_direction == "DOWN":
        if price_vs_vwap == "BELOW VWAP":
            alignment_points += 1
            alignment_reasons.append(
                "Price below VWAP"
            )
        elif price_vs_vwap == "ABOVE VWAP":
            conflict_reasons.append(
                "Price above VWAP"
            )

    # POC confirmation
    if (
        price_direction == "UP"
        and price_vs_poc == "ABOVE POC"
    ):
        alignment_points += 1
        alignment_reasons.append(
            "Price above POC"
        )

    elif (
        price_direction == "DOWN"
        and price_vs_poc == "BELOW POC"
    ):
        alignment_points += 1
        alignment_reasons.append(
            "Price below POC"
        )

    # Pressure confirmation
    if (
        price_direction == "UP"
        and buyer_pressure >= 55
    ):
        alignment_points += 1
        alignment_reasons.append(
            "Buyer pressure dominant"
        )

    elif (
        price_direction == "DOWN"
        and seller_pressure >= 55
    ):
        alignment_points += 1
        alignment_reasons.append(
            "Seller pressure dominant"
        )

    elif (
        price_direction == "UP"
        and seller_pressure >= 55
    ):
        conflict_reasons.append(
            "Seller pressure vs rising price"
        )

    elif (
        price_direction == "DOWN"
        and buyer_pressure >= 55
    ):
        conflict_reasons.append(
            "Buyer pressure vs falling price"
        )

    # --------------------------------------------------------
    # ALIGNMENT STATE
    # --------------------------------------------------------

    if alignment_points >= 4:
        alignment_state = "STRONG ALIGNMENT"

    elif alignment_points >= 2:
        alignment_state = "PARTIAL ALIGNMENT"

    elif len(conflict_reasons) >= 2:
        alignment_state = "FLOW / PRICE CONFLICT"

    else:
        alignment_state = "MIXED"

    # --------------------------------------------------------
    # CONFLICT DETECTION
    # --------------------------------------------------------

    if (
        absorption > 0
        and delta < 0
        and price_direction == "UP"
    ):
        conflict_reasons.append(
            "Upside price with seller absorption"
        )

    if (
        absorption > 0
        and delta > 0
        and price_direction == "DOWN"
    ):
        conflict_reasons.append(
            "Downside price with buyer absorption"
        )

    if (
        exhaustion > 0
        and abs(delta) < total_volume * 0.10
    ):
        conflict_reasons.append(
            "Exhaustion with weak delta"
        )

    if not conflict_reasons:
        conflict_reasons.append(
            "No major price/flow conflict"
        )

    # --------------------------------------------------------
    # UNIFIED STATE
    # --------------------------------------------------------

    if (
        price_direction == "UP"
        and alignment_state == "STRONG ALIGNMENT"
    ):
        unified_state = "BULLISH FLOW CONFIRMED"

    elif (
        price_direction == "DOWN"
        and alignment_state == "STRONG ALIGNMENT"
    ):
        unified_state = "BEARISH FLOW CONFIRMED"

    elif (
        alignment_state == "FLOW / PRICE CONFLICT"
    ):
        unified_state = "CONFLICT / WAIT"

    elif decision_state == "ABSORPTION":
        unified_state = "ABSORPTION / WAIT"

    elif decision_state == "EXHAUSTION":
        unified_state = "EXHAUSTION / WAIT"

    elif decision_state == "TRANSITION":
        unified_state = "TRANSITION"

    else:
        unified_state = "MIXED / WAIT"

    # --------------------------------------------------------
    # CONFIRMATION SCORE
    # --------------------------------------------------------

    confirmation_score = 50.0

    confirmation_score += (
        alignment_points * 8.0
    )

    confirmation_score -= (
        len(conflict_reasons)
        * 5.0
    )

    if stacked > 0:
        confirmation_score += 5.0

    if large_print > 0:
        confirmation_score += 3.0

    if (
        absorption > 0
        or exhaustion > 0
    ):
        confirmation_score -= 3.0

    confirmation_score = float(
        np.clip(
            confirmation_score,
            0.0,
            100.0,
        )
    )

    # --------------------------------------------------------
    # UNIFIED CONFIDENCE
    # --------------------------------------------------------

    unified_confidence = (
        confidence * 0.50
        + confirmation_score * 0.50
    )

    unified_confidence = float(
        np.clip(
            unified_confidence,
            0.0,
            100.0,
        )
    )

    # --------------------------------------------------------
    # PRIMARY RISK
    # --------------------------------------------------------

    if (
        len(conflict_reasons) >= 2
    ):
        primary_risk = (
            "Price and order-flow signals are conflicting."
        )

    elif absorption > 0:
        primary_risk = (
            "Absorption may invalidate continuation."
        )

    elif exhaustion > 0:
        primary_risk = (
            "Exhaustion may reduce follow-through."
        )

    elif (
        price_vs_vwap == "AT VWAP"
    ):
        primary_risk = (
            "Price is near VWAP; directional acceptance "
            "is not established."
        )

    else:
        primary_risk = (
            "Monitor acceptance around POC and key flow levels."
        )

    # --------------------------------------------------------
    # UNIFIED INVALIDATION
    # --------------------------------------------------------

    if poc is not None:

        if (
            unified_state
            == "BULLISH FLOW CONFIRMED"
        ):
            unified_invalidation = (
                f"Loss of POC {poc:,.2f} "
                f"with negative Delta/CVD."
            )

        elif (
            unified_state
            == "BEARISH FLOW CONFIRMED"
        ):
            unified_invalidation = (
                f"Acceptance above POC {poc:,.2f} "
                f"with positive Delta/CVD."
            )

        elif (
            unified_state
            == "CONFLICT / WAIT"
        ):
            unified_invalidation = (
                f"Wait for acceptance away from POC "
                f"{poc:,.2f} and flow confirmation."
            )

        else:
            unified_invalidation = (
                f"Clear acceptance away from POC "
                f"{poc:,.2f} with confirming flow."
            )

    else:
        unified_invalidation = (
            "Establish a validated structural level "
            "before using invalidation."
        )

    # --------------------------------------------------------
    # EVIDENCE STRIP
    # --------------------------------------------------------

    evidence = []

    if price_direction != "FLAT":
        evidence.append(
            f"Price {price_direction}"
        )

    evidence.append(
        price_vs_vwap
    )

    evidence.append(
        price_vs_poc
    )

    evidence.append(
        f"Delta {delta:+,.0f}"
    )

    evidence.append(
        f"CVD {cvd:+,.0f}"
    )

    evidence.append(
        f"Buy {buyer_pressure:.1f}%"
    )

    evidence.append(
        f"Sell {seller_pressure:.1f}%"
    )

    # --------------------------------------------------------
    # RENDER V0.6
    # --------------------------------------------------------

    st.markdown(
        "---"
    )

    st.markdown(
        "### CHT Decision Fusion"
    )

    st.caption(
        "Unified price + footprint + flow context"
    )

    # --------------------------------------------------------
    # TOP STATE
    # --------------------------------------------------------

    if (
        unified_state
        == "BULLISH FLOW CONFIRMED"
    ):
        st.success(
            f"▲ {unified_state}"
        )

    elif (
        unified_state
        == "BEARISH FLOW CONFIRMED"
    ):
        st.error(
            f"▼ {unified_state}"
        )

    elif (
        unified_state
        == "CONFLICT / WAIT"
    ):
        st.warning(
            f"◆ {unified_state}"
        )

    else:
        st.info(
            f"◆ {unified_state}"
        )

    # --------------------------------------------------------
    # CORE FUSION METRICS
    # --------------------------------------------------------

    f1, f2, f3 = st.columns(3)

    with f1:
        st.metric(
            "Alignment",
            alignment_state,
        )

    with f2:
        st.metric(
            "Confirmation",
            f"{confirmation_score:.0f}/100",
        )

    with f3:
        st.metric(
            "Unified Confidence",
            f"{unified_confidence:.0f}/100",
        )

    # --------------------------------------------------------
    # PRICE / FLOW MAP
    # --------------------------------------------------------

    st.markdown(
        "**Price / Flow Map**"
    )

    map_df = pd.DataFrame(
        [
            [
                "Price Direction",
                price_direction,
            ],
            [
                "VWAP",
                price_vs_vwap,
            ],
            [
                "POC",
                price_vs_poc,
            ],
            [
                "Market State",
                market_state,
            ],
            [
                "Flow Diagnosis",
                flow_diagnosis,
            ],
        ],
        columns=[
            "Factor",
            "State",
        ],
    )

    st.dataframe(
        map_df,
        width="stretch",
        hide_index=True,
        height=185,
    )

    # --------------------------------------------------------
    # CONFIRMATION EVIDENCE
    # --------------------------------------------------------

    st.markdown(
        "**Confirmation Evidence**"
    )

    if alignment_reasons:
        st.success(
            " • ".join(
                alignment_reasons[:5]
            )
        )
    else:
        st.info(
            "No strong confirmation factors."
        )

    # --------------------------------------------------------
    # CONFLICT DETECTION
    # --------------------------------------------------------

    st.markdown(
        "**Conflict Detection**"
    )

    if (
        len(conflict_reasons) > 0
        and conflict_reasons[0]
        != "No major price/flow conflict"
    ):
        st.warning(
            " • ".join(
                conflict_reasons[:4]
            )
        )
    else:
        st.info(
            "No major price/flow conflict detected."
        )

    # --------------------------------------------------------
    # PRIMARY RISK
    # --------------------------------------------------------

    st.markdown(
        "**Primary Risk**"
    )

    st.warning(
        primary_risk
    )

    # --------------------------------------------------------
    # INVALIDATION
    # --------------------------------------------------------

    st.markdown(
        "**Unified Invalidation**"
    )

    st.error(
        unified_invalidation
    )

    # --------------------------------------------------------
    # EVIDENCE STRIP
    # --------------------------------------------------------

    st.markdown(
        "**Decision Evidence**"
    )

    evidence_df = pd.DataFrame(
        {
            "Evidence": evidence
        }
    )

    st.dataframe(
        evidence_df,
        width="stretch",
        hide_index=True,
        height=170,
    )

    st.caption(
        "V0.6 • Decision Fusion uses existing CHT and "
        "footprint outputs • SIMULATED / PROXY"
    )



    st.caption(
        "CHT Footprint Intelligence V0.4.2 • "
        "Existing footprint engine • "
        "SIMULATED / PROXY"
    )
def _ifit_v083_charts_page(ctx):
    native_footprint = None
    """V0.8.4 advanced TradingView-style interactive chart workspace."""
    st.markdown("## Advanced Interactive Charts Workspace")
    st.caption(
        "Interactive research charting with configurable indicators, lower panes, IFIT flow overlays and drawing tools. "
        "Simulation/proxy series remain explicitly labelled until an authorized chart/depth feed is connected."
    )

    st.markdown("### CHT Workspace")
    cht_workspace = st.radio(
        "Chart Workspace",
        ["Interactive Chart", "Motion Charts", "Order Flow Footprint"],
        horizontal=True,
        key="ifit_cht_workspace",
    )

    if cht_workspace == "Motion Charts":
        _ifit_v086_motion_charts_page(ctx)
        return

    if cht_workspace == "Order Flow Footprint":
        _ifit_v087_order_flow_footprint_page(ctx)
        return

    # --------------------------------------------------------
    # CHT V2 — MULTI-INSTRUMENT / OPTION SCRIPT SUPPORT
    # --------------------------------------------------------
    st.markdown("### CHT Instrument")

    instrument_types = [
        "Equity",
        "Index",
        "Futures",
        "Options",
    ]

    instrument_type = st.selectbox(
        "Instrument Type",
        instrument_types,
        key="ifit_cht_instrument_type",
    )

    option_script = None
    option_underlying = None
    option_expiry = None
    option_strike = None
    option_type = None
    option_dte = None

    if instrument_type == "Options":

        st.markdown("#### Option Contract")

        oc1, oc2, oc3, oc4 = st.columns(4)

        option_underlying = oc1.selectbox(
            "Underlying",
            [
                "NIFTY",
                "BANKNIFTY",
                "SENSEX",
                "RELIANCE",
                "ICICIBANK",
                "HDFCBANK",
                "INFY",
                "TCS",
            ],
            key="ifit_cht_option_underlying",
        )

        option_expiry = oc2.selectbox(
            "Expiry",
            [
                "Current",
                "Next",
                "Far",
            ],
            key="ifit_cht_option_expiry",
        )

        default_strikes = {
            "NIFTY": 25000.0,
            "BANKNIFTY": 54000.0,
            "SENSEX": 82000.0,
            "RELIANCE": 1400.0,
            "ICICIBANK": 1400.0,
            "HDFCBANK": 2000.0,
            "INFY": 1600.0,
            "TCS": 3500.0,
        }

        strike_steps = {
            "NIFTY": 50.0,
            "BANKNIFTY": 100.0,
            "SENSEX": 100.0,
            "RELIANCE": 10.0,
            "ICICIBANK": 10.0,
            "HDFCBANK": 10.0,
            "INFY": 10.0,
            "TCS": 50.0,
        }

        option_strike = oc3.number_input(
            "Strike",
            min_value=1.0,
            value=default_strikes[option_underlying],
            step=strike_steps[option_underlying],
            key="ifit_cht_option_strike",
        )

        option_type = oc4.selectbox(
            "Option Type",
            ["CE", "PE"],
            key="ifit_cht_option_type",
        )

        dte_defaults = {
            "Current": 14,
            "Next": 35,
            "Far": 70,
        }

        option_dte = st.number_input(
            "Days To Expiry",
            min_value=1,
            max_value=365,
            value=dte_defaults[option_expiry],
            key="ifit_cht_option_dte",
        )

        option_spot_map = {
            "NIFTY": 25000.0,
            "BANKNIFTY": 54000.0,
            "SENSEX": 82000.0,
            "RELIANCE": 1400.0,
            "ICICIBANK": 1400.0,
            "HDFCBANK": 2000.0,
            "INFY": 1600.0,
            "TCS": 3500.0,
        }

        option_spot = option_spot_map[option_underlying]

        option_script = (
            f"{option_underlying} "
            f"{option_strike:,.0f} "
            f"{option_type}"
        )

        st.success(
            f"ACTIVE OPTION SCRIPT: {option_script}  |  "
            f"EXPIRY: {option_expiry}  |  "
            f"DTE: {option_dte}  |  "
            f"DATA: SIMULATED / PROXY"
        )

    c1, c2, c3, c4 = st.columns(4)

    chart_tf_options = [
        "Intraday",
        "5 min",
        "15 min",
        "1 hour",
        "Daily",
    ]

    chart_tf = c1.selectbox(
        "Timeframe",
        chart_tf_options,
        index=chart_tf_options.index(ctx.timeframe)
        if ctx.timeframe in chart_tf_options else 0,
        key="ifit_v084_tf",
    )

    bars_n = c2.selectbox(
        "Bars",
        [90, 120, 180, 240, 360],
        index=2,
        key="ifit_v084_bars",
    )

    chart_type = c3.selectbox(
        "Chart type",
        ["Candlestick", "Line", "Area"],
        key="ifit_v084_chart_type",
    )

    show_native_footprint = st.checkbox(
        "Native Order Flow Footprint",
        value=st.session_state.get(
            "ifit_cht_native_footprint",
            False,
        ),
        key="ifit_cht_native_footprint",
    )

    profile_bins = c4.slider(
        "Profile bins",
        15,
        60,
        30,
        5,
        key="ifit_v084_bins",
    )

    # --------------------------------------------------------
    # DATA ADAPTER
    # --------------------------------------------------------
    if instrument_type == "Options":

        cht_spot = option_spot

        ohlcv = build_option_ohlcv(
            underlying_spot=option_spot,
            strike=option_strike,
            option_type=option_type,
            dte=option_dte,
            bars=bars_n,
            timeframe=chart_tf,
            seed=42,
        )

    else:

        cht_spot = _ifit_cht_asset_reference(ctx)

        if ctx.data_mode == "DHAN LIVE":
            try:
                _live_service = _get_dhan_live_service()
                _live_ohlcv = _live_service.live_ohlcv(timeframe=chart_tf, bars=bars_n)
            except Exception:
                _live_ohlcv = pd.DataFrame()

            if not _live_ohlcv.empty:
                ohlcv = _live_ohlcv
                cht_spot = float(ohlcv["Close"].iloc[-1])
            else:
                ohlcv = build_ohlcv(
                    cht_spot,
                    bars_n,
                    chart_tf,
                )
        else:
            ohlcv = build_ohlcv(
                cht_spot,
                bars_n,
                chart_tf,
            )

    profile = build_volume_profile(
        ohlcv,
        profile_bins,
    )

    snap_reference = (
        float(ohlcv["Close"].iloc[-1])
        if instrument_type == "Options"
        else cht_spot
    )

    snap = chart_snapshot(
        ohlcv,
        profile,
        snap_reference,
    )
    snap = chart_snapshot(ohlcv, profile, cht_spot)

    st.markdown("### Indicator Stack")
    indicator_options = ["EMA", "SMA", "VWAP", "Bollinger Bands", "Supertrend", "RSI", "MACD", "ATR", "Volume", "CVD", "Delta"]

    st.markdown("### Indicator Stack")

    # Persistent indicator state survives navigation away from CHT Charts.
    if "ifit_v084_indicators_persist" not in st.session_state:
        st.session_state["ifit_v084_indicators_persist"] = ["EMA", "VWAP", "Volume"]
    st.session_state["ifit_v084_indicators"] = list(st.session_state["ifit_v084_indicators_persist"])

    st.markdown("#### ⚡ Quick Add")
    qa1, qa2, qa3, qa4, qa5, qa6 = st.columns(6)

    quick_adds = [
        ("EMA 20", "EMA"),
        ("VWAP", "VWAP"),
        ("RSI 14", "RSI"),
        ("Bollinger Bands", "Bollinger Bands"),
        ("MACD", "MACD"),
        ("Supertrend", "Supertrend"),
    ]

    for col, (label, indicator) in zip([qa1, qa2, qa3, qa4, qa5, qa6], quick_adds):
        if col.button(label, key=f"ifit_v084_quickadd_{indicator.replace(' ', '_').lower()}"):
            current = list(st.session_state.get("ifit_v084_indicators", []))
            if indicator not in current:
                current.append(indicator)
                st.session_state["ifit_v084_indicators"] = current
                st.session_state["ifit_v084_indicators_persist"] = list(current)
            st.rerun()

    selected = st.multiselect(
        "Indicators",
        indicator_options,
        key="ifit_v084_indicators",
        on_change=lambda: st.session_state.update(ifit_v084_indicators_persist=list(st.session_state["ifit_v084_indicators"])),
    )

    # Persistent chart parameter state survives navigation away from CHT Charts.
    _param_defaults = {
        "ifit_v084_ema": 20,
        "ifit_v084_sma": 50,
        "ifit_v084_rsi": 14,
        "ifit_v084_bbmult": 2.0,
        "ifit_v084_stmult": 3.0,
        "ifit_v084_macdfast": 12,
        "ifit_v084_macdslow": 26,
        "ifit_v084_macdsignal": 9,
        "ifit_v084_atr": 14,
        "ifit_v084_poc": True,
        "ifit_v084_profile": False,
        "ifit_v084_cvd": False,
        "ifit_v084_delta": False,
    }
    if "ifit_v084_params_persist" not in st.session_state:
        st.session_state["ifit_v084_params_persist"] = dict(_param_defaults)
    for _k, _v in st.session_state["ifit_v084_params_persist"].items():
        if _k not in st.session_state:
            st.session_state[_k] = _v

    def _ifit_v084_save_params():
        for _k in _param_defaults:
            if _k in st.session_state:
                st.session_state["ifit_v084_params_persist"][_k] = st.session_state[_k]

    p1, p2, p3, p4, p5 = st.columns(5)
    ema_n = p1.number_input("EMA", 2, 200, key="ifit_v084_ema", on_change=_ifit_v084_save_params)
    sma_n = p2.number_input("SMA", 2, 300, key="ifit_v084_sma", on_change=_ifit_v084_save_params)
    rsi_n = p3.number_input("RSI", 2, 100, key="ifit_v084_rsi", on_change=_ifit_v084_save_params)
    bb_mult = p4.number_input("BB σ", 0.5, 4.0, key="ifit_v084_bbmult", on_change=_ifit_v084_save_params)
    st_mult = p5.number_input("ST × ATR", 0.5, 8.0, key="ifit_v084_stmult", on_change=_ifit_v084_save_params)

    q1, q2, q3, q4 = st.columns(4)
    q1.number_input("MACD Fast", 2, 50, key="ifit_v084_macdfast", on_change=_ifit_v084_save_params)
    q2.number_input("MACD Slow", 3, 100, key="ifit_v084_macdslow", on_change=_ifit_v084_save_params)
    q3.number_input("MACD Signal", 2, 50, key="ifit_v084_macdsignal", on_change=_ifit_v084_save_params)
    q4.number_input("ATR", 2, 100, key="ifit_v084_atr", on_change=_ifit_v084_save_params)

    x1, x2, x3, x4 = st.columns(4)
    show_poc = x1.checkbox("POC", key="ifit_v084_poc", on_change=_ifit_v084_save_params)
    show_profile = x2.checkbox("Volume Profile", key="ifit_v084_profile", on_change=_ifit_v084_save_params)
    show_cvd = x3.checkbox("IFIT CVD", key="ifit_v084_cvd", on_change=_ifit_v084_save_params)
    show_delta = x4.checkbox("IFIT Delta", key="ifit_v084_delta", on_change=_ifit_v084_save_params)

    params = {
        "ema": ema_n, "sma": sma_n, "rsi": rsi_n, "bb_mult": bb_mult,
        "bb": 20, "st_period": 10, "st_mult": st_mult,
        "macd_fast": q1.number_input if False else st.session_state.get("ifit_v084_macdfast", 12),
        "macd_slow": st.session_state.get("ifit_v084_macdslow", 26),
        "macd_signal": st.session_state.get("ifit_v084_macdsignal", 9),
        "atr": st.session_state.get("ifit_v084_atr", 14),
    }

    m1,m2,m3,m4,m5,m6 = st.columns(6)
    m1.metric("Last", f'{snap["last"]:,.2f}', f'{snap["change_pct"]:+.2f}%')
    m2.metric("Structure", snap["structure"])
    m3.metric("VWAP", f'{snap["vwap"]:,.2f}')
    m4.metric("POC", f'{snap["poc"]:,.2f}')
    m5.metric("Delta", f'{snap["delta"]:+,.0f}')
    m6.metric("CVD", f'{snap["cvd"]:+,.0f}')

    if instrument_type == "Options":
        st.info(
            f"ACTIVE CHART • {option_script} • {chart_tf} • "
            f"{bars_n} bars • DATA SIMULATED / PROXY"
        )
    else:
        st.info(
            f"ACTIVE CHART • {ctx.instrument} • {chart_tf} • "
            f"{bars_n} bars • DATA {ctx.data_mode} • "
            f'{"SIMULATED / PROXY" if ctx.data_mode == "SIMULATION" else "AUTHORIZED SOURCE"}'
        )

    # --------------------------------------------------------
    # CHT V2 — NATIVE ORDER FLOW FOOTPRINT V0.2 DATA PREP
    # Build the existing frozen footprint dataframe BEFORE
    # constructing the CHT figure so the native candle overlay
    # receives the actual footprint data.
    # --------------------------------------------------------
    if show_native_footprint:
        footprint_start_price = float(
            ohlcv["Close"].iloc[-1]
        )

        native_periods = min(
            len(ohlcv),
            60,
        )

        native_footprint = build_footprint_data(
            periods=native_periods,
            levels=24,
            seed=42,
            start_price=footprint_start_price,
        )
    else:
        native_footprint = None

    if ctx.data_mode == "DHAN LIVE" and instrument_type != "Options":
        _render_cht_live_fragment(
            chart_tf=chart_tf,
            bars_n=bars_n,
            chart_type=chart_type,
            selected=selected,
            params=params,
            show_poc=show_poc,
            show_profile=show_profile,
            show_cvd=show_cvd,
            show_delta=show_delta,
            show_native_footprint=show_native_footprint,
            profile_bins=profile_bins,
            fallback_ohlcv=ohlcv,
            fallback_spot=cht_spot,
        )
    else:
        fig = build_interactive_figure(
            ohlcv, chart_type, selected, params,
            show_poc=show_poc, poc=snap["poc"], show_volume_profile=show_profile,
            profile=profile, show_cvd=show_cvd, show_delta=show_delta,
            show_native_footprint=show_native_footprint,
            footprint_df=(
                native_footprint
                if show_native_footprint
                else None
            ),
        )
        # ========================================================
        # CHT FOOTPRINT INTELLIGENCE V0.4
        # Chart + Order Flow Intelligence terminal layout.
        # ========================================================

        if show_native_footprint:
            chart_col, intelligence_col = st.columns(
                [3.45, 1.55],
                gap="medium",
            )

            with chart_col:
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key="ifit_v084_interactive_chart",
                    config={
                        "scrollZoom": True,
                        "displayModeBar": True,
                        "displaylogo": False,
                        "modeBarButtonsToAdd": [
                            "drawline",
                            "drawopenpath",
                            "drawrect",
                            "drawcircle",
                            "eraseshape",
                        ],
                        "modeBarButtonsToRemove": [
                            "lasso2d",
                            "select2d",
                        ],
                    },
                )

            with intelligence_col:
                _render_cht_footprint_intelligence(
                    native_footprint,
                    ohlcv,
                )

        else:
            st.plotly_chart(
                fig,
                use_container_width=True,
                key="ifit_v084_interactive_chart",
                config={
                    "scrollZoom": True,
                    "displayModeBar": True,
                    "displaylogo": False,
                    "modeBarButtonsToAdd": [
                        "drawline",
                        "drawopenpath",
                        "drawrect",
                        "drawcircle",
                        "eraseshape",
                    ],
                    "modeBarButtonsToRemove": [
                        "lasso2d",
                        "select2d",
                    ],
                },
            )

        # --------------------------------------------------------
    # CHT V2 — NATIVE ORDER FLOW FOOTPRINT
    # --------------------------------------------------------
    if show_native_footprint:

        # CHT V0.6.1: standalone footprint display consolidated into the intelligence panels.
        pass

    st.markdown("### Drawing & Chart Tools")
    st.info(
        "The drawing toolbar is now permanently visible on the chart. "
        "Use the line, freehand, rectangle and circle tools to annotate price structure; "
        "use the eraser to remove a selected drawing. Mouse-wheel zooms, drag pans, and double-click resets the view. "
        "Drawings are discretionary research annotations only and are not trade orders."
    )

    with st.expander("Active Indicator Stack", expanded=True):
        if selected:
            rows = []
            for item in selected:
                reading = {
                    "EMA": f"{ema_n}-period overlay", "SMA": f"{sma_n}-period overlay",
                    "VWAP": "IFIT session VWAP", "Bollinger Bands": f"20-period ± {bb_mult:.1f}σ",
                    "Supertrend": f"10-period ATR × {st_mult:.1f}", "RSI": f"{rsi_n}-period oscillator",
                    "MACD": f"{params['macd_fast']}/{params['macd_slow']}/{params['macd_signal']}",
                    "ATR": f"{params['atr']}-period range", "Volume": "bar volume",
                    "CVD": "IFIT cumulative delta proxy", "Delta": "IFIT per-bar delta proxy",
                }[item]
                rows.append([item, reading, "ACTIVE"])
            st.dataframe(pd.DataFrame(rows, columns=["Indicator", "Configuration", "Status"]), width="stretch", hide_index=True)
        else:
            st.caption("No indicators selected. Add indicators above to build the stack.")

    st.markdown("### Chart Engine Status")
    st.dataframe(pd.DataFrame(chart_capabilities()), width="stretch", hide_index=True)

    with st.expander("IFIT V0.8.4 Methodology"):
        st.markdown(
            "**Interactive price:** Plotly OHLC candles/line/area with synchronized hover, zoom and pan.\n\n"
            "**Indicators:** EMA, SMA, VWAP, Bollinger Bands, Supertrend, RSI, MACD and ATR are calculated from the current IFIT OHLCV snapshot.\n\n"
            "**IFIT flow:** CVD and Delta are surfaced as research overlays using the current provider/proxy-labelled flow fields.\n\n"
            "**Drawings:** chart-native drawing tools are provided for discretionary research; drawings are session-level browser interactions and are not trade orders.\n\n"
            "**Volume Profile:** IFIT's existing profile engine can be displayed alongside the price structure.\n\n"
            "All outputs are research diagnostics and are not automatic trading instructions."
        )


def _render_cht_live_fragment(chart_tf, bars_n, chart_type, selected, params, show_poc, show_profile, show_cvd, show_delta, show_native_footprint, profile_bins, fallback_ohlcv, fallback_spot):
    @st.fragment(run_every=1)
    def _cht_live_fragment():
        st.caption("CHT DEBUG • LIVE FRAGMENT EXECUTING")
        live_service = _get_dhan_live_service()
        historical_ohlcv = pd.DataFrame()
        live_ohlcv = pd.DataFrame()

        try:
            historical_candles = live_service.historical_candles(
                timeframe=chart_tf,
                bars=bars_n,
            )
            historical_ohlcv = build_dhan_historical_ohlcv(
                historical_candles,
                bars=bars_n,
            )
        except Exception:
            historical_ohlcv = pd.DataFrame()

        try:
            live_ohlcv = live_service.live_ohlcv(timeframe=chart_tf, bars=bars_n)
        except Exception:
            live_ohlcv = pd.DataFrame()

        chart_ohlcv = pd.DataFrame()
        if not historical_ohlcv.empty and not live_ohlcv.empty:
            try:
                merged = pd.concat(
                    [historical_ohlcv, live_ohlcv],
                    ignore_index=True,
                )
                merged["Timestamp"] = pd.to_datetime(
                    merged["Timestamp"],
                    errors="coerce",
                    utc=True,
                )
                merged = merged.dropna(subset=["Timestamp"])
                merged = merged.sort_values("Timestamp")
                merged = merged.drop_duplicates(
                    subset=["Timestamp"],
                    keep="last",
                )
                merged = merged.tail(int(max(1, bars_n))).reset_index(drop=True)
                merged["Bar"] = range(len(merged))
                chart_ohlcv = merged
            except Exception:
                chart_ohlcv = historical_ohlcv
        elif not historical_ohlcv.empty:
            chart_ohlcv = historical_ohlcv
        elif not live_ohlcv.empty:
            chart_ohlcv = live_ohlcv
        else:
            chart_ohlcv = fallback_ohlcv

        chart_profile = build_volume_profile(chart_ohlcv, profile_bins)
        chart_spot = float(chart_ohlcv["Close"].iloc[-1]) if not chart_ohlcv.empty else float(fallback_spot)
        chart_snap = chart_snapshot(chart_ohlcv, chart_profile, chart_spot)

        if show_native_footprint and not chart_ohlcv.empty:
            native_periods = min(len(chart_ohlcv), 60)
            tick_size = 0.05
            try:
                tick_size = float(live_service.instrument.metadata.get("tick_size", 0.05))
            except (AttributeError, TypeError, ValueError):
                tick_size = 0.05
            chart_ticks = live_service.tick_history()
            chart_footprint = build_live_tick_footprint(
                ticks=chart_ticks,
                tick_size=tick_size,
                bars=native_periods,
            )
        else:
            chart_footprint = None

        live_fig = build_interactive_figure(
            chart_ohlcv,
            chart_type,
            selected,
            params,
            show_poc=show_poc,
            poc=chart_snap["poc"],
            show_volume_profile=show_profile,
            profile=chart_profile,
            show_cvd=show_cvd,
            show_delta=show_delta,
            show_native_footprint=show_native_footprint,
            footprint_df=(chart_footprint if show_native_footprint else None),
        )

        if "Timestamp" in chart_ohlcv.columns:
            chart_timestamps = pd.to_datetime(chart_ohlcv["Timestamp"], errors="coerce", utc=True).tolist()
        else:
            chart_timestamps = pd.date_range(end=pd.Timestamp.now(tz="UTC"), periods=len(chart_ohlcv), freq="1min").tolist()

        if show_native_footprint:
            chart_col, intelligence_col = st.columns([3.45, 1.55], gap="medium")
            with chart_col:
                render_live_chart(live_fig, height=int(live_fig.layout.height or 700), key="ifit_v084_live_interactive_chart_footprint", timestamps=chart_timestamps, poc=chart_snap["poc"], profile=chart_profile, footprint_df=chart_footprint)
            with intelligence_col:
                _render_cht_footprint_intelligence(chart_footprint, chart_ohlcv)
        else:
            st.caption(f"CHT DEBUG • rows={len(chart_ohlcv)} • traces={len(live_fig.data)} • height={live_fig.layout.height}")
            render_live_chart(live_fig, height=int(live_fig.layout.height or 700), key="ifit_v084_live_interactive_chart_main", timestamps=chart_timestamps, poc=chart_snap["poc"], profile=chart_profile)

    _cht_live_fragment()

def _ifit_v081_equities_page():
    _ifit_v081_header("Equities")
    st.markdown("## Equities")
    st.caption("V0.8.2 establishes the equity workspace contract. Values below are demonstration inputs until an authorized fundamental/market-data source is connected.")
    ticker = st.selectbox("Security", ["RELIANCE","HDFCBANK","TCS","INFY","ICICIBANK","LT"], key="ifit_v081_equity")
    data = {
        "RELIANCE":[1510,24.1,15.8,19.4,.31,14.2,18.6],
        "HDFCBANK":[1840,19.6,16.2,17.1,.20,15.8,16.9],
        "TCS":[4120,28.2,46.0,51.3,.06,11.4,22.1],
        "INFY":[1740,25.4,31.8,35.1,.08,12.2,19.8],
        "ICICIBANK":[1455,18.4,17.5,18.2,.12,14.5,18.2],
        "LT":[3850,34.5,16.1,18.7,.72,12.8,14.9],
    }[ticker]
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    for c,n,v in zip([c1,c2,c3,c4,c5,c6], ["Price","P/E","ROE %","ROCE %","Debt/Equity","EPS Growth %","FCF Yield %"], data):
        c.metric(n, f"{v:,.2f}")
    left,right = st.columns(2)
    with left:
        st.markdown("### Equity Intelligence Map")
        st.dataframe(pd.DataFrame([
            ["Fundamentals","DEMO / CONNECTOR PENDING"],
            ["Valuation",f"P/E {data[1]:.1f}x"],
            ["Quality",f"ROE {data[2]:.1f}% • ROCE {data[3]:.1f}%"],
            ["Growth",f"EPS growth {data[5]:.1f}%"],
            ["Balance Sheet",f"Debt/Equity {data[4]:.2f}x"],
            ["Cash Flow",f"FCF yield {data[6]:.1f}%"],
        ], columns=["Layer","Reading"]), width="stretch", hide_index=True)
    with right:
        st.markdown("### IFIT Equity Score")
        score = float(np.clip(50 + data[5]*0.7 + data[2]*0.5 + data[3]*0.25 - data[1]*0.35 - data[4]*8, 0, 100))
        st.metric("Equity Score", f"{score:.1f}/100")
        st.info("The scoring framework is an architecture prototype; production scoring will require normalized historical fundamentals, peer data and revisions.")
def _ifit_v085_derivatives_screener_page():
    st.markdown("## 🔎 IFIT Screener — Derivatives")
    st.caption(
        "V0.8.5 • Options and derivatives positioning, volatility, "
        "Greeks and liquidity screening."
    )

    derivatives = build_derivatives_universe()

    st.markdown("### Derivatives Filters")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        option_type = st.selectbox(
            "Option Type",
            ["All", "CE", "PE"],
            key="ifit_v085_deriv_type",
        )

    with c2:
        expiry_options = [
            "All"
        ] + derivatives["Expiry"].drop_duplicates().tolist()

        expiry = st.selectbox(
            "Expiry",
            expiry_options,
            key="ifit_v085_deriv_expiry",
        )

    with c3:
        min_oi_lakh = st.number_input(
            "Minimum OI (Lakh)",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="ifit_v085_deriv_min_oi",
        )

    with c4:
        min_volume_lakh = st.number_input(
            "Minimum Volume (Lakh)",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key="ifit_v085_deriv_min_volume",
        )

    c5, c6, c7, c8 = st.columns(4)

    with c5:
        min_iv = st.number_input(
            "Minimum IV %",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=1.0,
            key="ifit_v085_deriv_min_iv",
        )

    with c6:
        max_iv = st.number_input(
            "Maximum IV %",
            min_value=0.0,
            max_value=100.0,
            value=100.0,
            step=1.0,
            key="ifit_v085_deriv_max_iv",
        )

    with c7:
        min_liquidity = st.number_input(
            "Minimum Liquidity",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=5.0,
            key="ifit_v085_deriv_liquidity",
        )

    with c8:
        signal_options = [
            "All",
            "LONG BUILDUP",
            "SHORT BUILDUP",
            "SHORT COVERING",
            "LONG UNWINDING",
        ]

        signal = st.selectbox(
            "Positioning Signal",
            signal_options,
            key="ifit_v085_deriv_signal",
        )

    filters = {
        "option_type": (
            None if option_type == "All" else option_type
        ),
        "expiry": (
            None if expiry == "All" else expiry
        ),
        "min_oi": min_oi_lakh * 100000,
        "min_volume": min_volume_lakh * 100000,
        "min_iv": min_iv,
        "max_iv": max_iv,
        "min_liquidity": min_liquidity,
        "signal": (
            None if signal == "All" else signal
        ),
    }

    screened = apply_derivatives_filters(
        derivatives,
        filters,
    )

    ranked = rank_derivatives(
        screened,
        "Liquidity Score",
        ascending=False,
    )

    st.markdown("### Screening Summary")

    m1, m2, m3, m4, m5 = st.columns(5)

    m1.metric("Contracts", f"{len(derivatives)}")

    m2.metric("Matches", f"{len(screened)}")

    m3.metric(
        "CE",
        f"{(screened['Option Type'] == 'CE').sum()}",
    )

    m4.metric(
        "PE",
        f"{(screened['Option Type'] == 'PE').sum()}",
    )

    m5.metric(
        "Avg IV",
        (
            f"{screened['IV %'].mean():.2f}%"
            if not screened.empty
            else "—"
        ),
    )

    st.markdown("### Ranked Derivatives")

    display_columns = [
        "Symbol",
        "Expiry",
        "DTE",
        "Strike",
        "Option Type",
        "Spot",
        "LTP",
        "Price Change %",
        "OI",
        "OI Change %",
        "Volume",
        "IV %",
        "Delta",
        "Gamma",
        "Vega",
        "Theta/Day",
        "Spread %",
        "Liquidity Score",
        "Signal",
    ]

    if ranked.empty:
        st.warning(
            "No derivatives contracts match the selected criteria."
        )
    else:
        st.dataframe(
            ranked[display_columns],
            width="stretch",
            hide_index=True,
        )

    st.markdown("### Positioning Summary")

    summary = signal_summary(screened)

    if summary.empty:
        st.info("No positioning statistics available.")
    else:
        st.dataframe(
            summary,
            width="stretch",
            hide_index=True,
        )

    st.caption(
        "Simulation-backed derivatives data. Production deployment "
        "will use an authorized derivatives data source."
    )

def _ifit_v085_hedging_page():
    st.markdown("## HEDGING INTELLIGENCE")
    st.caption("Portfolio exposure → hedge optimization → residual risk → recommended hedge")

    totals = st.session_state.get("ifit_portfolio_totals", None)

    def _pick(d, *keys, default=0.0):
        if not isinstance(d, dict):
            return float(default)
        for k in keys:
            if k in d:
                try:
                    return float(d[k])
                except Exception:
                    pass
        return float(default)

    if isinstance(totals, dict):
        exposure = PortfolioExposure(
            delta=_pick(totals, "Delta", "delta", "Total Delta"),
            gamma=_pick(totals, "Gamma", "gamma", "Total Gamma"),
            vega=_pick(totals, "Vega", "vega", "Total Vega"),
            theta=_pick(totals, "Theta", "theta", "Total Theta"),
        )
        source_label = "Portfolio/Risk engine"
    else:
        exposure = PortfolioExposure(
            delta=42.0,
            gamma=-0.65,
            vega=-18.0,
            theta=-7.0,
        )
        source_label = "Demo exposure"

    universe = build_live_hedge_universe(_get_dhan_live_service()) if st.session_state.get("ifit_data_mode") == "DHAN LIVE" else build_demo_hedge_universe()
    if st.session_state.get("ifit_data_mode") == "DHAN LIVE":
        st.success("HEDGE UNIVERSE: DHAN LIVE - Candidates: {}".format(len(universe)))
    singles = (
        optimize_single_hedges_v023(exposure, universe)
        if st.session_state.get("ifit_data_mode") == "DHAN LIVE"
        else optimize_single_hedges(exposure, universe)
    )
    combined = optimize_combined_hedges(exposure, universe)

    summary = hedge_summary(
        exposure,
        singles,
    )

    recommendation = hedge_recommendation(
        exposure,
        singles,
    )

    st.info(f"Exposure source: {source_label}")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Portfolio Delta",
        f"{exposure.delta:.2f}",
    )

    c2.metric(
        "Portfolio Gamma",
        f"{exposure.gamma:.4f}",
    )

    c3.metric(
        "Portfolio Vega",
        f"{exposure.vega:.2f}",
    )

    c4.metric(
        "Portfolio Theta",
        f"{exposure.theta:.2f}",
    )

    st.markdown("### Hedge Decision")

    r1, r2, r3 = st.columns(3)

    r1.metric(
        "Portfolio Risk Proxy",
        f"{summary['Portfolio Risk Proxy']:.2f}",
    )

    r2.metric(
        "Best Hedge Efficiency",
        f"{summary['Best Hedge Efficiency']:.2f}",
    )

    r3.metric(
        "Best Residual Risk",
        f"{summary['Best Residual Risk']:.2f}",
    )

    if recommendation:
        if not singles.empty:
            best_hedge = singles.iloc[0]

            instrument = best_hedge.get(
                                          "Instrument",
                                          "—",
        )

        quantity = best_hedge.get(
            "quantity",
            "—",
        )
    else:
                     instrument = "—"
                     quantity = "—"

    st.success(
            f"RECOMMENDED HEDGE: {instrument} × {quantity}"
        )

    st.caption(
            recommendation.get("reason", "")
        )

    st.markdown("### Best Single Hedges")

    if not singles.empty:
        st.dataframe(
            singles.sort_values(
                "Hedge Efficiency",
                ascending=False,
            ).head(10),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning(
            "No valid single-leg hedge candidates."
        )

    st.markdown("### Best Combined Hedges")

    if not combined.empty:
        st.dataframe(
            combined.sort_values(
                "Hedge Efficiency",
                ascending=False,
            ).head(10),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning(
            "No valid combined hedge candidates."
        )

    st.markdown("### Hedge Diagnostics")

    d1, d2, d3 = st.columns(3)

    d1.metric(
        "Best Hedge Cost",
        f"{summary['Best Hedge Cost']:.2f}",
    )

    d2.metric(
        "Recommended Direction",
        str(
            recommendation.get(
                "direction",
                "—",
            )
        ).upper(),
    )

    d3.metric(
        "Optimizer Efficiency",
        f"{recommendation.get('confidence', 0.0):.2f}",
    )

    st.caption(
        "Optimizer efficiency is a ranking metric, not a probability or statistical confidence."
    )

    # IFIT PAYOFF CHARTS V0.1
    render_payoff_charts(
        spot=float(spot),
        default_days=int(days),
    )

def _ifit_v085_mcx_page():
    subview = st.session_state.get("ifit_v082_subview", "Overview")

    st.markdown("## MCX / COMMODITIES INTELLIGENCE")
    st.caption(
        "Commodity price action, momentum, positioning, volatility, "
        "term structure, basis, roll and cross-commodity intelligence."
    )

    # =============================================================
    # BASE MCX UNIVERSE
    # =============================================================
    df = build_commodities_universe()

    # =============================================================
    # MCX FILTERS
    # =============================================================
    st.markdown("### MCX Filters")

    f1, f2, f3 = st.columns(3)

    with f1:
        selected_commodities = st.multiselect(
            "Commodities",
            available_commodities(df),
            default=[],
            key="ifit_mcx_commodities",
        )

    with f2:
        selected_signals = st.multiselect(
            "Signal",
            available_commodity_signals(),
            default=[],
            key="ifit_mcx_signals",
        )

    with f3:
        min_score = st.slider(
            "Minimum Commodity Score",
            0.0,
            100.0,
            0.0,
            1.0,
            key="ifit_mcx_min_score",
        )

    f4, f5, f6 = st.columns(3)

    with f4:
        min_momentum = st.slider(
            "Minimum Momentum Score",
            0.0,
            100.0,
            0.0,
            1.0,
            key="ifit_mcx_min_momentum",
        )

    with f5:
        min_volume_ratio = st.slider(
            "Minimum Volume Ratio",
            0.0,
            3.0,
            0.0,
            0.05,
            key="ifit_mcx_min_volume_ratio",
        )

    with f6:
        max_volatility = st.slider(
            "Max Volatility Percentile",
            0.0,
            100.0,
            100.0,
            1.0,
            key="ifit_mcx_max_volatility",
        )

    f7, f8, f9 = st.columns(3)

    with f7:
        min_oi_change = st.slider(
            "Minimum OI Change %",
            -100.0,
            100.0,
            -100.0,
            1.0,
            key="ifit_mcx_min_oi_change",
        )

    with f8:
        max_oi_change = st.slider(
            "Maximum OI Change %",
            -100.0,
            100.0,
            100.0,
            1.0,
            key="ifit_mcx_max_oi_change",
        )

    with f9:
        selected_term_structure = st.multiselect(
            "Term Structure",
            available_term_structures(),
            default=[],
            key="ifit_mcx_term_structure",
        )

    selected_roll = st.multiselect(
        "Roll Behaviour",
        available_roll_behaviours(),
        default=[],
        key="ifit_mcx_roll_behaviour",
    )

    # =============================================================
    # APPLY BASE MCX FILTERS
    # =============================================================
    filtered = apply_commodity_filters(
        df,
        commodities=selected_commodities,
        signals=selected_signals,
        min_score=min_score,
        min_momentum=min_momentum,
        min_volume_ratio=min_volume_ratio,
        min_oi_change=min_oi_change,
        max_oi_change=max_oi_change,
        max_volatility_percentile=max_volatility,
        term_structure=selected_term_structure,
        roll_behaviour=selected_roll,
    )

    ranked = rank_commodities(
        filtered,
        sort_by="Commodity Score",
        ascending=False,
    )

    summary = commodity_summary(ranked)

    # =============================================================
    # MCX SUBVIEW: COMMODITIES
    # =============================================================
    if subview == "Commodities":
        st.markdown("### Commodity Universe")

        st.dataframe(
            ranked[
                [
                    "Commodity",
                    "Unit",
                    "Price",
                    "Price Change %",
                    "Volume",
                    "Volume Ratio",
                    "Open Interest",
                    "OI Change %",
                    "Commodity Score",
                    "Signal",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
        return

    # =============================================================
    # MCX SUBVIEW: MOMENTUM
    # =============================================================
    if subview == "Momentum":
        st.markdown("### MCX Momentum Intelligence")

        momentum = ranked.sort_values(
            "Momentum Score",
            ascending=False,
        )

        if "Relative Performance %" in momentum.columns:
            momentum_columns = [
                "Commodity",
                "Price Change %",
                "Momentum 1M %",
                "Momentum Score",
                "Trend Strength",
                "Relative Performance %",
            ]
        else:
            momentum_columns = [
                "Commodity",
                "Price Change %",
                "Momentum 1M %",
                "Momentum Score",
                "Trend Strength",
                "Commodity Score",
            ]

        st.dataframe(
            momentum[momentum_columns],
            width="stretch",
            hide_index=True,
        )
        return

    # =============================================================
    # MCX SUBVIEW: POSITIONING
    # =============================================================
    if subview == "Positioning":
        st.markdown("### MCX Positioning Intelligence")

        positioning = ranked.sort_values(
            "Positioning Score",
            ascending=False,
        )

        st.dataframe(
            positioning[
                [
                    "Commodity",
                    "Price Change %",
                    "Open Interest",
                    "OI Change %",
                    "Volume",
                    "Volume Ratio",
                    "Positioning Score",
                    "Signal",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
        return

    # =============================================================
    # MCX SUBVIEW: VOLATILITY
    # =============================================================
    if subview == "Volatility":
        st.markdown("### MCX Volatility Intelligence")

        volatility = ranked.sort_values(
            "Volatility Percentile",
            ascending=False,
        )

        st.dataframe(
            volatility[
                [
                    "Commodity",
                    "Realized Volatility %",
                    "Volatility Percentile",
                    "Front IV %",
                    "Back IV %",
                    "Term Structure",
                    "Liquidity Score",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
        return

    # =============================================================
    # MCX SUBVIEW: TERM STRUCTURE
    # =============================================================
    if subview == "Term Structure":
        st.markdown("### MCX Term Structure Intelligence")

        term = ranked.sort_values(
            "Front IV %",
            ascending=False,
        )

        st.dataframe(
            term[
                [
                    "Commodity",
                    "Front IV %",
                    "Back IV %",
                    "Term Structure",
                    "Realized Volatility %",
                    "Volatility Percentile",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
        return

    # =============================================================
    # MCX SUBVIEW: BASIS & ROLL
    # =============================================================
    if subview == "Basis & Roll":
        st.markdown("### MCX Basis & Roll Intelligence")

        basis_roll = ranked.sort_values(
            "Basis %",
            ascending=False,
        )

        st.dataframe(
            basis_roll[
                [
                    "Commodity",
                    "Price",
                    "Basis %",
                    "Roll Behaviour",
                    "Front IV %",
                    "Back IV %",
                    "Open Interest",
                    "OI Change %",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
        return

    # =============================================================
    # MCX SUBVIEW: INTELLIGENCE V0.2
    # =============================================================
    if subview == "Intelligence":
        st.markdown("### MCX Intelligence V0.2")
        st.caption(
            "Cross-commodity intelligence combining momentum, "
            "price/OI positioning, IV vs realised volatility, "
            "term structure, basis, roll behaviour, liquidity "
            "and cross-asset context."
        )

        intelligence = build_mcx_intelligence()

        # Respect the commodity selection from the existing MCX filters.
        if selected_commodities:
            intelligence = apply_mcx_intelligence_filters(
                intelligence,
                commodities=selected_commodities,
            )

        intelligence = rank_mcx_intelligence(
            intelligence,
            ascending=False,
        )

        intel_summary = mcx_intelligence_summary(
            intelligence
        )

        # ---------------------------------------------------------
        # SUMMARY
        # ---------------------------------------------------------
        st.markdown("### Intelligence Summary")

        i1, i2, i3, i4, i5 = st.columns(5)

        with i1:
            st.metric(
                "Avg Intelligence",
                f'{intel_summary["Average Intelligence Score"]:.2f}',
            )

        with i2:
            st.metric(
                "Bullish",
                intel_summary["Bullish"]
                + intel_summary["Strong Bullish"],
            )

        with i3:
            st.metric(
                "Bearish",
                intel_summary["Bearish"]
                + intel_summary["Strong Bearish"],
            )

        with i4:
            st.metric(
                "IV-RV Spread",
                f'{intel_summary["Average IV-RV Spread"]:.2f}%',
            )

        with i5:
            st.metric(
                "MCX Signal",
                intel_summary["Signal"],
            )

        st.caption(
            f'Avg IV: {intel_summary["Average IV"]:.2f}% • '
            f'Avg RV: {intel_summary["Average RV"]:.2f}% • '
            f'Avg Momentum: {intel_summary["Average Momentum"]:.2f}% • '
            f'Avg OI Change: {intel_summary["Average OI Change"]:.2f}% • '
            f'Avg Liquidity: {intel_summary["Average Liquidity"]:.2f}'
        )

        # ---------------------------------------------------------
        # INTELLIGENCE MATRIX
        # ---------------------------------------------------------
        st.markdown("### Intelligence Matrix")

        if not intelligence.empty:

            intelligence_columns = [
                "Rank",
                "Commodity",
                "MCX Intelligence Score",
                "Signal",
                "Positioning",
                "Positioning Score",
                "Momentum 1M %",
                "Momentum Score",
                "IV %",
                "RV %",
                "IV-RV Spread %",
                "Volatility Regime",
                "Term Structure",
                "Term Structure Signal",
                "Basis %",
                "Basis Signal",
                "Roll Behaviour",
                "Roll Signal",
                "Liquidity Score",
                "Liquidity Regime",
                "Cross-Asset Score",
            ]

            intelligence_columns = [
                col
                for col in intelligence_columns
                if col in intelligence.columns
            ]

            st.dataframe(
                intelligence[intelligence_columns],
                width="stretch",
                hide_index=True,
            )

            # -----------------------------------------------------
            # POSITIONING + VOLATILITY
            # -----------------------------------------------------
            st.markdown("### Positioning & Volatility")

            p1, p2 = st.columns(2)

            with p1:
                st.markdown("**Positioning Intelligence**")

                positioning_view = intelligence[
                    [
                        "Commodity",
                        "Price Change %",
                        "OI Change %",
                        "Positioning",
                        "Positioning Score",
                        "MCX Intelligence Score",
                    ]
                ].sort_values(
                    "Positioning Score",
                    ascending=False,
                )

                st.dataframe(
                    positioning_view,
                    width="stretch",
                    hide_index=True,
                )

            with p2:
                st.markdown("**Volatility Intelligence**")

                volatility_view = intelligence[
                    [
                        "Commodity",
                        "IV %",
                        "RV %",
                        "IV-RV Spread %",
                        "Volatility Percentile",
                        "Volatility Regime",
                    ]
                ].sort_values(
                    "Volatility Percentile",
                    ascending=False,
                )

                st.dataframe(
                    volatility_view,
                    width="stretch",
                    hide_index=True,
                )

            # -----------------------------------------------------
            # STRUCTURE
            # -----------------------------------------------------
            st.markdown("### Term Structure, Basis & Roll")

            structure_view = intelligence[
                [
                    "Commodity",
                    "Term Structure",
                    "Term Structure Signal",
                    "Basis %",
                    "Basis Signal",
                    "Roll Behaviour",
                    "Roll Signal",
                ]
            ]

            st.dataframe(
                structure_view,
                width="stretch",
                hide_index=True,
            )

            # -----------------------------------------------------
            # TOP INTELLIGENCE THESIS
            # -----------------------------------------------------
            st.markdown("### Top MCX Intelligence")

            for _, row in intelligence.head(5).iterrows():
                st.markdown(
                    f"**{row['Commodity']} — "
                    f"{row['MCX Intelligence Score']:.2f} — "
                    f"{row['Signal']}**"
                )

                st.caption(
                    row["Thesis"]
                )

        else:
            st.warning(
                "No commodities match the MCX Intelligence universe."
            )

        return

    # =============================================================
    # DEFAULT MCX OVERVIEW
    # =============================================================
    st.markdown("### MCX Intelligence Summary")

    s1, s2, s3, s4, s5 = st.columns(5)

    s1.metric(
        "Commodities",
        summary["Commodities"],
    )

    s2.metric(
        "Bullish Signals",
        summary["Bullish Signals"],
    )

    s3.metric(
        "Bearish Signals",
        summary["Bearish Signals"],
    )

    s4.metric(
        "Avg Momentum",
        f'{summary["Average Momentum"]:.2f}%',
    )

    s5.metric(
        "Avg Commodity Score",
        f'{summary["Average Commodity Score"]:.2f}',
    )

    st.caption(
        f'Current MCX Signal: {summary["Signal"]} • '
        f'Avg Price Change: {summary["Average Price Change"]:.2f}% • '
        f'Avg Volatility: {summary["Average Volatility"]:.2f}% • '
        f'Avg OI Change: {summary["Average OI Change"]:.2f}%'
    )

    # =============================================================
    # RANKED TABLE
    # =============================================================
    st.markdown("### Ranked MCX Commodities")

    display_columns = [
        "Commodity",
        "Unit",
        "Price",
        "Price Change %",
        "Volume",
        "Volume Ratio",
        "Open Interest",
        "OI Change %",
        "Momentum 1M %",
        "Momentum Score",
        "Realized Volatility %",
        "Volatility Percentile",
        "Front IV %",
        "Back IV %",
        "Term Structure",
        "Basis %",
        "Roll Behaviour",
        "Trend Strength",
        "Positioning Score",
        "Liquidity Score",
        "Commodity Score",
        "Signal",
    ]

    display_columns = [
        col
        for col in display_columns
        if col in ranked.columns
    ]

    if not ranked.empty:
        st.dataframe(
            ranked[display_columns],
            width="stretch",
            hide_index=True,
        )
    else:
        st.warning(
            "No commodities match the current filters."
        )

    # =============================================================
    # INTELLIGENCE PANELS
    # =============================================================
    st.markdown("### Commodity Intelligence")

    p1, p2, p3 = st.columns(3)

    with p1:
        st.markdown("**Momentum Leaders**")

        if not ranked.empty:
            momentum = (
                ranked.sort_values(
                    "Momentum Score",
                    ascending=False,
                )[
                    [
                        "Commodity",
                        "Momentum Score",
                        "Momentum 1M %",
                    ]
                ]
                .head(5)
            )

            st.dataframe(
                momentum,
                width="stretch",
                hide_index=True,
            )

    with p2:
        st.markdown("**Positioning Leaders**")

        if not ranked.empty:
            positioning = (
                ranked.sort_values(
                    "Positioning Score",
                    ascending=False,
                )[
                    [
                        "Commodity",
                        "Positioning Score",
                        "OI Change %",
                    ]
                ]
                .head(5)
            )

            st.dataframe(
                positioning,
                width="stretch",
                hide_index=True,
            )

    with p3:
        st.markdown("**Volatility Watch**")

        if not ranked.empty:
            volatility = (
                ranked.sort_values(
                    "Volatility Percentile",
                    ascending=False,
                )[
                    [
                        "Commodity",
                        "Realized Volatility %",
                        "Volatility Percentile",
                        "Term Structure",
                    ]
                ]
                .head(5)
            )

            st.dataframe(
                volatility,
                width="stretch",
                hide_index=True,
            )

    # =============================================================
    # TERM STRUCTURE / ROLL
    # =============================================================
    st.markdown("### Term Structure & Roll")

    if not ranked.empty:
        term_roll = ranked[
            [
                "Commodity",
                "Front IV %",
                "Back IV %",
                "Term Structure",
                "Basis %",
                "Roll Behaviour",
            ]
        ]

        st.dataframe(
            term_roll,
            width="stretch",
            hide_index=True,
        )
def _ifit_v085_screener_page():
    _ifit_v081_header("Screener")

    subview = st.session_state.get(
        "ifit_v082_subview",
        "Equity",
    )

    # =========================================================
    # DERIVATIVES
    # =========================================================
    if subview == "Derivatives":
        _ifit_v085_derivatives_screener_page()
        return

    # =========================================================
    # MARKET
    # =========================================================
    if subview == "Market":

        st.markdown("## 🔎 IFIT Screener — Market")

        st.caption(
            "V0.8.5 • Market → Sector → Stock intelligence. "
            "Simulation data until an authorized market-data source is connected."
        )

        market_df = build_market_universe()

        st.markdown("### Market Summary")

        market_snapshot = market_summary(
            market_df
        )

        m1, m2, m3, m4, m5 = st.columns(5)

        m1.metric(
            "Universe",
            f"{market_snapshot['Stocks']}",
        )

        m2.metric(
            "Advancing",
            f"{market_snapshot['Advancing']}",
        )

        m3.metric(
            "Declining",
            f"{market_snapshot['Declining']}",
        )

        m4.metric(
            "Breadth",
            f"{market_snapshot['Breadth %']:.2f}%",
        )

        m5.metric(
            "Market Score",
            f"{market_snapshot['Market Score']:.2f}",
        )

        st.caption(
            f"{market_snapshot['Market']} • "
            f"Avg Change {market_snapshot['Average Change %']:+.2f}% • "
            f"RS {market_snapshot['Average Relative Strength']:.2f} • "
            f"Momentum {market_snapshot['Average Momentum']:.2f} • "
            f"Volume Ratio {market_snapshot['Average Volume Ratio']:.2f} • "
            f"Signal: {market_snapshot['Signal']}"
        )

        st.markdown("### Market Filters")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            selected_market_sector = st.selectbox(
                "Sector",
                available_sectors(market_df),
                key="ifit_v085_market_sector",
            )

        with c2:
            selected_market_signal = st.selectbox(
                "Signal",
                available_signals(),
                key="ifit_v085_market_signal",
            )

        with c3:
            market_min_score = st.number_input(
                "Minimum Market Score",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=5.0,
                key="ifit_v085_market_min_score",
            )

        with c4:
            market_min_rs = st.number_input(
                "Minimum Relative Strength",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=5.0,
                key="ifit_v085_market_min_rs",
            )

        c5, c6, c7 = st.columns(3)

        with c5:
            market_min_volume_ratio = st.number_input(
                "Minimum Volume Ratio",
                min_value=0.0,
                max_value=5.0,
                value=0.0,
                step=0.1,
                key="ifit_v085_market_min_volume_ratio",
            )

        with c6:
            market_min_momentum = st.number_input(
                "Minimum Momentum",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=5.0,
                key="ifit_v085_market_min_momentum",
            )

        with c7:
            market_max_volatility = st.number_input(
                "Maximum Volatility %",
                min_value=0.0,
                max_value=100.0,
                value=100.0,
                step=5.0,
                key="ifit_v085_market_max_volatility",
            )

        screened_market = apply_market_filters(
            market_df,
            sector=selected_market_sector,
            signal=selected_market_signal,
            min_score=market_min_score,
            min_relative_strength=market_min_rs,
            min_volume_ratio=market_min_volume_ratio,
            min_momentum=market_min_momentum,
            max_volatility=market_max_volatility,
        )

        ranked_market = rank_market(
            screened_market
        )

        st.markdown("### Screening Summary")

        s1, s2, s3, s4 = st.columns(4)

        s1.metric(
            "Matches",
            f"{len(screened_market)}",
        )

        s2.metric(
            "Top Market Score",
            (
                f"{ranked_market['Market Score'].max():.2f}"
                if not ranked_market.empty
                else "—"
            ),
        )

        s3.metric(
            "Avg Score",
            (
                f"{ranked_market['Market Score'].mean():.2f}"
                if not ranked_market.empty
                else "—"
            ),
        )

        s4.metric(
            "Leaders",
            f"{(screened_market['Signal'] == 'LEADER').sum()}",
        )

        st.markdown("### Sector Intelligence")

        market_sector_df = market_sector_summary(
            screened_market
        )

        if market_sector_df.empty:
            st.info(
                "No sector statistics available for the current screen."
            )
        else:
            st.dataframe(
                market_sector_df,
                width="stretch",
                hide_index=True,
            )

        st.markdown("### Ranked Market Results")

        market_display_columns = [
            "Market",
            "Sector",
            "Symbol",
            "Price",
            "Price Change %",
            "Relative Strength",
            "Volume",
            "Volume Ratio",
            "Momentum",
            "Volatility %",
            "52W High Distance %",
            "52W Low Distance %",
            "Sector Strength",
            "Breadth Score",
            "Market Score",
            "Signal",
        ]

        if ranked_market.empty:
            st.warning(
                "No stocks match the selected market screening criteria."
            )
        else:
            st.dataframe(
                ranked_market[
                    market_display_columns
                ],
                width="stretch",
                hide_index=True,
            )

        st.caption(
            "Architecture note: Market Score is a transparent prototype score. "
            "Production deployment requires normalized historical market data, "
            "sector/index definitions, corporate actions and authorized live data."
        )

        return

    # =========================================================
    # ORDER FLOW
    # =========================================================
    if subview == "Order Flow":

        from engines.orderflow_screener_engine import (
            build_orderflow_universe,
            apply_orderflow_filters,
            rank_orderflow,
            orderflow_summary,
            available_orderflow_signals,
        )

        st.markdown(
            "## 🔎 IFIT Screener — Order Flow"
        )

        st.caption(
            "V0.8.5 • CVD • Delta • Imbalance • Absorption • "
            "Volume Profile • POC • Order Flow Intelligence"
        )

        orderflow_df = (
            build_orderflow_universe()
        )

        st.markdown(
            "### Order Flow Filters"
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            selected_orderflow_signal = st.selectbox(
                "Signal",
                available_orderflow_signals(),
                key="ifit_v085_orderflow_signal",
            )

        with c2:
            orderflow_min_score = st.number_input(
                "Minimum Order Flow Score",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=5.0,
                key="ifit_v085_orderflow_min_score",
            )

        with c3:
            orderflow_min_absorption = st.number_input(
                "Minimum Absorption",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=5.0,
                key="ifit_v085_orderflow_min_absorption",
            )

        c4, c5, c6 = st.columns(3)

        with c4:
            orderflow_min_delta = st.number_input(
                "Minimum Delta %",
                min_value=-100.0,
                max_value=100.0,
                value=-100.0,
                step=5.0,
                key="ifit_v085_orderflow_min_delta",
            )

        with c5:
            orderflow_max_delta = st.number_input(
                "Maximum Delta %",
                min_value=-100.0,
                max_value=100.0,
                value=100.0,
                step=5.0,
                key="ifit_v085_orderflow_max_delta",
            )

        with c6:
            orderflow_min_imbalance = st.number_input(
                "Minimum Imbalance %",
                min_value=-100.0,
                max_value=100.0,
                value=-100.0,
                step=5.0,
                key="ifit_v085_orderflow_min_imbalance",
            )

        c7, c8 = st.columns(2)

        with c7:
            orderflow_max_imbalance = st.number_input(
                "Maximum Imbalance %",
                min_value=-100.0,
                max_value=100.0,
                value=100.0,
                step=5.0,
                key="ifit_v085_orderflow_max_imbalance",
            )

        with c8:
            orderflow_max_poc_distance = st.number_input(
                "Maximum POC Distance %",
                min_value=0.0,
                max_value=100.0,
                value=100.0,
                step=0.5,
                key="ifit_v085_orderflow_max_poc_distance",
            )

        screened_orderflow = (
            apply_orderflow_filters(
                orderflow_df,
                signal=selected_orderflow_signal,
                min_score=orderflow_min_score,
                min_delta_pct=orderflow_min_delta,
                max_delta_pct=orderflow_max_delta,
                min_imbalance=orderflow_min_imbalance,
                max_imbalance=orderflow_max_imbalance,
                min_absorption=orderflow_min_absorption,
                max_poc_distance=orderflow_max_poc_distance,
            )
        )

        ranked_orderflow = rank_orderflow(
            screened_orderflow
        )

        orderflow_snapshot = (
            orderflow_summary(
                screened_orderflow
            )
        )

        st.markdown(
            "### Order Flow Summary"
        )

        s1, s2, s3, s4, s5 = st.columns(5)

        s1.metric(
            "Matches",
            orderflow_snapshot["Stocks"],
        )

        s2.metric(
            "Buy Signals",
            orderflow_snapshot["Buy Signals"],
        )

        s3.metric(
            "Sell Signals",
            orderflow_snapshot["Sell Signals"],
        )

        s4.metric(
            "Avg Delta %",
            f'{orderflow_snapshot["Average Delta %"]:.2f}',
        )

        s5.metric(
            "Order Flow Score",
            f'{orderflow_snapshot["Average Order Flow Score"]:.2f}',
        )

        st.caption(
            f'Avg Imbalance '
            f'{orderflow_snapshot["Average Imbalance %"]:+.2f}% • '
            f'Avg Absorption '
            f'{orderflow_snapshot["Average Absorption"]:.2f} • '
            f'Avg CVD Change '
            f'{orderflow_snapshot["Average CVD Change %"]:+.2f}% • '
            f'Signal: {orderflow_snapshot["Signal"]}'
        )

        st.markdown(
            "### Ranked Order Flow Results"
        )

        orderflow_display_columns = [
            "Market",
            "Symbol",
            "Price",
            "Price Change %",
            "Volume",
            "CVD",
            "CVD Change %",
            "Delta",
            "Delta %",
            "Buy Volume",
            "Sell Volume",
            "Imbalance %",
            "Absorption Score",
            "Volume Profile Score",
            "POC Distance %",
            "Buy Pressure",
            "Sell Pressure",
            "Order Flow Score",
            "Signal",
        ]

        if ranked_orderflow.empty:
            st.warning(
                "No symbols match the selected order-flow criteria."
            )
        else:
            st.dataframe(
                ranked_orderflow[
                    orderflow_display_columns
                ],
                width="stretch",
                hide_index=True,
            )

        st.caption(
            "Architecture note: Order Flow metrics are currently "
            "simulation-backed. Production deployment requires "
            "authorized tick/order-flow data and historical normalization."
        )

        return

    # =========================================================
    # QUANT
    # =========================================================
    if subview == "Quant":

        from engines.quant_screener_engine import (
            build_quant_universe,
            apply_quant_filters,
            rank_quant,
            quant_summary,
            available_quant_signals,
            available_mean_reversion_states,
        )

        st.markdown(
            "## 🔎 IFIT Screener — Quant"
        )

        st.caption(
            "V0.8.5 • Momentum • Mean Reversion • Volatility • "
            "Correlation • Statistics • Trend • Relative Performance"
        )

        quant_df = build_quant_universe()

        st.markdown(
            "### Quant Filters"
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            selected_quant_signal = st.selectbox(
                "Signal",
                available_quant_signals(),
                key="ifit_v085_quant_signal",
            )

        with c2:
            quant_min_score = st.number_input(
                "Minimum Quant Score",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=5.0,
                key="ifit_v085_quant_min_score",
            )

        with c3:
            quant_min_momentum = st.number_input(
                "Minimum Momentum Score",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=5.0,
                key="ifit_v085_quant_min_momentum",
            )

        c4, c5, c6 = st.columns(3)

        with c4:
            quant_min_trend = st.number_input(
                "Minimum Trend Strength",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=5.0,
                key="ifit_v085_quant_min_trend",
            )

        with c5:
            quant_min_statistical = st.number_input(
                "Minimum Statistical Score",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=5.0,
                key="ifit_v085_quant_min_statistical",
            )

        with c6:
            quant_min_relative = st.number_input(
                "Minimum Relative Performance %",
                min_value=-100.0,
                max_value=100.0,
                value=-100.0,
                step=5.0,
                key="ifit_v085_quant_min_relative",
            )

        c7, c8, c9 = st.columns(3)

        with c7:
            quant_max_volatility = st.number_input(
                "Maximum Volatility Percentile",
                min_value=0.0,
                max_value=100.0,
                value=100.0,
                step=5.0,
                key="ifit_v085_quant_max_volatility",
            )

        with c8:
            quant_min_correlation = st.number_input(
                "Minimum Correlation",
                min_value=-1.0,
                max_value=1.0,
                value=-1.0,
                step=0.05,
                key="ifit_v085_quant_min_correlation",
            )

        with c9:
            quant_max_correlation = st.number_input(
                "Maximum Correlation",
                min_value=-1.0,
                max_value=1.0,
                value=1.0,
                step=0.05,
                key="ifit_v085_quant_max_correlation",
            )

        selected_mr_state = st.selectbox(
            "Mean Reversion State",
            available_mean_reversion_states(),
            key="ifit_v085_quant_mr_state",
        )

        screened_quant = apply_quant_filters(
            quant_df,
            signal=selected_quant_signal,
            min_quant_score=quant_min_score,
            min_momentum_score=quant_min_momentum,
            min_trend_strength=quant_min_trend,
            min_statistical_score=quant_min_statistical,
            min_relative_performance=quant_min_relative,
            max_volatility_percentile=quant_max_volatility,
            min_correlation=quant_min_correlation,
            max_correlation=quant_max_correlation,
            mean_reversion_state=selected_mr_state,
        )

        ranked_quant = rank_quant(
            screened_quant
        )

        quant_snapshot = quant_summary(
            screened_quant
        )

        st.markdown(
            "### Quant Summary"
        )

        s1, s2, s3, s4, s5 = st.columns(5)

        s1.metric(
            "Matches",
            quant_snapshot["Stocks"],
        )

        s2.metric(
            "Bullish Signals",
            quant_snapshot["Bullish Signals"],
        )

        s3.metric(
            "Bearish Signals",
            quant_snapshot["Bearish Signals"],
        )

        s4.metric(
            "Avg Momentum",
            f'{quant_snapshot["Average Momentum"]:.2f}',
        )

        s5.metric(
            "Quant Score",
            f'{quant_snapshot["Average Quant Score"]:.2f}',
        )

        st.caption(
            f'Avg Z-Score '
            f'{quant_snapshot["Average Z-Score"]:+.2f} • '
            f'Avg Volatility '
            f'{quant_snapshot["Average Volatility"]:.2f}% • '
            f'Avg Correlation '
            f'{quant_snapshot["Average Correlation"]:.3f} • '
            f'Signal: {quant_snapshot["Signal"]}'
        )

        st.markdown(
            "### Ranked Quant Results"
        )

        quant_display_columns = [
            "Market",
            "Symbol",
            "Price",
            "Price Change %",
            "Momentum 1M %",
            "Momentum 3M %",
            "Momentum Score",
            "Z-Score",
            "Mean Reversion Score",
            "Mean Reversion State",
            "Realized Volatility %",
            "Volatility Percentile",
            "Correlation to Market",
            "Correlation Score",
            "Trend Strength",
            "Relative Performance %",
            "Relative Performance Score",
            "Statistical Score",
            "Quant Score",
            "Signal",
        ]

        if ranked_quant.empty:
            st.warning(
                "No symbols match the selected quantitative criteria."
            )
        else:
            st.dataframe(
                ranked_quant[
                    quant_display_columns
                ],
                width="stretch",
                hide_index=True,
            )

        st.caption(
            "Architecture note: Quant metrics are currently "
            "simulation-backed. Production deployment requires "
            "normalized historical price series, benchmark data, "
            "corporate actions and authorized live market data."
        )

        return
    # =========================================================
    # DECISION INTELLIGENCE
    # =========================================================
    if subview == "Decision Intelligence":


        from engines.derivatives_screener_engine import (
            build_derivatives_universe,
            rank_derivatives,
            signal_summary,
        )

        from engines.orderflow_screener_engine import (
            build_orderflow_universe,
            rank_orderflow,
            orderflow_summary,
        )

        from engines.quant_screener_engine import (
            build_quant_universe,
            rank_quant,
            quant_summary,
        )

        from engines.decision_intelligence_engine import (
            build_decision_snapshot,
        )
        from engines.footprint_decision_fusion_engine import (
            fuse_decision_snapshot,
            build_footprint_decision_for_fusion,
            footprint_fusion_display,
        )

        st.markdown("## 🧠 IFIT Decision Intelligence")

        st.caption(
            "V0.8.5 • Market Regime • Derivatives • Order Flow • "
            "Quant • Explainable Decision Framework"
        )

        # =====================================================
        # BUILD MARKET INTELLIGENCE
        # =====================================================

        market_df = build_market_universe()

        ranked_market = rank_market(
            market_df
        )

        market_snapshot = market_summary(
            ranked_market
        )

        # =====================================================
        # BUILD DERIVATIVES INTELLIGENCE
        # =====================================================

        derivatives_df = build_derivatives_universe()

        ranked_derivatives = rank_derivatives(
            derivatives_df
        )

        derivatives_signal_df = signal_summary(
            ranked_derivatives
        )

        if derivatives_signal_df.empty:

            derivatives_snapshot = {
                "Signal": "NEUTRAL",
                "Average OI Change %": 0.0,
                "Average Liquidity": 0.0,
                "Contracts": 0,
            }

        else:

            total_contracts = float(
                derivatives_signal_df["Contracts"].sum()
            )

            if total_contracts > 0:

                avg_oi_change = float(
                    (
                        derivatives_signal_df[
                            "Average OI Change %"
                        ]
                        *
                        derivatives_signal_df[
                            "Contracts"
                        ]
                    ).sum()
                    / total_contracts
                )

                avg_liquidity = float(
                    (
                        derivatives_signal_df[
                            "Average Liquidity"
                        ]
                        *
                        derivatives_signal_df[
                            "Contracts"
                        ]
                    ).sum()
                    / total_contracts
                )

            else:

                avg_oi_change = 0.0
                avg_liquidity = 0.0

            derivatives_snapshot = {
                "Signal": str(
                    derivatives_signal_df.iloc[0]["Signal"]
                ),
                "Average OI Change %": avg_oi_change,
                "Average Liquidity": avg_liquidity,
                "Contracts": int(total_contracts),
            }

        # =====================================================
        # BUILD ORDER FLOW INTELLIGENCE
        # =====================================================

        orderflow_df = build_orderflow_universe()

        ranked_orderflow = rank_orderflow(
            orderflow_df
        )

        orderflow_snapshot = orderflow_summary(
            ranked_orderflow
        )

        # =====================================================
        # BUILD QUANT INTELLIGENCE
        # =====================================================

        quant_df = build_quant_universe()

        ranked_quant = rank_quant(
            quant_df
        )

        quant_snapshot = quant_summary(
            ranked_quant
        )

        # =====================================================
        # DECISION ENGINE
        # =====================================================

        decision = build_decision_snapshot(
            market_summary=market_snapshot,
            derivatives_summary=derivatives_snapshot,
            orderflow_summary=orderflow_snapshot,
            quant_summary=quant_snapshot,
        )
        # V0.6 Multi-Engine Decision Fusion
        # Native Footprint build: Decision Intelligence no longer depends on
        # first visiting CHT -> Order Flow Footprint in the same session.
        try:
            footprint_decision = build_footprint_decision_for_fusion(
                periods=60,
                levels=24,
            )
            st.session_state["ifit_footprint_decision_intelligence"] = footprint_decision
        except Exception as exc:
            footprint_decision = st.session_state.get(
                "ifit_footprint_decision_intelligence"
            )
            if footprint_decision is None:
                st.warning(f"Footprint fusion input unavailable: {exc}")

        decision = fuse_decision_snapshot(
            decision,
            footprint_decision=footprint_decision,
        )

        # =====================================================
        # SAFE OUTPUT NORMALIZATION
        # =====================================================

        def _di_pick(data, *keys, default=None):

            if not isinstance(data, dict):
                return default

            # Exact match
            for key in keys:

                if key in data:
                    return data[key]

            # Case-insensitive match
            lowered = {
                str(k).lower(): v
                for k, v in data.items()
            }

            for key in keys:

                if str(key).lower() in lowered:
                    return lowered[
                        str(key).lower()
                    ]

            return default

        # -----------------------------------------------------
        # Normalize primary decision fields
        # -----------------------------------------------------

        decision_value = _di_pick(
            decision,
            "Decision",
            "decision",
            "Direction",
            "direction",
            default="NEUTRAL",
        )

        score_value = _di_pick(
            decision,
            "Score",
            "score",
            "Decision Score",
            "decision_score",
            default=0.0,
        )

        confidence_value = _di_pick(
            decision,
            "Confidence",
            "confidence",
            "Decision Confidence",
            "decision_confidence",
            default=0.0,
        )

        regime_value = _di_pick(
            decision,
            "Regime",
            "regime",
            "Market Regime",
            "market_regime",
            default="UNKNOWN",
        )

        risk_value = _di_pick(
            decision,
            "Risk",
            "risk",
            "Risk Level",
            "risk_level",
            "Risk Regime",
            "risk_regime",
            default="UNKNOWN",
        )

        thesis_value = _di_pick(
            decision,
            "Thesis",
            "thesis",
            "Decision Thesis",
            "decision_thesis",
            default="No decision thesis available.",
        )

        framework_value = _di_pick(
            decision,
            "Framework",
            "framework",
            "Preferred Framework",
            "preferred_framework",
            default="No strategy framework available.",
        )

        direction_value = _di_pick(
            decision,
            "Direction",
            "direction",
            "Decision",
            "decision",
            default="NEUTRAL",
        )

        components = _di_pick(
            decision,
            "Components",
            "components",
            "Component Scores",
            "component_scores",
            default={},
        )

        if not isinstance(components, dict):
            components = {}

        def _di_component(name):

            if name in components:
                try:
                    return float(
                        components[name]
                    )
                except Exception:
                    return 0.0

            lowered = {
                str(k).lower(): v
                for k, v in components.items()
            }

            value = lowered.get(
                name.lower(),
                0.0,
            )

            try:
                return float(value)
            except Exception:
                return 0.0

        try:
            score_value = float(score_value)
        except Exception:
            score_value = 0.0

        try:
            confidence_value = float(
                confidence_value
            )
        except Exception:
            confidence_value = 0.0

        # =====================================================
        # PRIMARY DECISION
        # =====================================================

        st.markdown(
            "### IFIT Market Decision"
        )

        d1, d2, d3, d4, d5 = st.columns(5)

        d1.metric(
            "Decision",
            str(decision_value),
        )

        d2.metric(
            "Score",
            f"{score_value:.2f}",
        )

        d3.metric(
            "Confidence",
            f"{confidence_value:.2f}%",
        )

        d4.metric(
            "Regime",
            str(regime_value),
        )

        d5.metric(
            "Risk",
            str(risk_value),
        )

        # =====================================================
        # DECISION THESIS
        # =====================================================

        st.markdown(
            "### Decision Thesis"
        )

        st.info(
            str(thesis_value)
        )

        # =====================================================
        # INTELLIGENCE COMPONENTS
        # =====================================================

        st.markdown(
            "### Intelligence Components • V0.6 Multi-Engine Fusion"
        )

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Market",
            f'{_di_component("Market"):.2f}',
        )

        c2.metric(
            "Derivatives",
            f'{_di_component("Derivatives"):.2f}',
        )

        c3.metric(
            "Order Flow",
            f'{_di_component("Order Flow"):.2f}',
        )

        c4.metric(
            "Quant",
            f'{_di_component("Quant"):.2f}',
        )

        c5.metric(
            "Footprint",
            f'{_di_component("Footprint"):.2f}',
        )

        st.markdown("### V0.6 Decision Fusion")

        fp_display = footprint_fusion_display(footprint_decision or {})
        f1, f2, f3, f4 = st.columns(4)

        f1.metric("Fused Decision Score", f'{float(decision.get("Decision Score", 0)):.2f}')
        f2.metric("Fusion Direction", str(decision.get("Direction", "NEUTRAL")))
        f3.metric("Footprint State", str(fp_display["Auction State"]))
        f4.metric("Footprint Confidence", f'{fp_display["Confidence"]:.1f}')

        st.info(
            f'Footprint Thesis: {fp_display["Thesis"]}'
        )

        fp_detail = pd.DataFrame(
            [
                ["Auction State", fp_display["Auction State"]],
                ["Footprint Signal", fp_display["Signal"]],
                ["Footprint Confidence", fp_display["Confidence"]],
                ["POC Migration", fp_display["POC Migration"]],
                ["Delta Flip", fp_display["Delta Flip"]],
                ["CVD Divergence", fp_display["CVD Divergence"]],
                ["Failed Auction", fp_display["Failed Auction"]],
                ["Confirmation", fp_display["Confirmation"]],
                ["Strategy Context", fp_display["Strategy Context"]],
                ["Risk / Invalidation", fp_display["Risk / Invalidation"]],
            ],
            columns=["Footprint Fusion Field", "Value"],
        )
        st.dataframe(
            fp_detail,
            width="stretch",
            hide_index=True,
        )

        # =====================================================
        # PREFERRED FRAMEWORK
        # =====================================================

        st.markdown(
            "### Preferred Strategy Framework"
        )

        st.success(
            str(framework_value)
        )

        # =====================================================
        # DIRECTION / REGIME
        # =====================================================

        r1, r2 = st.columns(2)

        with r1:

            st.markdown(
                "#### Direction"
            )

            st.write(
                str(direction_value)
            )

        with r2:

            st.markdown(
                "#### Market Regime"
            )

            st.write(
                str(regime_value)
            )

        # =====================================================
        # EVIDENCE STACK
        # =====================================================

        st.markdown(
            "### Evidence Stack"
        )

        evidence_df = pd.DataFrame(
            {
                "Layer": [
                    "Market",
                    "Derivatives",
                    "Order Flow",
                    "Quant",
                    "Footprint",
                ],
                "Score": [
                    _di_component("Market"),
                    _di_component("Derivatives"),
                    _di_component("Order Flow"),
                    _di_component("Quant"),
                    _di_component("Footprint"),
                ],
            }
        )

        st.dataframe(
            evidence_df,
            width="stretch",
            hide_index=True,
        )

        # =====================================================
        # RAW ENGINE OUTPUT
        # =====================================================

        with st.expander(
            "Decision Engine Diagnostics"
        ):

            st.write(
                decision
            )

        st.caption(
            "Decision Intelligence combines Market, Derivatives, "
            "Order Flow and Quant evidence into an explainable "
            "decision framework. Current inputs are simulation-backed. "
            "This is research intelligence, not an automatic trading system."
        )

        return
    # =========================================================
    # EQUITY
    # =========================================================
    if subview != "Equity":
        st.markdown(
            f"## 🔎 IFIT Screener — {subview}"
        )

        st.info(
            f"V0.8.5 {subview} Screener workspace is connected "
            "to the navigation engine. The screening engine for "
            "this layer will be implemented next."
        )

        return

    st.markdown(
        "## 🔎 IFIT Screener"
    )

    st.caption(
        "V0.8.5 • Multi-factor equity screening engine. "
        "Simulation data until an authorized market-data/fundamental source is connected."
    )

    df = build_equity_universe()

    # ---------------------------------------------------------
    # Screener Controls
    # ---------------------------------------------------------
    st.markdown("### Screener Filters")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        sector_options = [
            "All"
        ] + sorted(
            df["Sector"].unique().tolist()
        )

        selected_sector = st.selectbox(
            "Sector",
            sector_options,
            key="ifit_v085_sector",
        )

    with c2:
        max_pe = st.number_input(
            "Maximum P/E",
            min_value=0.0,
            max_value=100.0,
            value=100.0,
            step=1.0,
            key="ifit_v085_max_pe",
        )

    with c3:
        min_roe = st.number_input(
            "Minimum ROE %",
            min_value=-50.0,
            max_value=50.0,
            value=-50.0,
            step=1.0,
            key="ifit_v085_min_roe",
        )

    with c4:
        max_de = st.number_input(
            "Maximum Debt/Equity",
            min_value=0.0,
            max_value=10.0,
            value=10.0,
            step=0.1,
            key="ifit_v085_max_de",
        )

    c5, c6, c7, c8 = st.columns(4)

    with c5:
        min_eps = st.number_input(
            "Minimum EPS Growth %",
            min_value=-50.0,
            max_value=100.0,
            value=-50.0,
            step=1.0,
            key="ifit_v085_min_eps",
        )

    with c6:
        min_momentum = st.number_input(
            "Minimum Momentum 1M %",
            min_value=-50.0,
            max_value=100.0,
            value=-50.0,
            step=1.0,
            key="ifit_v085_min_momentum",
        )

    with c7:
        min_rs = st.number_input(
            "Minimum Relative Strength",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=5.0,
            key="ifit_v085_min_rs",
        )

    with c8:
        trend_options = [
            "All",
            "BULLISH",
            "BEARISH",
        ]

        selected_trend = st.selectbox(
            "EMA Trend",
            trend_options,
            key="ifit_v085_trend",
        )

    filters = {
        "max_pe": (
            None
            if max_pe >= 100
            else max_pe
        ),
        "min_roe": (
            None
            if min_roe <= -50
            else min_roe
        ),
        "max_debt_equity": (
            None
            if max_de >= 10
            else max_de
        ),
        "min_eps_growth": (
            None
            if min_eps <= -50
            else min_eps
        ),
        "min_momentum": (
            None
            if min_momentum <= -50
            else min_momentum
        ),
        "min_relative_strength": (
            None
            if min_rs <= 0
            else min_rs
        ),
    }

    if selected_sector != "All":
        filters["sector"] = selected_sector

    if selected_trend != "All":
        filters["ema_trend"] = selected_trend

    screened = apply_filters(
        df,
        filters,
    )

    ranked = rank_equities(
        screened
    )

    # ---------------------------------------------------------
    # Summary Metrics
    # ---------------------------------------------------------
    st.markdown(
        "### Screening Summary"
    )

    m1, m2, m3, m4, m5 = st.columns(5)

    m1.metric(
        "Universe",
        f"{len(df)}",
    )

    m2.metric(
        "Matches",
        f"{len(screened)}",
    )

    m3.metric(
        "Top Equity Score",
        (
            f"{ranked['Equity Score'].max():.1f}"
            if not ranked.empty
            else "—"
        ),
    )

    m4.metric(
        "Avg Score",
        (
            f"{ranked['Equity Score'].mean():.1f}"
            if not ranked.empty
            else "—"
        ),
    )

    m5.metric(
        "Bullish EMA",
        f"{(screened['EMA Trend'] == 'BULLISH').sum()}",
    )

    # ---------------------------------------------------------
    # Ranked Results
    # ---------------------------------------------------------
    st.markdown(
        "### Ranked Equity Results"
    )

    display_columns = [
        "Symbol",
        "Sector",
        "Price",
        "Market Cap (Cr)",
        "P/E",
        "ROE %",
        "ROCE %",
        "Debt/Equity",
        "Revenue Growth %",
        "EPS Growth %",
        "FCF Yield %",
        "Delivery %",
        "RSI 14",
        "EMA Trend",
        "Momentum 1M %",
        "Volatility %",
        "Relative Strength",
        "Equity Score",
    ]

    if ranked.empty:
        st.warning(
            "No equities match the selected screening criteria."
        )
    else:
        st.dataframe(
            ranked[display_columns],
            width="stretch",
            hide_index=True,
        )

    # ---------------------------------------------------------
    # Sector Intelligence
    # ---------------------------------------------------------
    st.markdown(
        "### Sector Intelligence"
    )

    sector_df = sector_summary(
        screened
    )

    if sector_df.empty:
        st.info(
            "No sector statistics available for the current screen."
        )
    else:
        st.dataframe(
            sector_df,
            width="stretch",
            hide_index=True,
        )

    st.caption(
        "Architecture note: Equity Score is a transparent prototype score. "
        "Production deployment requires normalized historical fundamentals, "
        "peer groups, corporate actions and authorized live data."
    )

def _ifit_v081_portfolio_page():
    _ifit_v081_header("Portfolio")

    portfolio_view = st.radio(
        "Portfolio Workspace",
        [
            "Portfolio",
            "Hedging Intelligence",
        ],
        horizontal=True,
        key="ifit_portfolio_workspace_view",
    )

    if portfolio_view == "Hedging Intelligence":
        _ifit_v085_hedging_page()
        return

    st.markdown("## Portfolio")
    st.caption(
        "Portfolio workspace. The existing higher-order Greek and stress framework is surfaced here as the terminal portfolio layer."
    )
    _ifit_v075_render()


def _ifit_v081_risk_page():
    _ifit_v081_header("Risk Engine")
    st.markdown("## Risk Engine")
    st.caption("Terminal-level risk layer. Diagnostic research output — not statistical VaR, a capital requirement or an automatic trading instruction.")
    _ifit_v074_render()


def _ifit_v081_ai_page():
    _ifit_v081_header("AI Intelligence")
    st.markdown("## AI Intelligence")
    st.caption("V0.8.2 establishes the AI workspace and the grounding contract. The production AI layer will consume synchronized IFIT engine outputs rather than inventing market facts.")
    query = st.text_input("Ask IFIT", "Why is the current market regime risky?", key="ifit_v081_ai_query")
    x = _ifit_v080_cached(spot, days, atm_iv, hv30, flow_levels, imbalance_ratio)
    if st.button("Analyze with IFIT", key="ifit_v081_ai_button"):
        st.markdown("### IFIT Grounded Snapshot")
        st.info(
            f'**Question:** {query}\n\n'
            f'**Market:** {x["market"]["regime"]} • {x["market"]["score"]:.1f}/100\n\n'
            f'**Regime:** {x["regime"]["regime"]} • confidence {x["regime"]["confidence"]:.1f}/100\n\n'
            f'**Signal:** {x["signal"]["direction"]} • conviction {x["signal"]["conviction"]:.1f}/100\n\n'
            f'**Risk:** {x["risk"]["regime"]} • {x["risk"]["overall_score"]:.1f}/100\n\n'
            f'**Execution:** {x["liquidity"]["regime"]} • {x["liquidity"]["score"]:.1f}/100\n\n'
            f'**IFIT Score:** {x["overall_score"]:.1f}/100'
        )
        st.caption("Prototype grounding only. No external AI call, order placement or investment recommendation is performed by this V0.8.1 workspace.")


def _ifit_v081_global_layers(x):
    st.markdown("---")
    st.markdown("### Terminal Intelligence Layers")
    a,b = st.columns(2)
    with a:
        st.markdown("**RISK ENGINE**")
        st.metric("Risk", f'{x["risk"]["overall_score"]:.1f}/100', x["risk"]["regime"])
        st.caption("Cross-engine risk remains available globally from the terminal navigation.")
    with b:
        st.markdown("**AI INTELLIGENCE**")
        st.metric("Executive Confidence", f'{x["executive_confidence"]:.1f}/100')
        st.caption("AI workspace is grounded in the synchronized IFIT snapshot architecture.")


# ---------- V0.8.2 Terminal Navigation & Workspace Engine ----------
def _ifit_v082_sync_state():
    defaults = {
        "ifit_v082_module": "Command Center",
        "ifit_v082_subview": "Executive Overview",
        "ifit_v082_instrument": "NIFTY 50",
        "ifit_v082_timeframe": "Intraday",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _ifit_v082_terminal_header(ctx):
    st.markdown(
        '<div class="ifit-terminal-bar">'
        '<div><span class="ifit-logo">🇮🇳 <span class="ifit-logo-badge">IFIT</span></span><span class="ifit-terminal-name">TERMINAL</span></div>'
        f'<div class="ifit-active-pill"><span class="ifit-live-dot"></span>{workspace_code(ctx.module)} • {ctx.module.upper()} • {ctx.subview.upper()}</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="ifit-nav-note"><b>{ctx.instrument}</b> • {ctx.timeframe} • '
        f'{ctx.data_mode} • {workspace_description(ctx.module)}</div>',
        unsafe_allow_html=True,
    )


_ifit_v082_sync_state()

# Primary terminal navigation lives in the sidebar; the compact top rail mirrors the active workspace.
with st.sidebar:
    st.markdown("## ⚡ IFIT TERMINAL")
    st.caption("V0.8.2 • Navigation & Workspace Engine")
    module = st.selectbox(
        "Workspace",
        workspace_names(),
        index=workspace_names().index(st.session_state["ifit_v082_module"]),
        )
    if module != st.session_state["ifit_v082_module"]:
        st.session_state["ifit_v082_module"] = module
        st.session_state["ifit_v082_subview"] = subviews_for(module)[0]
        st.rerun()

    subviews = subviews_for(module)
    subview = st.radio(
        "Subview",
        subviews,
        index=subviews.index(st.session_state["ifit_v082_subview"]) if st.session_state["ifit_v082_subview"] in subviews else 0,
        )
    st.session_state["ifit_v082_subview"] = subview
    st.divider()
    instrument_options = [
        "NIFTY 50", "BANK NIFTY", "SENSEX",
        "EURUSD", "GBPUSD", "USDJPY", "USDINR", "EURINR",
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    ]
    current_instrument = st.session_state.get("ifit_v082_instrument", "NIFTY 50")
    if current_instrument not in instrument_options:
        current_instrument = "NIFTY 50"
    instrument = st.selectbox(
        "Instrument Context",
        instrument_options,
        index=instrument_options.index(current_instrument),
        key="ifit_v082_instrument_select",
    )
    timeframe = st.selectbox(
        "Timeframe",
        ["Intraday", "5 min", "15 min", "1 hour", "Daily"],
        index=["Intraday", "5 min", "15 min", "1 hour", "Daily"].index(st.session_state["ifit_v082_timeframe"]),
        key="ifit_v082_timeframe_select",
    )
    st.session_state["ifit_v082_instrument"] = instrument
    st.session_state["ifit_v082_timeframe"] = timeframe
    st.caption("Workspace context is shared across the terminal. Quantitative engines remain modular underneath.")

snapshot_status = _health.status if _health is not None else "UNKNOWN"
ctx = build_context(
    st.session_state["ifit_v082_module"],
    st.session_state["ifit_v082_subview"],
    st.session_state["ifit_v082_instrument"],
    st.session_state["ifit_v082_timeframe"],
    data_mode,
    snapshot_status,
)
st.session_state["ifit_v082_context"] = context_payload(ctx)
_ifit_v082_terminal_header(ctx)

# Compact top navigation mirrors the sidebar with balanced multi-row layout
st.markdown("##### ⚡ Terminal Workspaces")
ws_all = workspace_names()
row1 = ws_all[:8]
row2 = ws_all[8:]
for r_idx, ws_row in enumerate([row1, row2]):
    cols = st.columns(len(ws_row))
    for j, name in enumerate(ws_row):
        label = f"[{workspace_code(name)}] {name}"
        is_active = (name == ctx.module)
        if cols[j].button(label, use_container_width=True, type="primary" if is_active else "secondary", key=f"ifit_v082_topnav_{r_idx}_{j}"):
            st.session_state["ifit_v082_module"] = name
            st.session_state["ifit_v082_subview"] = subviews_for(name)[0]
            st.rerun()

st.info(
    f'ACTIVE WORKSPACE • {ctx.module} / {ctx.subview} • {ctx.instrument} • {ctx.timeframe} • '
    f'DATA {ctx.data_mode} • STATUS {ctx.snapshot_status}'
)

def _ifit_v086_gsec_page():
    st.markdown("## G-SEC INTELLIGENCE V0.1")
    st.caption("Indian government securities intelligence — simulation data")

    universe = build_gsec_intelligence()

    st.markdown("### G-Sec Filters")
    f1, f2, f3 = st.columns(3)
    with f1:
        signals = st.multiselect("Signal", available_gsec_signals(), key="ifit_gsec_signals")
    with f2:
        min_ytm = st.number_input("Min YTM %", value=0.0, step=0.25, key="ifit_gsec_min_ytm")
    with f3:
        max_ytm = st.number_input("Max YTM %", value=15.0, step=0.25, key="ifit_gsec_max_ytm")

    f4, f5, f6 = st.columns(3)
    with f4:
        min_duration = st.number_input("Min Duration", value=0.0, step=0.5, key="ifit_gsec_min_duration")
    with f5:
        max_duration = st.number_input("Max Duration", value=100.0, step=0.5, key="ifit_gsec_max_duration")
    with f6:
        min_score = st.number_input("Min Intelligence Score", value=0.0, min_value=0.0, max_value=100.0, step=5.0, key="ifit_gsec_min_score")

    filtered = apply_gsec_intelligence_filters(universe, signals=signals or None, min_ytm=min_ytm, max_ytm=max_ytm, min_duration=min_duration, max_duration=max_duration, min_score=min_score)
    ranked = rank_gsec_intelligence(filtered)
    summary = gsec_intelligence_summary(ranked)

    st.markdown("### G-Sec Intelligence Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("G-Secs", summary["G-Secs"])
    c2.metric("Buy", summary["Buy"])
    c3.metric("Sell", summary["Sell"])
    c4.metric("Average YTM", f'{summary["Average YTM"]:.3f}%')
    c5.metric("Intelligence Score", f'{summary["Average Intelligence Score"]:.2f}')
    st.caption(f'Average Duration: {summary["Average Duration"]:.2f}Y | Average Liquidity: {summary["Average Liquidity"]:.1f} | Signal: {summary["Signal"]}')

    st.markdown("### G-Sec Intelligence Matrix")
    if ranked.empty:
        st.warning("No G-Secs match the selected filters.")
        return

    display_cols = ["Bond", "Maturity Year", "Maturity Years", "Coupon %", "YTM %", "Duration", "Liquidity Score", "Yield Score", "Duration Score", "Relative Value Score", "Curve Position Score", "G-Sec Intelligence Score", "Signal"]
    st.dataframe(ranked[display_cols], width="stretch", hide_index=True)

    st.markdown("### G-Sec Thesis")
    for _, row in ranked.head(5).iterrows():
        st.markdown(f'**{row["Bond"]} — {row["G-Sec Intelligence Score"]:.2f} — {row["Signal"]}**')
        st.caption(row["Thesis"])

    st.info("Simulation data only. Connect an authorized G-Sec market/API data source before using this module for live market decisions.")

def _ifit_v086_bond_screener_page():
    st.markdown("## BOND SCREENER V0.1")
    st.caption("Unified fixed-income discovery across G-Secs, SDLs, Corporate Bonds and T-Bills — simulation data")
    universe = build_bond_screener()

    st.markdown("### Screener Filters")
    f1, f2, f3 = st.columns(3)
    with f1:
        asset_types = st.multiselect("Asset Type", available_bond_screener_asset_types(), key="ifit_bond_screen_asset_types")
    with f2:
        ratings = st.multiselect("Rating", available_bond_screener_ratings(), key="ifit_bond_screen_ratings")
    with f3:
        signals = st.multiselect("Signal", available_bond_screener_signals(), key="ifit_bond_screen_signals")

    f4, f5, f6 = st.columns(3)
    with f4:
        min_maturity = st.number_input("Min Maturity (Years)", value=0.0, min_value=0.0, step=0.5, key="ifit_bond_screen_min_maturity")
    with f5:
        max_maturity = st.number_input("Max Maturity (Years)", value=100.0, min_value=0.0, step=0.5, key="ifit_bond_screen_max_maturity")
    with f6:
        min_score = st.number_input("Min Intelligence Score", value=0.0, min_value=0.0, max_value=100.0, step=5.0, key="ifit_bond_screen_min_score")

    f7, f8, f9 = st.columns(3)
    with f7:
        min_ytm = st.number_input("Min YTM %", value=0.0, step=0.25, key="ifit_bond_screen_min_ytm")
    with f8:
        max_ytm = st.number_input("Max YTM %", value=20.0, step=0.25, key="ifit_bond_screen_max_ytm")
    with f9:
        max_duration = st.number_input("Max Duration", value=100.0, min_value=0.0, step=0.5, key="ifit_bond_screen_max_duration")

    filtered = apply_bond_screener_filters(universe, asset_types=asset_types or None, ratings=ratings or None, signals=signals or None, min_maturity=min_maturity, max_maturity=max_maturity, min_ytm=min_ytm, max_ytm=max_ytm, max_duration=max_duration, min_score=min_score)
    ranked = rank_bond_screener(filtered)
    summary = bond_screener_summary(ranked)

    st.markdown("### Bond Screener Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Instruments", summary["Instruments"])
    c2.metric("Asset Types", summary["Asset Types"])
    c3.metric("Buy", summary["Buy"])
    c4.metric("Average YTM", f'{summary["Average YTM"]:.3f}%')
    c5.metric("Average Score", f'{summary["Average Score"]:.2f}')
    st.caption(f'Average Duration: {summary["Average Duration"]:.2f}Y | Sell: {summary["Sell"]}')

    st.markdown("### Unified Bond Intelligence Matrix")
    if ranked.empty:
        st.warning("No instruments match the selected screener filters.")
        return
    display_cols = ["Instrument", "Asset Type", "Rating", "Issuer / State", "Maturity Year", "Maturity Years", "YTM %", "Duration", "Spread bp", "Liquidity Score", "Intelligence Score", "Signal"]
    st.dataframe(ranked[display_cols], width="stretch", hide_index=True)

    st.markdown("### Top Bond Opportunities")
    for _, row in ranked.head(5).iterrows():
        st.markdown(f'**{row["Instrument"]} — {row["Intelligence Score"]:.2f} — {row["Signal"]}**')
        st.caption(str(row["Thesis"]))

    st.info("Simulation data only. Connect authorized fixed-income market/API data sources before using this screener for live market decisions.")

def _ifit_v086_tbill_page():
    st.markdown("## T-BILL INTELLIGENCE V0.1")
    st.caption("Indian Treasury Bill intelligence — simulation data")
    universe = build_tbill_intelligence()

    st.markdown("### T-Bill Filters")
    f1, f2, f3 = st.columns(3)
    with f1:
        tenors = st.multiselect("Tenor (Days)", available_tbill_tenors(), key="ifit_tbill_tenors")
    with f2:
        signals = st.multiselect("Signal", available_tbill_signals(), key="ifit_tbill_signals")
    with f3:
        min_score = st.number_input("Min Intelligence Score", value=0.0, min_value=0.0, max_value=100.0, step=5.0, key="ifit_tbill_min_score")

    f4, f5 = st.columns(2)
    with f4:
        min_ytm = st.number_input("Min YTM %", value=0.0, step=0.25, key="ifit_tbill_min_ytm")
    with f5:
        max_ytm = st.number_input("Max YTM %", value=15.0, step=0.25, key="ifit_tbill_max_ytm")

    filtered = apply_tbill_intelligence_filters(universe, tenors=tenors or None, signals=signals or None, min_ytm=min_ytm, max_ytm=max_ytm, min_score=min_score)
    ranked = rank_tbill_intelligence(filtered)
    summary = tbill_intelligence_summary(ranked)

    st.markdown("### T-Bill Intelligence Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("T-Bills", summary["T-Bills"])
    c2.metric("Buy", summary["Buy"])
    c3.metric("Sell", summary["Sell"])
    c4.metric("Average YTM", f'{summary["Average YTM"]:.3f}%')
    c5.metric("Intelligence Score", f'{summary["Average Intelligence Score"]:.2f}')
    st.caption(f'Average Duration: {summary["Average Duration"]:.2f}Y | Average Liquidity: {summary["Average Liquidity"]:.1f} | Signal: {summary["Signal"]}')

    st.markdown("### T-Bill Intelligence Matrix")
    if ranked.empty:
        st.warning("No T-Bills match the selected filters.")
        return
    display_cols = ["T-Bill", "Tenor Days", "Maturity Years", "Coupon Equivalent %", "YTM %", "Duration", "Implied Discount Price", "Liquidity Score", "Yield Score", "Maturity Score", "Relative Value Score", "Safety Score", "T-Bill Intelligence Score", "Signal"]
    st.dataframe(ranked[display_cols], width="stretch", hide_index=True)

    st.markdown("### T-Bill Thesis")
    for _, row in ranked.head(5).iterrows():
        st.markdown(f'**{row["T-Bill"]} — {row["T-Bill Intelligence Score"]:.2f} — {row["Signal"]}**')
        st.caption(row["Thesis"])
    st.info("Simulation data only. Connect an authorized T-Bill market/API data source before using this module for live market decisions.")

def _ifit_v086_corporate_bond_page():
    st.markdown("## CORPORATE BOND INTELLIGENCE V0.1")
    st.caption("Indian corporate fixed-income intelligence — simulation data")
    universe = build_corporate_bond_intelligence()

    st.markdown("### Corporate Bond Filters")
    f1, f2, f3 = st.columns(3)
    with f1:
        ratings = st.multiselect("Rating", available_corporate_bond_ratings(), key="ifit_corp_ratings")
    with f2:
        issuer_types = st.multiselect("Issuer Type", available_corporate_issuer_types(), key="ifit_corp_issuer_types")
    with f3:
        signals = st.multiselect("Signal", available_corporate_bond_signals(), key="ifit_corp_signals")

    f4, f5, f6 = st.columns(3)
    with f4:
        min_ytm = st.number_input("Min YTM %", value=0.0, step=0.25, key="ifit_corp_min_ytm")
    with f5:
        max_ytm = st.number_input("Max YTM %", value=20.0, step=0.25, key="ifit_corp_max_ytm")
    with f6:
        min_score = st.number_input("Min Intelligence Score", value=0.0, min_value=0.0, max_value=100.0, step=5.0, key="ifit_corp_min_score")

    f7, f8 = st.columns(2)
    with f7:
        min_spread = st.number_input("Min Credit Spread bp", value=-100.0, step=25.0, key="ifit_corp_min_spread")
    with f8:
        max_spread = st.number_input("Max Credit Spread bp", value=2000.0, step=25.0, key="ifit_corp_max_spread")

    filtered = apply_corporate_bond_intelligence_filters(universe, ratings=ratings or None, issuer_types=issuer_types or None, signals=signals or None, min_ytm=min_ytm, max_ytm=max_ytm, min_spread=min_spread, max_spread=max_spread, min_score=min_score)
    ranked = rank_corporate_bond_intelligence(filtered)
    summary = corporate_bond_intelligence_summary(ranked)

    st.markdown("### Corporate Bond Intelligence Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Corporate Bonds", summary["Corporate Bonds"])
    c2.metric("Ratings", summary["Ratings"])
    c3.metric("Buy", summary["Buy"])
    c4.metric("Average YTM", f'{summary["Average YTM"]:.3f}%')
    c5.metric("Intelligence Score", f'{summary["Average Intelligence Score"]:.2f}')
    st.caption(f'Average Duration: {summary["Average Duration"]:.2f}Y | Average Spread: {summary["Average Spread"]:.1f} bp | Signal: {summary["Signal"]}')

    st.markdown("### Corporate Bond Intelligence Matrix")
    if ranked.empty:
        st.warning("No corporate bonds match the selected filters.")
        return
    display_cols = ["Bond", "Rating", "Issuer Type", "Maturity Year", "Coupon %", "YTM %", "Duration", "Credit Spread bp", "Liquidity Score", "Yield Score", "Credit Score", "Duration Score", "Spread Score", "Relative Value Score", "Corporate Bond Intelligence Score", "Signal"]
    st.dataframe(ranked[display_cols], width="stretch", hide_index=True)

    st.markdown("### Corporate Bond Thesis")
    for _, row in ranked.head(5).iterrows():
        st.markdown(f'**{row["Bond"]} — {row["Corporate Bond Intelligence Score"]:.2f} — {row["Signal"]}**')
        st.caption(row["Thesis"])
    st.info("Simulation data only. Connect an authorized corporate-bond market/API data source before using this module for live market decisions.")

def _ifit_v086_sdl_page():
    st.markdown("## SDL INTELLIGENCE V0.1")
    st.caption("State Development Loan intelligence — simulation data")
    universe = build_sdl_intelligence()

    st.markdown("### SDL Filters")
    f1, f2, f3 = st.columns(3)
    with f1:
        states = st.multiselect("State", available_sdl_states(), key="ifit_sdl_states")
    with f2:
        signals = st.multiselect("Signal", available_sdl_signals(), key="ifit_sdl_signals")
    with f3:
        min_score = st.number_input("Min Intelligence Score", value=0.0, min_value=0.0, max_value=100.0, step=5.0, key="ifit_sdl_min_score")

    f4, f5, f6 = st.columns(3)
    with f4:
        min_ytm = st.number_input("Min YTM %", value=0.0, step=0.25, key="ifit_sdl_min_ytm")
    with f5:
        max_ytm = st.number_input("Max YTM %", value=15.0, step=0.25, key="ifit_sdl_max_ytm")
    with f6:
        max_duration = st.number_input("Max Duration", value=100.0, min_value=0.0, step=0.5, key="ifit_sdl_max_duration")

    filtered = apply_sdl_intelligence_filters(universe, states=states or None, signals=signals or None, min_ytm=min_ytm, max_ytm=max_ytm, max_duration=max_duration, min_score=min_score)
    ranked = rank_sdl_intelligence(filtered)
    summary = sdl_intelligence_summary(ranked)

    st.markdown("### SDL Intelligence Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("SDLs", summary["SDLs"])
    c2.metric("States", summary["States"])
    c3.metric("Buy", summary["Buy"])
    c4.metric("Average YTM", f'{summary["Average YTM"]:.3f}%')
    c5.metric("Intelligence Score", f'{summary["Average Intelligence Score"]:.2f}')
    st.caption(f'Average Duration: {summary["Average Duration"]:.2f}Y | Average Spread: {summary["Average Spread"]:.1f} bp | Signal: {summary["Signal"]}')

    st.markdown("### SDL Intelligence Matrix")
    if ranked.empty:
        st.warning("No SDLs match the selected filters.")
        return
    display_cols = ["Bond", "State", "Maturity Year", "Coupon %", "YTM %", "Duration", "Spread to G-Sec bp", "Liquidity Score", "Yield Score", "Duration Score", "Spread Score", "Relative Value Score", "SDL Intelligence Score", "Signal"]
    st.dataframe(ranked[display_cols], width="stretch", hide_index=True)

    st.markdown("### SDL Thesis")
    for _, row in ranked.head(5).iterrows():
        st.markdown(f'**{row["Bond"]} — {row["SDL Intelligence Score"]:.2f} — {row["Signal"]}**')
        st.caption(row["Thesis"])
    st.info("Simulation data only. Connect an authorized SDL market/API data source before using this module for live market decisions.")

def _ifit_v086_yield_curve_page():
    st.markdown("## YIELD CURVE INTELLIGENCE V0.1")
    st.caption("Simulation-first sovereign term-structure intelligence")
    df = build_yield_curve()
    summary = yield_curve_summary(df)

    st.markdown("### Curve Snapshot")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("2Y–10Y Spread", f"{summary['2Y-10Y Spread bp']:.1f} bp")
    c2.metric("3M–10Y Spread", f"{summary['3M-10Y Spread bp']:.1f} bp")
    c3.metric("Curve Shape", summary["Curve Shape"])
    c4.metric("Curve Regime", summary["Curve Regime"])

    st.markdown("### Yield Curve")
    chart_df = df[["Maturity Years", "YTM %"]].set_index("Maturity Years")
    st.line_chart(chart_df, height=320)

    st.markdown("### Curve Intelligence")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Average YTM", f"{summary['Average YTM']:.3f}%")
    c2.metric("5Y–10Y Spread", f"{summary['5Y-10Y Spread bp']:.1f} bp")
    c3.metric("Curve Score", f"{summary['Curve Score']:.1f}")
    c4.metric("Signal", summary["Signal"])

    st.markdown("### Maturity Filter")
    min_m, max_m = st.slider("Maturity (Years)", 0.0, 30.0, (0.0, 30.0), 0.25, key="ifit_yield_curve_maturity")
    filtered = apply_yield_curve_filters(df, min_m, max_m)

    st.markdown("### Yield Curve Matrix")
    display_cols = ["Tenor", "Maturity Years", "YTM %", "Yield Change bp", "Duration", "Slope from 3M bp", "Curve Curvature bp"]
    st.dataframe(filtered[display_cols], width="stretch", hide_index=True)

    st.markdown("### Curve Interpretation")
    st.write(f"**Shape:** {summary['Curve Shape']}")
    st.write(f"**Regime:** {summary['Curve Regime']}")
    st.write(f"**Signal:** {summary['Signal']}")
    st.info("Simulation data only. Connect an authorized bond-market/API data source before using this module for live market decisions.")


def _ifit_v086_bond_overview_page():
    st.markdown("## BOND OVERVIEW V0.1")
    st.caption("Unified Indian fixed-income dashboard — simulation data")

    bonds = build_bond_intelligence()
    gsecs = build_gsec_intelligence()
    sdls = build_sdl_intelligence()
    corporates = build_corporate_bond_intelligence()
    tbills = build_tbill_intelligence()
    screener = build_bond_screener()
    curve = build_yield_curve()
    curve_summary = yield_curve_summary(curve)

    st.markdown("### Fixed-Income Universe")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Instruments", len(screener))
    c2.metric("G-Secs", len(gsecs))
    c3.metric("SDLs", len(sdls))
    c4.metric("Corporate Bonds", len(corporates))
    c5.metric("T-Bills", len(tbills))

    st.markdown("### Market Snapshot")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Average YTM", f'{screener["YTM %"].mean():.3f}%')
    c2.metric("Average Duration", f'{screener["Duration"].mean():.2f}Y')
    c3.metric("2Y–10Y Spread", f'{curve_summary["2Y-10Y Spread bp"]:.1f} bp')
    c4.metric("Curve Shape", curve_summary["Curve Shape"])
    c5.metric("Curve Regime", curve_summary["Curve Regime"])

    st.markdown("### Yield Curve")
    chart_df = curve[["Maturity Years", "YTM %"]].set_index("Maturity Years")
    st.line_chart(chart_df, height=280)

    st.markdown("### Segment Intelligence")
    segments = pd.DataFrame([
        {"Segment": "G-Secs", "Instruments": len(gsecs), "Average YTM %": gsecs["YTM %"].mean(), "Average Score": gsecs["G-Sec Intelligence Score"].mean()},
        {"Segment": "SDLs", "Instruments": len(sdls), "Average YTM %": sdls["YTM %"].mean(), "Average Score": sdls["SDL Intelligence Score"].mean()},
        {"Segment": "Corporate Bonds", "Instruments": len(corporates), "Average YTM %": corporates["YTM %"].mean(), "Average Score": corporates["Corporate Bond Intelligence Score"].mean()},
        {"Segment": "T-Bills", "Instruments": len(tbills), "Average YTM %": tbills["YTM %"].mean(), "Average Score": tbills["T-Bill Intelligence Score"].mean()},
    ])
    segments["Average YTM %"] = segments["Average YTM %"].round(3)
    segments["Average Score"] = segments["Average Score"].round(2)
    st.dataframe(segments, width="stretch", hide_index=True)

    st.markdown("### Top Fixed-Income Intelligence")
    top = rank_bond_screener(screener).head(10)
    st.dataframe(top[["Instrument", "Asset Type", "Rating", "YTM %", "Duration", "Spread bp", "Liquidity Score", "Intelligence Score", "Signal"]], width="stretch", hide_index=True)

    st.markdown("### Bond Intelligence Distribution")
    dist = screener["Signal"].value_counts().reindex(available_bond_screener_signals(), fill_value=0)
    st.bar_chart(dist, height=220)

    st.markdown("### Bond Workspace Status")
    status = pd.DataFrame([
        {"Module": "Bond Intelligence", "Status": "ACTIVE"},
        {"Module": "Yield Curve", "Status": "ACTIVE"},
        {"Module": "G-Secs", "Status": "ACTIVE"},
        {"Module": "SDLs", "Status": "ACTIVE"},
        {"Module": "Corporate Bonds", "Status": "ACTIVE"},
        {"Module": "T-Bills", "Status": "ACTIVE"},
        {"Module": "Bond Screener", "Status": "ACTIVE"},
    ])
    st.dataframe(status, width="stretch", hide_index=True)
    st.info("Simulation data only. Connect authorized fixed-income market/API sources before using this workspace for live market decisions.")

def _ifit_v086_bond_page():
    subview = st.session_state.get("ifit_v082_subview", "Overview")
    st.markdown("## BONDS / FIXED INCOME")
    st.caption("Indian fixed-income intelligence — simulation data until an authorized live bond feed is connected.")

    if subview == "Overview":
        _ifit_v086_bond_overview_page()
        return

    if subview == "G-Secs":
        _ifit_v086_gsec_page()
        return

    if subview == "SDLs":
        _ifit_v086_sdl_page()
        return

    if subview == "Corporate Bonds":
        _ifit_v086_corporate_bond_page()
        return

    if subview == "T-Bills":
        _ifit_v086_tbill_page()
        return

    if subview == "Bond Screener":
        _ifit_v086_bond_screener_page()
        return

    if subview == "Yield Curve":
        _ifit_v086_yield_curve_page()
        return

    if subview != "Intelligence":
        st.info(f"Bond workspace: {subview}. Bond Intelligence V0.1 is currently available under the Intelligence subview.")
        return

    st.markdown("### Bond Intelligence V0.1")
    st.caption("Yield, duration, credit, liquidity and relative-value intelligence across Indian fixed income.")
    universe = build_bond_intelligence()

    st.markdown("### Intelligence Filters")
    f1, f2, f3 = st.columns(3)
    with f1:
        asset_types = st.multiselect("Asset Type", available_bond_asset_types(), key="ifit_bond_asset_types")
    with f2:
        ratings = st.multiselect("Rating", available_bond_ratings(), key="ifit_bond_ratings")
    with f3:
        signals = st.multiselect("Signal", available_bond_signals(), key="ifit_bond_signals")

    f4, f5, f6 = st.columns(3)
    with f4:
        min_ytm = st.number_input("Min YTM %", value=0.0, step=0.25, key="ifit_bond_min_ytm")
    with f5:
        max_ytm = st.number_input("Max YTM %", value=15.0, step=0.25, key="ifit_bond_max_ytm")
    with f6:
        min_score = st.number_input("Min Intelligence Score", value=0.0, min_value=0.0, max_value=100.0, step=5.0, key="ifit_bond_min_score")

    filtered = apply_bond_intelligence_filters(universe, asset_types=asset_types or None, ratings=ratings or None, signals=signals or None, min_ytm=min_ytm, max_ytm=max_ytm, min_score=min_score)
    ranked = rank_bond_intelligence(filtered, ascending=False)
    summary = bond_intelligence_summary(ranked)

    st.markdown("### Intelligence Summary")
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Bonds", summary["Bonds"])
    s2.metric("Buy", summary["Buy"])
    s3.metric("Sell", summary["Sell"])
    s4.metric("Average YTM", f'{summary["Average YTM"]:.3f}%')
    s5.metric("Intelligence Score", f'{summary["Average Intelligence Score"]:.2f}')
    st.caption(f'Average Duration: {summary["Average Duration"]:.2f}Y | Average Spread: {summary["Average Spread"]:.3f}% | Signal: {summary["Signal"]}')

    st.markdown("### Bond Intelligence Matrix")
    if ranked.empty:
        st.warning("No bonds match the selected intelligence filters.")
        return
    display_cols = ["Bond", "Asset Type", "Rating", "YTM %", "Yield Change bp", "Duration", "Credit Spread %", "Liquidity Score", "Relative Value Score", "Bond Intelligence Score", "Signal"]
    st.dataframe(ranked[display_cols], width="stretch", hide_index=True)

    st.markdown("### Bond Thesis")
    for _, row in ranked.head(5).iterrows():
        st.markdown(f'**{row["Bond"]} — {row["Bond Intelligence Score"]:.2f} — {row["Signal"]}**')
        st.caption(row["Thesis"])
    st.info("Simulation data only. Connect an authorized bond-market/API data source before using this module for live market decisions.")


def _ifit_cross_asset_intelligence_page():
    snapshot = build_cross_asset_intelligence_snapshot()
    summary = cross_asset_summary(snapshot)

    st.markdown("## CROSS-ASSET INTELLIGENCE V0.1")
    st.caption("Simulation / proxy data — Cross-Asset Intelligence")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Cross-Asset Score", summary.get("Cross-Asset Score", 0))
    c2.metric("Risk State", summary.get("Risk State", "N/A"))
    c3.metric("Regime", summary.get("Regime", "N/A"))
    c4.metric("Leader", summary.get("Leader", "N/A"))
    c5.metric("Divergences", summary.get("Divergences", 0))

    st.divider()

    a, b, c, d, e = st.columns(5)
    a.metric("Equity", summary.get("Equity", 0))
    b.metric("Bonds", summary.get("Bonds", 0))
    c.metric("Commodities", summary.get("Commodities", 0))
    d.metric("FX", summary.get("FX", 0))
    e.metric("Crypto", summary.get("Crypto", 0))

    st.markdown("### Cross-Asset Universe")
    universe = snapshot.get("Asset Table", snapshot.get("Universe", []))
    if universe is not None:
        st.dataframe(universe, width="stretch", hide_index=True)

    corr = snapshot.get("Correlation")
    if corr is not None:
        st.markdown("### Cross-Asset Correlation Matrix")
        st.dataframe(corr, width="stretch")

    st.info("Cross-Asset Intelligence combines Equity, Bonds, Credit, Commodities, FX, Volatility, Crypto and Global Equity signals into a unified regime and risk view.")


def _ifit_global_markets_intelligence_page():
    snapshot = build_global_markets_intelligence_snapshot()
    summary = global_markets_summary(snapshot)

    st.markdown("## GLOBAL MARKETS INTELLIGENCE V0.1")
    st.caption("Simulation / proxy data — Global Markets Intelligence")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Global Score", summary.get("Global Score", 0))
    c2.metric("Risk State", summary.get("Risk State", "N/A"))
    c3.metric("Regime", summary.get("Regime", "N/A"))
    c4.metric("Leader", summary.get("Leader", "N/A"))
    c5.metric("Lagging", summary.get("Lagging", "N/A"))
    c6.metric("Divergences", summary.get("Divergences", 0))

    st.divider()

    a, b, c, d, e, f, g = st.columns(7)
    a.metric("India", summary.get("India", 0))
    b.metric("US", summary.get("US", 0))
    c.metric("Asia", summary.get("Asia", 0))
    d.metric("Europe", summary.get("Europe", 0))
    e.metric("Rates", summary.get("Rates", 0))
    f.metric("FX", summary.get("FX", 0))
    g.metric("Commodities", summary.get("Commodities", 0))

    st.markdown("### Global Markets Universe")
    universe = snapshot.get("Asset Table")
    if universe is not None:
        st.dataframe(universe, width="stretch", hide_index=True)

    corr = snapshot.get("Correlation")
    if corr is not None:
        st.markdown("### Global Markets Correlation Matrix")
        st.dataframe(corr, width="stretch")

    st.info("Global Markets Intelligence combines Indian, US, Asian and European equities with rates, FX, commodities and volatility into a unified global regime and risk view. Data shown is simulation / proxy data for the current prototype.")

if ctx.module == "Command Center":
    _ifit_v080_render()
elif ctx.module == "Markets":
    _ifit_v081_market_page()
elif ctx.module == "Equities":
    _ifit_v081_equities_page()
elif ctx.module == "Screener":
    _ifit_v085_screener_page()
elif ctx.module == "Options":
    _ifit_v081_options_page()
elif ctx.module == "Charts":
    _ifit_v083_charts_page(ctx)
elif ctx.module == "Portfolio":
    _ifit_v081_portfolio_page()
elif ctx.module == "Risk Engine":
    _ifit_v081_risk_page()
elif ctx.module == "AI Intelligence":
    _ifit_v081_ai_page()
elif ctx.module == "Bonds / Fixed Income":
    _ifit_v086_bond_page()
elif ctx.module == "MCX / Commodities":
          _ifit_v085_mcx_page()
elif ctx.module == "Cross-Asset":
    _ifit_cross_asset_intelligence_page()
elif ctx.module == "Forex":
    _ifit_forex_page(ctx)
elif ctx.module == "Crypto":
    _ifit_crypto_page(ctx)

elif ctx.module == "Global Markets":
    _ifit_global_markets_intelligence_page()
elif ctx.module == "Mutual Funds":
    render_mutual_funds_intelligence(ctx)

# Global data health footer for every terminal workspace.
st.markdown("---")
st.markdown("### IFIT Data Health Monitor")
if _health is not None:
    st.dataframe(
        health_frame(_health).style.format({"Data Age (s)":"{:.2f}", "Latency (ms)":"{:.0f}"}),
        width="stretch", hide_index=True
    )
    q = data_quality(_snapshot)
    if q["issues"]:
        st.warning(" | ".join(q["issues"]))
    else:
        st.success("Data schema and core market fields passed the adapter health checks.")

status_df = pd.DataFrame([
    ["Command Center", "ACTIVE", "Consolidated executive snapshot + IFIT score + conviction"],
    ["Markets", "ACTIVE", "Market state + breadth + volatility + futures + regime"],
    ["Equities", "ACTIVE", "Fundamentals + valuation + quality + growth + peers"],
    ["Screener", "ACTIVE", "Multi-factor equity, derivatives, market, order flow, & quant screening"],
    ["Cross-Asset", "ACTIVE", "Cross-asset regime intelligence + spillover analysis"],
    ["Global Markets", "ACTIVE", "US, European, Asian equities + global macro & rates"],
    ["Forex", "ACTIVE", "INR currency strength + FX derivatives & volatility"],
    ["Crypto", "ACTIVE", "Digital assets positioning + derivatives + CVD flow"],
    ["Mutual Funds", "ACTIVE", "AMFI mutual fund intelligence + risk-adjusted return screening"],
    ["Options", "ACTIVE", "Chain + Greeks (higher-order) + Heston + Gamma exposure + execution"],
    ["Charts", "ACTIVE", "Interactive TradingView-style candles + footprint + CVD + profile + drawing"],
    ["Portfolio", "ACTIVE", "Holdings + portfolio Greeks + concentration + stress testing"],
    ["Risk Engine", "ACTIVE", "Cross-engine risk drivers + tail diagnostics + scenario PnL"],
    ["AI Intelligence", "ACTIVE", "Grounded explanation + evidence ladder + methodology"],
    ["Bonds / Fixed Income", "ACTIVE", "G-Secs + SDLs + Corporate Bonds + T-Bills + Sovereign Yield Curve"],
    ["MCX / Commodities", "ACTIVE", "Crude, Gold, Silver + term structure + basis & roll intelligence"],
], columns=["Terminal Module", "Status", "Primary Capability"])
st.dataframe(status_df, width="stretch", hide_index=True)

st.caption("IFIT V0.8.4.1 • Institutional Financial Intelligence Terminal • Production-grade quantitative architecture.")










