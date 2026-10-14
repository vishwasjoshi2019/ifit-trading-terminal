"""IFIT Risk Engine Workspace.
Cross-engine institutional risk diagnostics: volatility, convexity, model dislocation,
signal uncertainty, regime confidence, flow pressure, and scenario stress testing.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from engines.risk_engine import build_risk_engine
from engines.live_market_intelligence_engine import build_market_intelligence
from engines.ifit_regime_engine import classify_regime
from engines.ifit_signal_engine import build_signal


def render_risk_engine(ctx, spot: float, days: int, atm_iv: float, hv30: float, flow_levels: int, imbalance_ratio: float):
    st.markdown("## 🛡️ RISK ENGINE — CROSS-ASSET RISK DIAGNOSTICS")
    st.caption("Terminal-level institutional risk synthesis. Evaluates non-linear convexity, model dislocation, and tail risks.")

    try:
        mi = build_market_intelligence(
            float(spot), int(days), float(atm_iv), float(hv30),
            int(flow_levels), float(imbalance_ratio), r_percent=6.0
        )
        move = float(mi["option_metrics"].get("move", 0.0))
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
            max_pain=spot,
        )

        risk_res = build_risk_engine(
            market_score=mi["score"],
            regime_confidence=reg["confidence"],
            flow_score=mi["flow_score"],
            vol_score=mi["vol_score"],
            gamma_risk=mi["gamma_risk"],
            model_dislocation=mi["mean_dislocation"],
            signal_confirmation=sig["conviction"],
            direction_score=sig["conviction"],
            event_count=0,
            active_alerts=0,
            scenario_stats=None,
        )

        r1, r2, r3, r4, r5 = st.columns(5)
        r1.metric("RISK SCORE", f"{risk_res['overall_score']:.1f}/100")
        r2.metric("RISK REGIME", risk_res["regime"])
        r3.metric("TAIL BIAS", risk_res["tail_bias"])
        r4.metric("GAMMA RISK", f"{mi['gamma_risk']:.1f}/100")
        r5.metric("MODEL DISLOCATION", f"{mi['mean_dislocation']:.1f}/100")

        if risk_res["regime"] == "RISK CONTROL":
            st.error("🛑 **RISK STATUS: HIGH ALERT / RISK CONTROL** — Extreme tail convexity or dislocation detected.")
        elif risk_res["regime"] == "ELEVATED":
            st.warning("🟠 **RISK STATUS: ELEVATED** — Monitor gamma concentration and implied volatility spikes.")
        else:
            st.success("🟢 **RISK STATUS: STABLE / CONTROLLED** — Cross-engine risk parameters within baseline limits.")

        # Risk Drivers Breakdown
        st.markdown("### Risk Factor Breakdown & Attribution")
        if isinstance(risk_res.get("drivers"), pd.DataFrame) and not risk_res["drivers"].empty:
            st.dataframe(risk_res["drivers"], width="stretch", hide_index=True)

        st.info(risk_res.get("summary", "Risk assessment derived from synchronized market and option surface data."))

    except Exception as exc:
        st.error(f"Risk engine diagnostics error: {exc}")
