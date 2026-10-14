"""IFIT Markets Workspace.
Real-time market state, trend regime classification, order flow confluence, and signal synthesis.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from engines.live_market_intelligence_engine import build_market_intelligence
from engines.ifit_regime_engine import classify_regime
from engines.ifit_signal_engine import build_signal


@st.cache_data(ttl=10, show_spinner=False)
def _get_market_intel(spot: float, days: int, atm_iv: float, hv30: float, flow_levels: int, imbalance_ratio: float):
    return build_market_intelligence(
        float(spot), int(days), float(atm_iv), float(hv30),
        int(flow_levels), float(imbalance_ratio), r_percent=6.0
    )


def render_markets(ctx, spot: float, days: int, atm_iv: float, hv30: float, flow_levels: int, imbalance_ratio: float):
    st.markdown("## 📈 MARKETS & MACRO REGIME")
    st.caption("Consolidated market state, order flow dynamics, volatility surface, and quantitative regime classification.")

    try:
        mi = _get_market_intel(spot, days, atm_iv, hv30, flow_levels, imbalance_ratio)
    except Exception as exc:
        st.error(f"Market intelligence engine unavailable: {exc}")
        return

    om = mi.get("option_metrics", {})
    move = om.get("move", spot * 0.015)
    max_pain = om.get("max_pain", spot)

    # Top KPI Metrics
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric(ctx.instrument, f"₹{spot:,.2f}")
    c2.metric("MARKET STATE", f"{mi['score']:.1f}/100", mi["regime"])
    c3.metric("PCR", f"{mi['pcr']:.2f}")
    c4.metric("IV − HV", f"{mi['iv_premium']:+.2f} pts")
    c5.metric("FLOW CONFLUENCE", f"{mi['flow_score']:.0f}/100", mi["flow_regime"])
    c6.metric("VOLATILITY", f"{mi['vol_score']:.0f}/100", mi["vol_regime"])

    st.info(
        f"**Expected Range:** ₹{spot - move:,.0f} — ₹{spot + move:,.0f} • "
        f"**Max Pain Strike:** ₹{max_pain:,.0f} • "
        f"**Gamma Expiry Risk:** {mi.get('gamma_risk', 0.0):.1f}/100"
    )

    # Subviews
    subview = ctx.subview or "Overview"

    if subview in ("Overview", "Executive Overview"):
        col_left, col_right = st.columns([2.2, 1])
        with col_left:
            st.markdown("### Simulated Intraday Price & Liquidity Path")
            rng = np.random.default_rng(42)
            sim_prices = spot * np.exp(np.cumsum(rng.normal(0, 0.0015, 180)))
            df_chart = pd.DataFrame({"Spot Price": sim_prices})
            st.line_chart(df_chart, height=320)
        with col_right:
            st.markdown("### Structural Map")
            st.metric("Trend Regime", mi["regime"])
            st.metric("Flow Regime", mi["flow_regime"])
            st.metric("Volatility Regime", mi["vol_regime"])
            st.metric("Model Dislocation", f"{mi['mean_dislocation']:.1f}/100")

        # Market Drivers & Risk Flags
        d_left, d_right = st.columns(2)
        with d_left:
            st.markdown("### Core Market Drivers")
            if mi.get("drivers"):
                driver_df = pd.DataFrame(mi["drivers"])
                if "impact" in driver_df.columns:
                    driver_df["Impact"] = driver_df["impact"].map(lambda x: f"{x:+.1f}")
                driver_df = driver_df.rename(columns={"name": "Driver", "reading": "Reading"})
                st.dataframe(driver_df[["Driver", "Impact", "Reading"]], width="stretch", hide_index=True)
        with d_right:
            st.markdown("### Active Market Risk Flags")
            risks = mi.get("risks", [])
            if risks:
                for r in risks:
                    st.warning(r)
            else:
                st.success("No active critical risk flags identified.")

    elif subview in ("Regime Classifier", "Regime"):
        st.markdown("### Quantitative Regime Classification")
        try:
            reg = classify_regime(
                market_score=mi["score"],
                market_confidence=mi["confidence"],
                flow_score=mi["flow_score"],
                vol_score=mi["vol_score"],
                vol_regime=mi["vol_regime"],
                gamma_risk=mi.get("gamma_risk", 0.0),
                mean_dislocation=mi["mean_dislocation"],
                pcr=mi["pcr"],
                iv_premium=mi["iv_premium"],
            )
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Classified Regime", reg.get("regime", "NEUTRAL"))
            r2.metric("Regime Confidence", f"{reg.get('confidence', 0.0):.1f}/100")
            r3.metric("Directional Strength", f"{reg.get('directional_strength', 0.0):.1f}/100")
            r4.metric("Risk Intensity", f"{reg.get('risk_intensity', 0.0):.1f}/100")
            st.markdown(f"**Regime Summary:** {reg.get('summary', 'Market regime classified from multi-factor inputs.')}")
        except Exception as exc:
            st.warning(f"Regime classifier error: {exc}")

    elif subview in ("Signal Confluence", "Signals"):
        st.markdown("### Multi-Strategy Signal Synthesis")
        try:
            reg = classify_regime(
                market_score=mi["score"],
                market_confidence=mi["confidence"],
                flow_score=mi["flow_score"],
                vol_score=mi["vol_score"],
                vol_regime=mi["vol_regime"],
                gamma_risk=mi.get("gamma_risk", 0.0),
                mean_dislocation=mi["mean_dislocation"],
                pcr=mi["pcr"],
                iv_premium=mi["iv_premium"],
            )
            sig = build_signal(
                market_score=mi["score"],
                market_confidence=mi["confidence"],
                market_regime=reg["regime"],
                regime_confidence=reg["confidence"],
                directional_strength=reg["directional_strength"],
                flow_score=mi["flow_score"],
                vol_score=mi["vol_score"],
                vol_regime=mi["vol_regime"],
                gamma_risk=mi.get("gamma_risk", 0.0),
                mean_dislocation=mi["mean_dislocation"],
                spot=spot,
                atm_strike=spot,
                expected_low=spot - move,
                expected_high=spot + move,
                pcr=mi["pcr"],
                max_pain=max_pain,
            )
            s1, s2, s3 = st.columns(3)
            s1.metric("Direction", sig.get("direction", "NEUTRAL"))
            s2.metric("Conviction Score", f"{sig.get('conviction', 0.0):.1f}/100")
            s3.metric("Conviction Label", sig.get("conviction_label", "N/A"))
            if sig.get("levels"):
                st.markdown("#### Key Synthesized Levels")
                st.dataframe(pd.DataFrame(sig["levels"]), width="stretch", hide_index=True)
        except Exception as exc:
            st.warning(f"Signal synthesizer error: {exc}")

    else:
        st.info(f"Market subview '{subview}' active.")
