
"""IFIT V0.6.8 — Market Regime Engine.

Classifies the current market environment from the already-synthesized IFIT
state. This is a transparent regime classifier, not a trade recommendation.
"""

from __future__ import annotations
import numpy as np


def _clamp(x, lo=0.0, hi=100.0):
    return float(np.clip(float(x), lo, hi))


def classify_regime(market_score, market_confidence, flow_score, vol_score,
                    vol_regime, gamma_risk, model_dislocation,
                    pcr=1.0, iv_premium=0.0):
    """Return regime, confidence, component scores and transition diagnostics."""
    market_score = float(market_score)
    market_confidence = float(market_confidence)
    flow_score = float(flow_score)
    vol_score = float(vol_score)
    gamma_risk = float(gamma_risk)
    model_dislocation = float(model_dislocation)
    pcr = float(pcr)
    iv_premium = float(iv_premium)

    directional_strength = _clamp(abs(market_score - 50.0) * 2.0)
    flow_strength = _clamp(abs(flow_score - 50.0) * 2.0)

    # Directional agreement: market state and flow should point the same way.
    same_direction = (
        (market_score >= 50 and flow_score >= 50) or
        (market_score < 50 and flow_score < 50)
    )
    directional_alignment = (
        (0.65 * directional_strength + 0.35 * flow_strength)
        if same_direction else
        (0.45 * directional_strength + 0.20 * flow_strength)
    )
    directional_alignment = _clamp(directional_alignment)

    expansion = vol_regime in ("VOL EXPANSION", "EXPANSION WATCH")
    compression = vol_regime in ("VOL COMPRESSION", "COMPRESSION WATCH")
    vol_extreme = max(abs(vol_score - 50.0) * 2.0, 0.0)

    # Range/mean-reversion environment is strongest when direction is weak,
    # volatility is compressed, and options positioning is not extreme.
    pcr_neutrality = _clamp(100.0 - abs(pcr - 1.0) * 120.0)
    range_score = _clamp(
        0.55 * (100.0 - directional_strength) +
        0.30 * (vol_score if compression else (100.0 - vol_extreme)) +
        0.15 * pcr_neutrality
    )

    # Transition risk rises when risk is high but direction is not decisive,
    # or when model/volatility dislocation is elevated.
    transition_risk = _clamp(
        0.35 * gamma_risk +
        0.30 * model_dislocation +
        0.20 * (100.0 - directional_strength) +
        0.15 * vol_extreme
    )

    if expansion and vol_score >= 70:
        regime = "VOLATILITY EXPANSION"
    elif transition_risk >= 72 and directional_strength < 55:
        regime = "HIGH-RISK TRANSITION"
    elif market_score >= 65 and directional_strength >= 30 and directional_alignment >= 45:
        regime = "TRENDING BULL"
    elif market_score <= 35 and directional_strength >= 30 and directional_alignment >= 45:
        regime = "TRENDING BEAR"
    elif range_score >= 65:
        regime = "RANGE / MEAN REVERSION"
    elif directional_strength < 28 and market_confidence < 60:
        regime = "NO EDGE"
    elif market_score >= 50:
        regime = "BULLISH BIAS / MIXED"
    else:
        regime = "BEARISH BIAS / MIXED"

    # Regime confidence reflects agreement between independent layers and
    # data/model quality; it is explicitly not probability of profit.
    agreement = 100.0 if same_direction else 45.0
    risk_penalty = min(35.0, transition_risk * 0.25)
    confidence = _clamp(
        0.40 * market_confidence +
        0.25 * directional_alignment +
        0.20 * agreement +
        0.15 * (100.0 - risk_penalty)
    )

    if regime == "HIGH-RISK TRANSITION":
        transition_label = "TRANSITION RISK HIGH"
    elif transition_risk >= 50:
        transition_label = "TRANSITION RISK ELEVATED"
    else:
        transition_label = "TRANSITION RISK NORMAL"

    drivers = [
        ("Directional Strength", directional_strength),
        ("Flow Alignment", directional_alignment),
        ("Volatility State", vol_extreme),
        ("Range Score", range_score),
        ("Transition Risk", transition_risk),
    ]
    drivers = sorted(drivers, key=lambda x: x[1], reverse=True)

    return {
        "regime": regime,
        "confidence": round(confidence, 2),
        "directional_strength": round(directional_strength, 2),
        "directional_alignment": round(directional_alignment, 2),
        "range_score": round(range_score, 2),
        "transition_risk": round(transition_risk, 2),
        "transition_label": transition_label,
        "volatility_score": round(vol_score, 2),
        "drivers": [{"name": n, "score": round(v, 2)} for n, v in drivers],
        "inputs": {
            "market_score": market_score,
            "market_confidence": market_confidence,
            "flow_score": flow_score,
            "vol_score": vol_score,
            "vol_regime": vol_regime,
            "gamma_risk": gamma_risk,
            "model_dislocation": model_dislocation,
            "pcr": pcr,
            "iv_premium": iv_premium,
        },
    }
