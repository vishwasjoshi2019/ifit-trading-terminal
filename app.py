"""IFIT — Indian Financial Intelligence Terminal.
High-density, professional Bloomberg/TradingView-grade terminal architecture.
"""
from __future__ import annotations

import os
import warnings
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

warnings.filterwarnings("ignore", message=".*use_container_width.*")
warnings.filterwarnings("ignore", category=FutureWarning)

load_dotenv()

from config import TERMINAL_CSS
from ui.header import render_terminal_header
from ui.navigation import render_workspace_rail
from ui.sidebar import render_terminal_sidebar
from ui.footer import render_terminal_footer

from engines.data_adapter import IFITDataAdapter, health_from_snapshot
from engines.workspace_engine import build_context, context_payload
from engines.live_data.dhan_live_service import DhanLiveService

import workspaces


# -----------------------------------------------------------------------------
# 1. Page Configuration & Terminal Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="IFIT — Institutional Financial Intelligence Terminal",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(TERMINAL_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. Live Data Feed Singleton
# -----------------------------------------------------------------------------
@st.cache_resource
def _get_dhan_live_service():
    """Cached singleton for Dhan WebSocket live feed."""
    service = DhanLiveService()
    service.start()
    return service


# -----------------------------------------------------------------------------
# 3. Sidebar Controls & Parameters
# -----------------------------------------------------------------------------
data_mode_requested = st.session_state.get("ifit_data_mode", "SIMULATION")
dhan_service = None
dhan_snapshot = None
dhan_health = None

# Crash-immune credential verification
if data_mode_requested == "DHAN LIVE":
    client_id = os.getenv("DHAN_CLIENT_ID", "").strip()
    access_token = os.getenv("DHAN_ACCESS_TOKEN", "").strip()
    if not client_id or not access_token:
        st.sidebar.warning("⚠️ DHAN credentials missing in .env. Falling back to simulation.")
        st.session_state["ifit_data_mode"] = "SIMULATION"
    else:
        try:
            dhan_service = _get_dhan_live_service()
            dhan_snapshot = dhan_service.snapshot()
            dhan_health = dhan_service.health()
        except Exception as exc:
            st.sidebar.error(f"Dhan connection error: {exc}. Using simulated feed.")
            st.session_state["ifit_data_mode"] = "SIMULATION"

sidebar_state = render_terminal_sidebar(dhan_snapshot=dhan_snapshot)

spot = float(sidebar_state["spot"])
dte_days = int(sidebar_state["dte_days"])
atm_iv = float(sidebar_state["atm_iv"])
hv30 = float(sidebar_state["hv30"])
flow_levels = int(sidebar_state["flow_levels"])
imbalance_ratio = float(sidebar_state["imbalance_ratio"])
data_mode = sidebar_state["data_mode"]
api_endpoint = sidebar_state["api_endpoint"]
refresh_data = sidebar_state["refresh_data"]


# -----------------------------------------------------------------------------
# 4. Market Snapshot & Data Health Resolution
# -----------------------------------------------------------------------------
_snapshot = None
_health = None

if data_mode == "DHAN LIVE" and dhan_service is not None:
    try:
        _dhan_snap = dhan_service.snapshot()
        _dhan_h = dhan_service.health()
        _chain = _dhan_snap.get("option_chain")
        if _chain is None:
            _chain = pd.DataFrame()
        _snapshot = {
            "timestamp": _dhan_snap.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            "spot": float(_dhan_snap.get("spot") or spot),
            "futures": 0.0,
            "option_chain": _chain,
            "source": "Dhan WebSocket + REST Option Chain",
        }
        _ticks = int(_dhan_snap.get("tick_count", 0))
        _health = type("LiveHealth", (), {})()
        _health.source = "Dhan WebSocket"
        _dhan_stat = _dhan_h.get("status", "CONNECTING")
        _health.status = "LIVE" if _dhan_stat == "LIVE" else ("CONNECTING" if _dhan_stat == "CONNECTING" else "ERROR")
        _health.last_update = str(_snapshot["timestamp"])
        _health.age_seconds = 0.0
        _health.records = _ticks
        _health.latency_ms = 0.0
        _health.message = f"Dhan WebSocket • {_ticks} live ticks received"
        _health.mode = "DHAN LIVE"
    except Exception as exc:
        st.warning(f"Dhan feed resolution note: {exc}")

if _snapshot is None or _health is None:
    _adapter_mode = "API" if data_mode == "AUTHORIZED API / BROKER" else "SIMULATION"
    _adapter = IFITDataAdapter(mode=_adapter_mode, endpoint=api_endpoint, api_key=None, timeout=8, symbol=sidebar_state["instrument"])
    if refresh_data or "ifit_market_snapshot" not in st.session_state:
        _snapshot, _health = _adapter.fetch()
        if _snapshot is not None:
            st.session_state["ifit_market_snapshot"] = _snapshot
        st.session_state["ifit_data_health"] = _health
    else:
        _snapshot = st.session_state.get("ifit_market_snapshot")
        _health = st.session_state.get("ifit_data_health")

if _snapshot is not None and _health is not None and data_mode != "DHAN LIVE":
    _health = health_from_snapshot(_snapshot, _health)
    st.session_state["ifit_data_health"] = _health


# -----------------------------------------------------------------------------
# 5. Terminal Context & Header Navigation
# -----------------------------------------------------------------------------
snapshot_status = getattr(_health, "status", "SIMULATION")
ctx = build_context(
    sidebar_state["module"],
    sidebar_state["subview"],
    sidebar_state["instrument"],
    sidebar_state["timeframe"],
    data_mode,
    snapshot_status,
)
st.session_state["ifit_v082_context"] = context_payload(ctx)

render_terminal_header(ctx)
render_workspace_rail(ctx.module)


# -----------------------------------------------------------------------------
# 6. Workspace Router Dispatch Table
# -----------------------------------------------------------------------------
DISPATCH_TABLE = {
    "Command Center": lambda: workspaces.render_command_center(ctx, spot, dte_days, atm_iv, hv30, flow_levels, imbalance_ratio),
    "Markets": lambda: workspaces.render_markets(ctx, spot, dte_days, atm_iv, hv30, flow_levels, imbalance_ratio),
    "Equities": lambda: workspaces.render_equities(ctx),
    "Screener": lambda: workspaces.render_screener(ctx),
    "Options": lambda: workspaces.render_options(ctx, spot, dte_days, atm_iv, hv30),
    "Charts": lambda: workspaces.render_charts(ctx, spot),
    "Portfolio": lambda: workspaces.render_portfolio(ctx, spot, dte_days, atm_iv),
    "Risk Engine": lambda: workspaces.render_risk_engine(ctx, spot, dte_days, atm_iv, hv30, flow_levels, imbalance_ratio),
    "AI Intelligence": lambda: workspaces.render_ai_intelligence(ctx, spot, dte_days, atm_iv, hv30, flow_levels, imbalance_ratio),
    "Bonds / Fixed Income": lambda: workspaces.render_bonds(ctx),
    "MCX / Commodities": lambda: workspaces.render_commodities(ctx),
    "Cross-Asset": lambda: workspaces.render_cross_asset(ctx),
    "Forex": lambda: workspaces.render_forex(ctx),
    "Crypto": lambda: workspaces.render_crypto(ctx),
    "Global Markets": lambda: workspaces.render_global_markets(ctx),
    "Mutual Funds": lambda: workspaces.render_mutual_funds(ctx),
}

workspace_renderer = DISPATCH_TABLE.get(ctx.module, DISPATCH_TABLE["Command Center"])
workspace_renderer()


# -----------------------------------------------------------------------------
# 7. Global Data Health Footer
# -----------------------------------------------------------------------------
render_terminal_footer(_health, _snapshot)
