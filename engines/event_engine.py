
"""IFIT V0.7.0 — Real-Time Event Engine.

Detects state changes across IFIT's signal, regime, flow, volatility, gamma,
model-dislocation and market-structure layers. Events are change-detection
diagnostics, not trade execution instructions.
"""
from __future__ import annotations
from datetime import datetime


def _num(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return float(default)


def _event(ts, kind, severity, title, detail, score=0.0):
    return {
        "timestamp": ts.strftime("%H:%M:%S"),
        "kind": kind,
        "severity": severity,
        "title": title,
        "detail": detail,
        "score": round(float(score), 1),
    }


def detect_events(previous, current, now=None):
    """Return newly detected events comparing the prior state with current."""
    now = now or datetime.now()
    events = []
    if previous is None:
        return [_event(now, "SYSTEM", "INFO", "EVENT ENGINE INITIALIZED",
                       "Baseline established; subsequent refreshes will detect state changes.", 0)]

    prev = previous
    cur = current

    # Regime transition
    if prev.get("regime") != cur.get("regime"):
        events.append(_event(
            now, "REGIME", "HIGH" if cur.get("transition_risk", 0) >= 70 else "MEDIUM",
            "REGIME TRANSITION",
            f'{prev.get("regime","UNKNOWN")} → {cur.get("regime","UNKNOWN")} '
            f'(confidence {cur.get("regime_confidence",0):.1f}/100)',
            cur.get("regime_confidence",0)
        ))

    # Directional signal transition
    if prev.get("signal") != cur.get("signal"):
        events.append(_event(
            now, "SIGNAL", "HIGH" if cur.get("conviction",0) >= 70 else "MEDIUM",
            "SIGNAL SHIFT",
            f'{prev.get("signal","UNKNOWN")} → {cur.get("signal","UNKNOWN")} '
            f'(score {cur.get("direction_score",0):.1f}/100)',
            cur.get("direction_score",0)
        ))

    # Flow regime / score acceleration
    flow_delta=_num(cur.get("flow_score"))-_num(prev.get("flow_score"))
    if cur.get("flow_regime") != prev.get("flow_regime"):
        events.append(_event(
            now, "FLOW", "HIGH", "FLOW REGIME CHANGE",
            f'{prev.get("flow_regime","UNKNOWN")} → {cur.get("flow_regime","UNKNOWN")}; '
            f'flow score {cur.get("flow_score",0):.0f}/100',
            abs(flow_delta)
        ))
    elif abs(flow_delta) >= 12:
        events.append(_event(
            now, "FLOW", "MEDIUM", "FLOW ACCELERATION",
            f'Flow score moved {flow_delta:+.1f} points to {cur.get("flow_score",0):.1f}/100.',
            abs(flow_delta)
        ))

    # Volatility regime / score
    vol_delta=_num(cur.get("vol_score"))-_num(prev.get("vol_score"))
    if cur.get("vol_regime") != prev.get("vol_regime"):
        events.append(_event(
            now, "VOL", "HIGH", "VOLATILITY REGIME CHANGE",
            f'{prev.get("vol_regime","UNKNOWN")} → {cur.get("vol_regime","UNKNOWN")}; '
            f'volatility score {cur.get("vol_score",0):.1f}/100',
            abs(vol_delta)
        ))
    elif abs(vol_delta) >= 12:
        events.append(_event(
            now, "VOL", "MEDIUM", "VOLATILITY SHIFT",
            f'Volatility score moved {vol_delta:+.1f} points to {cur.get("vol_score",0):.1f}/100.',
            abs(vol_delta)
        ))

    # Gamma risk
    gamma_delta=_num(cur.get("gamma_risk"))-_num(prev.get("gamma_risk"))
    if abs(gamma_delta) >= 15:
        sev="HIGH" if cur.get("gamma_risk",0)>=70 else "MEDIUM"
        events.append(_event(
            now, "GAMMA", sev, "GAMMA RISK SHIFT",
            f'Gamma risk moved {gamma_delta:+.1f} points to {cur.get("gamma_risk",0):.1f}/100.',
            abs(gamma_delta)
        ))

    # Model dislocation
    dis_delta=_num(cur.get("model_dislocation"))-_num(prev.get("model_dislocation"))
    if abs(dis_delta) >= 15:
        sev="HIGH" if cur.get("model_dislocation",0)>=70 else "MEDIUM"
        events.append(_event(
            now, "MODEL", sev, "MODEL DISLOCATION SHIFT",
            f'Model dislocation moved {dis_delta:+.1f} points to '
            f'{cur.get("model_dislocation",0):.1f}/100.',
            abs(dis_delta)
        ))

    # Expected move boundary breach
    spot=_num(cur.get("spot"))
    lo=_num(cur.get("expected_low"))
    hi=_num(cur.get("expected_high"))
    pspot=_num(prev.get("spot"))
    plo=_num(prev.get("expected_low"))
    phi=_num(prev.get("expected_high"))
    if pspot <= phi and spot > hi:
        events.append(_event(now,"STRUCTURE","HIGH","EXPECTED-MOVE UPSIDE BREACH",
                             f'NIFTY {spot:,.2f} moved above expected-move high {hi:,.0f}.',100))
    elif pspot >= plo and spot < lo:
        events.append(_event(now,"STRUCTURE","HIGH","EXPECTED-MOVE DOWNSIDE BREACH",
                             f'NIFTY {spot:,.2f} moved below expected-move low {lo:,.0f}.',100))

    # Support/resistance crossings
    sup=_num(cur.get("support")); res=_num(cur.get("resistance"))
    psup=_num(prev.get("support")); pres=_num(prev.get("resistance"))
    if pspot <= pres and spot > res:
        events.append(_event(now,"STRUCTURE","HIGH","RESISTANCE BREAK",
                             f'NIFTY crossed resistance {res:,.0f}.',100))
    elif pspot >= psup and spot < sup:
        events.append(_event(now,"STRUCTURE","HIGH","SUPPORT BREAK",
                             f'NIFTY crossed support {sup:,.0f}.',100))

    # Health transition
    if prev.get("health") != cur.get("health"):
        events.append(_event(
            now,"DATA","MEDIUM" if cur.get("health")!="LIVE" else "INFO",
            "DATA HEALTH CHANGE",
            f'{prev.get("health","UNKNOWN")} → {cur.get("health","UNKNOWN")}.',
            0
        ))

    return events


def monitored_conditions(current):
    """Return current conditions worth monitoring even when no new event fired."""
    out=[]
    if current.get("transition_risk",0)>=70:
        out.append(("HIGH","Regime transition risk elevated"))
    if current.get("gamma_risk",0)>=70:
        out.append(("HIGH","Gamma risk elevated"))
    if current.get("model_dislocation",0)>=70:
        out.append(("HIGH","Model dislocation elevated"))
    if current.get("vol_regime")=="VOL EXPANSION":
        out.append(("HIGH","Volatility expansion regime"))
    if current.get("conviction",0)>=70:
        out.append(("MEDIUM",f'High signal conviction: {current.get("signal")}'))
    if not out:
        out.append(("INFO","No high-priority event conditions currently active"))
    return out
