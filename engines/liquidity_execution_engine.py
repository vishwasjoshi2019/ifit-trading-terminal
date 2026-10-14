"""IFIT V0.7.6 — Liquidity & Execution Engine.

Normalized liquidity diagnostics for the active option chain. When a provider
supplies bid/ask and depth fields they are used directly; otherwise the
simulation builds deterministic execution proxies from LTP/OI. Outputs are
research diagnostics, not executable orders or guaranteed fill estimates.
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
    ltp = _num(row, [f"{side} LTP", f"{side}_LTP"], 0.0)
    bid = _num(row, [f"{side} Bid", f"{side} BID", f"{side}_bid", f"{side} bid"], np.nan)
    ask = _num(row, [f"{side} Ask", f"{side} ASK", f"{side}_ask", f"{side} ask"], np.nan)
    if not math.isfinite(bid) or not math.isfinite(ask) or bid <= 0 or ask <= 0 or ask < bid:
        # Simulation fallback: tighter spreads for larger OI / ATM contracts.
        oi = max(_num(row, [f"{side} OI", f"{side}_OI"], 0.0), 0.0)
        oi_factor = min(1.0, math.log10(max(oi, 10.0)) / 6.0)
        base_bps = 34.0 - 16.0 * oi_factor
        spread = max(0.05, ltp * base_bps / 10000.0)
        bid = max(0.01, ltp - spread / 2.0)
        ask = ltp + spread / 2.0
        source = "SIMULATED QUOTE"
    else:
        source = "PROVIDER QUOTE"
    return float(bid), float(ask), source


def _depth(row, side, bid, ask):
    """Return deterministic five-level depth quantities.

    Provider depth columns are accepted when available. Otherwise OI is used
    only as a simulation liquidity proxy; it is not presented as real depth.
    """
    direct = []
    for level in range(1, 6):
        v = _num(row, [f"{side} BidQty{level}", f"{side} Bid Qty {level}", f"{side} AskQty{level}", f"{side} Ask Qty {level}"], np.nan)
        direct.append(v)
    if all(math.isfinite(x) and x >= 0 for x in direct):
        return np.array(direct, dtype=float), "PROVIDER DEPTH"
    oi = max(_num(row, [f"{side} OI", f"{side}_OI"], 0.0), 0.0)
    # Conservative proxy: only a fraction of OI is treated as executable depth.
    top = max(1.0, oi * 0.008)
    return np.array([top / (1.0 + 0.20 * i) for i in range(5)], dtype=float), "OI PROXY"


def _contract_rows(chain_df):
    rows = []
    if not isinstance(chain_df, pd.DataFrame) or chain_df.empty:
        return pd.DataFrame()
    for _, r in chain_df.iterrows():
        strike = _num(r, ["Strike"], np.nan)
        if not math.isfinite(strike):
            continue
        for side in ("CE", "PE"):
            ltp = _num(r, [f"{side} LTP"], np.nan)
            oi = _num(r, [f"{side} OI"], 0.0)
            if not math.isfinite(ltp) or ltp <= 0:
                continue
            bid, ask, quote_source = _quote(r, side)
            spread = max(0.0, ask - bid)
            mid = (ask + bid) / 2.0
            spread_bps = spread / max(mid, 0.01) * 10000.0
            depth, depth_source = _depth(r, side, bid, ask)
            top_depth = float(depth[0])
            total_depth = float(depth.sum())
            oi_score = _clip(math.log10(max(oi, 10.0)) / 6.0 * 100.0)
            spread_score = _clip(100.0 - (spread_bps - 5.0) * 4.0)
            depth_score = _clip(math.log10(max(total_depth, 1.0)) / 5.0 * 100.0)
            quote_score = 100.0 if quote_source == "PROVIDER QUOTE" else 72.0
            liquidity_score = _clip(0.40 * spread_score + 0.30 * depth_score + 0.20 * oi_score + 0.10 * quote_score)

            rows.append({
                "Strike": strike, "Option": side, "LTP": ltp, "OI": oi,
                "Bid": bid, "Ask": ask, "Spread": spread, "Spread (bps)": spread_bps,
                "Top Depth": top_depth, "5-Level Depth": total_depth,
                "Liquidity Score": liquidity_score,
                "Quote Source": quote_source, "Depth Source": depth_source,
            })
    return pd.DataFrame(rows)


def _slippage(row, lots, multiplier=50):
    qty = max(float(lots), 1.0) * max(float(multiplier), 1.0)
    top = max(float(row["Top Depth"]), 1.0)
    depth = max(float(row["5-Level Depth"]), 1.0)
    spread = float(row["Spread"])
    participation = qty / depth
    # Crossing half-spread plus depth impact proxy, capped for readability.
    slippage_points = spread / 2.0 + max(0.0, participation - 0.10) * max(float(row["LTP"]), 0.01) * 0.08
    slippage_points = min(slippage_points, float(row["LTP"]) * 0.25)
    return {
        "Lots": int(lots),
        "Order Qty": qty,
        "Est. Slippage / pt": slippage_points,
        "Est. Slippage ₹": slippage_points * qty,
        "Top-Depth Utilization": min(999.0, qty / top * 100.0),
        "5-Level Utilization": min(999.0, participation * 100.0),
    }


def build_liquidity_execution(*, chain_df, spot, multiplier=50):
    """Build chain-wide liquidity and execution diagnostics."""
    contracts = _contract_rows(chain_df)
    if contracts.empty:
        return {
            "score": 0.0, "regime": "NO DATA", "contracts": contracts,
            "top_liquid": contracts, "execution_risk": 100.0,
            "alert": "No option-chain records available for liquidity analysis.",
            "summary": {}, "scenarios": pd.DataFrame(),
        }

    score = float(contracts["Liquidity Score"].mean())
    median_spread = float(contracts["Spread (bps)"].median())
    p90_spread = float(contracts["Spread (bps)"].quantile(0.90))
    median_depth = float(contracts["5-Level Depth"].median())
    execution_risk = _clip(100.0 - score)

    if score >= 80:
        regime = "DEEP / EFFICIENT"
    elif score >= 65:
        regime = "HEALTHY"
    elif score >= 45:
        regime = "SELECTIVE"
    elif score >= 25:
        regime = "THIN"
    else:
        regime = "FRAGILE"

    # ATM-focused execution ladder.
    atm_strike = round(float(spot) / 100.0) * 100.0
    atm = contracts.iloc[(contracts["Strike"] - atm_strike).abs().argsort()[:2]].copy()
    ladder_rows = []
    for _, row in atm.iterrows():
        for lots in (1, 5, 10):
            x = _slippage(row, lots, multiplier)
            ladder_rows.append({"Strike": row["Strike"], "Option": row["Option"], **x})
    ladder = pd.DataFrame(ladder_rows)

    display = contracts.sort_values(["Liquidity Score", "OI"], ascending=[False, False]).copy()
    top_liquid = display.head(5)
    risk_contracts = contracts.sort_values(["Liquidity Score", "Spread (bps)"], ascending=[True, False]).head(5)

    if p90_spread > 35:
        alert = "EXECUTION ALERT — wide spreads are present in the lower-liquidity tail of the chain."
    elif score < 55:
        alert = "LIQUIDITY ALERT — use selective strikes and smaller order sizes in the current diagnostic regime."
    else:
        alert = "Liquidity conditions are within the current diagnostic band."

    summary = {
        "contracts": int(len(contracts)),
        "score": round(score, 2),
        "execution_risk": round(execution_risk, 2),
        "median_spread_bps": round(median_spread, 2),
        "p90_spread_bps": round(p90_spread, 2),
        "median_5level_depth": round(median_depth, 0),
        "atm_strike": atm_strike,
    }
    return {
        "score": round(score, 2), "regime": regime, "contracts": contracts,
        "top_liquid": top_liquid, "risk_contracts": risk_contracts,
        "execution_risk": round(execution_risk, 2), "alert": alert,
        "summary": summary, "atm_ladder": ladder,
    }
