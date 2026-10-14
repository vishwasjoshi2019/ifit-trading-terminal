"""IFIT Screener Workspace.
Multi-factor screening across Equities, Derivatives, Market Breadth, Order Flow,
Quant Signals, and Decision Intelligence Fusion.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from engines.screener_engine import apply_filters, build_equity_universe, rank_equities, sector_summary
from engines.derivatives_screener_engine import build_derivatives_universe, rank_derivatives, signal_summary
from engines.market_screener_engine import available_sectors, build_market_universe, market_summary
from engines.orderflow_screener_engine import build_orderflow_universe, orderflow_summary, rank_orderflow
from engines.quant_screener_engine import build_quant_universe, quant_summary, rank_quant
from engines.decision_intelligence_engine import build_decision_snapshot
from engines.footprint_decision_fusion_engine import fuse_decision_snapshot


def _render_equity_screener():
    st.markdown("### Multi-Factor Equity Screener")
    df = build_equity_universe()

    f1, f2, f3, f4 = st.columns(4)
    sector_opts = ["All"] + sorted(list(df["Sector"].dropna().unique()))
    sec = f1.selectbox("Sector", sector_opts, key="scr_eq_sec")
    min_score = f2.number_input("Min Equity Score", value=0.0, min_value=0.0, max_value=100.0, step=5.0, key="scr_eq_score")
    trend_opt = f3.selectbox("EMA Trend", ["All", "BULLISH", "BEARISH"], key="scr_eq_trend")
    min_rs = f4.number_input("Min Relative Strength", value=0.0, step=0.1, key="scr_eq_rs")

    filters = {"min_score": min_score}
    if sec != "All":
        filters["sector"] = sec
    if trend_opt != "All":
        filters["trend"] = trend_opt
    if min_rs > 0:
        filters["min_rs"] = min_rs

    screened = apply_filters(df, filters)
    ranked = rank_equities(screened)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Universe", f"{len(df)}")
    m2.metric("Filtered Matches", f"{len(screened)}")
    m3.metric("Top Equity Score", f"{ranked['Equity Score'].max():.1f}" if not ranked.empty else "—")
    m4.metric("Avg Score", f"{ranked['Equity Score'].mean():.1f}" if not ranked.empty else "—")
    m5.metric("Bullish Trend", f"{(screened['EMA Trend'] == 'BULLISH').sum()}" if "EMA Trend" in screened.columns else "—")

    display_cols = [
        "Symbol", "Sector", "Price", "Market Cap (Cr)", "P/E", "ROE %", "ROCE %",
        "Debt/Equity", "Revenue Growth %", "Delivery %", "RSI 14", "EMA Trend",
        "Relative Strength", "Equity Score"
    ]
    avail_cols = [c for c in display_cols if c in ranked.columns]
    if ranked.empty:
        st.warning("No equities meet the active criteria.")
    else:
        st.dataframe(ranked[avail_cols], width="stretch", hide_index=True)


def _render_derivatives_screener():
    st.markdown("### Derivatives & Options Positioning Screener")
    try:
        derivs = build_derivatives_universe()
        ranked = rank_derivatives(derivs)
        summary_df = signal_summary(ranked)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Contracts", len(ranked))
        c2.metric("Signals Identified", len(summary_df))
        c3.metric("Top Strike", ranked.iloc[0]["Strike"] if not ranked.empty else "—")
        c4.metric("Avg IV", f"{ranked['IV %'].mean():.2f}%" if "IV %" in ranked.columns else "—")

        if not summary_df.empty:
            st.markdown("#### Signal Distribution Summary")
            st.dataframe(summary_df, width="stretch", hide_index=True)

        st.markdown("#### Ranked Derivatives Universe")
        st.dataframe(ranked, width="stretch", hide_index=True)
    except Exception as exc:
        st.error(f"Derivatives screener error: {exc}")


def _render_market_screener():
    st.markdown("### Market Breadth & Sector Velocity")
    try:
        m_df = build_market_universe()
        m_snap = market_summary(m_df)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Universe", f"{m_snap.get('Stocks', len(m_df))}")
        m2.metric("Advancing", f"{m_snap.get('Advancing', 0)}")
        m3.metric("Declining", f"{m_snap.get('Declining', 0)}")
        m4.metric("Breadth %", f"{m_snap.get('Breadth %', 0.0):.1f}%")
        m5.metric("Market Score", f"{m_snap.get('Market Score', 0.0):.1f}")

        st.dataframe(m_df, width="stretch", hide_index=True)
    except Exception as exc:
        st.error(f"Market breadth screener error: {exc}")


def _render_orderflow_screener():
    st.markdown("### Order Flow & Imbalance Screener")
    try:
        of_df = build_orderflow_universe()
        ranked = rank_orderflow(of_df)
        snap = orderflow_summary(ranked)

        o1, o2, o3, o4 = st.columns(4)
        o1.metric("Ranked Assets", len(ranked))
        o2.metric("Buy Aggression", snap.get("Buy Aggression Count", 0))
        o3.metric("Sell Aggression", snap.get("Sell Aggression Count", 0))
        o4.metric("Mean OF Score", f"{snap.get('Mean Score', 0.0):.1f}")

        st.dataframe(ranked, width="stretch", hide_index=True)
    except Exception as exc:
        st.error(f"Order flow screener error: {exc}")


def _render_quant_screener():
    st.markdown("### Quantitative Factor Screener")
    try:
        q_df = build_quant_universe()
        ranked = rank_quant(q_df)
        snap = quant_summary(ranked)

        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Quant Universe", len(ranked))
        q2.metric("Mean Reversion", snap.get("Mean Reversion Setups", 0))
        q3.metric("Trend Continuation", snap.get("Momentum Setups", 0))
        q4.metric("Top Quant Score", f"{ranked['Quant Score'].max():.1f}" if not ranked.empty and 'Quant Score' in ranked.columns else "—")

        st.dataframe(ranked, width="stretch", hide_index=True)
    except Exception as exc:
        st.error(f"Quant factor screener error: {exc}")


def _render_decision_intelligence():
    st.markdown("### Multi-Engine Decision Intelligence Fusion")
    try:
        m_df = build_market_universe()
        m_snap = market_summary(m_df)
        d_df = build_derivatives_universe()
        d_sig = signal_summary(d_df)
        d_snap = {
            "Signal": d_sig.iloc[0]["Signal"] if not d_sig.empty and "Signal" in d_sig.columns else "NEUTRAL",
            "Avg OI Change %": float(d_sig["Average OI Change %"].mean()) if not d_sig.empty and "Average OI Change %" in d_sig.columns else 0.0,
        }
        of_df = build_orderflow_universe()
        of_snap = orderflow_summary(of_df)
        q_df = build_quant_universe()
        q_snap = quant_summary(q_df)

        decision = build_decision_snapshot(
            market_summary=m_snap,
            derivatives_summary=d_snap,
            orderflow_summary=of_snap,
            quant_summary=q_snap,
        )
        fused = fuse_decision_snapshot(decision)

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Fused Action", fused.get("Action", "MONITOR"))
        d2.metric("Confidence", f"{fused.get('Confidence', 0.0):.1f}/100")
        d3.metric("Risk Posture", fused.get("Risk Posture", "MODERATE"))
        d4.metric("Timeframe Horizon", fused.get("Horizon", "INTRADAY"))

        st.markdown(f"**Action Rationale:** {fused.get('Rationale', 'Multi-factor model alignment.')}")
    except Exception as exc:
        st.error(f"Decision intelligence fusion note: {exc}")


def render_screener(ctx):
    subview = ctx.subview or "Equity"

    st.markdown("## 🔍 MULTI-ASSET & QUANTITATIVE SCREENER")

    mode = st.radio(
        "Screener Category",
        ["Equity", "Derivatives", "Market", "Order Flow", "Quant", "Decision Intelligence"],
        horizontal=True,
        index=[
            "Equity", "Derivatives", "Market", "Order Flow", "Quant", "Decision Intelligence"
        ].index(subview) if subview in [
            "Equity", "Derivatives", "Market", "Order Flow", "Quant", "Decision Intelligence"
        ] else 0,
        key="screener_subview_toggle",
    )

    if mode == "Derivatives":
        _render_derivatives_screener()
    elif mode == "Market":
        _render_market_screener()
    elif mode == "Order Flow":
        _render_orderflow_screener()
    elif mode == "Quant":
        _render_quant_screener()
    elif mode == "Decision Intelligence":
        _render_decision_intelligence()
    else:
        _render_equity_screener()
