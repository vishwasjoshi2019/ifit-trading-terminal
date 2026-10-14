
"""IFIT V0.7.4 — Risk Engine.

Cross-engine market-risk diagnostics. Scores are normalized research diagnostics,
not VaR forecasts, capital requirements, or investment advice.
"""
import pandas as pd


def _clip(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(x)))


def build_risk_engine(*, market_score, regime_confidence, flow_score, vol_score,
                      gamma_risk, model_dislocation, signal_confirmation,
                      direction_score, event_count=0, alert_count=0,
                      expected_low=0.0, expected_high=0.0, spot=0.0,
                      scenario_result=None):
    """Build a transparent cross-engine risk map."""
    # Component construction intentionally uses independent observable diagnostics.
    volatility_risk=_clip(0.55*float(vol_score)+0.45*float(gamma_risk))
    model_risk=_clip(float(model_dislocation))
    signal_uncertainty=_clip(100.0-float(signal_confirmation))
    regime_risk=_clip(100.0-float(regime_confidence))
    flow_risk=_clip(100.0-float(flow_score))
    event_risk=_clip(min(100.0, 25.0*float(event_count)+12.0*float(alert_count)))

    range_width=max(1e-9,float(expected_high)-float(expected_low))
    downside_room=max(0.0,float(spot)-float(expected_low))
    upside_room=max(0.0,float(expected_high)-float(spot))
    asymmetry=_clip(100.0*(1.0-downside_room/max(range_width,1e-9)))

    # Overall risk is a weighted blend; market strength moderates rather than
    # eliminates risk because a strong directional signal can still be fragile.
    overall=_clip(
        0.20*volatility_risk +
        0.18*model_risk +
        0.17*signal_uncertainty +
        0.15*regime_risk +
        0.12*flow_risk +
        0.10*event_risk +
        0.08*asymmetry
    )

    if overall >= 75:
        regime="EXTREME"
    elif overall >= 60:
        regime="HIGH"
    elif overall >= 40:
        regime="ELEVATED"
    else:
        regime="CONTROLLED"

    # Direction-aware tail diagnostics.
    if str(direction_score).upper()=="BEARISH":
        tail_bias="DOWNSIDE"
    elif str(direction_score).upper()=="BULLISH":
        tail_bias="UPSIDE"
    else:
        tail_bias="TWO-SIDED"

    components=pd.DataFrame([
        ["Volatility / Convexity", round(volatility_risk,2), "IV + gamma risk"],
        ["Model Risk", round(model_risk,2), "Heston / market dislocation"],
        ["Signal Uncertainty", round(signal_uncertainty,2), "100 - signal confirmation"],
        ["Regime Risk", round(regime_risk,2), "100 - regime confidence"],
        ["Flow Risk", round(flow_risk,2), "100 - flow score"],
        ["Event Risk", round(event_risk,2), "events + alerts"],
        ["Range Asymmetry", round(asymmetry,2), "current position in expected range"],
    ], columns=["Risk Driver","Score","Method"])
    drivers=components.sort_values("Score",ascending=False).head(3)

    scenario_stats={}
    if scenario_result is not None and hasattr(scenario_result,"get"):
        rows=scenario_result.get("rows")
        if rows is not None and len(rows):
            losses=rows[rows["Approx P&L"]<0]["Approx P&L"]
            scenario_stats={
                "scenario_count": int(len(rows)),
                "loss_scenarios": int(len(losses)),
                "loss_rate": round(100.0*len(losses)/len(rows),2),
                "worst_pnl": round(float(rows["Approx P&L"].min()),4),
                "best_pnl": round(float(rows["Approx P&L"].max()),4),
                "outside_range": int(scenario_result.get("outside_count",0)),
            }

    return {
        "overall_score":round(overall,2),
        "regime":regime,
        "tail_bias":tail_bias,
        "volatility_risk":round(volatility_risk,2),
        "model_risk":round(model_risk,2),
        "signal_uncertainty":round(signal_uncertainty,2),
        "regime_risk":round(regime_risk,2),
        "flow_risk":round(flow_risk,2),
        "event_risk":round(event_risk,2),
        "range_asymmetry":round(asymmetry,2),
        "components":components,
        "drivers":drivers,
        "scenario_stats":scenario_stats,
    }


def risk_summary(result):
    return [
        ("RISK SCORE",f'{result["overall_score"]:.1f}/100'),
        ("RISK REGIME",result["regime"]),
        ("TAIL BIAS",result["tail_bias"]),
        ("VOL / CONVEXITY",f'{result["volatility_risk"]:.1f}'),
        ("MODEL RISK",f'{result["model_risk"]:.1f}'),
        ("SIGNAL UNCERTAINTY",f'{result["signal_uncertainty"]:.1f}'),
    ]
