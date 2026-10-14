"""IFIT Command Center Workspace — V0.8.0 Consolidated Intelligence Terminal.
Synthesizes market state, regime, signals, risk layers, scenario stress, and portfolio diagnostics.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from engines.consolidated_engine import build_consolidated_intelligence


@st.cache_data(ttl=8, show_spinner=False)
def _ifit_v080_cached(spot_val, days_val, atm_iv_val, hv_val, flow_levels_val, imbalance_val):
    return build_consolidated_intelligence(
        spot=float(spot_val),
        days=int(days_val),
        atm_iv=float(atm_iv_val),
        hv30=float(hv_val),
        flow_levels=int(flow_levels_val),
        imbalance_ratio=float(imbalance_val),
        active_alerts=0,
    )


def render_command_center(ctx, spot: float, days: int, atm_iv: float, hv30: float, flow_levels: int, imbalance_ratio: float):
    st.markdown("## ⚡ COMMAND CENTER — CONSOLIDATED INTELLIGENCE TERMINAL")
    st.caption(
        "Real-time synchronized terminal snapshot across market state, regime classification, "
        "signal synthesis, volatility surface, model dislocations, scenarios, portfolio risk, and execution quality."
    )

    try:
        x = _ifit_v080_cached(spot, days, atm_iv, hv30, flow_levels, imbalance_ratio)
    except Exception as exc:
        st.error(f"Command Center consolidation unavailable: {type(exc).__name__}: {exc}")
        return

    # Executive KPI Metrics Row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("IFIT SCORE", f"{x['overall_score']:.1f}/100")
    c2.metric("OPERATING STATE", x["operating_state"])
    c3.metric("DIRECTION", x["signal"]["direction"])
    c4.metric("CONVICTION", f"{x['signal']['conviction']:.1f}/100")
    c5.metric("RISK REGIME", x["risk"]["regime"])
    c6.metric("CONFIDENCE", f"{x['executive_confidence']:.1f}/100")

    state = x["operating_state"]
    if state == "RISK CONTROL":
        st.error("🛑 **OPERATING STATE: RISK CONTROL** — Downside risk constraints dominate directional edge.")
    elif state == "HIGH-CONVICTION":
        st.success("🟢 **OPERATING STATE: HIGH-CONVICTION** — Multi-layer confluence across trend, order flow, and skew.")
    elif state == "WATCHLIST":
        st.warning("🟠 **OPERATING STATE: WATCHLIST** — Partial confluence present; awaiting confirmation.")
    elif state == "EXECUTION CONSTRAINED":
        st.warning("🟡 **OPERATING STATE: EXECUTION CONSTRAINED** — Spread or depth limits active positioning.")
    else:
        st.info("⚪ **OPERATING STATE: NEUTRAL / RANGE** — Edge is within normal statistical noise.")

    # Executive Market Map
    st.markdown("### Executive Market Map")
    a, b, c, d, e, f = st.columns(6)
    a.metric("Market State", f"{x['market']['score']:.1f}/100", x["market"]["regime"])
    b.metric("Regime", x["regime"]["regime"], f"{x['regime']['confidence']:.1f}/100")
    c.metric("Flow Score", f"{x['market']['flow_score']}/100", x["market"]["flow_regime"])
    d.metric("Volatility", f"{x['market']['vol_score']:.1f}/100", x["market"]["vol_regime"])
    e.metric("Model Dislocation", f"{x['market']['mean_dislocation']:.1f}/100")
    f.metric("Execution Quality", f"{x['liquidity']['score']:.1f}/100", x["liquidity"]["regime"])

    st.info(
        f"**{ctx.instrument}**: ₹{x['spot']:,.2f} • ATM Strike: {x['atm']:,.0f} • "
        f"Expected Range: ₹{x['expected_low']:,.0f} — ₹{x['expected_high']:,.0f} • "
        f"PCR: {x['market']['pcr']:.2f} • IV-HV Spread: {x['market']['iv_premium']:+.2f} pts"
    )

    # Decision Matrix & Risk/Execution
    left, right = st.columns(2)
    with left:
        st.markdown("### Decision Matrix")
        st.dataframe(
            pd.DataFrame([
                ["Setup", x["decision"]["setup"]],
                ["Direction Bias", x["decision"]["direction_bias"]],
                ["Directional Score", f"{x['decision']['directional_score']:.1f}/100"],
                ["Confirmation", f"{x['decision']['confirmation_score']:.1f}/100"],
                ["Risk Level", f"{x['decision']['risk_level']} ({x['decision']['risk_score']:.1f}/100)"],
                ["Location", x["decision"]["location"]],
                ["Confirmation Rule", x["decision"]["confirmation_rule"]],
                ["Invalidation Point", x["decision"]["invalidation"]],
            ], columns=["Dimension", "Terminal Diagnostic"]),
            width="stretch", hide_index=True
        )
    with right:
        st.markdown("### Risk & Microstructure")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Risk Score", f"{x['risk']['overall_score']:.1f}")
        r2.metric("Portfolio Risk", f"{x['portfolio']['score']:.1f}")
        r3.metric("Liquidity", f"{x['liquidity']['score']:.1f}")
        r4.metric("Microstructure", f"{x['microstructure']['score']:.1f}")
        st.markdown(
            f"**Tail Bias:** {x['risk']['tail_bias']}  \n"
            f"**Portfolio Tail:** {x['portfolio']['tail_bias']}  \n"
            f"**Execution Regime:** {x['liquidity']['regime']} / {x['microstructure']['regime']}"
        )
        if isinstance(x["risk"].get("drivers"), pd.DataFrame) and not x["risk"]["drivers"].empty:
            driver_name = x["risk"]["drivers"].iloc[0].get("Risk Driver", "Market Volatility")
            st.warning(f"**Primary Risk Driver:** {driver_name}")

    # Evidence Ladder
    st.markdown("### Cross-Engine Evidence Confluence")
    evidence = pd.DataFrame([
        ["Direction", x["signal"]["direction"], f"{x['signal']['direction_score']:.1f}", "Price action + flow + PCR"],
        ["Conviction", x["signal"]["conviction_label"], f"{x['signal']['conviction']:.1f}", "Cross-module consensus"],
        ["Regime", x["regime"]["regime"], f"{x['regime']['confidence']:.1f}", "Trend + vol + risk state"],
        ["Volatility", x["market"]["vol_regime"], f"{x['market']['vol_score']:.1f}", "IV premium / skew / surface"],
        ["Risk", x["risk"]["regime"], f"{x['risk']['overall_score']:.1f}", "Tail risk / dislocation / flow"],
        ["Execution", x["liquidity"]["regime"], f"{x['liquidity']['score']:.1f}", "Spread + depth + size elasticity"],
        ["Microstructure", x["microstructure"]["regime"], f"{x['microstructure']['score']:.1f}", "Quote + order book imbalance"],
        ["Portfolio", x["portfolio"]["regime"], f"{x['portfolio']['score']:.1f}", "Greeks + concentration + stress"],
    ], columns=["Layer", "Reading", "Score", "Methodology"])
    st.dataframe(evidence, width="stretch", hide_index=True)

    # Stress & Tail Map
    st.markdown("### Stress & Tail Map")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Scenarios", f"{x['scenario']['total']:,}")
    s2.metric("Breach Count", f"{x['scenario']['outside_count']:,}")
    s3.metric("Max Gain Scenario", f"₹{x['scenario']['best']['Approx P&L']:,.2f}")
    s4.metric("Max Loss Scenario", f"₹{x['scenario']['worst']['Approx P&L']:,.2f}")

    scenario_df = x["scenario"]["rows"].copy()
    pivot = scenario_df.pivot_table(
        index="Spot Shock", columns="IV Shock", values="Approx P&L", aggfunc="mean"
    )
    st.dataframe(pivot.round(2), width="stretch")

    # Key Levels & Execution Impact
    l1, l2 = st.columns(2)
    with l1:
        st.markdown("### Key Price Levels")
        levels = pd.DataFrame(x["signal"]["levels"])
        levels.columns = ["Level", "Price"]
        st.dataframe(levels.round(2), width="stretch", hide_index=True)
    with l2:
        st.markdown("### Liquidity & Execution Impact")
        ladder = x["microstructure"]["ladder"].copy()
        if not ladder.empty and len(ladder.columns) >= 7:
            display_ladder = ladder.iloc[:, [0, 1, 2, 3, 4, 6, 7]].copy() if len(ladder.columns) >= 8 else ladder
            st.dataframe(display_ladder.round(2), width="stretch", hide_index=True)
        else:
            st.info("Execution depth ladder is currently synchronizing.")

    # Portfolio Risk Snapshot
    st.markdown("### Portfolio Greek Exposure & Attribution")
    p = x["portfolio"]
    if isinstance(p.get("attribution"), pd.DataFrame) and not p["attribution"].empty:
        st.dataframe(p["attribution"].round(4), width="stretch", hide_index=True)
    else:
        st.info("Portfolio attribution ready for position input.")
