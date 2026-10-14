"""
IFIT V0.8.5 — Order Flow Screener Engine

Simulation-backed order-flow intelligence engine.

Core dimensions:
    CVD
    Delta
    Volume Imbalance
    Absorption
    Volume Profile / POC
    Buy/Sell Pressure
    Order Flow Score
    Order Flow Signal

The normalized output is designed so an authorized live
market-data adapter can replace simulation later without
changing the screening contract.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class OrderFlowScreenerConfig:
    seed: int = 8507
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
        return "STRONG BUY"
    if score >= 65:
        return "BUY"
    if score >= 50:
        return "NEUTRAL"
    if score >= 35:
        return "SELL"
    return "STRONG SELL"


def _pressure_label(delta_pct):
    if delta_pct >= 20:
        return "STRONG BUY PRESSURE"
    if delta_pct >= 8:
        return "BUY PRESSURE"
    if delta_pct <= -20:
        return "STRONG SELL PRESSURE"
    if delta_pct <= -8:
        return "SELL PRESSURE"
    return "BALANCED"


def _absorption_label(absorption):
    if absorption >= 75:
        return "HIGH ABSORPTION"
    if absorption >= 55:
        return "MODERATE ABSORPTION"
    return "LOW ABSORPTION"


def build_orderflow_universe(config=None):
    """
    Build the normalized order-flow screener universe.

    Output fields:
        Market
        Symbol
        Price
        Price Change %
        Volume
        CVD
        CVD Change %
        Delta
        Delta %
        Buy Volume
        Sell Volume
        Imbalance %
        Absorption Score
        Volume Profile Score
        POC Distance %
        Buy Pressure
        Sell Pressure
        Order Flow Score
        Signal
    """

    config = config or OrderFlowScreenerConfig()
    rng = np.random.default_rng(config.seed)

    rows = []

    for symbol in SYMBOLS:

        price = float(
            rng.uniform(500, 4500)
        )

        price_change = float(
            rng.normal(0, 1.8)
        )

        volume = int(
            rng.integers(
                300_000,
                8_500_000,
            )
        )

        delta_pct = float(
            np.clip(
                rng.normal(0, 18),
                -65,
                65,
            )
        )

        delta = int(
            volume * delta_pct / 100
        )

        buy_volume = int(
            max(
                volume * (0.50 + delta_pct / 200),
                0,
            )
        )

        sell_volume = int(
            max(
                volume - buy_volume,
                0,
            )
        )

        imbalance_pct = float(
            np.clip(
                delta_pct * 0.85
                + rng.normal(0, 7),
                -90,
                90,
            )
        )

        cvd_change = float(
            np.clip(
                delta_pct
                + rng.normal(0, 12),
                -80,
                80,
            )
        )

        cvd = int(
            rng.normal(
                loc=delta * 7,
                scale=max(volume * 1.2, 1),
            )
        )

        absorption_score = _clamp(
            50
            + abs(delta_pct) * 0.55
            + abs(imbalance_pct) * 0.20
            + rng.normal(0, 12)
        )

        volume_profile_score = _clamp(
            50
            + abs(imbalance_pct) * 0.25
            + rng.normal(0, 14)
        )

        poc_distance = float(
            np.clip(
                rng.normal(
                    0,
                    1.8,
                ),
                -7,
                7,
            )
        )

        buy_pressure = _clamp(
            50
            + delta_pct * 0.95
            + imbalance_pct * 0.30
            + rng.normal(0, 7)
        )

        sell_pressure = _clamp(
            50
            - delta_pct * 0.95
            - imbalance_pct * 0.30
            + rng.normal(0, 7)
        )

        orderflow_score = _clamp(
            buy_pressure * 0.28
            + (100 - sell_pressure) * 0.22
            + _clamp(
                50 + cvd_change * 0.60
            ) * 0.18
            + _clamp(
                50 + imbalance_pct * 0.40
            ) * 0.12
            + volume_profile_score * 0.10
            + (100 - absorption_score) * 0.05
            + _clamp(
                50 + price_change * 6
            ) * 0.05
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
                "Volume": volume,
                "CVD": cvd,
                "CVD Change %": round(
                    cvd_change,
                    2,
                ),
                "Delta": delta,
                "Delta %": round(
                    delta_pct,
                    2,
                ),
                "Buy Volume": buy_volume,
                "Sell Volume": sell_volume,
                "Imbalance %": round(
                    imbalance_pct,
                    2,
                ),
                "Absorption Score": round(
                    absorption_score,
                    2,
                ),
                "Volume Profile Score": round(
                    volume_profile_score,
                    2,
                ),
                "POC Distance %": round(
                    poc_distance,
                    2,
                ),
                "Buy Pressure": round(
                    buy_pressure,
                    2,
                ),
                "Sell Pressure": round(
                    sell_pressure,
                    2,
                ),
                "Order Flow Score": round(
                    orderflow_score,
                    2,
                ),
                "Signal": _signal(
                    orderflow_score
                ),
            }
        )

    return pd.DataFrame(rows)


def apply_orderflow_filters(
    df,
    signal="All",
    min_score=0.0,
    min_delta_pct=-100.0,
    max_delta_pct=100.0,
    min_imbalance=-100.0,
    max_imbalance=100.0,
    min_absorption=0.0,
    max_poc_distance=100.0,
):
    """
    Apply order-flow screening filters.
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

    out = out[
        out["Order Flow Score"]
        >= float(min_score)
    ]

    out = out[
        out["Delta %"]
        >= float(min_delta_pct)
    ]

    out = out[
        out["Delta %"]
        <= float(max_delta_pct)
    ]

    out = out[
        out["Imbalance %"]
        >= float(min_imbalance)
    ]

    out = out[
        out["Imbalance %"]
        <= float(max_imbalance)
    ]

    out = out[
        out["Absorption Score"]
        >= float(min_absorption)
    ]

    out = out[
        out["POC Distance %"].abs()
        <= float(max_poc_distance)
    ]

    return out.reset_index(
        drop=True
    )


def rank_orderflow(df):
    """
    Rank symbols by Order Flow Score.

    Secondary ranking:
        CVD Change %
        Delta %
        Imbalance %
        Buy Pressure
    """

    if df is None or df.empty:
        return pd.DataFrame(
            columns=df.columns
            if df is not None
            else []
        )

    return df.sort_values(
        by=[
            "Order Flow Score",
            "CVD Change %",
            "Delta %",
            "Imbalance %",
            "Buy Pressure",
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


def orderflow_summary(df):
    """
    Produce an order-flow market snapshot.
    """

    if df is None or df.empty:
        return {
            "Stocks": 0,
            "Buy Signals": 0,
            "Sell Signals": 0,
            "Average Delta %": 0.0,
            "Average Imbalance %": 0.0,
            "Average Absorption": 0.0,
            "Average CVD Change %": 0.0,
            "Average Order Flow Score": 0.0,
            "Signal": "NEUTRAL",
        }

    buy_signals = int(
        df["Signal"].isin(
            ["BUY", "STRONG BUY"]
        ).sum()
    )

    sell_signals = int(
        df["Signal"].isin(
            ["SELL", "STRONG SELL"]
        ).sum()
    )

    score = _clamp(
        df["Order Flow Score"].mean()
    )

    return {
        "Stocks": int(len(df)),
        "Buy Signals": buy_signals,
        "Sell Signals": sell_signals,
        "Average Delta %": round(
            df["Delta %"].mean(),
            2,
        ),
        "Average Imbalance %": round(
            df["Imbalance %"].mean(),
            2,
        ),
        "Average Absorption": round(
            df["Absorption Score"].mean(),
            2,
        ),
        "Average CVD Change %": round(
            df["CVD Change %"].mean(),
            2,
        ),
        "Average Order Flow Score": round(
            score,
            2,
        ),
        "Signal": _signal(score),
    }


def available_orderflow_signals():
    return [
        "All",
        "STRONG BUY",
        "BUY",
        "NEUTRAL",
        "SELL",
        "STRONG SELL",
    ]