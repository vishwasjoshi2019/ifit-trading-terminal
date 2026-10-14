"""IFIT Terminal Sidebar Controls & Parameters."""
from datetime import date, timedelta
import streamlit as st
from config import INSTRUMENT_OPTIONS, TIMEFRAME_OPTIONS
from engines.workspace_engine import workspace_names, subviews_for


def render_terminal_sidebar(dhan_snapshot=None):
    """Render the master sidebar with data controls, market parameters, and navigation."""
    with st.sidebar:
        st.header("🇮🇳 IFIT")
        st.caption("Indian Financial Intelligence Terminal")
        st.divider()

        data_mode = st.session_state.get("ifit_data_mode", "SIMULATION")

        # Spot Price Handling
        if data_mode == "DHAN LIVE" and dhan_snapshot:
            live_spot = float(dhan_snapshot.get("spot") or 0)
            if live_spot > 0:
                st.session_state["ifit_nifty_spot"] = live_spot
                st.metric("NIFTY Spot • LIVE", f"₹{live_spot:,.2f}")
                spot = live_spot
            else:
                st.metric("NIFTY Spot • LIVE", "Connecting...")
                spot = float(st.session_state.get("ifit_nifty_spot", 24782.35))
        else:
            spot = st.number_input(
                "NIFTY Spot",
                value=float(st.session_state.get("ifit_nifty_spot", 24782.35)),
                step=25.0,
                key="ifit_nifty_spot_input"
            )
            st.session_state["ifit_nifty_spot"] = spot

        # Expiry & Days to Expiration (DTE)
        today = date.today()
        expiry_dates = [
            today + timedelta(days=d)
            for d in range(1, 91)
            if (today + timedelta(days=d)).weekday() == 3
        ]
        expiry_labels = [d.strftime("%d %b %Y") for d in expiry_dates]

        selected_expiry_label = st.selectbox(
            "NIFTY Expiry",
            expiry_labels,
            index=0,
            key="ifit_expiry_select",
        )
        selected_expiry = expiry_dates[expiry_labels.index(selected_expiry_label)]
        dte_days = max((selected_expiry - today).days, 1)
        st.caption(f"DTE: {dte_days} days to expiration")

        # Market Volatility & Microstructure Controls
        atm_iv = st.slider("ATM IV (%)", 5.0, 60.0, 14.5, 0.1, key="ifit_atm_iv_slider")
        hv30 = st.slider("30D Realized Vol (%)", 5.0, 60.0, 12.8, 0.1, key="ifit_hv30_slider")
        flow_levels = st.slider("Footprint levels", 20, 100, 50, 5, key="ifit_flow_levels_slider")
        imbalance_ratio = st.slider("Imbalance ratio", 1.2, 3.0, 1.5, 0.1, key="ifit_imbalance_slider")

        st.divider()

        # Data Feed Selection
        st.subheader("Data Feed")
        selected_data_mode = st.selectbox(
            "Source",
            ["SIMULATION", "AUTHORIZED API / BROKER", "DHAN LIVE"],
            index=["SIMULATION", "AUTHORIZED API / BROKER", "DHAN LIVE"].index(data_mode) if data_mode in ["SIMULATION", "AUTHORIZED API / BROKER", "DHAN LIVE"] else 0,
            key="ifit_data_mode_select"
        )
        if selected_data_mode != data_mode:
            st.session_state["ifit_data_mode"] = selected_data_mode
            st.rerun()

        api_endpoint = ""
        if selected_data_mode == "AUTHORIZED API / BROKER":
            api_endpoint = st.text_input("JSON Endpoint", value="", key="ifit_api_endpoint_input")

        refresh_data = st.button("↻ Refresh Snapshot", use_container_width=True)

        st.divider()

        # Workspace Navigation
        st.subheader("Navigation")
        active_module = st.selectbox(
            "Workspace",
            workspace_names(),
            index=workspace_names().index(st.session_state.get("ifit_v082_module", "Command Center")),
            key="ifit_module_select"
        )
        if active_module != st.session_state.get("ifit_v082_module"):
            st.session_state["ifit_v082_module"] = active_module
            st.session_state["ifit_v082_subview"] = subviews_for(active_module)[0]
            st.rerun()

        subviews = subviews_for(active_module)
        current_subview = st.session_state.get("ifit_v082_subview", subviews[0])
        if current_subview not in subviews:
            current_subview = subviews[0]

        active_subview = st.radio(
            "Subview",
            subviews,
            index=subviews.index(current_subview),
            key="ifit_subview_select"
        )
        st.session_state["ifit_v082_subview"] = active_subview

        # Instrument & Timeframe Context
        current_instrument = st.session_state.get("ifit_v082_instrument", "NIFTY 50")
        if current_instrument not in INSTRUMENT_OPTIONS:
            current_instrument = "NIFTY 50"

        instrument = st.selectbox(
            "Context Instrument",
            INSTRUMENT_OPTIONS,
            index=INSTRUMENT_OPTIONS.index(current_instrument),
            key="ifit_inst_select"
        )
        st.session_state["ifit_v082_instrument"] = instrument

        current_tf = st.session_state.get("ifit_v082_timeframe", "Intraday")
        if current_tf not in TIMEFRAME_OPTIONS:
            current_tf = "Intraday"

        timeframe = st.selectbox(
            "Timeframe",
            TIMEFRAME_OPTIONS,
            index=TIMEFRAME_OPTIONS.index(current_tf),
            key="ifit_tf_select"
        )
        st.session_state["ifit_v082_timeframe"] = timeframe

        return {
            "spot": spot,
            "dte_days": dte_days,
            "atm_iv": atm_iv,
            "hv30": hv30,
            "flow_levels": flow_levels,
            "imbalance_ratio": imbalance_ratio,
            "data_mode": selected_data_mode,
            "api_endpoint": api_endpoint,
            "refresh_data": refresh_data,
            "module": active_module,
            "subview": active_subview,
            "instrument": instrument,
            "timeframe": timeframe,
        }
