"""
IFIT V0.8.5 — Market Screener Engine

Simulation-backed market / sector / stock screening engine.

Design:
    Market → Sector → Stock

The normalized output is designed so the UI can later consume
authorized live market data without changing the screening contract.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class MarketScreenerConfig:
    seed: int = 8506
    market_name: str = "NIFTY 50"


# ---------------------------------------------------------------------
# MARKET / SECTOR / STOCK UNIVERSE
# ---------------------------------------------------------------------

SECTOR_STOCKS = {
    "Banking": [
        "HDFCBANK",
        "ICICIBANK",
        "SBIN",
        "AXISBANK",
        "KOTAKBANK",
        "INDUSINDBK",
    ],
    "Financial Services": [
        "BAJFINANCE",
        "BAJAJFINSV",
        "SBILIFE",
        "HDFCLIFE",
        "SHRIRAMFIN",
        "CHOLAFIN",
    ],
    "IT": [
        "TCS",
        "INFY",
        "HCLTECH",
        "WIPRO",
        "TECHM",
        "LTIM",
    ],
    "Energy": [
        "RELIANCE",
        "ONGC",
        "NTPC",
        "POWERGRID",
        "COALINDIA",
        "ADANIGREEN",
    ],
    "Auto": [
        "MARUTI",
        "M&M",
        "TATAMOTORS",
        "EICHERMOT",
        "HEROMOTOCO",
        "BAJAJ-AUTO",
    ],
    "Pharma": [
        "SUNPHARMA",
        "DRREDDY",
        "CIPLA",
        "DIVISLAB",
        "APOLLOHOSP",
        "AUROPHARMA",
    ],
    "FMCG": [
        "HINDUNILVR",
        "ITC",
        "NESTLEIND",
        "BRITANNIA",
        "TATACONSUM",
        "DABUR",
    ],
    "Metals": [
        "TATASTEEL",
        "JSWSTEEL",
        "HINDALCO",
        "VEDL",
        "JINDALSTEL",
        "NMDC",
    ],
    "Telecom": [
        "BHARTIARTL",
        "INDUSTOWER",
        "IDEA",
    ],
    "Realty": [
        "DLF",
        "LODHA",
        "GODREJPROP",
        "OBEROIRLTY",
    ],
    "Infrastructure": [
        "LT",
        "ADANIPORTS",
        "SIEMENS",
        "ABB",
        "BEL",
        "HAL",
    ],
    "Consumer": [
        "TITAN",
        "TRENT",
        "ASIANPAINT",
        "PIDILITIND",
        "HAVELLS",
        "VOLTAS",
    ],
}


SECTOR_INDICES = [
    "NIFTY BANK",
    "NIFTY FIN SERVICE",
    "NIFTY IT",
    "NIFTY ENERGY",
    "NIFTY AUTO",
    "NIFTY PHARMA",
    "NIFTY FMCG",
    "NIFTY METAL",
    "NIFTY REALTY",
    "NIFTY INFRA",
    "NIFTY CONSUMPTION",
]


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def _clamp(value, low=0.0, high=100.0):
    return float(np.clip(value, low, high))


def _market_signal(score):
    if score >= 75:
        return "STRONG"
    if score >= 60:
        return "POSITIVE"
    if score >= 40:
        return "NEUTRAL"
    if score >= 25:
        return "WEAK"
    return "VERY WEAK"


def _sector_strength_label(score):
    if score >= 75:
        return "LEADING"
    if score >= 60:
        return "STRONG"
    if score >= 40:
        return "NEUTRAL"
    if score >= 25:
        return "WEAK"
    return "LAGGING"


def _stock_signal(score):
    if score >= 80:
        return "LEADER"
    if score >= 65:
        return "OUTPERFORM"
    if score >= 50:
        return "NEUTRAL"
    if score >= 35:
        return "UNDERPERFORM"
    return "LAGGARD"


# ---------------------------------------------------------------------
# BUILD STOCK UNIVERSE
# ---------------------------------------------------------------------

def build_market_universe(config=None):
    """
    Build the normalized market → sector → stock universe.

    Output fields:
        Market
        Sector
        Symbol
        Price
        Price Change %
        Relative Strength
        Volume
        Volume Ratio
        Momentum
        Volatility %
        52W High Distance %
        52W Low Distance %
        Sector Strength
        Breadth Score
        Market Score
        Signal
    """

    config = config or MarketScreenerConfig()
    rng = np.random.default_rng(config.seed)

    rows = []

    # -----------------------------------------------------------------
    # Simulated sector-level strength.
    # -----------------------------------------------------------------

    sector_strength = {
        sector: float(rng.uniform(25, 85))
        for sector in SECTOR_STOCKS
    }

    # -----------------------------------------------------------------
    # Stock-level data.
    # -----------------------------------------------------------------

    for sector, symbols in SECTOR_STOCKS.items():

        base_sector_strength = sector_strength[sector]

        for symbol in symbols:

            price = float(rng.uniform(250, 4500))

            price_change = float(
                rng.normal(
                    loc=(base_sector_strength - 50) * 0.055,
                    scale=2.25,
                )
            )

            relative_strength = _clamp(
                50
                + (base_sector_strength - 50) * 0.70
                + rng.normal(0, 12)
            )

            volume = int(
                rng.integers(
                    250_000,
                    8_000_000,
                )
            )

            volume_ratio = float(
                np.clip(
                    rng.normal(
                        loc=1.15
                        + (base_sector_strength - 50) / 180,
                        scale=0.35,
                    ),
                    0.40,
                    3.50,
                )
            )

            momentum = _clamp(
                50
                + price_change * 5.0
                + (relative_strength - 50) * 0.45
                + rng.normal(0, 8)
            )

            volatility = float(
                np.clip(
                    rng.normal(18, 5),
                    8,
                    45,
                )
            )

            high_distance = float(
                np.clip(
                    rng.normal(
                        loc=-9
                        + (base_sector_strength - 50) * 0.08,
                        scale=7,
                    ),
                    -40,
                    -0.2,
                )
            )

            low_distance = float(
                np.clip(
                    rng.normal(
                        loc=35
                        + (base_sector_strength - 50) * 0.15,
                        scale=18,
                    ),
                    3,
                    150,
                )
            )

            breadth_score = _clamp(
                50
                + (base_sector_strength - 50) * 0.55
                + rng.normal(0, 10)
            )

            # ---------------------------------------------------------
            # IFIT Market Score
            # ---------------------------------------------------------

            market_score = _clamp(
                relative_strength * 0.22
                + momentum * 0.20
                + volume_ratio * 18
                + breadth_score * 0.16
                + base_sector_strength * 0.24
                + np.clip(price_change + 2, 0, 8) * 1.5
                - max(volatility - 25, 0) * 0.25
            )

            signal = _stock_signal(market_score)

            rows.append(
                {
                    "Market": config.market_name,
                    "Sector": sector,
                    "Symbol": symbol,
                    "Price": round(price, 2),
                    "Price Change %": round(price_change, 2),
                    "Relative Strength": round(relative_strength, 2),
                    "Volume": volume,
                    "Volume Ratio": round(volume_ratio, 2),
                    "Momentum": round(momentum, 2),
                    "Volatility %": round(volatility, 2),
                    "52W High Distance %": round(high_distance, 2),
                    "52W Low Distance %": round(low_distance, 2),
                    "Sector Strength": round(base_sector_strength, 2),
                    "Breadth Score": round(breadth_score, 2),
                    "Market Score": round(market_score, 2),
                    "Signal": signal,
                }
            )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# FILTER ENGINE
# ---------------------------------------------------------------------

def apply_market_filters(
    df,
    sector="All",
    signal="All",
    min_score=0.0,
    min_relative_strength=0.0,
    min_volume_ratio=0.0,
    min_momentum=0.0,
    max_volatility=100.0,
):
    """
    Apply market / sector / stock filters.
    """

    if df is None or df.empty:
        return pd.DataFrame(columns=df.columns if df is not None else [])

    out = df.copy()

    if sector != "All":
        out = out[out["Sector"] == sector]

    if signal != "All":
        out = out[out["Signal"] == signal]

    out = out[out["Market Score"] >= float(min_score)]

    out = out[
        out["Relative Strength"]
        >= float(min_relative_strength)
    ]

    out = out[
        out["Volume Ratio"]
        >= float(min_volume_ratio)
    ]

    out = out[
        out["Momentum"]
        >= float(min_momentum)
    ]

    out = out[
        out["Volatility %"]
        <= float(max_volatility)
    ]

    return out.reset_index(drop=True)


# ---------------------------------------------------------------------
# RANKING ENGINE
# ---------------------------------------------------------------------

def rank_market(df):
    """
    Rank stocks by IFIT Market Score.

    Secondary ranking:
        Relative Strength
        Momentum
        Volume Ratio
    """

    if df is None or df.empty:
        return pd.DataFrame(
            columns=df.columns if df is not None else []
        )

    out = df.copy()

    return out.sort_values(
        by=[
            "Market Score",
            "Relative Strength",
            "Momentum",
            "Volume Ratio",
        ],
        ascending=[
            False,
            False,
            False,
            False,
        ],
        kind="mergesort",
    ).reset_index(drop=True)


# ---------------------------------------------------------------------
# SECTOR SUMMARY
# ---------------------------------------------------------------------

def sector_summary(df):
    """
    Aggregate stock-level intelligence into sector-level readings.
    """

    if df is None or df.empty:
        return pd.DataFrame(
            columns=[
                "Sector",
                "Stocks",
                "Average Price Change %",
                "Average Relative Strength",
                "Average Momentum",
                "Average Volume Ratio",
                "Average Market Score",
                "Breadth %",
                "Sector Strength",
                "Signal",
            ]
        )

    grouped = (
        df.groupby("Sector")
        .agg(
            Stocks=("Symbol", "count"),
            **{
                "Average Price Change %": (
                    "Price Change %",
                    "mean",
                ),
                "Average Relative Strength": (
                    "Relative Strength",
                    "mean",
                ),
                "Average Momentum": (
                    "Momentum",
                    "mean",
                ),
                "Average Volume Ratio": (
                    "Volume Ratio",
                    "mean",
                ),
                "Average Market Score": (
                    "Market Score",
                    "mean",
                ),
                "Sector Strength": (
                    "Sector Strength",
                    "mean",
                ),
            },
        )
        .reset_index()
    )

    breadth = (
        df.assign(
            positive=df["Price Change %"] > 0
        )
        .groupby("Sector")["positive"]
        .mean()
        .mul(100)
        .reset_index(name="Breadth %")
    )

    grouped = grouped.merge(
        breadth,
        on="Sector",
        how="left",
    )

    grouped["Signal"] = grouped[
        "Average Market Score"
    ].map(_sector_strength_label)

    numeric_columns = [
        "Average Price Change %",
        "Average Relative Strength",
        "Average Momentum",
        "Average Volume Ratio",
        "Average Market Score",
        "Breadth %",
        "Sector Strength",
    ]

    for column in numeric_columns:
        grouped[column] = grouped[column].round(2)

    return grouped.sort_values(
        "Average Market Score",
        ascending=False,
    ).reset_index(drop=True)


# ---------------------------------------------------------------------
# MARKET SUMMARY
# ---------------------------------------------------------------------

def market_summary(df):
    """
    Produce a top-level market snapshot from the stock universe.
    """

    if df is None or df.empty:
        return {
            "Market": "NIFTY 50",
            "Stocks": 0,
            "Advancing": 0,
            "Declining": 0,
            "Breadth %": 0.0,
            "Average Change %": 0.0,
            "Average Relative Strength": 0.0,
            "Average Momentum": 0.0,
            "Average Volume Ratio": 0.0,
            "Market Score": 0.0,
            "Signal": "VERY WEAK",
        }

    advancing = int(
        (df["Price Change %"] > 0).sum()
    )

    declining = int(
        (df["Price Change %"] < 0).sum()
    )

    breadth = (
        advancing
        / max(len(df), 1)
        * 100
    )

    score = _clamp(
        df["Market Score"].mean()
    )

    return {
        "Market": str(df["Market"].iloc[0]),
        "Stocks": int(len(df)),
        "Advancing": advancing,
        "Declining": declining,
        "Breadth %": round(breadth, 2),
        "Average Change %": round(
            df["Price Change %"].mean(),
            2,
        ),
        "Average Relative Strength": round(
            df["Relative Strength"].mean(),
            2,
        ),
        "Average Momentum": round(
            df["Momentum"].mean(),
            2,
        ),
        "Average Volume Ratio": round(
            df["Volume Ratio"].mean(),
            2,
        ),
        "Market Score": round(score, 2),
        "Signal": _market_signal(score),
    }


# ---------------------------------------------------------------------
# CONFIG / DISCOVERY HELPERS
# ---------------------------------------------------------------------

def available_sectors(df=None):
    if df is None or df.empty:
        return ["All"] + sorted(SECTOR_STOCKS.keys())

    return [
        "All"
    ] + sorted(
        df["Sector"].dropna().unique().tolist()
    )


def available_signals():
    return [
        "All",
        "LEADER",
        "OUTPERFORM",
        "NEUTRAL",
        "UNDERPERFORM",
        "LAGGARD",
    ]