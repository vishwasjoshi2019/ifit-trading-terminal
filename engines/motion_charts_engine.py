"""
IFIT Motion Charts Engine V0.1
Simulation-first motion intelligence designed for integration with the existing CHT chart architecture.

Three motion layers:
1. Momentum Motion
2. Volatility Motion
3. Liquidity / Flow Motion

This engine produces normalized, timestamped observations suitable for
CHT rendering and later live tick/data-adapter integration.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_motion_data(periods: int = 120, seed: int = 42) -> pd.DataFrame:
    """Build deterministic simulation data for CHT Motion Charts."""
    if periods < 20:
        raise ValueError("periods must be at least 20")

    rng = np.random.default_rng(seed)
    idx = pd.date_range(
        end=pd.Timestamp.now().floor("min"),
        periods=periods,
        freq="min",
    )

    t = np.arange(periods, dtype=float)

    # Price path with changing trend/regime.
    trend = 0.00035 * t + 0.0025 * np.sin(t / 17.0)
    shock = rng.normal(0.0, 0.0012, periods)
    returns = trend + shock
    price = 25000.0 * np.exp(np.cumsum(returns))

    # Momentum and acceleration.
    price_series = pd.Series(price)
    momentum = price_series.pct_change(5).fillna(0.0) * 100.0
    momentum_acceleration = momentum.diff().fillna(0.0)
    momentum_velocity = momentum.diff(2).fillna(0.0)

    # Realized volatility and simulated IV.
    rv = price_series.pct_change().rolling(20).std().fillna(0.0) * np.sqrt(252 * 390) * 100.0
    iv = 11.5 + 1.8 * np.sin(t / 13.0) + np.abs(rng.normal(0, 0.55, periods))
    iv = np.maximum(iv, 7.0)
    iv_rv_spread = iv - rv

    # Flow / liquidity.
    volume = np.maximum(
        10000.0,
        85000.0
        + 18000.0 * np.sin(t / 9.0)
        + rng.normal(0, 9000, periods),
    )
    delta = (
        volume
        * (
            0.18 * np.sin(t / 8.0)
            + 0.07 * np.sin(t / 3.5)
            + rng.normal(0, 0.045, periods)
        )
    )
    delta_pct = np.divide(
        delta,
        volume,
        out=np.zeros_like(delta),
        where=volume != 0,
    ) * 100.0

    cvd = np.cumsum(delta)
    cvd_slope = pd.Series(cvd).diff(5).fillna(0.0)

    imbalance = np.clip(
        1.0
        + 0.55 * np.sin(t / 7.0)
        + rng.normal(0, 0.12, periods),
        0.35,
        2.5,
    )

    absorption = np.clip(
        50.0
        + 28.0 * np.sin(t / 11.0)
        + rng.normal(0, 10, periods),
        0.0,
        100.0,
    )

    liquidity_pressure = np.clip(
        50.0
        + delta_pct * 1.8
        + (imbalance - 1.0) * 22.0,
        0.0,
        100.0,
    )

    # Regime classification.
    momentum_regime = np.where(
        momentum > 0.15,
        "BULLISH",
        np.where(momentum < -0.15, "BEARISH", "NEUTRAL"),
    )
    volatility_regime = np.where(
        iv_rv_spread > 2.0,
        "IV PREMIUM",
        np.where(iv_rv_spread < -1.0, "RV PREMIUM", "BALANCED"),
    )
    flow_regime = np.where(
        liquidity_pressure > 60,
        "BUY PRESSURE",
        np.where(liquidity_pressure < 40, "SELL PRESSURE", "BALANCED"),
    )

    motion_score = np.clip(
        50.0
        + momentum * 35.0
        + momentum_acceleration * 18.0
        + delta_pct * 0.7
        + (imbalance - 1.0) * 12.0,
        0.0,
        100.0,
    )

    return pd.DataFrame(
        {
            "Timestamp": idx,
            "Price": np.round(price, 2),
            "Return %": np.round(returns * 100.0, 4),
            "Momentum %": np.round(momentum, 4),
            "Momentum Acceleration": np.round(momentum_acceleration, 4),
            "Momentum Velocity": np.round(momentum_velocity, 4),
            "RV %": np.round(rv, 4),
            "IV %": np.round(iv, 4),
            "IV-RV Spread": np.round(iv_rv_spread, 4),
            "Volume": np.round(volume, 0),
            "Delta": np.round(delta, 0),
            "Delta %": np.round(delta_pct, 4),
            "CVD": np.round(cvd, 0),
            "CVD Slope": np.round(cvd_slope, 0),
            "Imbalance": np.round(imbalance, 4),
            "Absorption": np.round(absorption, 2),
            "Liquidity Pressure": np.round(liquidity_pressure, 2),
            "Momentum Regime": momentum_regime,
            "Volatility Regime": volatility_regime,
            "Flow Regime": flow_regime,
            "Motion Score": np.round(motion_score, 2),
        }
    )


def build_momentum_motion(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return the Momentum Motion view from the shared motion dataset."""
    if df is None:
        df = build_motion_data()
    return df[
        [
            "Timestamp",
            "Price",
            "Momentum %",
            "Momentum Acceleration",
            "Momentum Velocity",
            "Momentum Regime",
            "Motion Score",
        ]
    ].copy()


def build_volatility_motion(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return the Volatility Motion view from the shared motion dataset."""
    if df is None:
        df = build_motion_data()
    return df[
        [
            "Timestamp",
            "Price",
            "RV %",
            "IV %",
            "IV-RV Spread",
            "Volatility Regime",
            "Motion Score",
        ]
    ].copy()


def build_liquidity_flow_motion(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return the Liquidity / Flow Motion view from the shared motion dataset."""
    if df is None:
        df = build_motion_data()
    return df[
        [
            "Timestamp",
            "Price",
            "Volume",
            "Delta",
            "Delta %",
            "CVD",
            "CVD Slope",
            "Imbalance",
            "Absorption",
            "Liquidity Pressure",
            "Flow Regime",
            "Motion Score",
        ]
    ].copy()


def motion_summary(df: pd.DataFrame | None = None) -> dict:
    """Produce compact summary metrics for the Motion Charts header."""
    if df is None:
        df = build_motion_data()

    latest = df.iloc[-1]
    return {
        "Observations": int(len(df)),
        "Last Price": round(float(latest["Price"]), 2),
        "Momentum": round(float(latest["Momentum %"]), 4),
        "Momentum Acceleration": round(float(latest["Momentum Acceleration"]), 4),
        "IV": round(float(latest["IV %"]), 4),
        "RV": round(float(latest["RV %"]), 4),
        "IV-RV Spread": round(float(latest["IV-RV Spread"]), 4),
        "Delta": round(float(latest["Delta"]), 0),
        "CVD": round(float(latest["CVD"]), 0),
        "Imbalance": round(float(latest["Imbalance"]), 4),
        "Absorption": round(float(latest["Absorption"]), 2),
        "Motion Score": round(float(latest["Motion Score"]), 2),
        "Momentum Regime": str(latest["Momentum Regime"]),
        "Volatility Regime": str(latest["Volatility Regime"]),
        "Flow Regime": str(latest["Flow Regime"]),
    }


def available_motion_views() -> list[str]:
    return [
        "Motion Overview",
        "Momentum Motion",
        "Volatility Motion",
        "Liquidity / Flow Motion",
    ]


def build_motion_snapshot(periods: int = 120, seed: int = 42) -> dict:
    df = build_motion_data(periods=periods, seed=seed)
    return {
        "data": df,
        "momentum": build_momentum_motion(df),
        "volatility": build_volatility_motion(df),
        "liquidity_flow": build_liquidity_flow_motion(df),
        "summary": motion_summary(df),
    }


__all__ = [
    "build_motion_data",
    "build_momentum_motion",
    "build_volatility_motion",
    "build_liquidity_flow_motion",
    "motion_summary",
    "available_motion_views",
    "build_motion_snapshot",
]
