
import math
import numpy as np
import pandas as pd

from engines.greeks_engine import calculate_higher_order_greeks

GREEK_FIELDS = [
    "delta", "gamma", "theta", "vega", "rho",
    "vanna", "vomma", "charm", "zomma",
    "speed", "color", "ultima", "veta"
]

DISPLAY_NAMES = {
    "delta": "Delta", "gamma": "Gamma", "theta": "Theta",
    "vega": "Vega", "rho": "Rho", "vanna": "Vanna",
    "vomma": "Vomma / Volga", "charm": "Charm", "zomma": "Zomma",
    "speed": "Speed", "color": "Color", "ultima": "Ultima", "veta": "Veta"
}

def position_greeks(position, spot, r_percent=6.5, q_percent=0.0):
    option = position["Option"].upper()
    qty = float(position["Qty"])
    multiplier = float(position.get("Multiplier", 1))
    signed_qty = qty if position["Side"].upper() == "BUY" else -qty
    scale = signed_qty * multiplier

    g = calculate_higher_order_greeks(
        spot, float(position["Strike"]), float(position["DTE"]),
        float(position["IV"]), r_percent, q_percent, option
    )
    result = {"Instrument": position["Instrument"], "Side": position["Side"],
              "Qty": qty, "Multiplier": multiplier, "Signed Units": scale}
    for field in GREEK_FIELDS:
        result[field] = g[field] * scale
    return result

def portfolio_greeks(positions, spot, r_percent=6.5, q_percent=0.0):
    rows = [position_greeks(p, spot, r_percent, q_percent) for p in positions]
    if not rows:
        return pd.DataFrame(), {}

    df = pd.DataFrame(rows)
    totals = {field: float(df[field].sum()) for field in GREEK_FIELDS}
    totals["position_count"] = len(rows)
    return df, totals

def _safe_ratio(num, den):
    return abs(num) / max(abs(den), 1e-12)

def portfolio_regime(totals):
    gamma = totals.get("gamma", 0.0)
    vanna = totals.get("vanna", 0.0)
    vomma = totals.get("vomma", 0.0)
    charm = totals.get("charm", 0.0)
    third = np.mean([
        abs(totals.get("speed", 0.0)),
        abs(totals.get("color", 0.0)),
        abs(totals.get("ultima", 0.0)),
        abs(totals.get("veta", 0.0))
    ])

    # Relative risk indicators. These are diagnostics, not trade signals.
    gamma_score = min(100.0, 100.0 * _safe_ratio(gamma, 0.01))
    vanna_score = min(100.0, 100.0 * _safe_ratio(vanna, 2.0))
    vomma_score = min(100.0, 100.0 * _safe_ratio(vomma, 10.0))
    charm_score = min(100.0, 100.0 * _safe_ratio(charm, 1.0))
    third_score = min(100.0, 100.0 * _safe_ratio(third, 0.5))

    weighted = (
        0.28 * gamma_score +
        0.24 * vanna_score +
        0.18 * vomma_score +
        0.12 * charm_score +
        0.18 * third_score
    )
    score = float(np.clip(weighted, 0, 100))

    if gamma > 0.000001:
        gamma_regime = "LONG GAMMA"
    elif gamma < -0.000001:
        gamma_regime = "SHORT GAMMA"
    else:
        gamma_regime = "GAMMA NEUTRAL"

    if vanna > 0.000001:
        vanna_regime = "LONG VANNA"
    elif vanna < -0.000001:
        vanna_regime = "SHORT VANNA"
    else:
        vanna_regime = "VANNA NEUTRAL"

    if vomma > 0.000001:
        vomma_regime = "LONG VOL CONVEXITY"
    elif vomma < -0.000001:
        vomma_regime = "SHORT VOL CONVEXITY"
    else:
        vomma_regime = "VOL CONVEXITY NEUTRAL"

    if charm > 0.000001:
        charm_regime = "POSITIVE DELTA DRIFT"
    elif charm < -0.000001:
        charm_regime = "NEGATIVE DELTA DRIFT"
    else:
        charm_regime = "DELTA DRIFT NEUTRAL"

    if score >= 75:
        risk_band = "EXTREME"
    elif score >= 50:
        risk_band = "HIGH"
    elif score >= 25:
        risk_band = "MODERATE"
    else:
        risk_band = "LOW"

    drivers = sorted([
        ("Gamma", gamma_score),
        ("Vanna", vanna_score),
        ("Vomma / Volga", vomma_score),
        ("Charm", charm_score),
        ("Third-order", third_score)
    ], key=lambda x: x[1], reverse=True)

    return {
        "score": score,
        "risk_band": risk_band,
        "gamma_regime": gamma_regime,
        "vanna_regime": vanna_regime,
        "vomma_regime": vomma_regime,
        "charm_regime": charm_regime,
        "third_order_score": third_score,
        "drivers": drivers
    }

def scenario_pnl(totals, spot, spot_change_pct=0.0, iv_change_points=0.0, days_passed=0):
    """
    Local Taylor-style scenario estimate using portfolio Greeks.

    P&L approximation:
      Delta*dS + 0.5*Gamma*dS^2
      + Vega*dIV + Vanna*dS*dIV
      + 0.5*Vomma*dIV^2
      + Theta*days

    Here dIV is expressed in volatility points because Vega is per vol-point.
    This is an approximation, not a full repricing engine.
    """
    dS = float(spot) * float(spot_change_pct) / 100.0
    dIV = float(iv_change_points)
    dT = float(days_passed)

    pnl = (
        totals.get("delta", 0.0) * dS +
        0.5 * totals.get("gamma", 0.0) * dS * dS +
        totals.get("vega", 0.0) * dIV +
        totals.get("vanna", 0.0) * dS * dIV +
        0.5 * totals.get("vomma", 0.0) * dIV * dIV +
        totals.get("theta", 0.0) * dT
    )
    return float(pnl)

def scenario_matrix(totals, spot, spot_moves=(-2,-1,0,1,2), iv_moves=(-4,-2,0,2,4)):
    rows = []
    for sm in spot_moves:
        row = {"Spot %": sm}
        for iv in iv_moves:
            row[f"IV {iv:+g}pt"] = scenario_pnl(
                totals, spot, spot_change_pct=sm, iv_change_points=iv, days_passed=0
            )
        rows.append(row)
    return pd.DataFrame(rows).set_index("Spot %")

def portfolio_exposure_summary(totals):
    return pd.DataFrame([
        {"Greek": DISPLAY_NAMES[f], "Net Exposure": totals.get(f, 0.0)}
        for f in GREEK_FIELDS
    ])
