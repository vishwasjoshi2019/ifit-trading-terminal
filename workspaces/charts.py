"""IFIT Charts Workspace.
Advanced TradingView-grade interactive charting, volume profile, CVD,
footprint order flow, auction intelligence, and dynamic motion analysis.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from engines.interactive_chart_engine import build_interactive_figure
from engines.charts_engine import build_ohlcv, build_volume_profile, chart_snapshot
from engines.cht_live_component import render_live_chart
from engines.motion_charts_engine import build_motion_data, motion_summary
from engines.order_flow_footprint_engine import (
    aggregate_footprint,
    available_footprint_timeframes,
    build_bar_footprint,
    build_footprint_data,
    footprint_summary,
)
from engines.footprint_intelligence_engine import (
    classify_footprint_intelligence,
    footprint_intelligence_summary,
)


def _render_motion_charts(ctx):
    st.markdown("### ⚡ CHT Motion Intelligence")
    st.caption("Momentum, volatility, and order-flow motion velocity dynamics.")

    df = build_motion_data()
    summary = motion_summary(df)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Price", f"₹{summary.get('Last Price', 0.0):,.2f}")
    c2.metric("Momentum", f"{summary.get('Momentum', 0.0):.3f}%")
    c3.metric("IV", f"{summary.get('IV', 0.0):.2f}%")
    c4.metric("Realized Vol", f"{summary.get('RV', 0.0):.2f}%")
    c5.metric("Motion Score", f"{summary.get('Motion Score', 0.0):.1f}")

    if not df.empty:
        st.dataframe(df, width="stretch", hide_index=True)


def _render_order_flow_footprint(ctx):
    st.markdown("### ⚡ Order Flow Footprint & Auction Intelligence")
    st.caption("Price-level cluster volume, delta, imbalance, absorption, exhaustion, and POC migration.")

    tf_col, p_col, l_col = st.columns(3)
    timeframe = tf_col.selectbox("Timeframe", available_footprint_timeframes(), index=0, key="charts_fp_tf")
    periods = p_col.slider("Bars", 30, 120, 60, 15, key="charts_fp_periods")
    levels = l_col.slider("Price Levels / Bar", 12, 36, 24, 4, key="charts_fp_levels")

    df = build_footprint_data(periods=periods, levels=levels)
    bars = build_bar_footprint(periods=periods, levels=levels)
    summary = footprint_summary(df)

    latest = bars.iloc[-1] if not bars.empty else {}
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Bid Volume", f"{int(latest.get('Bid_Volume', 0)):,}")
    c2.metric("Ask Volume", f"{int(latest.get('Ask_Volume', 0)):,}")
    c3.metric("Delta", f"{int(latest.get('Delta', 0)):+,}")
    c4.metric("CVD", f"{summary.get('CVD', 0):+,.0f}")
    c5.metric("POC", f"₹{summary.get('POC', 0.0):,.2f}")
    c6.metric("OF Score", f"{summary.get('Order Flow Score', 0.0):.1f}")

    # Microstructure & Institutional Events
    st.markdown("#### Institutional Order-Flow Signals")
    intelligence_df = classify_footprint_intelligence(df)
    intel_summary = footprint_intelligence_summary(intelligence_df)

    i1, i2, i3, i4, i5, i6 = st.columns(6)
    i1.metric("Absorption Events", intel_summary.get("Absorption", 0))
    i2.metric("Exhaustion Events", intel_summary.get("Exhaustion", 0))
    i3.metric("Failed Auctions", intel_summary.get("Failed Auctions", 0))
    i4.metric("Delta Flips", intel_summary.get("Delta Flips", 0))
    i5.metric("CVD Divergences", intel_summary.get("CVD Divergences", 0))
    i6.metric("Large Prints", intel_summary.get("Large Prints", 0))

    if not intelligence_df.empty:
        st.markdown("#### Price-Level Cluster Matrix")
        latest_intel = intelligence_df[intelligence_df["Bar"] == intelligence_df["Bar"].max()].copy()
        display_cols = [c for c in [
            "Price", "Delta", "Delta %", "Bid/Ask Imbalance", "Dominant Side",
            "Absorption Signal", "Exhaustion Signal", "Footprint Intelligence Score"
        ] if c in latest_intel.columns]
        st.dataframe(latest_intel[display_cols].sort_values("Price", ascending=False), width="stretch", hide_index=True)


def _render_interactive_chart(ctx, spot: float):
    st.markdown("### ⚡ Interactive Quantitative Chart")

    c_type_col, bars_col, indicators_col = st.columns([1, 1, 2])
    chart_type = c_type_col.selectbox("Type", ["Candlestick", "Heikin-Ashi", "Line", "Area"], key="charts_type")
    bars_n = bars_col.slider("Display Bars", 30, 240, 90, 15, key="charts_bars")
    indicators = indicators_col.multiselect(
        "Overlays",
        ["EMA 9", "EMA 21", "EMA 50", "VWAP", "Bollinger Bands", "RSI", "MACD"],
        default=["EMA 21", "VWAP"],
        key="charts_overlays",
    )

    t1, t2, t3, t4 = st.columns(4)
    show_poc = t1.checkbox("POC", value=True, key="charts_poc")
    show_profile = t2.checkbox("Volume Profile", value=True, key="charts_profile")
    show_cvd = t3.checkbox("CVD Pane", value=True, key="charts_cvd")
    show_delta = t4.checkbox("Delta Bars", value=False, key="charts_delta")

    # Generate or fetch OHLCV series
    ohlcv = build_ohlcv(spot=spot, bars=bars_n)
    profile = build_volume_profile(ohlcv, bins=25)
    snap = chart_snapshot(ohlcv, profile, spot)

    fig = build_interactive_figure(
        ohlcv,
        chart_type=chart_type,
        selections=indicators,
        params={},
        show_poc=show_poc,
        poc=snap.get("poc"),
        show_volume_profile=show_profile,
        profile=profile,
        show_cvd=show_cvd,
        show_delta=show_delta,
    )

    render_live_chart(
        fig,
        height=int(getattr(fig.layout, "height", None) or 650),
        key="charts_live_view",
        symbol="NIFTY",
    )


def render_charts(ctx, spot: float):
    subview = ctx.subview or "Interactive Chart"

    st.markdown("## 📊 INSTITUTIONAL CHARTS & ORDER FLOW")

    mode = st.radio(
        "Chart Mode",
        ["Interactive Chart", "Order Flow Footprint", "Motion Charts"],
        horizontal=True,
        index=0 if subview not in ("Order Flow Footprint", "Motion Charts") else (
            1 if subview == "Order Flow Footprint" else 2
        ),
        key="charts_mode_toggle",
    )

    if mode == "Order Flow Footprint":
        _render_order_flow_footprint(ctx)
    elif mode == "Motion Charts":
        _render_motion_charts(ctx)
    else:
        _render_interactive_chart(ctx, spot)
