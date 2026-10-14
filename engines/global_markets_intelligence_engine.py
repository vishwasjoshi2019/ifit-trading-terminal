"""
IFIT Global Markets Intelligence V0.1
Simulation/proxy intelligence engine.

Purpose:
- Global equity, rates, FX, commodity and volatility context
- Cross-market scoring
- Leadership/lagging detection
- Divergence detection
- Correlation matrix
- Structured summary for IFIT UI / Decision Intelligence

No live market-data calls are made in this prototype.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd


GLOBAL_MARKETS_UNIVERSE = [
    ("NIFTY 50", "India Equity"),
    ("BANKNIFTY", "India Equity"),
    ("S&P 500", "US Equity"),
    ("NASDAQ 100", "US Equity"),
    ("DOW JONES", "US Equity"),
    ("NIKKEI 225", "Asia Equity"),
    ("DAX", "Europe Equity"),
    ("FTSE 100", "Europe Equity"),
    ("US 10Y", "US Rates"),
    ("G-SEC 10Y", "India Rates"),
    ("USDINR", "FX"),
    ("DXY", "FX"),
    ("GOLD", "Commodity"),
    ("CRUDE OIL", "Commodity"),
    ("INDIA VIX", "Volatility"),
]


def build_global_markets_universe(
    periods: int = 180,
    seed: int = 42,
) -> pd.DataFrame:
    """Build deterministic simulation/proxy data for the global universe."""
    if periods < 30:
        raise ValueError("periods must be >= 30")

    rng = np.random.default_rng(seed)
    dates = pd.date_range(
        end=pd.Timestamp.now().normalize(),
        periods=periods,
        freq="B",
    )

    rows = []

    for i, (symbol, asset_class) in enumerate(GLOBAL_MARKETS_UNIVERSE):
        base = 100.0 + i * 8.0
        drift = rng.normal(0.00025, 0.00015)
        vol = rng.uniform(0.006, 0.018)

        shocks = rng.normal(drift, vol, periods)

        if symbol == "INDIA VIX":
            shocks = rng.normal(0.0, 0.025, periods)

        prices = base * np.exp(np.cumsum(shocks))

        for j, timestamp in enumerate(dates):
            rows.append(
                {
                    "Timestamp": timestamp,
                    "Symbol": symbol,
                    "Asset Class": asset_class,
                    "Price": float(prices[j]),
                    "Return %": float(shocks[j] * 100.0),
                }
            )

    return pd.DataFrame(rows)


def _latest_scores(df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for symbol, asset_class in GLOBAL_MARKETS_UNIVERSE:
        x = df[df["Symbol"] == symbol].sort_values("Timestamp")

        if len(x) >= 6:
            ret_5 = (x["Price"].iloc[-1] / x["Price"].iloc[-6] - 1.0) * 100.0
        else:
            ret_5 = 0.0

        if len(x) >= 21:
            ret_20 = (x["Price"].iloc[-1] / x["Price"].iloc[-21] - 1.0) * 100.0
        else:
            ret_20 = 0.0

        vol_20 = float(x["Return %"].tail(20).std())

        score = float(
            np.clip(
                50.0
                + ret_5 * 3.0
                + ret_20 * 1.2
                - vol_20 * 0.5,
                0.0,
                100.0,
            )
        )

        rows.append(
            {
                "Symbol": symbol,
                "Asset Class": asset_class,
                "Price": round(float(x["Price"].iloc[-1]), 4),
                "5D Return %": round(float(ret_5), 3),
                "20D Return %": round(float(ret_20), 3),
                "Volatility %": round(vol_20, 3),
                "Global Score": round(score, 2),
            }
        )

    return pd.DataFrame(rows)


def _risk_state(score: float, volatility: float) -> str:
    if score >= 62.0 and volatility < 2.0:
        return "RISK-ON"
    if score <= 38.0 or volatility >= 3.0:
        return "RISK-OFF"
    return "NEUTRAL / MIXED"


def _regime(score: float, dispersion: float) -> str:
    if score >= 65.0 and dispersion < 18.0:
        return "GLOBAL RISK-ON"
    if score <= 35.0 and dispersion < 18.0:
        return "GLOBAL RISK-OFF"
    if dispersion >= 25.0:
        return "DIVERGENCE / ROTATION"
    return "MIXED / ROTATION"


def build_global_markets_snapshot(
    df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Build the complete Global Markets Intelligence snapshot."""
    data = df if df is not None else build_global_markets_universe()

    required = {"Timestamp", "Symbol", "Asset Class", "Price", "Return %"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    table = _latest_scores(data)

    score = float(table["Global Score"].mean())
    dispersion = float(table["Global Score"].std())

    def class_score(name: str) -> float:
        values = table.loc[
            table["Asset Class"] == name,
            "Global Score",
        ]
        return float(values.mean()) if not values.empty else 50.0

    india = float(
        table.loc[
            table["Asset Class"] == "India Equity",
            "Global Score",
        ].mean()
    )
    us = float(
        table.loc[
            table["Asset Class"] == "US Equity",
            "Global Score",
        ].mean()
    )
    rates = float(
        table.loc[
            table["Asset Class"].str.contains("Rates", regex=True),
            "Global Score",
        ].mean()
    )

    if np.isnan(india):
        india = 50.0
    if np.isnan(us):
        us = 50.0
    if np.isnan(rates):
        rates = 50.0

    fx = class_score("FX")
    commodities = class_score("Commodity")
    asia = class_score("Asia Equity")
    europe = class_score("Europe Equity")

    vol_series = table.loc[
        table["Asset Class"] == "Volatility",
        "Volatility %",
    ]
    volatility_proxy = (
        float(vol_series.mean()) if not vol_series.empty else 0.0
    )

    ranked = table.sort_values("Global Score", ascending=False)
    leader = str(ranked.iloc[0]["Symbol"])
    lagging = str(ranked.iloc[-1]["Symbol"])

    divergence_count = (
        int(abs(india - us) >= 8.0)
        + int(abs(((india + us) / 2.0) - rates) >= 8.0)
    )

    corr_symbols = [symbol for symbol, _ in GLOBAL_MARKETS_UNIVERSE]
    price_matrix = (
        data.pivot(
            index="Timestamp",
            columns="Symbol",
            values="Price",
        )
        .reindex(columns=corr_symbols)
        .sort_index()
    )

    correlation = price_matrix.pct_change().corr().round(2)

    return {
        "Asset Count": int(len(table)),
        "Global Score": round(score, 2),
        "Risk State": _risk_state(score, volatility_proxy),
        "Regime": _regime(score, dispersion),
        "Leadership": leader,
        "Lagging": lagging,
        "Divergence Count": divergence_count,
        "India Equity Score": round(india, 2),
        "US Equity Score": round(us, 2),
        "Asia Equity Score": round(asia, 2),
        "Europe Equity Score": round(europe, 2),
        "Rates Score": round(rates, 2),
        "FX Score": round(fx, 2),
        "Commodity Score": round(commodities, 2),
        "Volatility Proxy": round(volatility_proxy, 3),
        "Dispersion": round(dispersion, 2),
        "Correlation": correlation,
        "Asset Table": table,
    }


def global_markets_summary(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Return the compact schema used by IFIT presentation layers."""
    return {
        "Assets": snapshot.get("Asset Count", 0),
        "Global Score": snapshot.get("Global Score", 0),
        "Risk State": snapshot.get("Risk State", "N/A"),
        "Regime": snapshot.get("Regime", "N/A"),
        "Leader": snapshot.get("Leadership", "N/A"),
        "Lagging": snapshot.get("Lagging", "N/A"),
        "Divergences": snapshot.get("Divergence Count", 0),
        "India": snapshot.get("India Equity Score", 0),
        "US": snapshot.get("US Equity Score", 0),
        "Asia": snapshot.get("Asia Equity Score", 0),
        "Europe": snapshot.get("Europe Equity Score", 0),
        "Rates": snapshot.get("Rates Score", 0),
        "FX": snapshot.get("FX Score", 0),
        "Commodities": snapshot.get("Commodity Score", 0),
    }


def build_global_markets_intelligence_snapshot(
    periods: int = 180,
    seed: int = 42,
) -> Dict[str, Any]:
    return build_global_markets_snapshot(
        build_global_markets_universe(
            periods=periods,
            seed=seed,
        )
    )


def available_global_market_views() -> list[str]:
    return [
        "Overview",
        "Global Equity",
        "Rates & FX",
        "Commodities",
        "Volatility",
    ]
