"""
IFIT Bond Screener V0.1
Unified simulation-first screener across G-Secs, SDLs, Corporate Bonds and T-Bills.
"""

from __future__ import annotations

import pandas as pd

from engines.bond_intelligence_engine import build_bond_intelligence
from engines.gsec_intelligence_engine import build_gsec_intelligence
from engines.sdl_intelligence_engine import build_sdl_intelligence
from engines.corporate_bond_intelligence_engine import build_corporate_bond_intelligence
from engines.tbill_intelligence_engine import build_tbill_intelligence


def build_bond_screener() -> pd.DataFrame:
    frames = []

    bond = build_bond_intelligence().copy()
    bond["Screener Asset Type"] = bond["Asset Type"]
    bond["Screener Score"] = bond["Bond Intelligence Score"]
    frames.append(_normalize(bond, "Bond"))

    gsec = build_gsec_intelligence().copy()
    gsec["Screener Asset Type"] = "G-SEC"
    gsec["Screener Score"] = gsec["G-Sec Intelligence Score"]
    frames.append(_normalize(gsec, "Bond"))

    sdl = build_sdl_intelligence().copy()
    sdl["Screener Asset Type"] = "SDL"
    sdl["Screener Score"] = sdl["SDL Intelligence Score"]
    frames.append(_normalize(sdl, "Bond"))

    corp = build_corporate_bond_intelligence().copy()
    corp["Screener Asset Type"] = "CORPORATE"
    corp["Screener Score"] = corp["Corporate Bond Intelligence Score"]
    frames.append(_normalize(corp, "Bond"))

    tb = build_tbill_intelligence().copy()
    tb["Screener Asset Type"] = "T-BILL"
    tb["Screener Score"] = tb["T-Bill Intelligence Score"]
    frames.append(_normalize(tb, "T-Bill"))

    clean_frames = [f.dropna(how="all", axis=1) for f in frames if not f.empty]
    out = pd.concat(clean_frames, ignore_index=True, sort=False)

    for col in [
        "Instrument", "Asset Type", "Rating", "Issuer / State",
        "Maturity Year", "Maturity Years", "YTM %",
        "Duration", "Spread bp", "Liquidity Score", "Intelligence Score",
        "Signal", "Thesis",
    ]:
        if col not in out.columns:
            out[col] = pd.NA

    return out[
        [
            "Instrument", "Asset Type", "Rating", "Issuer / State",
            "Maturity Year", "Maturity Years", "YTM %",
            "Duration", "Spread bp", "Liquidity Score",
            "Intelligence Score", "Signal", "Thesis",
        ]
    ].reset_index(drop=True)


def _normalize(df: pd.DataFrame, name_col: str) -> pd.DataFrame:
    out = df.copy()

    out["Instrument"] = out[name_col]

    if "Screener Asset Type" in out:
        out["Asset Type"] = out["Screener Asset Type"]

    if "State" in out:
        out["Issuer / State"] = out["State"]
    elif "Issuer Type" in out:
        out["Issuer / State"] = out["Issuer Type"]
    else:
        out["Issuer / State"] = pd.NA

    if "Credit Spread bp" in out:
        out["Spread bp"] = out["Credit Spread bp"]
    elif "Spread to G-Sec bp" in out:
        out["Spread bp"] = out["Spread to G-Sec bp"]
    else:
        out["Spread bp"] = pd.NA

    if "G-Sec Intelligence Score" in out:
        out["Intelligence Score"] = out["G-Sec Intelligence Score"]
    elif "SDL Intelligence Score" in out:
        out["Intelligence Score"] = out["SDL Intelligence Score"]
    elif "Corporate Bond Intelligence Score" in out:
        out["Intelligence Score"] = out["Corporate Bond Intelligence Score"]
    elif "T-Bill Intelligence Score" in out:
        out["Intelligence Score"] = out["T-Bill Intelligence Score"]
    elif "Bond Intelligence Score" in out:
        out["Intelligence Score"] = out["Bond Intelligence Score"]
    else:
        out["Intelligence Score"] = out["Screener Score"]

    if "Thesis" not in out:
        out["Thesis"] = ""

    if "Rating" not in out:
        out["Rating"] = pd.NA

    return out


def apply_bond_screener_filters(
    df: pd.DataFrame,
    asset_types: list[str] | None = None,
    ratings: list[str] | None = None,
    signals: list[str] | None = None,
    min_maturity: float = 0.0,
    max_maturity: float = 100.0,
    min_ytm: float = 0.0,
    max_ytm: float = 20.0,
    min_duration: float = 0.0,
    max_duration: float = 100.0,
    min_spread: float = -1000.0,
    max_spread: float = 5000.0,
    min_score: float = 0.0,
) -> pd.DataFrame:
    out = df.copy()

    if asset_types:
        out = out[out["Asset Type"].isin(asset_types)]
    if ratings:
        out = out[out["Rating"].isin(ratings)]
    if signals:
        out = out[out["Signal"].isin(signals)]

    out = out[
        out["Maturity Years"].fillna(-1).between(float(min_maturity), float(max_maturity))
        & out["YTM %"].fillna(-1).between(float(min_ytm), float(max_ytm))
        & out["Duration"].fillna(-1).between(float(min_duration), float(max_duration))
        & out["Spread bp"].fillna(0).between(float(min_spread), float(max_spread))
        & (out["Intelligence Score"].fillna(0) >= float(min_score))
    ]

    return out.reset_index(drop=True)


def rank_bond_screener(
    df: pd.DataFrame, ascending: bool = False
) -> pd.DataFrame:
    return df.sort_values(
        ["Intelligence Score", "YTM %"],
        ascending=[ascending, ascending],
        na_position="last",
    ).reset_index(drop=True)


def bond_screener_summary(df: pd.DataFrame | None = None) -> dict:
    if df is None:
        df = build_bond_screener()

    if df.empty:
        return {
            "Instruments": 0,
            "Asset Types": 0,
            "Average YTM": 0.0,
            "Average Duration": 0.0,
            "Average Score": 0.0,
            "Buy": 0,
            "Sell": 0,
        }

    buy = int(df["Signal"].isin(["BUY", "STRONG BUY"]).sum())
    sell = int(df["Signal"].isin(["SELL", "STRONG SELL"]).sum())

    return {
        "Instruments": int(len(df)),
        "Asset Types": int(df["Asset Type"].nunique()),
        "Average YTM": round(float(df["YTM %"].dropna().mean()), 3),
        "Average Duration": round(float(df["Duration"].dropna().mean()), 2),
        "Average Score": round(float(df["Intelligence Score"].mean()), 2),
        "Buy": buy,
        "Sell": sell,
    }


def available_bond_screener_asset_types() -> list[str]:
    return ["G-SEC", "SDL", "CORPORATE", "T-BILL"]


def available_bond_screener_signals() -> list[str]:
    return ["STRONG BUY", "BUY", "NEUTRAL", "SELL", "STRONG SELL"]


def available_bond_screener_ratings() -> list[str]:
    return ["SOVEREIGN", "STATE", "AAA", "AA+", "AA", "AA-", "A+"]


__all__ = [
    "build_bond_screener",
    "apply_bond_screener_filters",
    "rank_bond_screener",
    "bond_screener_summary",
    "available_bond_screener_asset_types",
    "available_bond_screener_signals",
    "available_bond_screener_ratings",
]
