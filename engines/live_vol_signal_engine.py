
"""IFIT V0.6.6 - Live Volatility Signal Engine.

A transparent research regime engine combining IV premium, skew/smile,
Heston residuals, model dislocation and gamma structure.
"""

from __future__ import annotations
import math
import numpy as np
import pandas as pd

from engines.live_vol_surface_engine import build_surface, surface_summary
from engines.live_model_dislocation_engine import analyze_live_dislocation
from engines.volatility_engine import gamma_exposure


def _clamp(x, lo=0.0, hi=100.0):
    return float(np.clip(float(x), lo, hi))


def _signed_score(value, scale):
    """Map a signed market-vol input to roughly -20..+20."""
    if scale <= 0:
        return 0.0
    return float(np.clip(float(value) / float(scale) * 20.0, -20.0, 20.0))


def _regime(score):
    if score >= 70:
        return "VOL EXPANSION"
    if score >= 55:
        return "EXPANSION WATCH"
    if score <= 30:
        return "VOL COMPRESSION"
    if score <= 45:
        return "COMPRESSION WATCH"
    return "NEUTRAL"


def build_vol_signal(spot, chain, atm_iv, hv30, days, r_percent=6.0):
    """Build a transparent 0-100 volatility regime score."""
    rows = build_surface(chain, float(spot))
    if not rows:
        raise ValueError("No valid IV observations available.")

    surf = surface_summary(rows, float(spot))
    dis = analyze_live_dislocation(
        float(spot), chain, int(days), float(r_percent)
    )
    ranked = dis["ranked"]

    # 1) IV premium: positive premium = expansion pressure.
    iv_premium = float(atm_iv) - float(hv30)
    premium_component = _signed_score(iv_premium, 5.0)

    # 2) Downside skew: positive put skew = volatility stress/expansion.
    skew_component = _signed_score(float(surf["put_skew"]), 2.0)

    # 3) Smile curvature: a positive smile proxy implies wings are richer.
    smile_component = _signed_score(float(surf["smile"]), 2.0)

    # 4) Heston residual: Market IV below Heston IV = model says richer vol.
    mean_iv_gap = float(ranked["IV Gap"].mean()) if len(ranked) else 0.0
    heston_component = _signed_score(-mean_iv_gap, 2.0)

    # 5) Model dislocation is an alert/intensity factor rather than direction.
    dislocation_intensity = _clamp(
        float(ranked["Dislocation Score"].mean()) if len(ranked) else 0.0
    )

    # 6) Gamma structure: negative aggregate gamma tends to amplify realized
    # movement; positive gamma tends to dampen it. Normalize by median abs.
    try:
        ge = gamma_exposure(chain)
        values = ge["Gamma Exposure"].astype(float)
        median_abs = max(float(values.abs().median()), 1.0)
        net_gamma = float(values.sum())
        gamma_component = float(np.clip(-net_gamma / median_abs * 5.0, -20.0, 20.0))
    except Exception:
        net_gamma = 0.0
        gamma_component = 0.0

    components = [
        ("IV Premium", premium_component, f"{iv_premium:+.2f} vol pts"),
        ("Put Skew", skew_component, f"{surf['put_skew']:+.2f} vol pts"),
        ("Smile", smile_component, f"{surf['smile']:+.2f} vol pts"),
        ("Heston Residual", heston_component, f"{mean_iv_gap:+.2f} vol pts market−model"),
        ("Gamma Structure", gamma_component, f"{net_gamma:+,.0f} net exposure"),
    ]

    directional = sum(x[1] for x in components)
    # Dislocation raises signal conviction modestly without changing its sign.
    conviction = 0.5 * dislocation_intensity
    if directional > 0:
        score = 50.0 + directional + conviction
    elif directional < 0:
        score = 50.0 + directional - conviction
    else:
        score = 50.0

    score = _clamp(score)
    regime = _regime(score)
    strength = _clamp(abs(score - 50.0) * 2.0)

    drivers = sorted(components, key=lambda x: abs(x[1]), reverse=True)
    top_drivers = [
        {"name": name, "impact": round(float(impact), 2), "reading": reading}
        for name, impact, reading in drivers[:4]
    ]

    if regime in ("VOL EXPANSION", "EXPANSION WATCH"):
        interpretation = (
            "The current volatility inputs lean toward higher realized-volatility "
            "conditions. Confirm with fresh market data and persistence across refreshes."
        )
    elif regime in ("VOL COMPRESSION", "COMPRESSION WATCH"):
        interpretation = (
            "The current volatility inputs lean toward dampening/mean-reverting "
            "conditions. This is a regime classification, not a return forecast."
        )
    else:
        interpretation = (
            "Volatility inputs are mixed and do not establish a strong directional "
            "volatility regime."
        )

    return {
        "score": round(score, 2),
        "regime": regime,
        "strength": round(strength, 2),
        "directional_bias": "EXPANSION" if directional > 0 else ("COMPRESSION" if directional < 0 else "NEUTRAL"),
        "components": components,
        "drivers": top_drivers,
        "interpretation": interpretation,
        "iv_premium": iv_premium,
        "put_skew": float(surf["put_skew"]),
        "call_skew": float(surf["call_skew"]),
        "smile": float(surf["smile"]),
        "mean_heston_gap": mean_iv_gap,
        "net_gamma": net_gamma,
        "mean_dislocation": dislocation_intensity,
        "calibration_confidence": float(dis["confidence"]),
    }
