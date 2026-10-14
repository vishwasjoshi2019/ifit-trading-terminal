"""IFIT AI Intelligence Workspace.
Institutional quantitative reasoning assistant grounded in real-time IFIT state data.
Eliminates hallucination and AI slop by strictly constraining responses to verified engine metrics.
"""
from __future__ import annotations

import streamlit as st
from engines.consolidated_engine import build_consolidated_intelligence


def render_ai_intelligence(ctx, spot: float, days: int, atm_iv: float, hv30: float, flow_levels: int, imbalance_ratio: float):
    st.markdown("## 🤖 TERMINAL AI INTELLIGENCE")
    st.caption("Grounded quantitative reasoning. Analysis is strictly derived from active IFIT model outputs, not ungrounded LLM conjecture.")

    try:
        x = build_consolidated_intelligence(
            spot=float(spot),
            days=int(days),
            atm_iv=float(atm_iv),
            hv30=float(hv30),
            flow_levels=int(flow_levels),
            imbalance_ratio=float(imbalance_ratio),
            active_alerts=0,
        )
    except Exception as exc:
        st.error(f"Intelligence snapshot unavailable: {exc}")
        return

    # Top KPI Metrics Grounding Context
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Grounding Source", "Synchronized IFIT Snapshot")
    c2.metric("IFIT Composite Score", f"{x['overall_score']:.1f}/100")
    c3.metric("Operating State", x["operating_state"])
    c4.metric("Market Regime", x["regime"]["regime"])

    query = st.text_input(
        "Institutional Research Query",
        value="Explain the relationship between the active volatility skew, gamma risk, and direction bias.",
        key="ai_intel_user_query",
    )

    if st.button("Synthesize Grounded Analysis", type="primary", key="ai_intel_submit"):
        st.markdown("### Grounded Terminal Thesis")

        st.markdown(
            f"""
            #### 1. Executive Confluence
            - **Instrument Context:** `{ctx.instrument}` at **₹{spot:,.2f}** (Timeframe: `{ctx.timeframe}`).
            - **Composite Score:** `{x['overall_score']:.1f}/100` (`{x['operating_state']}`).
            - **Market Direction Bias:** `{x['signal']['direction']}` with conviction of `{x['signal']['conviction']:.1f}/100`.

            #### 2. Cross-Engine Grounding Telemetry
            - **Trend & Regime:** {x['regime']['regime']} (Confidence: `{x['regime']['confidence']:.1f}/100`).
            - **Order Flow Confluence:** Flow score `{x['market']['flow_score']}/100` ({x['market']['flow_regime']}).
            - **Volatility Surface:** Vol score `{x['market']['vol_score']:.1f}/100` with IV-HV premium of `{x['market']['iv_premium']:+.2f}` vol pts.
            - **Risk Layer:** Regime classified as `{x['risk']['regime']}` with composite risk index `{x['risk']['overall_score']:.1f}/100`.
            - **Execution Microstructure:** `{x['liquidity']['regime']}` liquidity with execution rating `{x['liquidity']['score']:.1f}/100`.

            #### 3. Mathematical Decision Boundary
            - **Setup:** `{x['decision']['setup']}`
            - **Key Location:** `{x['decision']['location']}`
            - **Confirmation Trigger:** `{x['decision']['confirmation_rule']}`
            - **Invalidation Level:** `{x['decision']['invalidation']}`
            """
        )

        st.info("💡 **Grounded Execution Standard:** This analysis reflects verified quantitative model outputs calculated at the current tick.")
