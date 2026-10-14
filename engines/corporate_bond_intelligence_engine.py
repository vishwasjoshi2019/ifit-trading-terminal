"""
IFIT Corporate Bond Intelligence Engine V0.1
Simulation-first Indian corporate fixed-income intelligence.
"""

from __future__ import annotations
import pandas as pd


_CORPORATES = [
    ("AAA PSU 2029", "AAA", "PSU", 2029, 3.0, 7.18, 7.24, 2.55, 96.0),
    ("AAA PSU 2031", "AAA", "PSU", 2031, 5.0, 7.28, 7.35, 4.05, 94.0),
    ("AAA BANK 2030", "AAA", "BANK", 2030, 4.0, 7.22, 7.30, 3.25, 95.0),
    ("AAA NBFI 2032", "AAA", "NBFI", 2032, 6.0, 7.38, 7.48, 4.75, 88.0),
    ("AA+ CORP 2029", "AA+", "CORPORATE", 2029, 3.0, 7.55, 7.70, 2.65, 86.0),
    ("AA CORP 2031", "AA", "CORPORATE", 2031, 5.0, 7.72, 7.90, 4.20, 82.0),
    ("AA CORP 2033", "AA", "CORPORATE", 2033, 7.0, 7.86, 8.08, 5.65, 76.0),
    ("A+ CORP 2030", "A+", "CORPORATE", 2030, 4.0, 8.18, 8.62, 3.40, 67.0),
    ("A+ NBFC 2032", "A+", "NBFI", 2032, 6.0, 8.35, 8.85, 4.95, 62.0),
    ("AA- CORP 2034", "AA-", "CORPORATE", 2034, 8.0, 7.95, 8.28, 6.35, 73.0),
]


def build_corporate_bond_intelligence() -> pd.DataFrame:
    rows = []
    for bond, rating, issuer_type, maturity, years, coupon, ytm, duration, liquidity in _CORPORATES:
        spread = round((ytm - 7.14) * 100, 1)

        rating_base = {
            "AAA": 95, "AA+": 90, "AA": 84, "AA-": 79, "A+": 70
        }[rating]
        yield_score = max(0.0, min(100.0, 65.0 + (ytm - 7.20) * 75.0))
        credit_score = rating_base
        duration_score = max(0.0, min(100.0, 94.0 - duration * 4.5))
        liquidity_score = liquidity
        spread_score = max(0.0, min(100.0, 62.0 + spread * 0.55))
        relative_value_score = max(
            0.0,
            min(100.0, 68.0 + (ytm - 7.45) * 80.0 + (liquidity - 80.0) * 0.12),
        )

        score = round(
            yield_score * 0.22
            + credit_score * 0.24
            + duration_score * 0.12
            + liquidity_score * 0.18
            + spread_score * 0.10
            + relative_value_score * 0.14,
            2,
        )

        if score >= 78:
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
            f"{bond} ({rating}) offers {ytm:.2f}% YTM and {spread:.0f} bp "
            f"spread versus the illustrative sovereign reference, with "
            f"{duration:.2f}Y duration and liquidity score {liquidity:.0f}. "
            f"Credit quality and secondary-market liquidity should be monitored."
        )

        rows.append({
            "Bond": bond,
            "Rating": rating,
            "Issuer Type": issuer_type,
            "Maturity Year": maturity,
            "Maturity Years": years,
            "Coupon %": coupon,
            "YTM %": ytm,
            "Duration": duration,
            "Credit Spread bp": spread,
            "Liquidity Score": liquidity,
            "Yield Score": round(yield_score, 2),
            "Credit Score": round(credit_score, 2),
            "Duration Score": round(duration_score, 2),
            "Spread Score": round(spread_score, 2),
            "Relative Value Score": round(relative_value_score, 2),
            "Corporate Bond Intelligence Score": score,
            "Signal": signal,
            "Thesis": thesis,
        })
    return pd.DataFrame(rows)


def apply_corporate_bond_intelligence_filters(
    df: pd.DataFrame,
    ratings: list[str] | None = None,
    issuer_types: list[str] | None = None,
    signals: list[str] | None = None,
    min_ytm: float = 0.0,
    max_ytm: float = 20.0,
    min_spread: float = -100.0,
    max_spread: float = 2000.0,
    min_score: float = 0.0,
) -> pd.DataFrame:
    out = df.copy()
    if ratings:
        out = out[out["Rating"].isin(ratings)]
    if issuer_types:
        out = out[out["Issuer Type"].isin(issuer_types)]
    if signals:
        out = out[out["Signal"].isin(signals)]
    out = out[
        out["YTM %"].between(float(min_ytm), float(max_ytm))
        & out["Credit Spread bp"].between(float(min_spread), float(max_spread))
        & (out["Corporate Bond Intelligence Score"] >= float(min_score))
    ]
    return out.reset_index(drop=True)


def rank_corporate_bond_intelligence(
    df: pd.DataFrame, ascending: bool = False
) -> pd.DataFrame:
    return df.sort_values(
        ["Corporate Bond Intelligence Score", "YTM %"],
        ascending=[ascending, ascending],
    ).reset_index(drop=True)


def corporate_bond_intelligence_summary(df: pd.DataFrame | None = None) -> dict:
    if df is None:
        df = build_corporate_bond_intelligence()
    if df.empty:
        return {
            "Corporate Bonds": 0, "Ratings": 0, "Average YTM": 0.0,
            "Average Spread": 0.0, "Average Duration": 0.0,
            "Average Intelligence Score": 0.0, "Buy": 0, "Sell": 0,
            "Signal": "NEUTRAL",
        }
    buy = int(df["Signal"].isin(["BUY", "STRONG BUY"]).sum())
    sell = int(df["Signal"].isin(["SELL", "STRONG SELL"]).sum())
    return {
        "Corporate Bonds": int(len(df)),
        "Ratings": int(df["Rating"].nunique()),
        "Average YTM": round(float(df["YTM %"].mean()), 3),
        "Average Spread": round(float(df["Credit Spread bp"].mean()), 1),
        "Average Duration": round(float(df["Duration"].mean()), 2),
        "Average Intelligence Score": round(
            float(df["Corporate Bond Intelligence Score"].mean()), 2
        ),
        "Buy": buy,
        "Sell": sell,
        "Signal": "BUY" if buy > sell else "SELL" if sell > buy else "NEUTRAL",
    }


def available_corporate_bond_ratings() -> list[str]:
    return ["AAA", "AA+", "AA", "AA-", "A+"]


def available_corporate_issuer_types() -> list[str]:
    return ["PSU", "BANK", "NBFI", "CORPORATE"]


def available_corporate_bond_signals() -> list[str]:
    return ["STRONG BUY", "BUY", "NEUTRAL", "SELL", "STRONG SELL"]


def build_corporate_bond_intelligence_snapshot() -> dict:
    df = build_corporate_bond_intelligence()
    return {"data": df, "summary": corporate_bond_intelligence_summary(df)}


__all__ = [
    "build_corporate_bond_intelligence",
    "apply_corporate_bond_intelligence_filters",
    "rank_corporate_bond_intelligence",
    "corporate_bond_intelligence_summary",
    "available_corporate_bond_ratings",
    "available_corporate_issuer_types",
    "available_corporate_bond_signals",
    "build_corporate_bond_intelligence_snapshot",
]
