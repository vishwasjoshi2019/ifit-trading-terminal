"""
IFIT SDL Intelligence Engine V0.1
Simulation-first State Development Loan intelligence.
"""

from __future__ import annotations

import pandas as pd


_SDLS = [
    ("SDL MH 2034", "Maharashtra", 2034, 7.65, 7.72, 6.25, 91.0),
    ("SDL GJ 2035", "Gujarat", 2035, 7.62, 7.70, 6.55, 89.0),
    ("SDL KA 2036", "Karnataka", 2036, 7.70, 7.78, 7.10, 87.0),
    ("SDL TN 2034", "Tamil Nadu", 2034, 7.66, 7.75, 6.30, 88.0),
    ("SDL RJ 2035", "Rajasthan", 2035, 7.72, 7.84, 6.65, 82.0),
    ("SDL UP 2036", "Uttar Pradesh", 2036, 7.75, 7.88, 7.05, 80.0),
    ("SDL WB 2037", "West Bengal", 2037, 7.82, 8.02, 7.55, 73.0),
    ("SDL AP 2035", "Andhra Pradesh", 2035, 7.76, 7.91, 6.70, 79.0),
]


def build_sdl_intelligence() -> pd.DataFrame:
    rows = []

    for bond, state, maturity, coupon, ytm, duration, liquidity in _SDLS:
        spread_to_gsec = round((ytm - 7.14) * 100, 1)

        yield_score = max(0.0, min(100.0, 65.0 + (ytm - 7.60) * 90.0))
        liquidity_score = liquidity
        duration_score = max(0.0, min(100.0, 92.0 - duration * 4.0))
        spread_score = max(0.0, min(100.0, 72.0 + spread_to_gsec * 0.8))
        relative_value_score = max(
            0.0,
            min(100.0, 68.0 + (ytm - 7.65) * 100.0 + (liquidity - 80.0) * 0.15),
        )

        score = (
            yield_score * 0.28
            + liquidity_score * 0.20
            + duration_score * 0.15
            + spread_score * 0.15
            + relative_value_score * 0.22
        )
        score = round(score, 2)

        if score >= 76:
            signal = "STRONG BUY"
        elif score >= 66:
            signal = "BUY"
        elif score >= 53:
            signal = "NEUTRAL"
        elif score >= 43:
            signal = "SELL"
        else:
            signal = "STRONG SELL"

        thesis = (
            f"{bond} ({state}) offers {ytm:.2f}% YTM versus the "
            f"illustrative G-Sec reference, with {duration:.2f}Y duration "
            f"and {spread_to_gsec:.0f} bp spread. State credit and liquidity "
            f"characteristics should be monitored."
        )

        rows.append(
            {
                "Bond": bond,
                "State": state,
                "Maturity Year": maturity,
                "Coupon %": coupon,
                "YTM %": ytm,
                "Duration": duration,
                "Spread to G-Sec bp": spread_to_gsec,
                "Liquidity Score": liquidity_score,
                "Yield Score": round(yield_score, 2),
                "Duration Score": round(duration_score, 2),
                "Spread Score": round(spread_score, 2),
                "Relative Value Score": round(relative_value_score, 2),
                "SDL Intelligence Score": score,
                "Signal": signal,
                "Thesis": thesis,
            }
        )

    return pd.DataFrame(rows)


def apply_sdl_intelligence_filters(
    df: pd.DataFrame,
    states: list[str] | None = None,
    signals: list[str] | None = None,
    min_ytm: float = 0.0,
    max_ytm: float = 15.0,
    min_duration: float = 0.0,
    max_duration: float = 100.0,
    min_score: float = 0.0,
) -> pd.DataFrame:
    out = df.copy()

    if states:
        out = out[out["State"].isin(states)]
    if signals:
        out = out[out["Signal"].isin(signals)]

    out = out[
        out["YTM %"].between(float(min_ytm), float(max_ytm))
        & out["Duration"].between(float(min_duration), float(max_duration))
        & (out["SDL Intelligence Score"] >= float(min_score))
    ]

    return out.reset_index(drop=True)


def rank_sdl_intelligence(
    df: pd.DataFrame, ascending: bool = False
) -> pd.DataFrame:
    return df.sort_values(
        ["SDL Intelligence Score", "YTM %"],
        ascending=[ascending, ascending],
    ).reset_index(drop=True)


def sdl_intelligence_summary(df: pd.DataFrame | None = None) -> dict:
    if df is None:
        df = build_sdl_intelligence()

    if df.empty:
        return {
            "SDLs": 0,
            "States": 0,
            "Average YTM": 0.0,
            "Average Duration": 0.0,
            "Average Spread": 0.0,
            "Average Intelligence Score": 0.0,
            "Buy": 0,
            "Sell": 0,
            "Signal": "NEUTRAL",
        }

    buy = int(df["Signal"].isin(["BUY", "STRONG BUY"]).sum())
    sell = int(df["Signal"].isin(["SELL", "STRONG SELL"]).sum())

    return {
        "SDLs": int(len(df)),
        "States": int(df["State"].nunique()),
        "Average YTM": round(float(df["YTM %"].mean()), 3),
        "Average Duration": round(float(df["Duration"].mean()), 2),
        "Average Spread": round(float(df["Spread to G-Sec bp"].mean()), 1),
        "Average Intelligence Score": round(
            float(df["SDL Intelligence Score"].mean()), 2
        ),
        "Buy": buy,
        "Sell": sell,
        "Signal": "BUY" if buy > sell else "SELL" if sell > buy else "NEUTRAL",
    }


def available_sdl_states() -> list[str]:
    return [x[1] for x in _SDLS]


def available_sdl_signals() -> list[str]:
    return ["STRONG BUY", "BUY", "NEUTRAL", "SELL", "STRONG SELL"]


def build_sdl_intelligence_snapshot() -> dict:
    df = build_sdl_intelligence()
    return {"data": df, "summary": sdl_intelligence_summary(df)}


__all__ = [
    "build_sdl_intelligence",
    "apply_sdl_intelligence_filters",
    "rank_sdl_intelligence",
    "sdl_intelligence_summary",
    "available_sdl_states",
    "available_sdl_signals",
    "build_sdl_intelligence_snapshot",
]
