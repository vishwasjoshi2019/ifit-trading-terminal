"""
IFIT T-Bill Intelligence Engine V0.1
Simulation-first Indian Treasury Bill intelligence.
"""

from __future__ import annotations

import pandas as pd


_TBILLS = [
    ("T-BILL 91D", 91, 0.25, 6.58, 6.62, 0.24, 98.0),
    ("T-BILL 182D", 182, 0.50, 6.65, 6.70, 0.47, 97.0),
    ("T-BILL 364D", 364, 1.00, 6.72, 6.78, 0.91, 96.0),
    ("T-BILL 91D", 91, 0.25, 6.58, 6.61, 0.24, 97.0),
    ("T-BILL 182D", 182, 0.50, 6.65, 6.69, 0.47, 96.0),
    ("T-BILL 364D", 364, 1.00, 6.72, 6.77, 0.91, 95.0),
]


def build_tbill_intelligence() -> pd.DataFrame:
    rows = []
    for i, (bill, days, years, coupon, ytm, duration, liquidity) in enumerate(_TBILLS):
        discount = round(100.0 - (ytm * years), 3)
        yield_score = max(0.0, min(100.0, 70.0 + (ytm - 6.60) * 120.0))
        maturity_score = max(0.0, min(100.0, 100.0 - years * 12.0))
        liquidity_score = liquidity
        relative_value_score = max(
            0.0, min(100.0, 72.0 + (ytm - 6.60) * 100.0 + (liquidity - 95.0) * 0.3)
        )
        safety_score = 99.0

        score = round(
            yield_score * 0.30
            + maturity_score * 0.15
            + liquidity_score * 0.20
            + relative_value_score * 0.20
            + safety_score * 0.15,
            2,
        )

        if score >= 80:
            signal = "STRONG BUY"
        elif score >= 68:
            signal = "BUY"
        elif score >= 54:
            signal = "NEUTRAL"
        elif score >= 44:
            signal = "SELL"
        else:
            signal = "STRONG SELL"

        thesis = (
            f"{bill} provides short-duration sovereign exposure with {ytm:.2f}% "
            f"illustrative YTM, {days}-day maturity and liquidity score "
            f"{liquidity:.0f}. Reinvestment and short-rate risk should be monitored."
        )

        rows.append({
            "T-Bill": bill,
            "Tenor Days": days,
            "Maturity Years": years,
            "Coupon Equivalent %": coupon,
            "YTM %": ytm,
            "Duration": duration,
            "Implied Discount Price": discount,
            "Liquidity Score": liquidity,
            "Yield Score": round(yield_score, 2),
            "Maturity Score": round(maturity_score, 2),
            "Relative Value Score": round(relative_value_score, 2),
            "Safety Score": safety_score,
            "T-Bill Intelligence Score": score,
            "Signal": signal,
            "Thesis": thesis,
        })

    return pd.DataFrame(rows)


def apply_tbill_intelligence_filters(
    df: pd.DataFrame,
    tenors: list[int] | None = None,
    signals: list[str] | None = None,
    min_ytm: float = 0.0,
    max_ytm: float = 15.0,
    min_score: float = 0.0,
) -> pd.DataFrame:
    out = df.copy()
    if tenors:
        out = out[out["Tenor Days"].isin(tenors)]
    if signals:
        out = out[out["Signal"].isin(signals)]
    out = out[
        out["YTM %"].between(float(min_ytm), float(max_ytm))
        & (out["T-Bill Intelligence Score"] >= float(min_score))
    ]
    return out.reset_index(drop=True)


def rank_tbill_intelligence(
    df: pd.DataFrame, ascending: bool = False
) -> pd.DataFrame:
    return df.sort_values(
        ["T-Bill Intelligence Score", "YTM %"],
        ascending=[ascending, ascending],
    ).reset_index(drop=True)


def tbill_intelligence_summary(df: pd.DataFrame | None = None) -> dict:
    if df is None:
        df = build_tbill_intelligence()
    if df.empty:
        return {
            "T-Bills": 0, "Average YTM": 0.0, "Average Duration": 0.0,
            "Average Liquidity": 0.0, "Average Intelligence Score": 0.0,
            "Buy": 0, "Sell": 0, "Signal": "NEUTRAL",
        }
    buy = int(df["Signal"].isin(["BUY", "STRONG BUY"]).sum())
    sell = int(df["Signal"].isin(["SELL", "STRONG SELL"]).sum())
    return {
        "T-Bills": int(len(df)),
        "Average YTM": round(float(df["YTM %"].mean()), 3),
        "Average Duration": round(float(df["Duration"].mean()), 2),
        "Average Liquidity": round(float(df["Liquidity Score"].mean()), 2),
        "Average Intelligence Score": round(
            float(df["T-Bill Intelligence Score"].mean()), 2
        ),
        "Buy": buy,
        "Sell": sell,
        "Signal": "BUY" if buy > sell else "SELL" if sell > buy else "NEUTRAL",
    }


def available_tbill_tenors() -> list[int]:
    return [91, 182, 364]


def available_tbill_signals() -> list[str]:
    return ["STRONG BUY", "BUY", "NEUTRAL", "SELL", "STRONG SELL"]


def build_tbill_intelligence_snapshot() -> dict:
    df = build_tbill_intelligence()
    return {"data": df, "summary": tbill_intelligence_summary(df)}


__all__ = [
    "build_tbill_intelligence",
    "apply_tbill_intelligence_filters",
    "rank_tbill_intelligence",
    "tbill_intelligence_summary",
    "available_tbill_tenors",
    "available_tbill_signals",
    "build_tbill_intelligence_snapshot",
]
