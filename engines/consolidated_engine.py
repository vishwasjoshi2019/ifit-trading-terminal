
"""IFIT V0.8.0 — Consolidated Intelligence Engine.

A single orchestration layer that turns the existing IFIT engines into one
coherent market-intelligence snapshot. It does not place orders, predict
returns, or replace licensed market-data/execution infrastructure.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from engines.live_market_intelligence_engine import build_market_intelligence
from engines.ifit_regime_engine import classify_regime
from engines.ifit_signal_engine import build_signal
from engines.decision_matrix_engine import build_decision_matrix
from engines.scenario_engine import build_scenario_matrix
from engines.risk_engine import build_risk_engine
from engines.liquidity_execution_engine import build_liquidity_execution
from engines.microstructure_engine import build_microstructure
from engines.greeks_engine import build_greek_surface
from engines.portfolio_greeks_engine import portfolio_greeks
from engines.portfolio_risk_engine import build_portfolio_risk
from engines.live_greeks_engine import chain_greek_rows


def _clip(x, lo=0.0, hi=100.0):
    return float(np.clip(float(x), lo, hi))


def _atm_greek_inputs(chain_df, spot, days, rate=0.06):
    """Get an ATM Greek vector for the compact scenario layer."""
    try:
        records = []
        for _, r in chain_df.iterrows():
            for side in ("CE", "PE"):
                records.append({
                    "expiry": str(r.get("Expiry", "")),
                    "strike": float(r["Strike"]),
                    "option": side,
                    "ltp": float(r[f"{side} LTP"]),
                    "oi": float(r[f"{side} OI"]),
                    "iv": float(r[f"{side} IV"]),
                })
        rows = chain_greek_rows(records, float(spot), float(rate))
        gdf = pd.DataFrame(rows)
        if gdf.empty:
            return {}
        atm = round(float(spot) / 100.0) * 100.0
        row = gdf.iloc[(gdf["strike"].astype(float) - atm).abs().argsort()[0]]
        return {
            k: float(row.get(k, 0.0) or 0.0)
            for k in ("delta", "gamma", "vega", "theta", "vanna", "vomma")
        }
    except Exception:
        return {}


def _default_portfolio(spot, atm_iv):
    atm = round(float(spot) / 100.0) * 100.0
    return [
        {"Instrument": f"NIFTY {int(atm+200)} CE", "Side": "BUY", "Qty": 1,
         "Multiplier": 50, "Strike": atm+200, "DTE": 14, "IV": atm_iv, "Option": "CE"},
        {"Instrument": f"NIFTY {int(atm-100)} PE", "Side": "BUY", "Qty": 1,
         "Multiplier": 50, "Strike": atm-100, "DTE": 14, "IV": atm_iv+0.3, "Option": "PE"},
        {"Instrument": f"NIFTY {int(atm+100)} CE", "Side": "SELL", "Qty": 1,
         "Multiplier": 50, "Strike": atm+100, "DTE": 14, "IV": atm_iv+0.1, "Option": "CE"},
    ]


def build_consolidated_intelligence(
    *, spot, days, atm_iv, hv30, flow_levels=50, imbalance_ratio=1.5,
    portfolio_positions=None, active_alerts=0
):
    """Build the V0.8.0 single-snapshot IFIT intelligence stack."""
    spot = float(spot)
    days = int(days)
    atm_iv = float(atm_iv)
    hv30 = float(hv30)

    # 1) Market intelligence is the common upstream state.
    mi = build_market_intelligence(
        spot, days, atm_iv, hv30, flow_levels, imbalance_ratio, r_percent=6.0
    )
    om = mi["option_metrics"]
    chain = om.get("chain")
    if chain is None or not isinstance(chain, pd.DataFrame) or chain.empty:
        # The current options engine exposes the chain separately; keep a safe fallback.
        from engines.options_engine import build_option_chain
        chain = build_option_chain(spot, days, atm_iv)

    move = float(om.get("move", 0.0))
    expected_low = spot - move
    expected_high = spot + move
    atm = round(spot / 100.0) * 100.0

    # 2) Regime.
    regime = classify_regime(
        mi["score"], mi["confidence"], mi["flow_score"], mi["vol_score"],
        mi["vol_regime"], mi["gamma_risk"], mi["mean_dislocation"],
        mi["pcr"], mi["iv_premium"]
    )

    # 3) Signal.
    signal = build_signal(
        mi["score"], mi["confidence"], regime["regime"], regime["confidence"],
        regime["directional_strength"], mi["flow_score"], mi["vol_score"],
        mi["vol_regime"], mi["gamma_risk"], mi["mean_dislocation"],
        spot, atm, expected_low, expected_high, mi["pcr"], atm
    )

    # 4) Decision matrix.
    decision = build_decision_matrix(
        market_score=mi["score"],
        regime_confidence=regime["confidence"],
        directional_strength=regime["directional_strength"],
        flow_score=mi["flow_score"],
        vol_score=mi["vol_score"],
        gamma_risk=mi["gamma_risk"],
        model_dislocation=mi["mean_dislocation"],
        signal_direction=signal["direction"],
        conviction=signal["conviction"],
        transition_risk=regime["transition_risk"],
        spot=spot,
        support=signal["support"],
        resistance=signal["resistance"],
        expected_low=expected_low,
        expected_high=expected_high,
        pcr=mi["pcr"],
        iv_premium=mi["iv_premium"],
        active_alerts=int(active_alerts),
    )

    # 5) Volatility / model / scenario context.
    gd = _atm_greek_inputs(chain, spot, days)
    scenario = build_scenario_matrix(
        spot=spot,
        expected_low=expected_low,
        expected_high=expected_high,
        direction_bias=signal["direction"],
        directional_score=regime["directional_strength"],
        confirmation_score=regime["confidence"],
        risk_score=mi["gamma_risk"],
        vol_score=mi["vol_score"],
        gamma_risk=mi["gamma_risk"],
        model_dislocation=mi["mean_dislocation"],
        base_iv=atm_iv,
        delta=gd.get("delta", 0.0),
        gamma=gd.get("gamma", 0.0),
        vega=gd.get("vega", 0.0),
        theta_per_day=gd.get("theta", 0.0) / 365.0,
        vanna=gd.get("vanna", 0.0),
        vomma=gd.get("vomma", 0.0),
    )

    # 6) Cross-engine risk.
    risk = build_risk_engine(
        market_score=mi["score"],
        regime_confidence=regime["confidence"],
        flow_score=mi["flow_score"],
        vol_score=mi["vol_score"],
        gamma_risk=mi["gamma_risk"],
        model_dislocation=mi["mean_dislocation"],
        signal_confirmation=signal["conviction"],
        direction_score=signal["direction"],
        event_count=0,
        alert_count=int(active_alerts),
        expected_low=expected_low,
        expected_high=expected_high,
        spot=spot,
        scenario_result=scenario,
    )

    # 7) Execution / microstructure.
    liquidity = build_liquidity_execution(
        chain_df=chain, spot=spot, multiplier=50
    )
    micro = build_microstructure(
        chain_df=chain, spot=spot, multiplier=50
    )

    # 8) Portfolio risk — illustrative default positions unless supplied.
    positions = portfolio_positions or _default_portfolio(spot, atm_iv)
    try:
        pg_df, totals = portfolio_greeks(positions, spot, r_percent=6.5, q_percent=0.0)
        portfolio = build_portfolio_risk(
            positions_df=pg_df, totals=totals, spot=spot
        )
    except Exception:
        portfolio = {
            "score": 0.0, "regime": "NO DATA", "tail_bias": "TWO-SIDED",
            "concentration_risk": 0.0, "stress_score": 0.0,
            "drivers": pd.DataFrame(), "attribution": pd.DataFrame(),
            "worst": {}, "best": {}, "alert": "Portfolio diagnostics unavailable."
        }

    # 9) Executive score. Directional strength is deliberately separated from risk.
    risk_quality = 100.0 - float(risk["overall_score"])
    execution_quality = float(liquidity["score"])
    micro_quality = float(micro["score"])
    model_quality = 100.0 - float(mi["mean_dislocation"])
    regime_quality = float(regime["confidence"])

    executive_confidence = _clip(
        0.28 * regime_quality +
        0.22 * float(signal["conviction"]) +
        0.18 * model_quality +
        0.17 * risk_quality +
        0.15 * execution_quality
    )

    # A concise state machine for the command center.
    if risk["regime"] in ("EXTREME", "HIGH"):
        operating_state = "RISK CONTROL"
    elif decision["setup"] == "HIGH-QUALITY SETUP":
        operating_state = "HIGH-CONVICTION"
    elif decision["setup"] == "WATCHLIST SETUP":
        operating_state = "WATCHLIST"
    elif liquidity["regime"] in ("THIN", "FRAGILE") or micro["regime"] in ("THIN", "FRAGILE"):
        operating_state = "EXECUTION CONSTRAINED"
    else:
        operating_state = "NO CLEAR EDGE"

    # Overall score is a diagnostic quality/edge index, not a probability.
    overall = _clip(
        0.24 * float(mi["confidence"]) +
        0.20 * float(signal["conviction"]) +
        0.16 * float(regime["confidence"]) +
        0.15 * risk_quality +
        0.10 * execution_quality +
        0.08 * micro_quality +
        0.07 * model_quality
    )

    return {
        "overall_score": round(overall, 2),
        "operating_state": operating_state,
        "executive_confidence": round(executive_confidence, 2),
        "spot": spot,
        "atm": atm,
        "expected_low": expected_low,
        "expected_high": expected_high,
        "market": mi,
        "regime": regime,
        "signal": signal,
        "decision": decision,
        "scenario": scenario,
        "risk": risk,
        "liquidity": liquidity,
        "microstructure": micro,
        "portfolio": portfolio,
        "portfolio_positions": positions,
        "health_note": (
            "Simulation/proxy outputs remain illustrative until an authorized "
            "real-time market-data and depth feed is connected."
        ),
    }
