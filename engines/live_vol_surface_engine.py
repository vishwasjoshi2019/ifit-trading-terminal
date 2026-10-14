
"""IFIT V0.6.3 - Live volatility surface intelligence."""

from __future__ import annotations
from typing import Any, Dict, List
import math


def _f(x, default=0.0):
    try:
        return float(x) if x not in (None, "") else default
    except (TypeError, ValueError):
        return default


def _iv_pct(x):
    x = _f(x)
    return x * 100.0 if 0 < x <= 3.0 else x


def build_surface(chain, spot):
    """Normalize a V0.6.x option-chain DataFrame/list into surface rows."""
    rows = []
    if chain is None:
        return rows

    # DataFrame path used by the current IFIT Options Intelligence module.
    if hasattr(chain, "iterrows"):
        for _, r in chain.iterrows():
            strike = _f(r.get("Strike", r.get("strikePrice")))
            expiry = r.get("Expiry", r.get("expiry", r.get("expiryDate")))
            if expiry in (None, ""):
                expiry = "Current"
            for side in ("CE", "PE"):
                iv = _iv_pct(r.get(f"{side} IV", 0))
                if strike > 0 and iv > 0:
                    rows.append({
                        "expiry": str(expiry),
                        "strike": strike,
                        "option": side,
                        "iv": iv,
                        "moneyness_pct": (strike / spot - 1.0) * 100.0 if spot else 0.0,
                    })
        return rows

    # Normalized list path.
    if isinstance(chain, list):
        for item in chain:
            strike = _f(item.get("strikePrice", item.get("strike")))
            expiry = item.get("expiryDate", item.get("expiry", "Current"))
            for side in ("CE", "PE"):
                leg = item.get(side) or item.get(side.lower())
                if not isinstance(leg, dict):
                    continue
                iv = _iv_pct(leg.get("impliedVolatility", leg.get("iv", leg.get("IV"))))
                if strike > 0 and iv > 0:
                    rows.append({
                        "expiry": str(expiry),
                        "strike": strike,
                        "option": side,
                        "iv": iv,
                        "moneyness_pct": (strike / spot - 1.0) * 100.0 if spot else 0.0,
                    })
    return rows


def surface_summary(rows, spot):
    if not rows:
        return {
            "atm_iv": 0.0, "call_skew": 0.0, "put_skew": 0.0,
            "smile": 0.0, "expiries": 0, "strikes": 0
        }

    strikes = sorted({r["strike"] for r in rows})
    atm = min(strikes, key=lambda x: abs(x - spot))
    atm_vals = [r["iv"] for r in rows if r["strike"] == atm]
    atm_iv = sum(atm_vals) / len(atm_vals) if atm_vals else 0.0

    # Use nearest available strikes around ATM for robust skew measures.
    below = [r for r in rows if r["strike"] < atm]
    above = [r for r in rows if r["strike"] > atm]
    put_near = min(below, key=lambda r: abs(r["strike"] - spot)) if below else None
    call_near = min(above, key=lambda r: abs(r["strike"] - spot)) if above else None

    put_iv = put_near["iv"] if put_near else atm_iv
    call_iv = call_near["iv"] if call_near else atm_iv

    return {
        "atm_iv": atm_iv,
        "put_skew": put_iv - atm_iv,
        "call_skew": call_iv - atm_iv,
        "smile": (put_iv + call_iv) / 2.0 - atm_iv,
        "expiries": len({r["expiry"] for r in rows}),
        "strikes": len(strikes),
    }


def term_structure(rows):
    out = []
    for expiry in sorted({r["expiry"] for r in rows}):
        vals = [r["iv"] for r in rows if r["expiry"] == expiry]
        if vals:
            out.append({"expiry": expiry, "mean_iv": sum(vals) / len(vals)})
    return out
