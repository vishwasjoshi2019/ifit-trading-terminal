import numpy as np


def _clamp(v, lo=0, hi=100):
    return int(max(lo, min(hi, round(v))))


def build_flow_confluence(tm, ci, ae):
    """
    Transparent multi-factor order-flow confluence model.

    The score is intentionally additive and explainable. It is a research
    prototype and does not represent hidden dealer positioning or a trade
    recommendation.
    """
    components = []
    score = 50.0

    # Price structure: +/- 12
    if ci.get("price_trend") == "UP":
        v = 12
    elif ci.get("price_trend") == "DOWN":
        v = -12
    else:
        v = 0
    score += v
    components.append(("Price structure", v, ci.get("price_trend", "FLAT")))

    # CVD trend: +/- 18
    if ci.get("cvd_trend") == "UP":
        v = 18
    elif ci.get("cvd_trend") == "DOWN":
        v = -18
    else:
        v = 0
    score += v
    components.append(("CVD trend", v, ci.get("cvd_trend", "FLAT")))

    # Delta momentum: +/- 12
    m = ci.get("momentum", "NEUTRAL")
    if "BUYING PRESSURE STRENGTHENING" in m:
        v = 12
    elif "SELLING PRESSURE STRENGTHENING" in m:
        v = -12
    elif "BUYING PRESSURE WEAKENING" in m:
        v = -6
    elif "SELLING PRESSURE WEAKENING" in m:
        v = 6
    else:
        v = 0
    score += v
    components.append(("Delta momentum", v, m))

    # Imbalance pressure: +/- 10
    buys = int(tm.get("buy_imbalances", 0))
    sells = int(tm.get("sell_imbalances", 0))
    total = max(1, buys + sells)
    v = 10.0 * (buys - sells) / total
    score += v
    components.append(("Imbalance pressure", v, f"BUY {buys} / SELL {sells}"))

    # CVD divergence: +/- up to 15
    div = ci.get("divergence", "NONE")
    strength = float(ci.get("strength", 0))
    if div == "BULLISH":
        v = min(15.0, strength * 0.15)
    elif div == "BEARISH":
        v = -min(15.0, strength * 0.15)
    else:
        v = 0
    score += v
    components.append(("CVD divergence", v, f"{div} {int(strength)}/100" if div != "NONE" else "NONE"))

    # Absorption/exhaustion: directional, capped at +/- 15.
    ba = int(ae.get("buy_absorption_bars", 0))
    sa = int(ae.get("sell_absorption_bars", 0))
    be = int(ae.get("buyer_exhaustion_bars", 0))
    se = int(ae.get("seller_exhaustion_bars", 0))
    v = min(15.0, ba * 4 - sa * 4 - be * 3 + se * 3)
    score += v
    components.append(("Absorption / exhaustion", v, f"BA {ba} / SA {sa} / BE {be} / SE {se}"))

    score = _clamp(score)
    if score >= 70:
        regime = "BUY PRESSURE"
        confidence = _clamp(55 + (score - 70) * 1.2)
    elif score <= 30:
        regime = "SELL PRESSURE"
        confidence = _clamp(55 + (30 - score) * 1.2)
    else:
        regime = "BALANCED / NO EDGE"
        confidence = _clamp(55 + abs(score - 50) * 0.8)

    # Identify the strongest directional contributors for explanation.
    ranked = sorted(components, key=lambda x: abs(x[1]), reverse=True)
    drivers = [
        {"name": name, "impact": round(float(impact), 1), "reading": reading}
        for name, impact, reading in ranked if impact != 0
    ][:4]

    if regime == "BUY PRESSURE":
        summary = "Multiple flow factors are aligned to the buy side."
    elif regime == "SELL PRESSURE":
        summary = "Multiple flow factors are aligned to the sell side."
    else:
        summary = "The flow factors are mixed or lack enough alignment to establish an edge."

    return {
        "score": score,
        "regime": regime,
        "confidence": confidence,
        "components": components,
        "drivers": drivers,
        "summary": summary,
    }
