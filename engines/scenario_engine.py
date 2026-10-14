
"""IFIT V0.7.3 — Scenario Engine.

Stress-tests the current IFIT state across simultaneous spot, IV and time shocks.
Outputs are analytical research scenarios, not forecasts or trading instructions.
"""

import pandas as pd


def _clip(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(x)))


def scenario_pnl_approx(*, delta, gamma, vega, theta_per_day,
                         vanna=0.0, vomma=0.0, dspot=0.0, div=0.0, days=0.0):
    """Second-order spot/IV approximation with cross and time terms."""
    return (
        float(delta)*float(dspot)
        + 0.5*float(gamma)*(float(dspot)**2)
        + float(vega)*float(div)
        + float(vanna)*float(dspot)*float(div)
        + 0.5*float(vomma)*(float(div)**2)
        + float(theta_per_day)*float(days)
    )


def build_scenario_matrix(*, spot, expected_low, expected_high,
                           direction_bias, directional_score, confirmation_score,
                           risk_score, vol_score, gamma_risk, model_dislocation,
                           base_iv, delta=0.0, gamma=0.0, vega=0.0,
                           theta_per_day=0.0, vanna=0.0, vomma=0.0,
                           spot_shocks=(-0.02,-0.01,-0.005,0.0,0.005,0.01,0.02),
                           iv_shocks=(-0.04,-0.02,0.0,0.02,0.04),
                           horizons=(0,1,3)):
    """Return scenario rows and summary across spot/IV/time shocks."""
    s=float(spot); iv=float(base_iv)
    rows=[]
    for horizon in horizons:
        for shock in spot_shocks:
            for iv_shock in iv_shocks:
                dS=s*float(shock)
                dIV=float(iv_shock)
                pnl=scenario_pnl_approx(
                    delta=delta,gamma=gamma,vega=vega,theta_per_day=theta_per_day,
                    vanna=vanna,vomma=vomma,dspot=dS,div=dIV,days=horizon
                )
                future=s+dS
                if future < float(expected_low):
                    zone="BELOW EXPECTED RANGE"
                elif future > float(expected_high):
                    zone="ABOVE EXPECTED RANGE"
                else:
                    zone="INSIDE EXPECTED RANGE"

                # Stress score increases with distance, IV shock, gamma/model risk.
                stress=_clip(
                    35*abs(float(shock))/0.02 +
                    25*abs(dIV)/0.04 +
                    20*float(gamma_risk)/100 +
                    20*float(model_dislocation)/100
                )
                directional_fit = (
                    1 if direction_bias=="BULLISH" and shock>0 else
                    1 if direction_bias=="BEARISH" and shock<0 else
                    0.5 if direction_bias=="NEUTRAL" or shock==0 else 0
                )
                # Scenario confidence is deliberately reduced under stress.
                scenario_conf=_clip(
                    0.45*float(confirmation_score) +
                    0.25*float(directional_score)*directional_fit +
                    0.30*(100-stress)
                )
                rows.append({
                    "Horizon (D)":int(horizon),
                    "Spot Shock":f"{shock*100:+.1f}%",
                    "IV Shock":f"{dIV*100:+.1f} pts",
                    "Scenario Spot":round(future,2),
                    "IV":round(iv+dIV,3),
                    "Approx P&L":round(pnl,4),
                    "Range Zone":zone,
                    "Stress":round(stress,1),
                    "Confidence":round(scenario_conf,1),
                })
    df=pd.DataFrame(rows)
    worst=df.loc[df["Approx P&L"].idxmin()]
    best=df.loc[df["Approx P&L"].idxmax()]
    outside=int((df["Range Zone"]!="INSIDE EXPECTED RANGE").sum())
    return {
        "rows":df,
        "best":best.to_dict(),
        "worst":worst.to_dict(),
        "outside_count":outside,
        "total":len(df),
        "base_iv":iv,
        "spot":s,
    }


def scenario_summary(result):
    df=result["rows"]
    return [
        ("BASE SPOT",f'{result["spot"]:,.2f}'),
        ("BASE IV",f'{result["base_iv"]:.2f}%'),
        ("SCENARIOS",f'{result["total"]:,}'),
        ("OUTSIDE EXPECTED RANGE",f'{result["outside_count"]:,}'),
        ("BEST APPROX P&L",f'{result["best"]["Approx P&L"]:,.2f}'),
        ("WORST APPROX P&L",f'{result["worst"]["Approx P&L"]:,.2f}'),
    ]
