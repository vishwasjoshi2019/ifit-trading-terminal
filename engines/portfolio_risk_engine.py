"""IFIT V0.7.5 — Portfolio Risk Engine.

Portfolio-level risk diagnostics built on the existing IFIT higher-order Greeks.
Scores are normalized research diagnostics, not VaR, margin requirements,
or investment advice.
"""
import numpy as np
import pandas as pd


def _clip(x, lo=0.0, hi=100.0):
    return float(np.clip(float(x), lo, hi))


def _safe_abs(x):
    try:
        return abs(float(x))
    except Exception:
        return 0.0


def _scenario_rows(totals, spot):
    """Build a compact portfolio stress cube using the existing Taylor engine."""
    from engines.portfolio_greeks_engine import scenario_pnl

    rows = []
    spot_moves = (-5, -3, -1, 0, 1, 3, 5)
    iv_moves = (-8, -4, 0, 4, 8)
    horizons = (0, 1, 3, 5)
    for days in horizons:
        for sm in spot_moves:
            for iv in iv_moves:
                rows.append({
                    "Days": days,
                    "Spot Shock %": sm,
                    "IV Shock pt": iv,
                    "Approx P&L": scenario_pnl(
                        totals, spot,
                        spot_change_pct=sm,
                        iv_change_points=iv,
                        days_passed=days,
                    ),
                })
    return pd.DataFrame(rows)


def build_portfolio_risk(*, positions_df, totals, spot):
    """Create explainable portfolio risk diagnostics and stress attribution."""
    df = positions_df.copy() if isinstance(positions_df, pd.DataFrame) else pd.DataFrame()
    spot = max(float(spot), 1.0)

    net_delta = float(totals.get("delta", 0.0))
    net_gamma = float(totals.get("gamma", 0.0))
    net_theta = float(totals.get("theta", 0.0))
    net_vega = float(totals.get("vega", 0.0))
    net_vanna = float(totals.get("vanna", 0.0))
    net_vomma = float(totals.get("vomma", 0.0))
    net_speed = float(totals.get("speed", 0.0))
    net_color = float(totals.get("color", 0.0))
    net_ultima = float(totals.get("ultima", 0.0))
    net_veta = float(totals.get("veta", 0.0))

    # Transparent normalized component diagnostics. The denominators are
    # screening scales, not calibrated probabilities.
    delta_risk = _clip(abs(net_delta) / 100.0 * 100.0)
    gamma_risk = _clip(abs(net_gamma) * 10000.0)
    vol_risk = _clip(abs(net_vega) / 5.0 + abs(net_vomma) / 100.0)
    convexity_risk = _clip(
        0.55 * gamma_risk +
        0.20 * _clip(abs(net_vanna) * 20.0) +
        0.25 * _clip(abs(net_vomma) / 50.0)
    )
    theta_risk = _clip(max(0.0, -net_theta) / 100.0 * 100.0)
    third_order_risk = _clip(
        0.35 * _clip(abs(net_speed) * 100.0) +
        0.25 * _clip(abs(net_color) * 100.0) +
        0.25 * _clip(abs(net_ultima) / 50.0) +
        0.15 * _clip(abs(net_veta) / 50.0)
    )

    concentration = 0.0
    attribution = pd.DataFrame()
    if not df.empty:
        abs_delta = df["delta"].abs()
        gross = float(abs_delta.sum())
        if gross > 0:
            concentration = _clip(float(abs_delta.max()) / gross * 100.0)
        attribution = df[["Instrument", "Side", "Qty", "Multiplier"]].copy()
        attribution["Delta Risk"] = df["delta"].abs()
        attribution["Gamma Risk"] = df["gamma"].abs()
        attribution["Vega Risk"] = df["vega"].abs()
        attribution["Vol Convexity"] = df["vomma"].abs() + df["vanna"].abs()
        attribution["Total Risk Contribution"] = (
            attribution["Delta Risk"] +
            attribution["Gamma Risk"] * spot / 100.0 +
            attribution["Vega Risk"] / 10.0 +
            attribution["Vol Convexity"] / 10.0
        )
        total_contrib = float(attribution["Total Risk Contribution"].sum())
        if total_contrib > 0:
            attribution["Risk Share %"] = 100.0 * attribution["Total Risk Contribution"] / total_contrib
        else:
            attribution["Risk Share %"] = 0.0
        attribution = attribution.sort_values("Risk Share %", ascending=False)

    scenarios = _scenario_rows(totals, spot)
    worst = scenarios.loc[scenarios["Approx P&L"].idxmin()].to_dict()
    best = scenarios.loc[scenarios["Approx P&L"].idxmax()].to_dict()
    loss_rate = float((scenarios["Approx P&L"] < 0).mean() * 100.0)

    gross_delta_notional = max(abs(net_delta) * spot, 1.0)
    tail_loss_score = _clip(abs(float(worst["Approx P&L"])) / gross_delta_notional * 100.0)
    stress_score = _clip(0.55 * tail_loss_score + 0.45 * loss_rate)

    # Directional tail asymmetry compares the worst downside/upside shocks.
    down = scenarios[scenarios["Spot Shock %"] < 0]["Approx P&L"]
    up = scenarios[scenarios["Spot Shock %"] > 0]["Approx P&L"]
    downside_worst = float(down.min()) if len(down) else 0.0
    upside_worst = float(up.min()) if len(up) else 0.0
    if abs(downside_worst) > abs(upside_worst) * 1.15:
        tail_bias = "DOWNSIDE"
    elif abs(upside_worst) > abs(downside_worst) * 1.15:
        tail_bias = "UPSIDE"
    else:
        tail_bias = "TWO-SIDED"

    overall = _clip(
        0.16 * delta_risk +
        0.18 * convexity_risk +
        0.15 * vol_risk +
        0.08 * theta_risk +
        0.12 * third_order_risk +
        0.13 * concentration +
        0.18 * stress_score
    )

    if overall >= 80:
        regime = "EXTREME"
    elif overall >= 65:
        regime = "HIGH"
    elif overall >= 45:
        regime = "ELEVATED"
    elif overall >= 25:
        regime = "MODERATE"
    else:
        regime = "CONTROLLED"

    components = pd.DataFrame([
        ["Directional / Delta Risk", round(delta_risk, 2), "|Net Delta| / screening scale"],
        ["Convexity Risk", round(convexity_risk, 2), "Gamma + Vanna + Vomma"],
        ["Volatility Risk", round(vol_risk, 2), "Vega + Vomma"],
        ["Theta / Carry Risk", round(theta_risk, 2), "negative theta exposure"],
        ["Third-Order Risk", round(third_order_risk, 2), "Speed + Color + Ultima + Veta"],
        ["Concentration Risk", round(concentration, 2), "largest position risk share"],
        ["Stress / Tail Risk", round(stress_score, 2), "scenario loss rate + tail loss"],
    ], columns=["Risk Driver", "Score", "Method"])
    drivers = components.sort_values("Score", ascending=False).head(3).reset_index(drop=True)

    alert = None
    if overall >= 80:
        alert = "CRITICAL PORTFOLIO RISK — multiple independent risk layers are elevated."
    elif overall >= 65:
        alert = "HIGH PORTFOLIO RISK — review concentration and tail scenarios before increasing exposure."
    elif concentration >= 60:
        alert = "CONCENTRATION ALERT — one position contributes a large share of modeled risk."
    elif tail_loss_score >= 50:
        alert = "TAIL ALERT — modeled stress loss is large relative to net delta notional."
    else:
        alert = "Portfolio risk is within the current diagnostic band."

    return {
        "score": round(overall, 2),
        "regime": regime,
        "tail_bias": tail_bias,
        "delta_risk": round(delta_risk, 2),
        "convexity_risk": round(convexity_risk, 2),
        "volatility_risk": round(vol_risk, 2),
        "theta_risk": round(theta_risk, 2),
        "third_order_risk": round(third_order_risk, 2),
        "concentration_risk": round(concentration, 2),
        "stress_score": round(stress_score, 2),
        "tail_loss_score": round(tail_loss_score, 2),
        "loss_rate": round(loss_rate, 2),
        "worst": worst,
        "best": best,
        "components": components,
        "drivers": drivers,
        "attribution": attribution,
        "scenarios": scenarios,
        "alert": alert,
        "net_delta_notional": round(abs(net_delta) * spot, 2),
        "net_delta": net_delta,
        "net_gamma": net_gamma,
        "net_theta": net_theta,
        "net_vega": net_vega,
        "net_vanna": net_vanna,
        "net_vomma": net_vomma,
        "net_speed": net_speed,
        "net_color": net_color,
        "net_ultima": net_ultima,
        "net_veta": net_veta,
    }
