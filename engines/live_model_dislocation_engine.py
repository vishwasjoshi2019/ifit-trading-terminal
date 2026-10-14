
"""IFIT V0.6.5 - Live model dislocation and volatility intelligence."""

from __future__ import annotations
import math
import numpy as np
import pandas as pd

from engines.live_heston_engine import calibrate_live_heston


def _score_abs(value, threshold):
    try:
        v = abs(float(value))
    except (TypeError, ValueError):
        return 0.0
    return float(np.clip(v / max(float(threshold), 1e-12) * 100.0, 0.0, 100.0))


def _regime(score):
    if score >= 75:
        return "EXTREME"
    if score >= 50:
        return "ELEVATED"
    if score >= 25:
        return "WATCH"
    return "NORMAL"


def _confidence(iv_rmse, points, iterations, params):
    # Confidence is a calibration-quality indicator, not probability of profit.
    rmse_component = 100.0 / (1.0 + max(float(iv_rmse), 0.0))
    point_component = min(100.0, 100.0 * float(points) / 15.0)
    iteration_component = 100.0 if int(iterations) < 12 else 70.0
    boundary_hits = 0
    for key, lo, hi in (
        ("v0", 0.005, 0.30), ("kappa", 0.10, 8.0),
        ("theta", 0.005, 0.30), ("sigma_v", 0.05, 2.0),
        ("rho", -0.95, -0.05),
    ):
        value = float(params[key])
        if abs(value - lo) < 1e-5 or abs(value - hi) < 1e-5:
            boundary_hits += 1
    boundary_penalty = max(0.0, 100.0 - 15.0 * boundary_hits)
    return float(np.clip(
        0.45 * rmse_component + 0.25 * point_component +
        0.15 * iteration_component + 0.15 * boundary_penalty,
        0.0, 100.0
    ))


def analyze_live_dislocation(spot, chain, days, r_percent=6.0):
    """Calibrate Heston and build an explainable contract-level dislocation table."""
    params, fit, stats, h_surface, ranked, summary = calibrate_live_heston(
        float(spot), chain, int(days), float(r_percent), max_nfev=12
    )
    if fit.empty:
        raise ValueError("No calibration observations were produced.")

    quality = _confidence(
        stats["iv_rmse"], stats["points"], stats["iterations"], params
    )

    rows = []
    for _, row in fit.iterrows():
        iv_gap = float(row["IV Residual"])
        price_gap = float(row["Price Residual"])
        gap_score = _score_abs(iv_gap, 0.50)
        price_score = _score_abs(price_gap, max(float(spot) * 0.002, 1.0))

        # Higher-order sensitivity is calculated from the market IV.
        from engines.greeks_engine import calculate_higher_order_greeks
        g = calculate_higher_order_greeks(
            float(spot), float(row["Strike"]), float(row["DTE"]),
            float(row["Market IV"]), r_percent=float(r_percent),
            q_percent=0.0, option="CE"
        )
        greek_score = float(np.mean([
            _score_abs(g["gamma"], 0.0005),
            _score_abs(g["vanna"], 0.10),
            _score_abs(g["vomma"], 0.50),
            _score_abs(g["zomma"], 0.0003),
            _score_abs(g["ultima"], 5.0),
        ]))
        expiry_score = float(np.clip(
            100.0 * math.sqrt(14.0 / max(float(row["DTE"]), 1.0)),
            0.0, 100.0
        ))

        score = float(np.clip(
            0.40 * gap_score + 0.20 * price_score +
            0.15 * expiry_score + 0.15 * greek_score +
            0.10 * quality,
            0.0, 100.0
        ))

        drivers = {
            "IV Residual": 0.40 * gap_score,
            "Price Residual": 0.20 * price_score,
            "Expiry Sensitivity": 0.15 * expiry_score,
            "Higher-Order Greeks": 0.15 * greek_score,
            "Calibration Quality": 0.10 * quality,
        }
        ordered = sorted(drivers.items(), key=lambda x: abs(x[1]), reverse=True)
        top_driver = ordered[0][0]
        second_driver = ordered[1][0]

        if iv_gap > 0:
            direction = "Heston > Market IV"
        elif iv_gap < 0:
            direction = "Heston < Market IV"
        else:
            direction = "Aligned"

        rows.append({
            "Strike": float(row["Strike"]),
            "DTE": float(row["DTE"]),
            "Market IV": float(row["Market IV"]),
            "Heston IV": float(row["Heston IV"]),
            "IV Gap": iv_gap,
            "Price Gap": price_gap,
            "Gap Score": gap_score,
            "Price Score": price_score,
            "Greek Sensitivity": greek_score,
            "Expiry Sensitivity": expiry_score,
            "Calibration Quality": quality,
            "Dislocation Score": score,
            "Regime": _regime(score),
            "Direction": direction,
            "Primary Driver": top_driver,
            "Secondary Driver": second_driver,
        })

    out = pd.DataFrame(rows).sort_values(
        ["Dislocation Score", "IV Gap"], ascending=[False, False]
    ).reset_index(drop=True)

    return {
        "params": params,
        "fit": fit,
        "stats": stats,
        "heston_surface": h_surface,
        "ranked": out,
        "summary": summary,
        "confidence": quality,
    }
