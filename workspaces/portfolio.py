"""IFIT Portfolio Workspace.
Portfolio Greek attribution, concentration risk, multi-dimensional stress testing,
and quantitative hedge optimization (delta, gamma, vega rebalancing).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from engines.portfolio_risk_engine import build_portfolio_risk
from engines.portfolio_greeks_engine import portfolio_greeks
from engines.hedging_engine import (
    PortfolioExposure,
    build_demo_hedge_universe,
    hedge_recommendation,
    hedge_summary,
    optimize_combined_hedges,
    optimize_single_hedges,
)


def _render_portfolio_risk(ctx, spot: float, days: int, atm_iv: float):
    st.markdown("### Portfolio Greek Exposure & Stress Attribution")
    st.caption("Positions matrix with first-order and higher-order Greeks aggregation and concentration risk.")

    default_positions = [
        {"Instrument": "NIFTY 25000 CE", "Side": "BUY", "Qty": 1, "Multiplier": 50, "Strike": 25000, "DTE": 14, "IV": atm_iv},
        {"Instrument": "NIFTY 24700 PE", "Side": "BUY", "Qty": 1, "Multiplier": 50, "Strike": 24700, "DTE": 14, "IV": atm_iv + 0.3},
        {"Instrument": "NIFTY 24900 CE", "Side": "SELL", "Qty": 1, "Multiplier": 50, "Strike": 24900, "DTE": 14, "IV": atm_iv + 0.1},
    ]

    st.markdown("#### Active Portfolio Book")
    pos_df = pd.DataFrame(default_positions)
    edited = st.data_editor(
        pos_df,
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        column_config={
            "Side": st.column_config.SelectboxColumn("Side", options=["BUY", "SELL"]),
            "Qty": st.column_config.NumberColumn("Qty", min_value=1, step=1),
            "Multiplier": st.column_config.NumberColumn("Multiplier", min_value=1, step=1),
            "Strike": st.column_config.NumberColumn("Strike", min_value=1, step=50),
            "DTE": st.column_config.NumberColumn("DTE", min_value=1, step=1),
            "IV": st.column_config.NumberColumn("IV %", min_value=0.1, step=0.1),
        },
        key="portfolio_positions_editor",
    )

    try:
        pos_rows = []
        for p in edited.to_dict("records"):
            if not p.get("Instrument"):
                continue
            inst = str(p["Instrument"])
            opt = "PE" if inst.upper().endswith("PE") or " PE" in inst.upper() else "CE"
            pos_rows.append({
                "Instrument": inst,
                "Side": str(p.get("Side", "BUY")),
                "Qty": float(p.get("Qty", 1)),
                "Multiplier": float(p.get("Multiplier", 50)),
                "Strike": float(p.get("Strike", spot)),
                "DTE": float(p.get("DTE", days)),
                "IV": float(p.get("IV", atm_iv)),
                "Option": opt,
            })

        pg_df, totals = portfolio_greeks(pos_rows, float(spot), r_percent=6.5, q_percent=0.0)
        st.session_state["ifit_portfolio_totals"] = totals

        if not totals:
            st.info("Add portfolio positions to compute Greeks and risk diagnostics.")
            return

        result = build_portfolio_risk(positions_df=pg_df, totals=totals, spot=float(spot))

        # Risk Metrics Row
        a, b, c, d, e, f = st.columns(6)
        a.metric("PORTFOLIO RISK", f"{result['score']:.1f}/100")
        b.metric("RISK REGIME", result["regime"])
        c.metric("NET DELTA", f"{totals.get('delta', 0.0):+.2f}")
        d.metric("NET GAMMA", f"{totals.get('gamma', 0.0):+.4f}")
        e.metric("NET VEGA", f"{totals.get('vega', 0.0):+.1f}")
        f.metric("NET THETA", f"₹{totals.get('theta', 0.0) / 365.0:+.2f}/day")

        st.markdown("#### Position-Level Greek Attribution")
        st.dataframe(pg_df, width="stretch", hide_index=True)

        if isinstance(result.get("stress"), pd.DataFrame) and not result["stress"].empty:
            st.markdown("#### Stress Grid (Spot × Volatility)")
            st.dataframe(result["stress"], width="stretch", hide_index=True)

    except Exception as exc:
        st.error(f"Portfolio calculation note: {exc}")


def _render_hedging_intelligence(ctx, spot: float):
    st.markdown("### ⚡ Quantitative Hedge Optimization")
    st.caption("Calculates optimal hedging candidates to neutralize unwanted delta, gamma, and vega risk.")

    totals = st.session_state.get("ifit_portfolio_totals", {})

    delta_val = float(totals.get("delta", 42.0))
    gamma_val = float(totals.get("gamma", -0.65))
    vega_val = float(totals.get("vega", -18.0))
    theta_val = float(totals.get("theta", -7.0))

    exposure = PortfolioExposure(
        delta=delta_val,
        gamma=gamma_val,
        vega=vega_val,
        theta=theta_val,
    )

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Unhedged Delta", f"{exposure.delta:+.2f}")
    h2.metric("Unhedged Gamma", f"{exposure.gamma:+.4f}")
    h3.metric("Unhedged Vega", f"{exposure.vega:+.2f}")
    h4.metric("Unhedged Theta", f"{exposure.theta:+.2f}")

    universe = build_demo_hedge_universe()
    singles = optimize_single_hedges(exposure, universe)
    combined = optimize_combined_hedges(exposure, universe)
    summary = hedge_summary(exposure, singles)
    recom = hedge_recommendation(exposure, singles)

    st.markdown("#### Top Single-Leg Hedge Recommendations")
    if isinstance(singles, pd.DataFrame) and not singles.empty:
        st.dataframe(singles, width="stretch", hide_index=True)
    elif isinstance(singles, list):
        st.dataframe(pd.DataFrame(singles), width="stretch", hide_index=True)

    st.markdown("#### Multi-Leg Structural Hedge Solutions")
    if isinstance(combined, pd.DataFrame) and not combined.empty:
        st.dataframe(combined, width="stretch", hide_index=True)
    elif isinstance(combined, list):
        st.dataframe(pd.DataFrame(combined), width="stretch", hide_index=True)


def render_portfolio(ctx, spot: float, days: int = 14, atm_iv: float = 14.5):
    subview = ctx.subview or "Portfolio"

    st.markdown("## 💼 PORTFOLIO RISK & HEDGING")

    mode = st.radio(
        "Workspace View",
        ["Portfolio", "Hedging Intelligence"],
        horizontal=True,
        index=0 if subview != "Hedging Intelligence" else 1,
        key="portfolio_mode_toggle",
    )

    if mode == "Hedging Intelligence":
        _render_hedging_intelligence(ctx, spot)
    else:
        _render_portfolio_risk(ctx, spot, days, atm_iv)
