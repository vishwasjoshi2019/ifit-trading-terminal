
"""IFIT V0.6.9 — Signal Engine.

Decision-intelligence layer above IFIT's market state and regime analytics.
It converts cross-module evidence into direction, conviction, risk, key levels
and invalidation. It is a research signal, not a guaranteed forecast or order.
"""

from __future__ import annotations
import numpy as np


def _clamp(x, lo=0.0, hi=100.0):
    return float(np.clip(float(x), lo, hi))


def _direction_label(score):
    if score >= 67:
        return "BULLISH"
    if score <= 33:
        return "BEARISH"
    return "NEUTRAL"


def _conviction_label(conviction):
    if conviction >= 75:
        return "HIGH"
    if conviction >= 55:
        return "MODERATE"
    if conviction >= 35:
        return "LOW"
    return "VERY LOW"


def build_signal(market_score, market_confidence, market_regime,
                 regime_confidence, directional_strength, flow_score,
                 vol_score, vol_regime, gamma_risk, model_dislocation,
                 spot, atm, expected_low, expected_high, pcr,
                 max_pain, va_l=None, va_h=None, poc=None):
    """Synthesize the current IFIT state into an explainable signal."""
    market_score=float(market_score)
    market_confidence=float(market_confidence)
    directional_strength=float(directional_strength)
    flow_score=float(flow_score)
    vol_score=float(vol_score)
    gamma_risk=float(gamma_risk)
    model_dislocation=float(model_dislocation)
    spot=float(spot)
    atm=float(atm)
    expected_low=float(expected_low)
    expected_high=float(expected_high)
    pcr=float(pcr)
    max_pain=float(max_pain)

    # Direction is led by market state and flow. PCR is a small positioning input.
    direction_score = _clamp(
        0.62 * market_score +
        0.28 * flow_score +
        0.10 * _clamp(50.0 + (pcr-1.0)*80.0)
    )
    direction = _direction_label(direction_score)

    # Evidence alignment and model quality determine conviction.
    agreement = 100.0 - abs(market_score-flow_score)*1.35
    regime_penalty = 20.0 if market_regime in ("HIGH-RISK TRANSITION","NO EDGE") else 0.0
    risk_penalty = min(30.0, 0.15*gamma_risk + 0.15*model_dislocation)
    volatility_penalty = 10.0 if vol_regime == "VOL EXPANSION" else 0.0
    conviction = _clamp(
        0.35*market_confidence +
        0.20*regime_confidence +
        0.20*directional_strength +
        0.15*agreement +
        0.10*flow_score -
        regime_penalty - risk_penalty - volatility_penalty
    )
    conviction_label=_conviction_label(conviction)

    # Signal risk is independent from direction.
    if gamma_risk >= 80 or model_dislocation >= 80 or vol_regime == "VOL EXPANSION":
        risk="HIGH"
    elif gamma_risk >= 50 or model_dislocation >= 50 or market_regime=="HIGH-RISK TRANSITION":
        risk="ELEVATED"
    else:
        risk="NORMAL"

    # Key levels: preserve the expected-move bounds and enrich with options/flow levels.
    levels=[]
    for name,val in [
        ("Expected Move Low", expected_low),
        ("VA Low", va_l),
        ("POC", poc),
        ("ATM", atm),
        ("Max Pain", max_pain),
        ("VA High", va_h),
        ("Expected Move High", expected_high),
    ]:
        if val is not None and np.isfinite(float(val)):
            levels.append((name,float(val)))
    levels=sorted(levels,key=lambda x:x[1])

    below=[(n,v) for n,v in levels if v < spot]
    above=[(n,v) for n,v in levels if v > spot]
    support=max(below,key=lambda x:x[1]) if below else ("Expected Move Low",expected_low)
    resistance=min(above,key=lambda x:x[1]) if above else ("Expected Move High",expected_high)

    # Invalidation is intentionally conservative: signal invalidates beyond the
    # nearest structural level in the opposite direction, bounded by expected move.
    if direction=="BULLISH":
        invalidation=min(spot, resistance[1])
        invalidation=max(expected_low, invalidation - max(1.0, abs(spot-atm)*0.10))
        invalidation_rule=f"Below {invalidation:,.0f}"
    elif direction=="BEARISH":
        invalidation=max(spot, support[1])
        invalidation=min(expected_high, invalidation + max(1.0, abs(spot-atm)*0.10))
        invalidation_rule=f"Above {invalidation:,.0f}"
    else:
        # For a neutral signal there is no directional invalidation; use the
        # expected-move boundaries as the neutral-state boundary.
        invalidation=float(expected_low)
        invalidation_rule=f"Outside {expected_low:,.0f}–{expected_high:,.0f}"

    # Driver attribution in signal-space.
    raw=[
        ("Market State", abs(market_score-50.0), market_score),
        ("Flow", abs(flow_score-50.0), flow_score),
        ("Directional Strength", directional_strength, directional_strength),
        ("PCR", min(20.0,abs(pcr-1.0)*100.0), pcr),
        ("Volatility Risk", abs(vol_score-50.0), vol_score),
    ]
    drivers=sorted(raw,key=lambda x:x[1],reverse=True)[:5]

    if direction=="BULLISH":
        summary=f"IFIT leans bullish with {conviction_label.lower()} conviction; monitor {resistance[0]} at {resistance[1]:,.0f}."
    elif direction=="BEARISH":
        summary=f"IFIT leans bearish with {conviction_label.lower()} conviction; monitor {support[0]} at {support[1]:,.0f}."
    else:
        summary=f"IFIT has no strong directional edge; treat {expected_low:,.0f}–{expected_high:,.0f} as the primary expected-move zone."

    return {
        "direction":direction,
        "direction_score":round(direction_score,2),
        "conviction":round(conviction,2),
        "conviction_label":conviction_label,
        "risk":risk,
        "market_regime":market_regime,
        "regime_confidence":round(regime_confidence,2),
        "summary":summary,
        "support_name":support[0],
        "support":round(support[1],2),
        "resistance_name":resistance[0],
        "resistance":round(resistance[1],2),
        "invalidation":round(float(invalidation),2),
        "invalidation_rule":invalidation_rule,
        "levels":[{"name":n,"level":round(v,2)} for n,v in levels],
        "drivers":[{"name":n,"strength":round(st,2),"reading":round(float(rd),4)} for n,st,rd in drivers],
        "inputs":{
            "market_score":market_score,"flow_score":flow_score,
            "vol_score":vol_score,"gamma_risk":gamma_risk,
            "model_dislocation":model_dislocation,"pcr":pcr,
            "spot":spot,"expected_low":expected_low,"expected_high":expected_high,
        }
    }
