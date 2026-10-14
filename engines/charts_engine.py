"""IFIT V0.8.3 — Professional Charts Workspace.

Chart-data and analytical helpers for the terminal chart workspace. All generated
series are deterministic simulation/proxy data unless an authorized provider
snapshot is supplied. The module contains no order-placement logic.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd


def build_option_ohlcv(
    underlying_spot: float,
    strike: float,
    option_type: str = 'CE',
    dte: int = 14,
    bars: int = 180,
    timeframe: str = 'Daily',
    seed: int = 42,
):
    """Build deterministic simulated/proxy OHLCV for an option contract."""

    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(seed)

    option_type = str(option_type).upper().strip()
    if option_type not in ('CE', 'PE'):
        option_type = 'CE'

    underlying_spot = float(underlying_spot)
    strike = float(strike)
    dte = max(int(dte), 1)
    bars = max(int(bars), 30)

    if option_type == 'CE':
        intrinsic = max(underlying_spot - strike, 0.0)
    else:
        intrinsic = max(strike - underlying_spot, 0.0)

    moneyness = abs(underlying_spot - strike) / max(underlying_spot, 1.0)

    time_value = max(
        underlying_spot * 0.008 * np.sqrt(dte / 30.0)
        * np.exp(-2.0 * moneyness),
        max(underlying_spot * 0.001, 1.0),
    )

    option_price = max(intrinsic + time_value, 1.0)

    shock = rng.normal(0.0, 0.006, bars)
    cumulative = np.cumsum(shock)
    underlying_path = underlying_spot * np.exp(
        cumulative - np.mean(cumulative)
    )

    if option_type == 'CE':
        intrinsic_path = np.maximum(underlying_path - strike, 0.0)
    else:
        intrinsic_path = np.maximum(strike - underlying_path, 0.0)

    distance = np.abs(underlying_path - strike) / np.maximum(
        underlying_path, 1.0
    )

    time_fraction = np.linspace(
        max(dte / 30.0, 1.0 / 365.0),
        1.0 / 365.0,
        bars,
    )

    tv_path = np.maximum(
        underlying_spot
        * 0.008
        * np.sqrt(time_fraction)
        * np.exp(-2.0 * distance),
        max(underlying_spot * 0.0008, 0.5),
    )

    close = np.maximum(intrinsic_path + tv_path, 0.5)
    close *= option_price / max(float(close[-1]), 0.01)
    close = np.maximum(
        close * (1.0 + rng.normal(0.0, 0.012, bars)),
        0.5,
    )

    open_ = np.roll(close, 1)
    open_[0] = close[0] * (1.0 + rng.normal(0.0, 0.008))

    high = np.maximum(open_, close) * (
        1.0 + np.abs(rng.normal(0.0, 0.008, bars))
    )

    low = np.minimum(open_, close) * (
        1.0 - np.abs(rng.normal(0.0, 0.008, bars))
    )

    volume_base = max(
        10000.0,
        250000.0 * np.exp(-3.0 * moneyness),
    )

    volume = np.maximum(
        volume_base * (1.0 + rng.normal(0.0, 0.25, bars)),
        100.0,
    ).astype(int)

    if timeframe == 'Intraday':
        freq = '15min'
    elif timeframe == '5 min':
        freq = '5min'
    elif timeframe == '15 min':
        freq = '15min'
    elif timeframe == '1 hour':
        freq = '1h'
    else:
        freq = '1D'

    idx = pd.date_range(
        end=pd.Timestamp.now().floor('min'),
        periods=bars,
        freq=freq,
    )

    # Match the analytical schema used by the existing CHT build_ohlcv()
    # pipeline so chart_snapshot(), CVD, Delta, VWAP and downstream
    # indicators can consume option contracts without special handling.
    buy_frac = np.clip(
        0.5
        + (close - open_)
        / np.maximum(high - low, 1e-9)
        * 0.22,
        0.08,
        0.92,
    )

    buy_volume = np.rint(volume * buy_frac).astype(int)
    sell_volume = volume - buy_volume

    delta = buy_volume - sell_volume
    cvd = np.cumsum(delta)

    typical = (high + low + close) / 3.0

    vwap = (
        np.cumsum(typical * volume)
        / np.maximum(np.cumsum(volume), 1)
    )

    return pd.DataFrame(
        {
            'Bar': np.arange(bars),
            'Open': open_,
            'High': high,
            'Low': low,
            'Close': close,
            'Volume': volume,
            'Buy Volume': buy_volume,
            'Sell Volume': sell_volume,
            'Delta': delta,
            'CVD': cvd,
            'VWAP': vwap,
        },
        index=idx,
    )


def build_ohlcv(spot: float, bars: int = 180, timeframe: str = "Intraday") -> pd.DataFrame:
    """Create deterministic OHLCV proxy bars for the chart workspace."""
    bars = int(np.clip(bars, 30, 500))
    seed = 8300 + sum(ord(c) for c in str(timeframe))
    rng = np.random.default_rng(seed)
    # Slightly different volatility by timeframe keeps the demo visually useful.
    vol = {"Intraday": .0017, "5 min": .0012, "15 min": .0017, "1 hour": .0026, "Daily": .0065}.get(timeframe, .0017)
    drift = {"Intraday": -.00005, "5 min": -.00002, "15 min": .00002, "1 hour": .00004, "Daily": .00012}.get(timeframe, 0.0)
    ret = rng.normal(drift, vol, bars)
    close = float(spot) * np.exp(np.cumsum(ret))
    open_ = np.r_[close[0] * (1 + rng.normal(0, vol / 3)), close[:-1]]
    spread = rng.uniform(.00035, .0018, bars)
    high = np.maximum(open_, close) * (1 + spread)
    low = np.minimum(open_, close) * (1 - spread)
    volume = rng.integers(1200, 12000, bars).astype(float)
    # Add deterministic participation clusters.
    for idx in (bars // 3, bars // 2, int(bars * .78)):
        lo, hi = max(0, idx - 2), min(bars, idx + 3)
        volume[lo:hi] *= rng.uniform(1.4, 2.2)
    volume = np.rint(volume).astype(int)
    buy_frac = np.clip(.5 + (close - open_) / np.maximum(high - low, 1e-9) * .22, .08, .92)
    buy_volume = np.rint(volume * buy_frac).astype(int)
    sell_volume = volume - buy_volume
    delta = buy_volume - sell_volume
    cvd = np.cumsum(delta)
    typical = (high + low + close) / 3.0
    vwap = np.cumsum(typical * volume) / np.maximum(np.cumsum(volume), 1)
    return pd.DataFrame({
        "Bar": np.arange(bars), "Open": open_, "High": high, "Low": low,
        "Close": close, "Volume": volume, "Buy Volume": buy_volume,
        "Sell Volume": sell_volume, "Delta": delta, "CVD": cvd, "VWAP": vwap,
    })


def build_volume_profile(ohlcv: pd.DataFrame, bins: int = 30) -> pd.DataFrame:
    """Approximate volume-at-price profile from OHLCV bars."""
    if ohlcv is None or ohlcv.empty:
        return pd.DataFrame(columns=["Price", "Volume"])
    bins = int(np.clip(bins, 10, 80))
    lo = float(ohlcv["Low"].min())
    hi = float(ohlcv["High"].max())
    if not math.isfinite(lo) or not math.isfinite(hi) or hi <= lo:
        return pd.DataFrame(columns=["Price", "Volume"])
    edges = np.linspace(lo, hi, bins + 1)
    centers = (edges[:-1] + edges[1:]) / 2
    profile = np.zeros(bins)
    for _, row in ohlcv.iterrows():
        a, b = float(row["Low"]), float(row["High"])
        mask = (centers >= a) & (centers <= b)
        count = int(mask.sum())
        if count:
            profile[mask] += float(row["Volume"]) / count
        else:
            idx = int(np.clip(np.searchsorted(edges, float(row["Close"])) - 1, 0, bins - 1))
            profile[idx] += float(row["Volume"])
    out = pd.DataFrame({"Price": centers, "Volume": profile})
    return out.sort_values("Price").reset_index(drop=True)


def profile_levels(profile: pd.DataFrame, value_area: float = .70) -> dict:
    if profile is None or profile.empty:
        return {"poc": math.nan, "vah": math.nan, "val": math.nan}
    p = profile.sort_values("Volume", ascending=False).reset_index(drop=True)
    total = float(p["Volume"].sum())
    target = total * float(value_area)
    used = 0.0
    selected = []
    for i, row in p.iterrows():
        selected.append(i)
        used += float(row["Volume"])
        if used >= target:
            break
    area = p.loc[selected]
    poc = float(p.iloc[0]["Price"])
    return {"poc": poc, "vah": float(area["Price"].max()), "val": float(area["Price"].min())}


def chart_snapshot(ohlcv: pd.DataFrame, profile: pd.DataFrame, spot: float) -> dict:
    levels = profile_levels(profile)
    last = ohlcv.iloc[-1]
    price_change = float(last["Close"] - ohlcv.iloc[0]["Open"])
    delta = float(ohlcv["Delta"].sum())
    cvd_change = float(ohlcv["CVD"].iloc[-1] - ohlcv["CVD"].iloc[0])
    above_vwap = float(last["Close"]) >= float(last["VWAP"])
    structure = "BULLISH" if price_change > 0 and cvd_change >= 0 else "BEARISH" if price_change < 0 and cvd_change <= 0 else "MIXED"
    return {
        "last": float(last["Close"]), "change": price_change,
        "change_pct": price_change / max(abs(float(ohlcv.iloc[0]["Open"])), 1e-9) * 100,
        "delta": delta, "cvd": cvd_change, "vwap": float(last["VWAP"]),
        "above_vwap": above_vwap, "structure": structure,
        **levels,
        "distance_to_poc": float(last["Close"] - levels["poc"]) if math.isfinite(levels["poc"]) else math.nan,
        "spot": float(spot),
    }
