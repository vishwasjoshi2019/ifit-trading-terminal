
"""IFIT V0.6.7 - Real-Time Market Intelligence Engine.

Transparent synthesis of the active IFIT options, volatility and order-flow
analytics. It produces a market-state score and explanation; it is not a
guarantee of direction or a trade recommendation.
"""

from __future__ import annotations

import math
import numpy as np
import pandas as pd

from engines.options_engine import build_option_chain, calculate_metrics
from engines.volatility_engine import volatility_snapshot, gamma_exposure
from engines.orderflow_engine import build_orderflow, orderflow_metrics
from engines.time_footprint_engine import build_time_footprint, time_footprint_metrics
from engines.absorption_engine import detect_absorption_exhaustion
from engines.cvd_engine import analyze_cvd_divergence
from engines.flow_confluence_engine import build_flow_confluence
from engines.live_vol_signal_engine import build_vol_signal


def _clamp(v, lo=0.0, hi=100.0):
    return float(np.clip(float(v), lo, hi))


def _market_regime(score):
    if score >= 70:
        return "BULLISH"
    if score <= 30:
        return "BEARISH"
    return "NEUTRAL"


def build_market_intelligence(spot, days, atm_iv, hv30, flow_levels=50,
                              imbalance_ratio=1.5, r_percent=6.0):
    """Build a transparent cross-module market intelligence snapshot."""
    spot = float(spot)
    days = int(days)
    atm_iv = float(atm_iv)
    hv30 = float(hv30)

    chain = build_option_chain(spot, days, atm_iv)
    option_metrics = calculate_metrics(chain, spot, days, atm_iv)

    # Order-flow stack uses the same active spot and configurable footprint.
    flow = build_orderflow(spot, int(flow_levels), float(imbalance_ratio))
    fm = orderflow_metrics(flow, spot)

    tf, bars = build_time_footprint(spot, 12, 7)
    tm = time_footprint_metrics(tf, bars, spot, float(imbalance_ratio))
    tf_events, bar_events, ae = detect_absorption_exhaustion(
        tf, bars, spot, min_delta_ratio=max(1.6, float(imbalance_ratio)),
        exhaustion_window=3
    )
    cvd_bars, ci = analyze_cvd_divergence(
        bars, absorption_events=ae, spot=spot, pivot_window=1
    )
    fc = build_flow_confluence(tm, ci, ae)

    vol = build_vol_signal(
        spot, chain, atm_iv, hv30, days, r_percent=r_percent
    )

    # Convert the volatility regime to directional market-state information
    # only through its interaction with flow and gamma; volatility by itself
    # is not inherently bullish or bearish.
    flow_bias = (float(fc["score"]) - 50.0) * 0.42
    vol_bias = 0.0
    if vol["regime"] in ("VOL EXPANSION", "EXPANSION WATCH"):
        # Expansion increases risk intensity, but direction follows flow.
        vol_bias = math.copysign(min(8.0, abs(float(vol["score"]) - 50.0) * 0.10),
                                 flow_bias if flow_bias != 0 else 1.0)
    elif vol["regime"] in ("VOL COMPRESSION", "COMPRESSION WATCH"):
        vol_bias = math.copysign(min(5.0, abs(float(vol["score"]) - 50.0) * 0.08),
                                 flow_bias if flow_bias != 0 else 1.0)

    # Options positioning: PCR above 1 is treated as a modest supportive input
    # and below 1 as a modest negative input; deliberately low weight.
    pcr = float(option_metrics.get("pcr", 1.0))
    pcr_bias = float(np.clip((pcr - 1.0) * 12.0, -8.0, 8.0))

    # Gamma: negative net gamma tends to amplify movement, so it increases
    # risk intensity rather than directly choosing a direction.
    ge = gamma_exposure(chain)
    net_gamma = float(ge["Gamma Exposure"].sum())
    gamma_abs = max(float(ge["Gamma Exposure"].abs().median()), 1.0)
    gamma_risk = _clamp(abs(net_gamma) / gamma_abs * 20.0)

    # Model dislocation is a confidence/risk modifier, not directional alpha.
    dislocation_risk = float(vol["mean_dislocation"])

    score = _clamp(50.0 + flow_bias + pcr_bias + vol_bias)
    regime = _market_regime(score)

    # Confidence is alignment, not probability of profit.
    flow_alignment = _clamp(100.0 - abs(float(fc["score"]) - 50.0) * 0.5)
    if regime == "NEUTRAL":
        directional_alignment = 55.0
    else:
        directional_alignment = _clamp(abs(score - 50.0) * 2.0)
    confidence = _clamp(
        0.45 * directional_alignment +
        0.30 * float(fc["confidence"]) +
        0.15 * float(vol["calibration_confidence"]) +
        0.10 * (100.0 - min(100.0, dislocation_risk))
    )

    # Risk state is intentionally separate from directional state.
    if gamma_risk >= 70 or dislocation_risk >= 75 or vol["regime"] == "VOL EXPANSION":
        risk_state = "HIGH"
    elif gamma_risk >= 40 or dislocation_risk >= 50 or vol["regime"] == "EXPANSION WATCH":
        risk_state = "ELEVATED"
    else:
        risk_state = "NORMAL"

    drivers = []
    for name, impact, reading in fc["components"]:
        if impact:
            drivers.append({
                "name": name,
                "impact": float(impact),
                "reading": reading,
            })
    drivers.extend([
        {"name": "PCR", "impact": pcr_bias, "reading": f"{pcr:.2f}"},
        {"name": "Volatility Regime",
         "impact": vol_bias, "reading": vol["regime"]},
    ])
    drivers = sorted(drivers, key=lambda x: abs(x["impact"]), reverse=True)[:5]

    risks = []
    if gamma_risk >= 50:
        risks.append(f"Gamma risk {gamma_risk:.0f}/100")
    if dislocation_risk >= 50:
        risks.append(f"Model dislocation {dislocation_risk:.0f}/100")
    if vol["regime"] in ("VOL EXPANSION", "EXPANSION WATCH"):
        risks.append(f"{vol['regime']}")
    if not risks:
        risks.append("No major cross-module risk flag")

    if regime == "BULLISH":
        summary = "Flow and options structure lean bullish; volatility and model risk should be monitored separately."
    elif regime == "BEARISH":
        summary = "Flow and options structure lean bearish; volatility and model risk should be monitored separately."
    else:
        summary = "Cross-module inputs are mixed and do not establish a strong directional market state."

    return {
        "score": round(score, 2),
        "regime": regime,
        "confidence": round(confidence, 2),
        "risk_state": risk_state,
        "summary": summary,
        "drivers": drivers,
        "risks": risks,
        "flow_score": int(fc["score"]),
        "flow_regime": fc["regime"],
        "flow_confidence": int(fc["confidence"]),
        "vol_score": float(vol["score"]),
        "vol_regime": vol["regime"],
        "vol_strength": float(vol["strength"]),
        "pcr": pcr,
        "atm_iv": atm_iv,
        "hv30": hv30,
        "iv_premium": float(vol["iv_premium"]),
        "net_gamma": net_gamma,
        "gamma_risk": gamma_risk,
        "mean_dislocation": dislocation_risk,
        "calibration_confidence": float(vol["calibration_confidence"]),
        "option_metrics": option_metrics,
        "vol_signal": vol,
    }
