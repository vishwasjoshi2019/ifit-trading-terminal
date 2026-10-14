"""
IFIT V0.8.5 — Equity Screener Engine

Simulation-backed equity universe for the first Screener milestone.

Design principle:
    Simulation → Authorized live vendor
without requiring changes to the Screener UI/filter contract.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class ScreenerConfig:
    universe_size: int = 100
    seed: int = 8405


SECTORS = [
    "Banking",
    "IT",
    "Energy",
    "Pharma",
    "Auto",
    "FMCG",
    "Industrials",
    "Telecom",
    "Metals",
    "Consumer",
]
SECTOR_MAP = {
    "RELIANCE": "Energy",
    "HDFCBANK": "Banking",
    "ICICIBANK": "Banking",
    "SBIN": "Banking",
    "AXISBANK": "Banking",
    "KOTAKBANK": "Banking",
    "INDUSINDBK": "Banking",
    "BAJFINANCE": "Financial Services",
    "BAJAJFINSV": "Financial Services",
    "HDFC": "Financial Services",

    "TCS": "IT",
    "INFY": "IT",
    "HCLTECH": "IT",
    "WIPRO": "IT",
    "TECHM": "IT",
    "LTIM": "IT",
    "MPHASIS": "IT",
    "COFORGE": "IT",
    "PERSISTENT": "IT",
    "LTTS": "IT",

    "LT": "Industrials",
    "ADANIENT": "Conglomerate",
    "ADANIPORTS": "Infrastructure",
    "POWERGRID": "Power",
    "NTPC": "Power",
    "ONGC": "Energy",
    "IOC": "Energy",
    "BPCL": "Energy",
    "COALINDIA": "Mining",
    "GAIL": "Energy",

    "SUNPHARMA": "Pharma",
    "DRREDDY": "Pharma",
    "CIPLA": "Pharma",
    "DIVISLAB": "Pharma",
    "APOLLOHOSP": "Healthcare",

    "M&M": "Auto",
    "MARUTI": "Auto",
    "TATAMOTORS": "Auto",
    "EICHERMOT": "Auto",
    "HEROMOTOCO": "Auto",

    "ITC": "FMCG",
    "HINDUNILVR": "FMCG",
    "NESTLEIND": "FMCG",
    "BRITANNIA": "FMCG",
    "TATACONSUM": "FMCG",

    "BHARTIARTL": "Telecom",
    "INDUSTOWER": "Telecom",

    "TATASTEEL": "Metals",
    "JSWSTEEL": "Metals",
    "HINDALCO": "Metals",
}

SYMBOLS = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK",
    "KOTAKBANK", "INDUSINDBK", "BAJFINANCE", "BAJAJFINSV", "HDFC",
    "TCS", "INFY", "HCLTECH", "WIPRO", "TECHM",
    "LTIM", "MPHASIS", "COFORGE", "PERSISTENT", "LTTS",
    "LT", "ADANIENT", "ADANIPORTS", "POWERGRID", "NTPC",
    "ONGC", "IOC", "BPCL", "COALINDIA", "GAIL",
    "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP",
    "M&M", "MARUTI", "TATAMOTORS", "EICHERMOT", "HEROMOTOCO",
    "ITC", "HINDUNILVR", "NESTLEIND", "BRITANNIA", "TATACONSUM",
    "BHARTIARTL", "INDUSTOWER", "TATASTEEL", "JSWSTEEL", "HINDALCO",
]


def _build_symbol_list(size: int) -> list[str]:
    """Return a deterministic universe of the requested size."""
    symbols = list(SYMBOLS)

    for i in range(len(symbols), size):
        symbols.append(f"IFIT{i + 1:03d}")

    return symbols[:size]


def build_equity_universe(config: Optional[ScreenerConfig] = None) -> pd.DataFrame:
    """
    Build the normalized equity-universe contract used by the Screener.

    This is intentionally deterministic so QA results are reproducible.
    """
    config = config or ScreenerConfig()
    rng = np.random.default_rng(config.seed)

    symbols = _build_symbol_list(config.universe_size)
    rows = []

    for i, symbol in enumerate(symbols):
        sector = SECTOR_MAP.get(symbol, SECTORS[i % len(SECTORS)])

        price = float(rng.uniform(180, 6200))
        market_cap = float(rng.uniform(18000, 950000))

        pe = float(np.clip(rng.normal(24, 10), 7, 75))
        roe = float(np.clip(rng.normal(17, 7), 2, 42))
        roce = float(np.clip(roe + rng.normal(3, 4), 3, 48))
        debt_equity = float(np.clip(rng.lognormal(-0.15, 0.65), 0.02, 4.0))

        revenue_growth = float(np.clip(rng.normal(13, 11), -25, 55))
        eps_growth = float(np.clip(rng.normal(15, 16), -35, 70))
        fcf_yield = float(np.clip(rng.normal(4.5, 3), -5, 18))

        avg_volume = float(rng.uniform(250000, 25000000))
        delivery_pct = float(np.clip(rng.normal(48, 12), 15, 85))

        rsi = float(np.clip(rng.normal(52, 14), 20, 85))
        ema_trend = "BULLISH" if rng.random() > 0.46 else "BEARISH"

        momentum_1m = float(np.clip(rng.normal(4, 12), -30, 40))
        volatility = float(np.clip(rng.normal(24, 9), 8, 65))
        relative_strength = float(np.clip(rng.normal(50, 18), 5, 95))

        rows.append({
            "Symbol": symbol,
            "Sector": sector,
            "Price": round(price, 2),
            "Market Cap (Cr)": round(market_cap, 2),
            "P/E": round(pe, 2),
            "ROE %": round(roe, 2),
            "ROCE %": round(roce, 2),
            "Debt/Equity": round(debt_equity, 2),
            "Revenue Growth %": round(revenue_growth, 2),
            "EPS Growth %": round(eps_growth, 2),
            "FCF Yield %": round(fcf_yield, 2),
            "Avg Volume": int(avg_volume),
            "Delivery %": round(delivery_pct, 2),
            "RSI 14": round(rsi, 2),
            "EMA Trend": ema_trend,
            "Momentum 1M %": round(momentum_1m, 2),
            "Volatility %": round(volatility, 2),
            "Relative Strength": round(relative_strength, 2),
        })

    df = pd.DataFrame(rows)

    return add_equity_score(df)


def add_equity_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a transparent architecture-level Equity Score.

    This is not a production investment score. Production scoring will
    require normalized historical data, peer groups and revisions.
    """
    result = df.copy()

    score = (
        50
        + result["ROE %"] * 0.45
        + result["ROCE %"] * 0.20
        + result["Revenue Growth %"] * 0.35
        + result["EPS Growth %"] * 0.35
        + result["FCF Yield %"] * 0.60
        + result["Momentum 1M %"] * 0.25
        + result["Relative Strength"] * 0.15
        - result["P/E"] * 0.30
        - result["Debt/Equity"] * 6.0
    )

    result["Equity Score"] = np.clip(score, 0, 100).round(2)

    return result


def apply_filters(
    df: pd.DataFrame,
    filters: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Apply optional Screener filters.

    Supported keys:
        sector
        min_price / max_price
        min_market_cap / max_market_cap
        min_roe
        min_roce
        max_pe
        max_debt_equity
        min_revenue_growth
        min_eps_growth
        min_fcf_yield
        min_volume
        min_delivery
        min_rsi / max_rsi
        ema_trend
        min_momentum
        min_relative_strength
        max_volatility
    """
    result = df.copy()

    if not filters:
        return result

    def minimum(column, key):
        if key in filters and filters[key] is not None:
            result_nonlocal[0] = result_nonlocal[0][
                result_nonlocal[0][column] >= filters[key]
            ]

    result_nonlocal = [result]

    minimum("Price", "min_price")
    minimum("Market Cap (Cr)", "min_market_cap")
    minimum("ROE %", "min_roe")
    minimum("ROCE %", "min_roce")
    minimum("Revenue Growth %", "min_revenue_growth")
    minimum("EPS Growth %", "min_eps_growth")
    minimum("FCF Yield %", "min_fcf_yield")
    minimum("Avg Volume", "min_volume")
    minimum("Delivery %", "min_delivery")
    minimum("Momentum 1M %", "min_momentum")
    minimum("Relative Strength", "min_relative_strength")

    result = result_nonlocal[0]

    if filters.get("sector"):
        result = result[result["Sector"] == filters["sector"]]

    if filters.get("ema_trend"):
        result = result[result["EMA Trend"] == filters["ema_trend"]]

    if filters.get("max_price") is not None:
        result = result[result["Price"] <= filters["max_price"]]

    if filters.get("max_market_cap") is not None:
        result = result[result["Market Cap (Cr)"] <= filters["max_market_cap"]]

    if filters.get("max_pe") is not None:
        result = result[result["P/E"] <= filters["max_pe"]]

    if filters.get("max_debt_equity") is not None:
        result = result[result["Debt/Equity"] <= filters["max_debt_equity"]]

    if filters.get("min_rsi") is not None:
        result = result[result["RSI 14"] >= filters["min_rsi"]]

    if filters.get("max_rsi") is not None:
        result = result[result["RSI 14"] <= filters["max_rsi"]]

    if filters.get("max_volatility") is not None:
        result = result[result["Volatility %"] <= filters["max_volatility"]]

    return result.reset_index(drop=True)


def rank_equities(
    df: pd.DataFrame,
    column: str = "Equity Score",
    ascending: bool = False,
) -> pd.DataFrame:
    """Return equities ranked by a selected field."""
    if column not in df.columns:
        raise ValueError(f"Unknown ranking column: {column}")

    return (
        df.sort_values(column, ascending=ascending)
        .reset_index(drop=True)
    )


def sector_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return high-level sector statistics for the screened universe."""
    if df.empty:
        return pd.DataFrame(
            columns=[
                "Sector",
                "Stocks",
                "Average Score",
                "Average Momentum %",
                "Average Relative Strength",
            ]
        )

    return (
        df.groupby("Sector")
        .agg(
            Stocks=("Symbol", "count"),
            **{
                "Average Score": ("Equity Score", "mean"),
                "Average Momentum %": ("Momentum 1M %", "mean"),
                "Average Relative Strength": ("Relative Strength", "mean"),
            },
        )
        .reset_index()
        .sort_values("Average Score", ascending=False)
        .reset_index(drop=True)
    )