"""IFIT Options Workspace.
Institutional option chain matrix, BSM Greeks (primary and higher-order),
implied volatility surface, Heston stochastic volatility calibration,
gamma exposure (GEX), and execution liquidity diagnostics.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from engines.options_engine import build_option_chain, calculate_metrics
from engines.volatility_engine import expected_move_table, gamma_exposure
from engines.live_greeks_engine import bsm_greeks
from engines.live_vol_surface_engine import build_surface, surface_summary, term_structure
from engines.live_heston_engine import calibrate_live_heston
from engines.live_model_dislocation_engine import analyze_live_dislocation
from engines.live_vol_signal_engine import build_vol_signal
from engines.liquidity_execution_engine import build_liquidity_execution


def _render_chain_view(chain: pd.DataFrame, om: dict, spot: float, days: int, atm_iv: float, hv30: float):
    st.markdown("### Institutional Option Chain Matrix")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("SPOT", f"₹{spot:,.2f}")
    c2.metric("ATM STRIKE", f"{om['atm']:,.0f}")
    c3.metric("PCR", f"{om['pcr']:.2f}")
    c4.metric("ATM IV", f"{atm_iv:.2f}%")
    c5.metric("IV / HV", f"{atm_iv / max(hv30, 0.01):.2f}x")
    c6.metric("MAX PAIN", f"{om['max_pain']:,.0f}")

    move = om.get("move", spot * 0.015)
    st.info(f"**1σ Expected Expiry Range:** ₹{spot - move:,.0f} — ₹{spot + move:,.0f}")

    near = chain.iloc[(chain["Strike"] - spot).abs().argsort()[:15]].sort_values("Strike")
    display_positions = [1, 2, 3, 4, 5, 6, 17, 0, 10, 11, 12, 9, 15, 16]

    if len(near.columns) > max(display_positions):
        display = near.iloc[:, display_positions].copy()
        display.columns = [
            "CE OI", "CE Δ OI", "CE LTP", "CE IV", "CE Delta", "CE Gamma", "Moneyness",
            "Strike", "PE IV", "PE Delta", "PE Gamma", "PE LTP", "PE Δ OI", "PE OI"
        ]
        st.dataframe(display, width="stretch", hide_index=True, height=430)
    else:
        st.dataframe(near, width="stretch", hide_index=True)

    a, b, c = st.columns(3)
    with a:
        st.markdown("### Implied Volatility Smile")
        if "CE IV" in chain.columns and "PE IV" in chain.columns:
            st.line_chart(chain[["Strike", "CE IV", "PE IV"]].set_index("Strike"), height=260)
    with b:
        st.markdown("### Gamma Exposure (GEX)")
        gdf = gamma_exposure(chain)
        st.bar_chart(gdf.set_index("Strike"), height=260)
    with c:
        st.markdown("### Expected Move Horizon")
        st.dataframe(expected_move_table(spot, atm_iv, days), width="stretch", hide_index=True)


def _render_greeks_view(chain: pd.DataFrame, spot: float, days: int, atm_iv: float):
    st.markdown("### ⚡ Live BSM Greeks Engine (Primary & Higher-Order)")
    st.caption("Analytical Black-Scholes-Merton model outputs with full Greeks hierarchy.")

    rate = 6.0
    T = max(float(days), 1.0) / 365.0
    rows = []
    for _, r in chain.iterrows():
        for side in ("CE", "PE"):
            iv = float(r[f"{side} IV"])
            g = bsm_greeks(float(spot), float(r["Strike"]), T, rate / 100.0, iv, side).as_dict()
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
    atm_strike = min(strikes, key=lambda x: abs(float(x) - float(spot)))
    atm = df[df["Strike"] == atm_strike]
    ce = atm[atm["Option"] == "CE"]
    pe = atm[atm["Option"] == "PE"]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Spot Price", f"₹{spot:,.2f}")
    c2.metric("ATM Strike", f"{atm_strike:,.0f}")
    if not ce.empty:
        c3.metric("CE Delta", f"{float(ce.iloc[0]['delta']):.4f}")
        c4.metric("PE Delta", f"{float(pe.iloc[0]['delta']):.4f}")
        c5.metric("ATM Gamma", f"{float(ce.iloc[0]['gamma']):.6f}")

    cols = [
        "Strike", "Option", "LTP", "OI", "IV", "delta", "gamma", "theta", "vega", "rho",
        "vanna", "vomma", "charm", "zomma", "speed", "color", "ultima", "veta"
    ]
    st.dataframe(df[cols].round(6), width="stretch", hide_index=True)


def _render_volatility_view(chain: pd.DataFrame, spot: float, atm_iv: float, hv30: float, days: int):
    st.markdown("### ⚡ Live Volatility Surface & Intelligence")
    rows = build_surface(chain, spot)
    if not rows:
        st.warning("Insufficient IV points to reconstruct volatility surface.")
        return

    df = pd.DataFrame(rows)
    summary = surface_summary(rows, spot)
    ts = pd.DataFrame(term_structure(rows))

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Live ATM IV", f"{summary['atm_iv']:.2f}%")
    c2.metric("Put Skew", f"{summary['put_skew']:+.2f} vol pts")
    c3.metric("Call Skew", f"{summary['call_skew']:+.2f} vol pts")
    c4.metric("Smile Curvature", f"{summary['smile']:+.2f} vol pts")
    c5.metric("Observed Points", f"{summary['strikes']} strikes")

    left, right = st.columns(2)
    with left:
        st.markdown("**Live IV Smile (Moneyness %)**")
        smile = df.copy()
        smile["moneyness"] = smile["moneyness_pct"]
        pivot = smile.pivot_table(index="moneyness", columns="option", values="iv", aggfunc="mean").sort_index()
        st.line_chart(pivot, height=280)
    with right:
        st.markdown("**Term Structure & Skew**")
        if len(ts):
            st.dataframe(ts.round(4), width="stretch", hide_index=True)

    try:
        vi = build_vol_signal(spot, chain, atm_iv, hv30, days, 6.0)
        st.markdown("#### Volatility Signal Confluence")
        v1, v2, v3 = st.columns(3)
        v1.metric("Volatility Regime", vi.get("regime", "NORMAL"))
        v2.metric("Intelligence Score", f"{vi.get('score', 0.0):.1f}/100")
        v3.metric("IV Premium", f"{vi.get('iv_premium', 0.0):+.2f} pts")
    except Exception:
        pass


def _render_heston_view(chain: pd.DataFrame, spot: float, days: int):
    st.markdown("### ⚡ Heston Stochastic Volatility Calibration")
    try:
        calib = calibrate_live_heston(float(spot), chain, int(days), 6.0, max_nfev=12)
        params = calib.get("params", {})
        h1, h2, h3, h4, h5 = st.columns(5)
        h1.metric("Initial Var (v0)", f"{params.get('v0', 0.0):.4f}")
        h2.metric("Mean Rev Rate (κ)", f"{params.get('kappa', 0.0):.3f}")
        h3.metric("Long Run Var (θ)", f"{params.get('theta', 0.0):.4f}")
        h4.metric("Vol of Vol (σ)", f"{params.get('sigma', 0.0):.4f}")
        h5.metric("Correlation (ρ)", f"{params.get('rho', 0.0):.4f}")

        analysis = analyze_live_dislocation(float(spot), chain, int(days), 6.0)
        st.markdown("#### Heston Dynamics & Model Risk")
        st.dataframe(pd.DataFrame(analysis.get("table", [])), width="stretch", hide_index=True)
    except Exception as exc:
        st.info(f"Heston calibration note: {exc}")


def _render_execution_view(chain: pd.DataFrame, spot: float):
    st.markdown("### ⚡ Option Liquidity & Execution Engine")
    try:
        result = build_liquidity_execution(chain_df=chain, spot=float(spot), multiplier=50)
        a, b, c, d, e = st.columns(5)
        a.metric("LIQUIDITY SCORE", f"{result['score']:.1f}/100")
        a.metric("EXECUTION REGIME", result["regime"])
        c.metric("EXECUTION RISK", f"{result['execution_risk']:.1f}")
        d.metric("MEDIAN SPREAD", f"{result['summary'].get('median_spread_bps', 0):.1f} bps")
        e.metric("P90 SPREAD", f"{result['summary'].get('p90_spread_bps', 0):.1f} bps")

        st.markdown("**ATM Execution Ladder & Estimated Slippage**")
        ladder = result.get("atm_ladder", pd.DataFrame())
        if not ladder.empty:
            st.dataframe(ladder, width="stretch", hide_index=True)
    except Exception as exc:
        st.warning(f"Liquidity & execution engine note: {exc}")


def render_options(ctx, spot: float, days: int, atm_iv: float, hv30: float):
    subview = ctx.subview or "Option Chain"
    chain = build_option_chain(spot, days, atm_iv)
    om = calculate_metrics(chain, spot, days, atm_iv)

    if subview in ("Greeks", "Live Greeks"):
        _render_greeks_view(chain, spot, days, atm_iv)
    elif subview in ("Volatility", "Vol Surface"):
        _render_volatility_view(chain, spot, atm_iv, hv30, days)
    elif subview in ("OI & Gamma", "Gamma"):
        st.markdown("### Open Interest & Gamma Exposure Matrix")
        gdf = gamma_exposure(chain)
        st.bar_chart(gdf.set_index("Strike"), height=380)
        _render_greeks_view(chain, spot, days, atm_iv)
    elif subview in ("Heston", "Stochastic Vol"):
        _render_heston_view(chain, spot, days)
    elif subview in ("Execution", "Liquidity"):
        _render_execution_view(chain, spot)
    else:
        _render_chain_view(chain, om, spot, days, atm_iv, hv30)
