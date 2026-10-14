
import numpy as np
import pandas as pd

def _norm_abs(x, scale):
    if scale <= 0:
        return 0.0
    return float(np.clip(abs(x) / scale, 0.0, 1.0))

def _band(score):
    if score >= 75:
        return "EXTREME"
    if score >= 55:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"

def _directional_label(value, positive, negative):
    if value > positive:
        return "POSITIVE"
    if value < negative:
        return "NEGATIVE"
    return "NEUTRAL"

def analyze_greek_regime(surface_map, selected_greek="Vanna"):
    """
    Analyze a dictionary of Greek -> strike x expiry DataFrames.
    Produces normalized risk scores plus an explainable overall convexity score.
    """
    metrics = {}
    for greek, df in surface_map.items():
        arr = np.asarray(df.values, dtype=float)
        finite = arr[np.isfinite(arr)]
        if finite.size == 0:
            metrics[greek] = {"magnitude": 0.0, "score": 0.0, "mean": 0.0,
                              "max_abs": 0.0, "positive_share": 0.0}
            continue
        max_abs = float(np.max(np.abs(finite)))
        mean = float(np.mean(finite))
        positive_share = float(np.mean(finite > 0))
        # Robust concentration measure: median absolute magnitude vs max.
        med_abs = float(np.median(np.abs(finite)))
        magnitude = med_abs / max(max_abs, 1e-12)
        score = float(np.clip(100 * (0.55*magnitude + 0.45*_norm_abs(mean, max_abs)), 0, 100))
        metrics[greek] = {
            "magnitude": magnitude, "score": score, "mean": mean,
            "max_abs": max_abs, "positive_share": positive_share
        }

    # Weight the most decision-relevant convexity terms more heavily.
    weights = {
        "Gamma": 1.25, "Vanna": 1.15, "Vomma / Volga": 1.10,
        "Charm": 0.80, "Zomma": 1.00, "Speed": 0.90,
        "Color": 0.80, "Ultima": 0.95, "Veta": 0.75,
        "Delta": 0.35, "Theta": 0.35, "Vega": 0.50, "Rho": 0.20
    }
    total_w = 0.0
    weighted = 0.0
    for k, m in metrics.items():
        w = weights.get(k, 0.5)
        weighted += w * m["score"]
        total_w += w
    overall = float(np.clip(weighted / max(total_w, 1e-9), 0, 100))

    # Regime interpretation.
    gamma = metrics.get("Gamma", {})
    vanna = metrics.get("Vanna", {})
    vomma = metrics.get("Vomma / Volga", {})
    charm = metrics.get("Charm", {})
    zomma = metrics.get("Zomma", {})
    third = np.mean([metrics.get(k, {}).get("score", 0.0)
                     for k in ["Speed","Color","Ultima","Veta"]])

    if overall >= 75:
        overall_label = "EXTREME CONVEXITY"
    elif overall >= 55:
        overall_label = "HIGH CONVEXITY"
    elif overall >= 30:
        overall_label = "MODERATE CONVEXITY"
    else:
        overall_label = "LOW CONVEXITY"

    if gamma.get("positive_share", 0.5) > 0.60:
        gamma_label = "POSITIVE GAMMA DOMINANT"
    elif gamma.get("positive_share", 0.5) < 0.40:
        gamma_label = "NEGATIVE GAMMA DOMINANT"
    else:
        gamma_label = "MIXED GAMMA"

    def sensitivity_label(m):
        s = m.get("score", 0)
        return _band(s) if s >= 30 else "LOW"

    if vanna.get("score", 0) >= 65:
        vanna_label = "HIGH VOL → DELTA COUPLING"
    elif vanna.get("score", 0) >= 35:
        vanna_label = "MODERATE VOL → DELTA COUPLING"
    else:
        vanna_label = "LOW VOL → DELTA COUPLING"

    if vomma.get("score", 0) >= 65:
        vomma_label = "HIGH VOL CONVEXITY"
    elif vomma.get("score", 0) >= 35:
        vomma_label = "MODERATE VOL CONVEXITY"
    else:
        vomma_label = "LOW VOL CONVEXITY"

    if charm.get("score", 0) >= 65:
        charm_label = "HIGH DELTA DRIFT"
    elif charm.get("score", 0) >= 35:
        charm_label = "MODERATE DELTA DRIFT"
    else:
        charm_label = "LOW DELTA DRIFT"

    if zomma.get("score", 0) >= 65:
        zomma_label = "HIGH VOL → GAMMA COUPLING"
    elif zomma.get("score", 0) >= 35:
        zomma_label = "MODERATE VOL → GAMMA COUPLING"
    else:
        zomma_label = "LOW VOL → GAMMA COUPLING"

    # Concentration: locate the largest absolute value in selected surface.
    sel = surface_map.get(selected_greek)
    hotspot = None
    if sel is not None:
        a = np.asarray(sel.values, dtype=float)
        if np.isfinite(a).any():
            idx = np.unravel_index(np.nanargmax(np.abs(a)), a.shape)
            hotspot = {
                "strike": float(sel.index[idx[0]]),
                "expiry": str(sel.columns[idx[1]]),
                "value": float(a[idx])
            }

    # Strongest drivers.
    drivers = sorted(
        [(k, float(v.get("score", 0))) for k, v in metrics.items()],
        key=lambda x: x[1], reverse=True
    )[:4]

    explanation = (
        f"IFIT detects {overall_label.lower()}. "
        f"{gamma_label.replace('_',' ').lower()} is the current gamma backdrop, "
        f"while {vanna_label.lower()} and {vomma_label.lower()} describe the "
        f"volatility coupling. Third-order risk averages {third:.0f}/100."
    )

    return {
        "overall_score": overall,
        "overall_label": overall_label,
        "gamma_label": gamma_label,
        "vanna_label": vanna_label,
        "vomma_label": vomma_label,
        "charm_label": charm_label,
        "zomma_label": zomma_label,
        "third_order_score": float(third),
        "metrics": metrics,
        "drivers": drivers,
        "hotspot": hotspot,
        "explanation": explanation,
    }

def regime_component_table(result):
    names = ["Gamma","Vanna","Vomma / Volga","Charm","Zomma","Speed","Color","Ultima","Veta"]
    rows=[]
    for name in names:
        m=result["metrics"].get(name, {})
        rows.append({
            "Greek": name,
            "Risk Score": round(m.get("score",0),1),
            "Mean": m.get("mean",0),
            "Max |Greek|": m.get("max_abs",0),
            "Regime": _band(m.get("score",0))
        })
    return pd.DataFrame(rows)
