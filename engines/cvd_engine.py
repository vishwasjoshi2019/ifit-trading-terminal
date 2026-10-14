import numpy as np
import pandas as pd


def _safe_slope(values):
    y = np.asarray(values, dtype=float)
    if len(y) < 2:
        return 0.0
    x = np.arange(len(y), dtype=float)
    return float(np.polyfit(x, y, 1)[0])


def _find_pivots(series, mode="high", window=1):
    s = pd.Series(series).reset_index(drop=True)
    pivots = []
    w = max(1, int(window))
    for i in range(w, len(s) - w):
        left = s.iloc[i-w:i]
        right = s.iloc[i+1:i+w+1]
        v = float(s.iloc[i])
        if mode == "high" and v >= float(left.max()) and v >= float(right.max()):
            pivots.append(i)
        elif mode == "low" and v <= float(left.min()) and v <= float(right.min()):
            pivots.append(i)
    return pivots


def analyze_cvd_divergence(bars, absorption_events=None, spot=None, pivot_window=1):
    """Transparent CVD/price divergence and flow-confluence engine."""
    b = bars.copy().reset_index(drop=True)
    if b.empty:
        return b, {
            "divergence": "NONE",
            "strength": 0,
            "price_trend": "FLAT",
            "cvd_trend": "FLAT",
            "momentum": "NEUTRAL",
            "latest_price": float(spot or 0),
            "latest_cvd": 0,
            "confluence_score": 50,
            "confluence": "NEUTRAL",
            "reason": "No bar data available.",
            "pivot_type": "NONE",
        }

    b["PriceChange"] = b["Close"].diff().fillna(0.0)
    b["CVDChange"] = b["CVD"].diff().fillna(0.0)
    b["DeltaAcceleration"] = b["Delta"].diff().fillna(0.0)

    # Short-term slopes give a continuous read in addition to discrete pivots.
    n = min(5, len(b))
    price_slope = _safe_slope(b["Close"].tail(n))
    cvd_slope = _safe_slope(b["CVD"].tail(n))

    price_trend = "UP" if price_slope > 0.75 else "DOWN" if price_slope < -0.75 else "FLAT"
    cvd_trend = "UP" if cvd_slope > 75 else "DOWN" if cvd_slope < -75 else "FLAT"

    if len(b) >= 3:
        recent_delta = b["Delta"].tail(3).tolist()
        if all(recent_delta[i] > recent_delta[i+1] for i in range(2)):
            momentum = "BUYING PRESSURE WEAKENING" if recent_delta[0] > 0 else "SELLING PRESSURE STRENGTHENING"
        elif all(recent_delta[i] < recent_delta[i+1] for i in range(2)):
            momentum = "SELLING PRESSURE WEAKENING" if recent_delta[0] < 0 else "BUYING PRESSURE STRENGTHENING"
        else:
            momentum = "MIXED"
    else:
        momentum = "NEUTRAL"

    highs = _find_pivots(b["Close"], "high", pivot_window)
    lows = _find_pivots(b["Close"], "low", pivot_window)

    candidates = []

    if len(highs) >= 2:
        i1, i2 = highs[-2], highs[-1]
        p1, p2 = float(b.loc[i1, "Close"]), float(b.loc[i2, "Close"])
        c1, c2 = float(b.loc[i1, "CVD"]), float(b.loc[i2, "CVD"])
        if p2 > p1 and c2 < c1:
            price_move = abs(p2-p1) / max(abs(p1), 1) * 10000
            cvd_move = abs(c2-c1) / max(float(b["CVD"].abs().max()), 1) * 100
            strength = int(np.clip(55 + min(price_move, 40) * 0.5 + min(cvd_move, 30) * 0.7, 55, 95))
            candidates.append((i2, "BEARISH", strength, "HIGH", i1, i2))

    if len(lows) >= 2:
        i1, i2 = lows[-2], lows[-1]
        p1, p2 = float(b.loc[i1, "Close"]), float(b.loc[i2, "Close"])
        c1, c2 = float(b.loc[i1, "CVD"]), float(b.loc[i2, "CVD"])
        if p2 < p1 and c2 > c1:
            price_move = abs(p2-p1) / max(abs(p1), 1) * 10000
            cvd_move = abs(c2-c1) / max(float(b["CVD"].abs().max()), 1) * 100
            strength = int(np.clip(55 + min(price_move, 40) * 0.5 + min(cvd_move, 30) * 0.7, 55, 95))
            candidates.append((i2, "BULLISH", strength, "LOW", i1, i2))

    # Prefer the most recent qualifying divergence.
    if candidates:
        candidates.sort(key=lambda x: x[0])
        pivot_idx, divergence, strength, pivot_type, prev_idx, cur_idx = candidates[-1]
        if divergence == "BEARISH":
            reason = "Price printed a higher pivot while CVD printed a lower pivot. Aggressive buying is not confirming the new high."
        else:
            reason = "Price printed a lower pivot while CVD printed a higher pivot. Aggressive selling is not confirming the new low."
        divergence_time = str(b.loc[cur_idx, "Time"])
    else:
        divergence = "NONE"
        strength = 0
        pivot_type = "NONE"
        prev_idx = cur_idx = None
        reason = "No confirmed higher-high/lower-high or lower-low/higher-low CVD divergence in the available bars."
        divergence_time = str(b.iloc[-1]["Time"])

    # Confluence starts from the flow score and adjusts for CVD divergence,
    # pressure momentum, and absorption/exhaustion evidence.
    base = 50
    if price_trend == "UP":
        base += 10
    elif price_trend == "DOWN":
        base -= 10
    if cvd_trend == "UP":
        base += 10
    elif cvd_trend == "DOWN":
        base -= 10

    if divergence == "BEARISH":
        base -= int(round(strength * 0.25))
    elif divergence == "BULLISH":
        base += int(round(strength * 0.25))

    if absorption_events is not None:
        ae = absorption_events
        base += min(10, int(ae.get("buy_absorption_bars", 0)) * 2)
        base -= min(10, int(ae.get("sell_absorption_bars", 0)) * 2)
        base -= min(8, int(ae.get("buyer_exhaustion_bars", 0)) * 2)
        base += min(8, int(ae.get("seller_exhaustion_bars", 0)) * 2)

    confluence_score = int(np.clip(base, 0, 100))
    if confluence_score >= 70:
        confluence = "BULLISH FLOW"
    elif confluence_score <= 30:
        confluence = "BEARISH FLOW"
    else:
        confluence = "NEUTRAL / MIXED"

    b["Divergence"] = ""
    if cur_idx is not None:
        b.loc[cur_idx, "Divergence"] = f"{divergence} {pivot_type}"

    return b, {
        "divergence": divergence,
        "strength": strength,
        "pivot_type": pivot_type,
        "pivot_previous": prev_idx,
        "pivot_current": cur_idx,
        "divergence_time": divergence_time,
        "price_trend": price_trend,
        "cvd_trend": cvd_trend,
        "momentum": momentum,
        "latest_price": float(b.iloc[-1]["Close"]),
        "latest_cvd": int(b.iloc[-1]["CVD"]),
        "price_slope": price_slope,
        "cvd_slope": cvd_slope,
        "confluence_score": confluence_score,
        "confluence": confluence,
        "reason": reason,
    }
