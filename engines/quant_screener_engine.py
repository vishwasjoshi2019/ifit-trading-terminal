"""
IFIT V0.8.5 — Quant Screener Engine

Simulation-backed quantitative screening engine.

Core dimensions:
    Momentum
    Mean Reversion
    Volatility
    Correlation
    Statistical / Z-Score
    Trend Strength
    Relative Performance
    Quant Composite Score
    Quant Signal

The normalized output is designed so an authorized live
market-data adapter can replace simulation later without
changing the screening contract.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class QuantScreenerConfig:
    seed: int = 8508
    market_name: str = "NIFTY 50"


SYMBOLS = [
    "RELIANCE",
    "HDFCBANK",
    "ICICIBANK",
    "SBIN",
    "AXISBANK",
    "TCS",
    "INFY",
    "HCLTECH",
    "BHARTIARTL",
    "ITC",
    "LT",
    "M&M",
    "SUNPHARMA",
    "TATASTEEL",
    "MARUTI",
    "BAJFINANCE",
    "TITAN",
    "ADANIPORTS",
    "NTPC",
    "POWERGRID",
]


def _clamp(value, low=0.0, high=100.0):
    return float(np.clip(value, low, high))


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


def _mean_reversion_label(zscore):
    if zscore <= -2.0:
        return "OVERSOLD"
    if zscore <= -1.0:
        return "BELOW MEAN"
    if zscore >= 2.0:
        return "OVERBOUGHT"
    if zscore >= 1.0:
        return "ABOVE MEAN"
    return "MEAN"


def build_quant_universe(config=None):
    """
    Build the normalized quantitative screener universe.

    Output fields:
        Market
        Symbol
        Price
        Price Change %
        Momentum 1M %
        Momentum 3M %
        Momentum Score
        Z-Score
        Mean Reversion Score
        Mean Reversion State
        Realized Volatility %
        Volatility Percentile
        Correlation to Market
        Trend Strength
        Relative Performance %
        Statistical Score
        Quant Score
        Signal
    """

    config = config or QuantScreenerConfig()
    rng = np.random.default_rng(config.seed)

    rows = []

    for symbol in SYMBOLS:

        price = float(
            rng.uniform(500, 4500)
        )

        price_change = float(
            rng.normal(0, 1.8)
        )

        momentum_1m = float(
            np.clip(
                rng.normal(2.0, 7.0),
                -20,
                25,
            )
        )

        momentum_3m = float(
            np.clip(
                momentum_1m * 1.25
                + rng.normal(2.0, 8.0),
                -35,
                45,
            )
        )

        momentum_score = _clamp(
            50
            + momentum_1m * 3.0
            + momentum_3m * 1.15
            + rng.normal(0, 7)
        )

        zscore = float(
            np.clip(
                rng.normal(0, 1.35),
                -3.5,
                3.5,
            )
        )

        mean_reversion_score = _clamp(
            50
            - abs(zscore) * 9
            + rng.normal(0, 8)
        )

        realized_volatility = float(
            np.clip(
                rng.normal(18, 5),
                7,
                45,
            )
        )

        volatility_percentile = _clamp(
            50
            + (realized_volatility - 18) * 5
            + rng.normal(0, 10)
        )

        correlation = float(
            np.clip(
                rng.normal(0.58, 0.18),
                -0.20,
                0.95,
            )
        )

        correlation_score = _clamp(
            75
            - abs(correlation - 0.55) * 75
            + rng.normal(0, 7)
        )

        trend_strength = _clamp(
            50
            + momentum_1m * 2.0
            + momentum_3m * 0.75
            + rng.normal(0, 9)
        )

        relative_performance = float(
            np.clip(
                momentum_3m
                + rng.normal(0, 5),
                -30,
                40,
            )
        )

        relative_performance_score = _clamp(
            50
            + relative_performance * 2.0
            + rng.normal(0, 7)
        )

        statistical_score = _clamp(
            mean_reversion_score * 0.35
            + correlation_score * 0.15
            + trend_strength * 0.20
            + relative_performance_score * 0.20
            + (100 - volatility_percentile) * 0.10
        )

        quant_score = _clamp(
            momentum_score * 0.25
            + mean_reversion_score * 0.15
            + (100 - volatility_percentile) * 0.15
            + correlation_score * 0.10
            + trend_strength * 0.15
            + relative_performance_score * 0.10
            + statistical_score * 0.10
        )

        rows.append(
            {
                "Market": config.market_name,
                "Symbol": symbol,
                "Price": round(price, 2),
                "Price Change %": round(
                    price_change,
                    2,
                ),
                "Momentum 1M %": round(
                    momentum_1m,
                    2,
                ),
                "Momentum 3M %": round(
                    momentum_3m,
                    2,
                ),
                "Momentum Score": round(
                    momentum_score,
                    2,
                ),
                "Z-Score": round(
                    zscore,
                    2,
                ),
                "Mean Reversion Score": round(
                    mean_reversion_score,
                    2,
                ),
                "Mean Reversion State": (
                    _mean_reversion_label(zscore)
                ),
                "Realized Volatility %": round(
                    realized_volatility,
                    2,
                ),
                "Volatility Percentile": round(
                    volatility_percentile,
                    2,
                ),
                "Correlation to Market": round(
                    correlation,
                    3,
                ),
                "Correlation Score": round(
                    correlation_score,
                    2,
                ),
                "Trend Strength": round(
                    trend_strength,
                    2,
                ),
                "Relative Performance %": round(
                    relative_performance,
                    2,
                ),
                "Relative Performance Score": round(
                    relative_performance_score,
                    2,
                ),
                "Statistical Score": round(
                    statistical_score,
                    2,
                ),
                "Quant Score": round(
                    quant_score,
                    2,
                ),
                "Signal": _signal(
                    quant_score
                ),
            }
        )

    return pd.DataFrame(rows)


def apply_quant_filters(
    df,
    signal="All",
    min_quant_score=0.0,
    min_momentum_score=0.0,
    min_trend_strength=0.0,
    min_statistical_score=0.0,
    min_relative_performance=-100.0,
    max_volatility_percentile=100.0,
    min_correlation=-1.0,
    max_correlation=1.0,
    mean_reversion_state="All",
):
    """
    Apply quantitative screening filters.
    """

    if df is None or df.empty:
        return pd.DataFrame(
            columns=df.columns
            if df is not None
            else []
        )

    out = df.copy()

    if signal != "All":
        out = out[
            out["Signal"] == signal
        ]

    if mean_reversion_state != "All":
        out = out[
            out["Mean Reversion State"]
            == mean_reversion_state
        ]

    out = out[
        out["Quant Score"]
        >= float(min_quant_score)
    ]

    out = out[
        out["Momentum Score"]
        >= float(min_momentum_score)
    ]

    out = out[
        out["Trend Strength"]
        >= float(min_trend_strength)
    ]

    out = out[
        out["Statistical Score"]
        >= float(min_statistical_score)
    ]

    out = out[
        out["Relative Performance %"]
        >= float(min_relative_performance)
    ]

    out = out[
        out["Volatility Percentile"]
        <= float(max_volatility_percentile)
    ]

    out = out[
        out["Correlation to Market"]
        >= float(min_correlation)
    ]

    out = out[
        out["Correlation to Market"]
        <= float(max_correlation)
    ]

    return out.reset_index(
        drop=True
    )


def rank_quant(df):
    """
    Rank symbols by Quant Score.

    Secondary ranking:
        Momentum Score
        Statistical Score
        Trend Strength
        Relative Performance Score
    """

    if df is None or df.empty:
        return pd.DataFrame(
            columns=df.columns
            if df is not None
            else []
        )

    return df.sort_values(
        by=[
            "Quant Score",
            "Momentum Score",
            "Statistical Score",
            "Trend Strength",
            "Relative Performance Score",
        ],
        ascending=[
            False,
            False,
            False,
            False,
            False,
        ],
        kind="mergesort",
    ).reset_index(
        drop=True
    )


def quant_summary(df):
    """
    Produce a quantitative market snapshot.
    """

    if df is None or df.empty:
        return {
            "Stocks": 0,
            "Bullish Signals": 0,
            "Bearish Signals": 0,
            "Average Momentum": 0.0,
            "Average Z-Score": 0.0,
            "Average Volatility": 0.0,
            "Average Correlation": 0.0,
            "Average Quant Score": 0.0,
            "Signal": "NEUTRAL",
        }

    bullish = int(
        df["Signal"].isin(
            [
                "BULLISH",
                "STRONG BULLISH",
            ]
        ).sum()
    )

    bearish = int(
        df["Signal"].isin(
            [
                "BEARISH",
                "STRONG BEARISH",
            ]
        ).sum()
    )

    score = _clamp(
        df["Quant Score"].mean()
    )

    if score >= 65:
        market_signal = "BULLISH"
    elif score >= 50:
        market_signal = "NEUTRAL"
    else:
        market_signal = "BEARISH"

    return {
        "Stocks": int(len(df)),
        "Bullish Signals": bullish,
        "Bearish Signals": bearish,
        "Average Momentum": round(
            df["Momentum 1M %"].mean(),
            2,
        ),
        "Average Z-Score": round(
            df["Z-Score"].mean(),
            2,
        ),
        "Average Volatility": round(
            df["Realized Volatility %"].mean(),
            2,
        ),
        "Average Correlation": round(
            df["Correlation to Market"].mean(),
            3,
        ),
        "Average Quant Score": round(
            score,
            2,
        ),
        "Signal": market_signal,
    }


def available_quant_signals():
    return [
        "All",
        "STRONG BULLISH",
        "BULLISH",
        "NEUTRAL",
        "BEARISH",
        "STRONG BEARISH",
    ]


def available_mean_reversion_states():
    return [
        "All",
        "OVERSOLD",
        "BELOW MEAN",
        "MEAN",
        "ABOVE MEAN",
        "OVERBOUGHT",
    ]