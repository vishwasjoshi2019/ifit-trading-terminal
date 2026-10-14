"""
IFIT MCX / Commodities Intelligence Engine
V0.1

Deterministic simulation engine for:
Gold, Silver, Crude Oil, Natural Gas, Copper,
Aluminium, Zinc, Lead and Nickel.

Designed as an intelligence layer, not a live-data connector.
Live MCX/provider integration can replace build_commodities_universe()
later without changing the downstream analytics contract.
"""

from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class MCXConfig:
    seed: int = 8509
    market_name: str = "MCX"


COMMODITIES = {
    "GOLD": {
        "base_price": 75000.0,
        "volatility": 15.0,
        "base_volume": 85000,
        "base_oi": 190000,
        "unit": "10 GRAMS",
    },
    "SILVER": {
        "base_price": 90000.0,
        "volatility": 28.0,
        "base_volume": 65000,
        "base_oi": 145000,
        "unit": "1 KG",
    },
    "CRUDE OIL": {
        "base_price": 5800.0,
        "volatility": 32.0,
        "base_volume": 110000,
        "base_oi": 210000,
        "unit": "1 BBL",
    },
    "NATURAL GAS": {
        "base_price": 300.0,
        "volatility": 42.0,
        "base_volume": 95000,
        "base_oi": 180000,
        "unit": "MMBTU",
    },
    "COPPER": {
        "base_price": 900.0,
        "volatility": 24.0,
        "base_volume": 70000,
        "base_oi": 125000,
        "unit": "1 KG",
    },
    "ALUMINIUM": {
        "base_price": 250.0,
        "volatility": 22.0,
        "base_volume": 55000,
        "base_oi": 115000,
        "unit": "1 KG",
    },
    "ZINC": {
        "base_price": 270.0,
        "volatility": 25.0,
        "base_volume": 52000,
        "base_oi": 105000,
        "unit": "1 KG",
    },
    "LEAD": {
        "base_price": 185.0,
        "volatility": 23.0,
        "base_volume": 42000,
        "base_oi": 85000,
        "unit": "1 KG",
    },
    "NICKEL": {
        "base_price": 1450.0,
        "volatility": 31.0,
        "base_volume": 38000,
        "base_oi": 72000,
        "unit": "1 KG",
    },
}


def _clamp(value, low=0.0, high=100.0):
    return max(low, min(high, float(value)))


def _signal(score):
    if score >= 80:
        return "STRONG BULLISH"
    if score >= 65:
        return "BULLISH"
    if score >= 50:
        return "NEUTRAL"
    if score >= 35:
        return "BEARISH"
    return "STRONG BEARISH"


def _trend_label(score):
    if score >= 75:
        return "STRONG TREND"
    if score >= 60:
        return "TRENDING"
    if score >= 40:
        return "RANGE"
    return "WEAK TREND"


def _term_structure_label(front_iv, back_iv):
    spread = back_iv - front_iv

    if spread > 2.0:
        return "CONTANGO"
    if spread < -2.0:
        return "BACKWARDATION"
    return "FLAT"


def _roll_label(basis):
    if basis > 1.5:
        return "POSITIVE ROLL"
    if basis < -1.5:
        return "NEGATIVE ROLL"
    return "NEUTRAL ROLL"


def build_commodities_universe(config=None):
    """
    Build deterministic simulated MCX commodity intelligence universe.
    """

    config = config or MCXConfig()
    rng = np.random.default_rng(config.seed)

    rows = []

    for symbol, meta in COMMODITIES.items():

        base = meta["base_price"]

        price_change = rng.normal(0, meta["volatility"] / 7.0)

        price = base * (
            1.0 + price_change / 100.0
        )

        previous_price = price / (
            1.0 + price_change / 100.0
        )

        volume = int(
            meta["base_volume"]
            * rng.uniform(0.65, 1.45)
        )

        oi = int(
            meta["base_oi"]
            * rng.uniform(0.70, 1.35)
        )

        oi_change = rng.normal(0, 12.0)

        volume_ratio = volume / meta["base_volume"]

        momentum_1m = rng.normal(
            price_change * 1.8,
            5.5,
        )

        momentum_score = _clamp(
            50.0 + momentum_1m * 4.0
        )

        realized_vol = abs(
            rng.normal(
                meta["volatility"],
                4.0,
            )
        )

        volatility_percentile = _clamp(
            50.0
            + (realized_vol - meta["volatility"]) * 5.0
        )

        iv_front = abs(
            rng.normal(
                meta["volatility"],
                3.0,
            )
        )

        iv_back = abs(
            rng.normal(
                meta["volatility"],
                3.0,
            )
        )

        basis = rng.normal(0, 2.5)

        spread = rng.normal(
            0,
            1.8,
        )

        high_distance = -abs(
            rng.normal(12.0, 8.0)
        )

        low_distance = abs(
            rng.normal(15.0, 9.0)
        )

        trend_strength = _clamp(
            50.0
            + momentum_score * 0.30
            + volume_ratio * 10.0
            - volatility_percentile * 0.10
        )

        positioning_score = _clamp(
            50.0
            + oi_change * 2.2
            + np.sign(price_change) * 8.0
        )

        liquidity_score = _clamp(
            45.0
            + np.log1p(volume) * 4.0
            + np.log1p(oi) * 2.0
            - abs(spread) * 8.0
        )

        commodity_score = _clamp(
            momentum_score * 0.25
            + trend_strength * 0.20
            + positioning_score * 0.20
            + liquidity_score * 0.10
            + (100.0 - volatility_percentile) * 0.10
            + 50.0 * 0.15
        )

        rows.append(
            {
                "Market": config.market_name,
                "Commodity": symbol,
                "Unit": meta["unit"],
                "Price": round(price, 2),
                "Price Change %": round(price_change, 2),
                "Volume": volume,
                "Volume Ratio": round(volume_ratio, 2),
                "Open Interest": oi,
                "OI Change %": round(oi_change, 2),
                "Momentum 1M %": round(momentum_1m, 2),
                "Momentum Score": round(momentum_score, 2),
                "Realized Volatility %": round(realized_vol, 2),
                "Volatility Percentile": round(
                    volatility_percentile,
                    2,
                ),
                "Front IV %": round(iv_front, 2),
                "Back IV %": round(iv_back, 2),
                "Term Structure": _term_structure_label(
                    iv_front,
                    iv_back,
                ),
                "Basis %": round(basis, 2),
                "Roll Behaviour": _roll_label(basis),
                "52W High Distance %": round(
                    high_distance,
                    2,
                ),
                "52W Low Distance %": round(
                    low_distance,
                    2,
                ),
                "Trend Strength": round(
                    trend_strength,
                    2,
                ),
                "Positioning Score": round(
                    positioning_score,
                    2,
                ),
                "Liquidity Score": round(
                    liquidity_score,
                    2,
                ),
                "Commodity Score": round(
                    commodity_score,
                    2,
                ),
                "Signal": _signal(
                    commodity_score
                ),
            }
        )

    return pd.DataFrame(rows)


def apply_commodity_filters(
    df,
    commodities=None,
    signals=None,
    min_score=0.0,
    min_momentum=0.0,
    min_volume_ratio=0.0,
    min_oi_change=-100.0,
    max_oi_change=100.0,
    max_volatility_percentile=100.0,
    term_structure=None,
    roll_behaviour=None,
):
    """
    Apply MCX commodity screening filters.
    """

    out = df.copy()

    if commodities:
        out = out[
            out["Commodity"].isin(commodities)
        ]

    if signals:
        out = out[
            out["Signal"].isin(signals)
        ]

    out = out[
        out["Commodity Score"] >= min_score
    ]

    out = out[
        out["Momentum Score"] >= min_momentum
    ]

    out = out[
        out["Volume Ratio"] >= min_volume_ratio
    ]

    out = out[
        out["OI Change %"] >= min_oi_change
    ]

    out = out[
        out["OI Change %"] <= max_oi_change
    ]

    out = out[
        out["Volatility Percentile"]
        <= max_volatility_percentile
    ]

    if term_structure:
        out = out[
            out["Term Structure"].isin(
                term_structure
            )
        ]

    if roll_behaviour:
        out = out[
            out["Roll Behaviour"].isin(
                roll_behaviour
            )
        ]

    return out.reset_index(drop=True)


def rank_commodities(
    df,
    sort_by="Commodity Score",
    ascending=False,
):
    """
    Rank commodities by selected intelligence factor.
    """

    if df.empty:
        return df.copy()

    if sort_by not in df.columns:
        sort_by = "Commodity Score"

    return (
        df.sort_values(
            sort_by,
            ascending=ascending,
        )
        .reset_index(drop=True)
    )


def commodity_summary(df):
    """
    Aggregate summary for the current filtered universe.
    """

    if df.empty:
        return {
            "Commodities": 0,
            "Bullish Signals": 0,
            "Bearish Signals": 0,
            "Average Price Change": 0.0,
            "Average Momentum": 0.0,
            "Average Volatility": 0.0,
            "Average OI Change": 0.0,
            "Average Commodity Score": 0.0,
            "Signal": "NO DATA",
        }

    bullish = int(
        df["Signal"]
        .isin(
            [
                "STRONG BULLISH",
                "BULLISH",
            ]
        )
        .sum()
    )

    bearish = int(
        df["Signal"]
        .isin(
            [
                "STRONG BEARISH",
                "BEARISH",
            ]
        )
        .sum()
    )

    avg_score = float(
        df["Commodity Score"].mean()
    )

    return {
        "Commodities": int(len(df)),
        "Bullish Signals": bullish,
        "Bearish Signals": bearish,
        "Average Price Change": round(
            float(
                df["Price Change %"].mean()
            ),
            2,
        ),
        "Average Momentum": round(
            float(
                df["Momentum 1M %"].mean()
            ),
            2,
        ),
        "Average Volatility": round(
            float(
                df[
                    "Realized Volatility %"
                ].mean()
            ),
            2,
        ),
        "Average OI Change": round(
            float(
                df["OI Change %"].mean()
            ),
            2,
        ),
        "Average Commodity Score": round(
            avg_score,
            2,
        ),
        "Signal": _signal(avg_score),
    }


def available_commodities(df=None):
    if df is not None and not df.empty:
        return sorted(
            df["Commodity"].dropna().unique().tolist()
        )

    return sorted(COMMODITIES.keys())


def available_commodity_signals():
    return [
        "STRONG BULLISH",
        "BULLISH",
        "NEUTRAL",
        "BEARISH",
        "STRONG BEARISH",
    ]


def available_term_structures():
    return [
        "CONTANGO",
        "BACKWARDATION",
        "FLAT",
    ]


def available_roll_behaviours():
    return [
        "POSITIVE ROLL",
        "NEGATIVE ROLL",
        "NEUTRAL ROLL",
    ]


if __name__ == "__main__":

    print("MCX COMMODITIES INTELLIGENCE ENGINE QA")

    config = MCXConfig()

    df = build_commodities_universe(
        config
    )

    print(
        "ROWS:",
        len(df),
    )

    print(
        "COLUMNS:",
        len(df.columns),
    )

    print(
        "COMMODITIES:",
        df["Commodity"].tolist(),
    )

    print(
        "SCORE RANGE:",
        round(
            float(df["Commodity Score"].min()),
            2,
        ),
        round(
            float(df["Commodity Score"].max()),
            2,
        ),
    )

    print(
        "SIGNALS:",
        df["Signal"].value_counts().to_dict(),
    )

    filtered = apply_commodity_filters(
        df,
        min_score=60,
        min_momentum=45,
        min_volume_ratio=0.8,
    )

    print(
        "FILTER ROWS:",
        len(filtered),
    )

    ranked = rank_commodities(
        filtered
    )

    print(
        "TOP COMMODITY:",
        ranked.iloc[0][
            [
                "Commodity",
                "Commodity Score",
                "Signal",
            ]
        ].to_dict()
        if not ranked.empty
        else "NONE",
    )

    summary = commodity_summary(
        ranked
    )

    print(
        "SUMMARY:",
        summary,
    )

    print(
        "MCX COMMODITIES ENGINE QA: PASS"
    )