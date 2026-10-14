"""IFIT V0.7.7 — Market Microstructure / Execution Intelligence.

Cross-contract microstructure diagnostics derived from normalized quote/depth
fields. When provider bid/ask/depth is unavailable, IFIT uses the V0.7.6
simulation quote/depth proxies and labels them accordingly. Outputs are
research diagnostics, not order instructions or guaranteed fills.
"""
import math
import numpy as np
import pandas as pd


def _clip(x, lo=0.0, hi=100.0):
    try:
        return float(np.clip(float(x), lo, hi))
    except Exception:
        return lo


def _num(row, names, default=np.nan):
    for n in names:
        if n in row.index:
            try:
                v = float(row[n])
                if math.isfinite(v):
                    return v
            except Exception:
                pass
    return default


def _quote(row, side):
    ltp = _num(row, [f"{side} LTP"], 0.0)
    bid = _num(row, [f"{side} Bid", f"{side} BID", f"{side}_bid"], np.nan)
    ask = _num(row, [f"{side} Ask", f"{side} ASK", f"{side}_ask"], np.nan)
    if not (math.isfinite(bid) and math.isfinite(ask) and bid > 0 and ask >= bid):
        oi = max(_num(row, [f"{side} OI"], 0.0), 0.0)
        oi_factor = min(1.0, math.log10(max(oi, 10.0)) / 6.0)
        bps = 34.0 - 16.0 * oi_factor
        half = max(0.025, ltp * bps / 20000.0)
        bid, ask = max(0.01, ltp - half), ltp + half
        source = "SIMULATED QUOTE"
    else:
        source = "PROVIDER QUOTE"
    return float(bid), float(ask), source


def _depth(row, side):
    vals = []
    # Accept common provider naming conventions.
    for level in range(1, 6):
        names = [
            f"{side} BidQty{level}", f"{side} Bid Qty {level}",
            f"{side} AskQty{level}", f"{side} Ask Qty {level}",
        ]
        vals.append(_num(row, names, np.nan))
    if all(math.isfinite(v) and v >= 0 for v in vals):
        return np.array(vals, dtype=float), "PROVIDER DEPTH"
    oi = max(_num(row, [f"{side} OI"], 0.0), 0.0)
    top = max(1.0, oi * 0.008)
    return np.array([top / (1.0 + 0.20 * i) for i in range(5)], dtype=float), "OI PROXY"


def _side_micro(row, side):
    ltp = max(_num(row, [f"{side} LTP"], 0.0), 0.01)
    oi = max(_num(row, [f"{side} OI"], 0.0), 0.0)
    bid, ask, quote_source = _quote(row, side)
    depth, depth_source = _depth(row, side)
    spread = max(0.0, ask - bid)
    mid = max((bid + ask) / 2.0, 0.01)
    spread_bps = spread / mid * 10000.0
    top = float(depth[0])
    total = float(depth.sum())
    # Queue-pressure proxy: deeper top-of-book liquidity relative to total depth
    queue_concentration = top / max(total, 1.0)
    # A quote-location diagnostic: where LTP sits inside the quoted market.
    quote_position = _clip((ltp - bid) / max(spread, 0.01) * 100.0, -100.0, 200.0)
    spread_eff = _clip(100.0 - max(0.0, spread_bps - 5.0) * 4.0)
    depth_score = _clip(math.log10(max(total, 1.0)) / 5.0 * 100.0)
    oi_score = _clip(math.log10(max(oi, 10.0)) / 6.0 * 100.0)
    return {
        "Bid": bid, "Ask": ask, "Mid": mid, "Spread": spread,
        "Spread (bps)": spread_bps, "Top Depth": top,
        "5-Level Depth": total, "Quote Position": quote_position,
        "Queue Concentration": queue_concentration * 100.0,
        "Spread Efficiency": spread_eff, "Depth Score": depth_score,
        "OI Score": oi_score, "Quote Source": quote_source,
        "Depth Source": depth_source,
    }


def build_microstructure(*, chain_df, spot, multiplier=50):
    """Build chain-wide market microstructure and execution diagnostics."""
    if not isinstance(chain_df, pd.DataFrame) or chain_df.empty:
        empty = pd.DataFrame()
        return {
            "score": 0.0, "regime": "NO DATA", "contracts": empty,
            "top_contracts": empty, "risk_contracts": empty,
            "alert": "No option-chain records available for microstructure analysis.",
            "summary": {}, "atm": empty, "ladder": empty,
        }

    rows = []
    for _, r in chain_df.iterrows():
        strike = _num(r, ["Strike"], np.nan)
        if not math.isfinite(strike):
            continue
        ce = _side_micro(r, "CE") if _num(r, ["CE LTP"], np.nan) > 0 else None
        pe = _side_micro(r, "PE") if _num(r, ["PE LTP"], np.nan) > 0 else None
        for side, x in (("CE", ce), ("PE", pe)):
            if x is None:
                continue
            # Microstructure quality weights execution efficiency, depth and quote quality.
            quote_quality = 100.0 if x["Quote Source"] == "PROVIDER QUOTE" else 72.0
            score = _clip(
                0.40 * x["Spread Efficiency"]
                + 0.30 * x["Depth Score"]
                + 0.15 * x["OI Score"]
                + 0.10 * quote_quality
                + 0.05 * (100.0 - abs(x["Queue Concentration"] - 20.0) * 2.0)
            )
            # Execution-friction proxy: higher spread + lower depth + high queue concentration.
            friction = _clip(
                0.45 * (100.0 - x["Spread Efficiency"])
                + 0.35 * (100.0 - x["Depth Score"])
                + 0.20 * _clip(x["Queue Concentration"] * 2.0)
            )
            rows.append({
                "Strike": strike, "Option": side,
                "LTP": x.get("Mid", 0.0), "OI": _num(r, [f"{side} OI"], 0.0),
                **x, "Microstructure Score": score,
                "Execution Friction": friction,
            })
    contracts = pd.DataFrame(rows)
    if contracts.empty:
        return {
            "score": 0.0, "regime": "NO DATA", "contracts": contracts,
            "top_contracts": contracts, "risk_contracts": contracts,
            "alert": "No valid option quotes available.", "summary": {},
            "atm": contracts, "ladder": contracts,
        }

    # Chain-level score and directional pressure proxy from call/put microstructure.
    score = float(contracts["Microstructure Score"].mean())
    friction = float(contracts["Execution Friction"].mean())
    median_spread = float(contracts["Spread (bps)"].median())
    p90_spread = float(contracts["Spread (bps)"].quantile(0.90))
    median_depth = float(contracts["5-Level Depth"].median())

    # ATM microstructure summary.
    atm_strike = round(float(spot) / 100.0) * 100.0
    atm = contracts.iloc[(contracts["Strike"] - atm_strike).abs().argsort()[:2]].copy()
    atm_pressure = 0.0
    if len(atm):
        ce = atm[atm["Option"] == "CE"]["Microstructure Score"]
        pe = atm[atm["Option"] == "PE"]["Microstructure Score"]
        if len(ce) and len(pe):
            atm_pressure = float(ce.iloc[0] - pe.iloc[0])

    if score >= 80:
        regime = "EFFICIENT / DEEP"
    elif score >= 65:
        regime = "HEALTHY"
    elif score >= 45:
        regime = "SELECTIVE"
    elif score >= 25:
        regime = "THIN"
    else:
        regime = "FRAGILE"

    if friction >= 65 or p90_spread > 35:
        alert = "MICROSTRUCTURE ALERT — execution friction is elevated in part of the chain."
    elif score < 55:
        alert = "MICROSTRUCTURE ALERT — prefer liquid strikes and smaller order sizes in the current diagnostic regime."
    else:
        alert = "Microstructure conditions are within the current diagnostic band."

    ranked = contracts.sort_values(["Microstructure Score", "OI"], ascending=[False, False])
    risky = contracts.sort_values(["Execution Friction", "Spread (bps)"], ascending=[False, False])

    # Size ladder at ATM using the same local impact framework as V0.7.6, now adding
    # spread crossing, depth participation and a normalized execution-friction score.
    ladder_rows = []
    for _, row in atm.iterrows():
        for lots in (1, 5, 10, 20):
            qty = float(lots * max(multiplier, 1))
            spread_cost = row["Spread"] / 2.0 * qty
            depth = max(float(row["5-Level Depth"]), 1.0)
            participation = qty / depth
            impact_pt = max(0.0, participation - 0.10) * max(float(row["LTP"]), 0.01) * 0.08
            total_slip = spread_cost + impact_pt * qty
            ladder_rows.append({
                "Strike": row["Strike"], "Option": row["Option"], "Lots": lots,
                "Order Qty": qty, "Spread Cost ₹": spread_cost,
                "Impact / pt": impact_pt, "Est. Slippage ₹": total_slip,
                "5-Level Utilization": min(999.0, participation * 100.0),
                "Execution Friction": row["Execution Friction"],
            })
    ladder = pd.DataFrame(ladder_rows)

    # A normalized chain concentration measure: share of OI in the five most active contracts.
    oi_total = float(contracts["OI"].sum())
    top5_oi = float(contracts.nlargest(5, "OI")["OI"].sum())
    concentration = top5_oi / max(oi_total, 1.0) * 100.0

    summary = {
        "contracts": int(len(contracts)),
        "score": round(score, 2), "friction": round(friction, 2),
        "median_spread_bps": round(median_spread, 2),
        "p90_spread_bps": round(p90_spread, 2),
        "median_depth": round(median_depth, 0),
        "atm_strike": atm_strike, "atm_pressure": round(atm_pressure, 2),
        "top5_oi_concentration": round(concentration, 2),
    }
    return {
        "score": round(score, 2), "regime": regime, "contracts": contracts,
        "top_contracts": ranked.head(7), "risk_contracts": risky.head(7),
        "alert": alert, "summary": summary, "atm": atm, "ladder": ladder,
    }
