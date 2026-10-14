"""
IFIT Yield Curve Intelligence Engine V0.1
Simulation-first fixed-income term-structure engine.
"""

from __future__ import annotations

from typing import Iterable, Optional
import numpy as np
import pandas as pd


_YIELD_CURVE = [
    ("3M", 0.25, 6.72),
    ("6M", 0.50, 6.78),
    ("1Y", 1.00, 6.84),
    ("2Y", 2.00, 6.91),
    ("3Y", 3.00, 7.00),
    ("5Y", 5.00, 7.10),
    ("7Y", 7.00, 7.18),
    ("10Y", 10.00, 7.22),
    ("15Y", 15.00, 7.28),
    ("20Y", 20.00, 7.34),
    ("30Y", 30.00, 7.41),
]


def build_yield_curve() -> pd.DataFrame:
    """Return the deterministic illustrative Indian sovereign yield curve."""
    rows = []
    for i, (tenor, years, ytm) in enumerate(_YIELD_CURVE):
        prev_ytm = _YIELD_CURVE[i - 1][2] if i else ytm - 0.03
        change_bp = round((ytm - prev_ytm) * 100, 1)

        if years <= 1:
            duration = max(0.20, years * 0.92)
        else:
            duration = years * (0.84 + 0.01 * min(years, 10) / 10)

        slope_bp = round((ytm - _YIELD_CURVE[0][2]) * 100, 1)
        curvature = round((ytm - 7.10) * 100, 1)

        rows.append({
            "Tenor": tenor,
            "Maturity Years": years,
            "YTM %": round(ytm, 3),
            "Yield Change bp": change_bp,
            "Duration": round(duration, 2),
            "Slope from 3M bp": slope_bp,
            "Curve Curvature bp": curvature,
        })

    df = pd.DataFrame(rows)
    return _add_curve_metrics(df)


def _add_curve_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    y = out["YTM %"].to_numpy(dtype=float)
    x = out["Maturity Years"].to_numpy(dtype=float)

    # Local slopes between adjacent maturity points, expressed in bp/year.
    slopes = np.gradient(y, x) * 100
    out["Local Slope bp/Yr"] = np.round(slopes, 2)

    # Illustrative normalized curve score: higher for orderly positive slope.
    total_slope = (y[-1] - y[0]) * 100
    score = np.clip(50.0 + total_slope * 1.8, 0, 100)
    out["Curve Score"] = round(float(score), 2)

    return out


def _curve_shape(df: pd.DataFrame) -> str:
    y = df["YTM %"].to_numpy(dtype=float)
    if np.all(np.diff(y) >= -0.01):
        if y[-1] - y[0] > 0.30:
            return "STEEPENING"
        return "NORMAL"
    if y[-1] - y[0] < -0.30:
        return "INVERTED"
    return "HUMPED"


def _curve_regime(df: pd.DataFrame) -> str:
    shape = _curve_shape(df)
    short = float(df.iloc[2]["YTM %"])
    long = float(df.iloc[-1]["YTM %"])
    spread = (long - short) * 100

    if shape == "INVERTED":
        return "INVERSION"
    if spread >= 50:
        return "POSITIVE TERM PREMIUM"
    if spread <= 15:
        return "FLAT"
    return "NORMALIZATION"


def yield_curve_summary(df: Optional[pd.DataFrame] = None) -> dict:
    """Return structural yield-curve summary metrics."""
    if df is None:
        df = build_yield_curve()

    def y(tenor: str) -> float:
        return float(df.loc[df["Tenor"].eq(tenor), "YTM %"].iloc[0])

    spread_2_10 = round((y("10Y") - y("2Y")) * 100, 1)
    spread_3m_10 = round((y("10Y") - y("3M")) * 100, 1)
    spread_5_10 = round((y("10Y") - y("5Y")) * 100, 1)

    shape = _curve_shape(df)
    regime = _curve_regime(df)

    score = float(df["Curve Score"].iloc[0])
    if shape == "INVERTED":
        signal = "CAUTION"
    elif regime == "FLAT":
        signal = "WATCH"
    else:
        signal = "CONSTRUCTIVE"

    return {
        "Tenors": int(len(df)),
        "Average YTM": round(float(df["YTM %"].mean()), 3),
        "2Y-10Y Spread bp": spread_2_10,
        "3M-10Y Spread bp": spread_3m_10,
        "5Y-10Y Spread bp": spread_5_10,
        "Curve Shape": shape,
        "Curve Regime": regime,
        "Curve Score": round(score, 2),
        "Signal": signal,
    }


def apply_yield_curve_filters(
    df: pd.DataFrame,
    min_maturity: float = 0.0,
    max_maturity: float = 100.0,
) -> pd.DataFrame:
    """Filter the curve by maturity range."""
    out = df.copy()
    return out[
        out["Maturity Years"].between(float(min_maturity), float(max_maturity))
    ].reset_index(drop=True)


def rank_yield_curve(df: pd.DataFrame) -> pd.DataFrame:
    """Rank curve points by YTM, highest first."""
    return df.sort_values(
        ["YTM %", "Maturity Years"], ascending=[False, True]
    ).reset_index(drop=True)


def available_yield_curve_tenors() -> list[str]:
    return [x[0] for x in _YIELD_CURVE]


def build_yield_curve_snapshot() -> dict:
    df = build_yield_curve()
    return {
        "data": df,
        "summary": yield_curve_summary(df),
    }


__all__ = [
    "build_yield_curve",
    "apply_yield_curve_filters",
    "rank_yield_curve",
    "yield_curve_summary",
    "available_yield_curve_tenors",
    "build_yield_curve_snapshot",
]
