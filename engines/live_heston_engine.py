
"""IFIT V0.6.4 - Live Heston model intelligence."""

from __future__ import annotations
from typing import Dict, Tuple
import math
import pandas as pd

from engines.heston_calibration_engine import (
    calibrate_heston,
    calibrated_iv_surface,
)
from engines.dislocation_engine import build_dislocation_rank, dislocation_summary


def prepare_iv_surface(chain, days: int) -> Tuple[list, list, pd.DataFrame]:
    """Build a single-expiry market IV surface from legacy or live option-chain schema."""
    rows = []
    if chain is None:
        return [], [], pd.DataFrame()

    strike_col = "Strike" if "Strike" in chain.columns else "strike"
    ce_iv_col = "CE IV" if "CE IV" in chain.columns else "CE_IV"
    pe_iv_col = "PE IV" if "PE IV" in chain.columns else "PE_IV"

    if not all(col in chain.columns for col in (strike_col, ce_iv_col, pe_iv_col)):
        return [], [], pd.DataFrame()

    for _, r in chain.iterrows():
        try:
            strike = float(r[strike_col])
            ce = float(r[ce_iv_col])
            pe = float(r[pe_iv_col])
        except (KeyError, TypeError, ValueError):
            continue
        if strike <= 0:
            continue
        if ce > 0 and pe > 0:
            market_iv = (ce + pe) / 2.0
        elif ce > 0:
            market_iv = ce
        elif pe > 0:
            market_iv = pe
        else:
            continue
        rows.append({"Strike": strike, "Market IV": market_iv, "CE IV": ce, "PE IV": pe})

    if not rows:
        return [], [], pd.DataFrame()

    df = pd.DataFrame(rows).drop_duplicates("Strike").sort_values("Strike")
    strikes = [float(x) for x in df["Strike"].tolist()]
    surface = pd.DataFrame({f"{int(days)}D": df["Market IV"].to_numpy()}, index=strikes)
    surface.index.name = "Strike"
    return strikes, [int(days)], surface

def calibrate_live_heston(
    spot: float,
    chain,
    days: int,
    r_percent: float = 6.0,
    max_nfev: int = 12,
):
    """Calibrate Heston to the active live/simulated IV smile."""
    strikes, expiries, surface = prepare_iv_surface(chain, days)
    if len(strikes) < 5:
        raise ValueError("At least 5 valid strikes are required for calibration.")

    # Use an ATM-centered subset when the chain is very wide.
    if len(strikes) > 15:
        ordered = sorted(strikes, key=lambda k: abs(k - float(spot)))
        selected = sorted(ordered[:15])
        strikes = selected
        surface = surface.loc[selected]

    params, fit, stats = calibrate_heston(
        float(spot),
        strikes,
        expiries,
        surface,
        r_percent=float(r_percent),
        q_percent=0.0,
        option="CE",
        max_nfev=int(max_nfev),
    )

    h_surface = calibrated_iv_surface(
        float(spot),
        strikes,
        expiries,
        params,
        r_percent=float(r_percent),
        q_percent=0.0,
        option="CE",
    )

    ranked = build_dislocation_rank(
        fit,
        float(spot),
        stats,
        r_percent=float(r_percent),
        q_percent=0.0,
        top_n=15,
    )

    summary = dislocation_summary(ranked)
    return params, fit, stats, h_surface, ranked, summary
