
"""IFIT V0.7.2 — Decision Matrix Engine.

Combines existing IFIT research layers into an explainable decision-support matrix.
This is not an order-generation or probability-of-profit engine.
"""

def _clip(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(x)))


def _dir_score(value, neutral=50.0):
    """Map a 0-100 input into a signed -1..+1 contribution."""
    return (float(value)-neutral)/50.0


def build_decision_matrix(*, market_score, regime_confidence, directional_strength,
                          flow_score, vol_score, gamma_risk, model_dislocation,
                          signal_direction, conviction, transition_risk,
                          spot, support, resistance, expected_low, expected_high,
                          pcr, iv_premium, active_alerts=0):
    """Return an explainable decision-support matrix."""
    # Directional agreement: market, flow and signal carry positive directional weight.
    market_c=_dir_score(market_score)
    flow_c=_dir_score(flow_score)
    signal_c={"BULLISH":1.0,"BEARISH":-1.0,"NEUTRAL":0.0}.get(str(signal_direction).upper(),0.0)
    directional = 50 + 20*market_c + 20*flow_c + 15*signal_c
    directional=_clip(directional)

    # Confirmation rewards regime confidence and conviction, penalizes transition risk.
    confirmation=_clip(
        0.45*float(regime_confidence) +
        0.35*float(conviction) +
        0.20*(100-float(transition_risk))
    )

    # Risk is intentionally independent of direction.
    risk=_clip(
        0.30*float(gamma_risk) +
        0.30*float(model_dislocation) +
        0.20*float(transition_risk) +
        0.20*min(100,float(active_alerts)*25)
    )

    # Volatility context: high vol score means expansion; high IV premium adds risk.
    vol_context=_clip(0.70*float(vol_score) + 0.30*min(100,max(0,float(iv_premium)*10)))

    # Location / invalidation distance.
    s=float(spot); sup=float(support); res=float(resistance)
    low=float(expected_low); high=float(expected_high)
    if s < sup:
        location="BELOW SUPPORT"
    elif s > res:
        location="ABOVE RESISTANCE"
    elif res > sup and s >= sup and s <= res:
        location="INSIDE STRUCTURAL RANGE"
    else:
        location="INSIDE EXPECTED RANGE"

    # Setup classification.
    agreement=(directional*0.45 + confirmation*0.35 + (100-risk)*0.20)
    if agreement >= 72 and risk < 45:
        setup="HIGH-QUALITY SETUP"
    elif agreement >= 58 and risk < 65:
        setup="WATCHLIST SETUP"
    elif risk >= 75:
        setup="RISK-OFF / NO EDGE"
    else:
        setup="NO CLEAR EDGE"

    direction=str(signal_direction).upper()
    if direction not in ("BULLISH","BEARISH"):
        direction_bias="NEUTRAL"
    elif directional >= 60:
        direction_bias=direction
    elif directional <= 40:
        direction_bias="BEARISH" if direction=="BULLISH" else "BULLISH"
    else:
        direction_bias="NEUTRAL"

    if risk >= 75:
        risk_level="EXTREME"
    elif risk >= 60:
        risk_level="HIGH"
    elif risk >= 40:
        risk_level="MODERATE"
    else:
        risk_level="LOW"

    # Research boundary / invalidation.
    if direction_bias=="BULLISH":
        invalidation=f"Below {sup:,.0f}"
        confirmation_rule=f"Hold above {res:,.0f} with improving flow/conviction"
    elif direction_bias=="BEARISH":
        invalidation=f"Above {res:,.0f}"
        confirmation_rule=f"Hold below {sup:,.0f} with weakening flow/conviction"
    else:
        invalidation=f"Outside {low:,.0f} – {high:,.0f}"
        confirmation_rule=f"Break and acceptance beyond {sup:,.0f} / {res:,.0f}"

    drivers=[
        ("Market State", round(float(market_score),1), "Directional context"),
        ("Flow", round(float(flow_score),1), "Order-flow confirmation"),
        ("Signal", round(float(conviction),1), f"{direction} / conviction"),
        ("Regime Confidence", round(float(regime_confidence),1), "Regime confirmation"),
        ("Volatility", round(float(vol_score),1), "Volatility context"),
        ("Gamma Risk", round(float(gamma_risk),1), "Convexity risk"),
        ("Model Dislocation", round(float(model_dislocation),1), "Model-vs-market risk"),
    ]
    drivers_sorted=sorted(drivers,key=lambda x:abs(x[1]-50),reverse=True)

    return {
        "setup":setup,
        "direction_bias":direction_bias,
        "directional_score":round(directional,1),
        "confirmation_score":round(confirmation,1),
        "risk_score":round(risk,1),
        "risk_level":risk_level,
        "volatility_context":round(vol_context,1),
        "location":location,
        "expected_move":f"{low:,.0f} – {high:,.0f}",
        "invalidation":invalidation,
        "confirmation_rule":confirmation_rule,
        "agreement_score":round(agreement,1),
        "pcr":round(float(pcr),2),
        "iv_premium":round(float(iv_premium),2),
        "active_alerts":int(active_alerts),
        "strongest_drivers":drivers_sorted[:4],
    }


def decision_table(matrix):
    """Compact table-ready representation."""
    return [
        ("SETUP",matrix["setup"]),
        ("DIRECTION BIAS",matrix["direction_bias"]),
        ("DIRECTIONAL SCORE",f'{matrix["directional_score"]:.1f}/100'),
        ("CONFIRMATION",f'{matrix["confirmation_score"]:.1f}/100'),
        ("RISK",f'{matrix["risk_level"]} ({matrix["risk_score"]:.1f}/100)'),
        ("LOCATION",matrix["location"]),
        ("EXPECTED MOVE",matrix["expected_move"]),
        ("CONFIRMATION RULE",matrix["confirmation_rule"]),
        ("INVALIDATION",matrix["invalidation"]),
    ]
