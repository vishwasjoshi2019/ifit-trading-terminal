"""
IFIT V0.8.5 — Derivatives Screener Engine

Simulation-backed derivatives universe for the first Screener milestone.

Design principle:
    Simulation → Authorized live options/derivatives vendor

The normalized output contract is designed so the UI does not need to
change when simulation data is replaced by an authorized live feed.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class DerivativesScreenerConfig:
    symbol: str = "NIFTY"
    spot: float = 24782.35
    seed: int = 8505
    strikes_each_side: int = 15
    strike_step: int = 50


def _expiry_dates(days_forward: int = 90) -> list[date]:
    """
    Return upcoming Thursday expiries.
    """
    today = date.today()

    return [
        today + timedelta(days=d)
        for d in range(1, days_forward + 1)
        if (today + timedelta(days=d)).weekday() == 3
    ]


def _option_price(
    spot: float,
    strike: float,
    iv: float,
    dte: int,
    option_type: str,
    rng: np.random.Generator,
) -> float:
    """
    Lightweight simulation price model.

    This is intentionally not presented as a production pricing engine.
    Existing IFIT Greeks/model engines remain the source of truth for
    production calculations.
    """
    intrinsic = (
        max(spot - strike, 0.0)
        if option_type == "CE"
        else max(strike - spot, 0.0)
    )

    time_value = (
        spot
        * (iv / 100.0)
        * np.sqrt(max(dte, 1) / 365.0)
        * 0.40
    )

    noise = float(rng.normal(0, max(0.10, time_value * 0.04)))

    return max(0.05, intrinsic + time_value + noise)


def _delta(
    spot: float,
    strike: float,
    iv: float,
    dte: int,
    option_type: str,
) -> float:
    """
    Approximate option delta for screening purposes.
    """
    t = max(dte, 1) / 365.0
    sigma = max(iv / 100.0, 0.01)

    z = (spot - strike) / (spot * sigma * np.sqrt(t))

    call_delta = float(
        np.clip(
            0.5 + 0.38 * np.tanh(z * 1.25),
            0.01,
            0.99,
        )
    )

    if option_type == "CE":
        return call_delta

    return call_delta - 1.0


def _gamma(
    spot: float,
    strike: float,
    iv: float,
    dte: int,
) -> float:
    """
    Approximate positive gamma magnitude.
    """
    t = max(dte, 1) / 365.0
    sigma = max(iv / 100.0, 0.01)

    distance = abs(spot - strike) / max(
        spot * sigma * np.sqrt(t),
        1.0,
    )

    return float(
        max(
            0.00001,
            (0.0025 / (sigma * np.sqrt(t)))
            * np.exp(-0.5 * distance * distance),
        )
    )


def _vega(
    spot: float,
    iv: float,
    dte: int,
) -> float:
    """
    Approximate vega per 1 volatility point.
    """
    t = max(dte, 1) / 365.0
    sigma = max(iv / 100.0, 0.01)

    return float(
        spot
        * np.sqrt(t)
        * np.exp(-0.5 * sigma * sigma)
        * 0.01
    )


def _theta(
    option_price: float,
    dte: int,
) -> float:
    """
    Simple daily theta proxy.
    """
    return float(-option_price / max(dte, 1))


def classify_signal(
    option_type: str,
    oi_change_pct: float,
    price_change_pct: float,
) -> str:
    """
    Classify basic option positioning.

    Price ↑ + OI ↑ = Long Buildup
    Price ↓ + OI ↑ = Short Buildup
    Price ↑ + OI ↓ = Short Covering
    Price ↓ + OI ↓ = Long Unwinding
    """
    if oi_change_pct >= 0 and price_change_pct >= 0:
        return "LONG BUILDUP"

    if oi_change_pct >= 0 and price_change_pct < 0:
        return "SHORT BUILDUP"

    if oi_change_pct < 0 and price_change_pct >= 0:
        return "SHORT COVERING"

    return "LONG UNWINDING"


def build_derivatives_universe(
    config: Optional[DerivativesScreenerConfig] = None,
) -> pd.DataFrame:
    """
    Build deterministic simulated derivatives universe.

    Returns CE and PE contracts across multiple upcoming expiries.
    """
    config = config or DerivativesScreenerConfig()

    rng = np.random.default_rng(config.seed)

    expiries = _expiry_dates()

    if not expiries:
        raise RuntimeError("No upcoming expiry dates available.")

    rows = []

    atm_strike = round(
        config.spot / config.strike_step
    ) * config.strike_step

    strikes = [
        atm_strike + i * config.strike_step
        for i in range(
            -config.strikes_each_side,
            config.strikes_each_side + 1,
        )
    ]

    for expiry_index, expiry in enumerate(expiries[:4]):
        dte = max(
            (expiry - date.today()).days,
            1,
        )

        for strike in strikes:
            moneyness = abs(
                strike - config.spot
            ) / config.spot

            base_iv = (
                14.5
                + 2.5 * moneyness * 100
                + rng.normal(0, 0.25)
            )

            base_iv = float(
                np.clip(
                    base_iv,
                    10.0,
                    40.0,
                )
            )

            for option_type in ("CE", "PE"):
                iv = float(
                    np.clip(
                        base_iv
                        + (
                            0.35
                            if option_type == "PE"
                            else 0.0
                        )
                        + rng.normal(0, 0.15),
                        8.0,
                        50.0,
                    )
                )

                ltp = _option_price(
                    config.spot,
                    strike,
                    iv,
                    dte,
                    option_type,
                    rng,
                )

                previous_ltp = max(
                    0.05,
                    ltp
                    * (
                        1.0
                        + rng.normal(0, 0.08)
                    ),
                )

                oi = int(
                    rng.uniform(
                        50000,
                        3500000,
                    )
                    * (
                        1.8
                        if abs(
                            strike - atm_strike
                        ) <= config.strike_step
                        else 1.0
                    )
                )

                oi_change_pct = float(
                    np.clip(
                        rng.normal(0, 18),
                        -60,
                        80,
                    )
                )

                volume = int(
                    rng.uniform(
                        25000,
                        1800000,
                    )
                    * (
                        1.5
                        if abs(
                            strike - atm_strike
                        ) <= config.strike_step
                        else 1.0
                    )
                )

                price_change_pct = float(
                    (
                        (ltp - previous_ltp)
                        / previous_ltp
                    )
                    * 100
                )

                delta = _delta(
                    config.spot,
                    strike,
                    iv,
                    dte,
                    option_type,
                )

                gamma = _gamma(
                    config.spot,
                    strike,
                    iv,
                    dte,
                )

                vega = _vega(
                    config.spot,
                    iv,
                    dte,
                )

                theta = _theta(
                    ltp,
                    dte,
                )

                # Higher liquidity for higher volume/OI
                # and lower spread.
                spread_pct = float(
                    np.clip(
                        1.8
                        - np.log10(
                            max(volume, 1)
                        ) * 0.08
                        + rng.normal(0, 0.08),
                        0.20,
                        2.50,
                    )
                )

                # Raw liquidity factor.
                #
                # This intentionally remains unbounded here.
                # The complete universe is normalized to 0–100
                # after all contracts have been generated.
                liquidity_raw = (
                    np.log1p(volume) * 0.45
                    + np.log1p(oi) * 0.45
                    - spread_pct * 0.10
                    - (moneyness * 100) * 0.05
                )

                signal = classify_signal(
                    option_type,
                    oi_change_pct,
                    price_change_pct,
                )

                rows.append(
                    {
                        "Symbol": config.symbol,
                        "Expiry": expiry.strftime(
                            "%d %b %Y"
                        ),
                        "DTE": dte,
                        "Strike": strike,
                        "Option Type": option_type,
                        "Spot": round(
                            config.spot,
                            2,
                        ),
                        "LTP": round(
                            ltp,
                            2,
                        ),
                        "Price Change %": round(
                            price_change_pct,
                            2,
                        ),
                        "OI": oi,
                        "OI Change %": round(
                            oi_change_pct,
                            2,
                        ),
                        "Volume": volume,
                        "IV %": round(
                            iv,
                            2,
                        ),
                        "Delta": round(
                            delta,
                            4,
                        ),
                        "Gamma": round(
                            gamma,
                            6,
                        ),
                        "Vega": round(
                            vega,
                            2,
                        ),
                        "Theta/Day": round(
                            theta,
                            4,
                        ),
                        "Spread %": round(
                            spread_pct,
                            2,
                        ),
                        "Liquidity Score": liquidity_raw,
                        "Signal": signal,
                    }
                )

    df = pd.DataFrame(rows)

    # Normalize liquidity across the complete universe.
    #
    # This prevents the previous saturation problem where
    # almost every contract reached 100.
    if not df.empty:
        df["Liquidity Score"] = (
            df["Liquidity Score"]
            .rank(
                pct=True,
                method="average",
            )
            * 100
        ).round(2)

    return df


def apply_derivatives_filters(
    df: pd.DataFrame,
    filters: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Apply optional derivatives screening filters.

    Supported keys:

        option_type
        min_dte / max_dte
        min_strike / max_strike
        min_oi
        min_oi_change
        min_volume
        min_iv
        max_iv
        min_delta
        max_delta
        min_gamma
        min_vega
        max_theta
        min_liquidity
        max_spread
        signal
        expiry
    """
    result = df.copy()

    if not filters:
        return result.reset_index(
            drop=True
        )

    if filters.get("option_type"):
        result = result[
            result["Option Type"]
            == filters["option_type"]
        ]

    if filters.get("expiry"):
        result = result[
            result["Expiry"]
            == filters["expiry"]
        ]

    numeric_filters = {
        "DTE": (
            "min_dte",
            "max_dte",
        ),
        "Strike": (
            "min_strike",
            "max_strike",
        ),
        "OI": (
            "min_oi",
            None,
        ),
        "OI Change %": (
            "min_oi_change",
            None,
        ),
        "Volume": (
            "min_volume",
            None,
        ),
        "IV %": (
            "min_iv",
            "max_iv",
        ),
        "Delta": (
            "min_delta",
            "max_delta",
        ),
        "Gamma": (
            "min_gamma",
            None,
        ),
        "Vega": (
            "min_vega",
            None,
        ),
        "Theta/Day": (
            None,
            "max_theta",
        ),
        "Liquidity Score": (
            "min_liquidity",
            None,
        ),
        "Spread %": (
            None,
            "max_spread",
        ),
    }

    for column, (
        minimum_key,
        maximum_key,
    ) in numeric_filters.items():

        if (
            minimum_key
            and filters.get(minimum_key)
            is not None
        ):
            result = result[
                result[column]
                >= filters[minimum_key]
            ]

        if (
            maximum_key
            and filters.get(maximum_key)
            is not None
        ):
            result = result[
                result[column]
                <= filters[maximum_key]
            ]

    if filters.get("signal"):
        result = result[
            result["Signal"]
            == filters["signal"]
        ]

    return result.reset_index(
        drop=True
    )


def rank_derivatives(
    df: pd.DataFrame,
    column: str = "Liquidity Score",
    ascending: bool = False,
) -> pd.DataFrame:
    """
    Rank contracts by a selected field.
    """
    if column not in df.columns:
        raise ValueError(
            f"Unknown ranking column: {column}"
        )

    return (
        df.sort_values(
            column,
            ascending=ascending,
        )
        .reset_index(
            drop=True
        )
    )


def signal_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Summarize contract counts and average metrics
    by positioning signal.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "Signal",
                "Contracts",
                "Average OI Change %",
                "Average Volume",
                "Average IV %",
                "Average Liquidity",
            ]
        )

    return (
        df.groupby("Signal")
        .agg(
            Contracts=("Symbol", "count"),
            **{
                "Average OI Change %": (
                    "OI Change %",
                    "mean",
                ),
                "Average Volume": (
                    "Volume",
                    "mean",
                ),
                "Average IV %": (
                    "IV %",
                    "mean",
                ),
                "Average Liquidity": (
                    "Liquidity Score",
                    "mean",
                ),
            },
        )
        .reset_index()
        .sort_values(
            "Contracts",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )