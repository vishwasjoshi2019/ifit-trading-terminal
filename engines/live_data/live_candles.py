from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd


def _to_datetime(value: Any) -> pd.Timestamp | None:
    if value is None:
        return None
    try:
        if isinstance(value, pd.Timestamp):
            ts = value
        elif isinstance(value, datetime):
            ts = pd.Timestamp(value)
        elif isinstance(value, (int, float)):
            # Dhan timestamps may be epoch seconds or milliseconds.
            unit = "ms" if abs(float(value)) > 10_000_000_000 else "s"
            ts = pd.to_datetime(value, unit=unit, utc=True)
        else:
            ts = pd.to_datetime(value, utc=True)
        if pd.isna(ts):
            return None
        return ts
    except Exception:
        return None


def _tick_time(tick: Any) -> pd.Timestamp | None:
    ts = _to_datetime(getattr(tick, "last_trade_time", None))
    if ts is not None:
        return ts
    return _to_datetime(getattr(tick, "timestamp", None))


def _timeframe_rule(timeframe: str) -> str:
    return {
        "Intraday": "1min",
        "1 min": "1min",
        "5 min": "5min",
        "15 min": "15min",
        "1 hour": "1h",
        "Daily": "1D",
    }.get(str(timeframe), "1min")



def build_dhan_historical_ohlcv(candles: list[dict[str, Any]], bars: int = 180) -> pd.DataFrame:
    columns = [
        "Bar", "Open", "High", "Low", "Close", "Volume",
        "Buy Volume", "Sell Volume", "Delta", "CVD", "VWAP", "Timestamp",
    ]
    if not candles:
        return pd.DataFrame(columns=columns)

    rows = []
    for candle in candles:
        timestamp = _to_datetime(candle.get("timestamp"))
        if timestamp is None:
            continue
        rows.append({
"Timestamp": timestamp, "Open": candle.get("open"), "High": candle.get("high"), "Low": candle.get("low"), "Close": candle.get("close"), "Volume": candle.get("volume", 0), "Buy Volume": 0.0, "Sell Volume": 0.0 })

    if not rows:
        return pd.DataFrame(columns=columns)

    frame = pd.DataFrame(rows).sort_values("Timestamp")
    frame = frame.drop_duplicates("Timestamp", keep="last")

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")

    frame = frame.dropna(subset=["Open", "High", "Low", "Close"])
    frame["Volume"] = frame["Volume"].fillna(0.0).clip(lower=0.0)
    frame["Delta"] = frame["Buy Volume"] - frame["Sell Volume"]
    frame["CVD"] = frame["Delta"].cumsum()

    typical = (frame["High"] + frame["Low"] + frame["Close"]) / 3.0
    denominator = frame["Volume"].cumsum().replace(0, float("nan"))
    frame["VWAP"] = (typical * frame["Volume"]).cumsum() / denominator
    frame["VWAP"] = frame["VWAP"].fillna(frame["Close"])

    frame = frame.tail(int(max(1, bars))).reset_index(drop=True)
    frame["Bar"] = range(len(frame))
    return frame[columns]


def build_live_ohlcv(ticks: list[Any], timeframe: str = "Intraday", bars: int = 180) -> pd.DataFrame:
    """Build OHLCV candles from normalized live ticks only."""
    columns = [
        "Bar", "Open", "High", "Low", "Close", "Volume",
        "Buy Volume", "Sell Volume", "Delta", "CVD", "VWAP", "Timestamp",
    ]
    if not ticks:
        return pd.DataFrame(columns=columns)

    rows = []
    previous_cumulative_volume = None
    for tick in ticks:
        ts = _tick_time(tick)
        price = getattr(tick, "ltp", None)
        if ts is None or price is None:
            continue
        try:
            price = float(price)
        except Exception:
            continue
        if price <= 0:
            continue

        cumulative_volume = getattr(tick, "volume", None)
        try:
            cumulative_volume = float(cumulative_volume) if cumulative_volume is not None else None
        except Exception:
            cumulative_volume = None

        last_qty = getattr(tick, "last_quantity", None)
        if last_qty is None:
            last_qty = getattr(tick, "trade_qty", None)
        try:
            last_qty = float(last_qty) if last_qty is not None else 0.0
        except Exception:
            last_qty = 0.0

        if cumulative_volume is not None and previous_cumulative_volume is not None:
            volume_delta = max(cumulative_volume - previous_cumulative_volume, 0.0)
        else:
            volume_delta = max(last_qty, 0.0)
        if cumulative_volume is not None:
            previous_cumulative_volume = cumulative_volume

        rows.append({
            "timestamp": ts,
            "price": price,
            "volume": volume_delta,
            "buy_qty": getattr(tick, "buy_quantity", None),
            "sell_qty": getattr(tick, "sell_quantity", None),
        })

    if not rows:
        return pd.DataFrame(columns=columns)

    frame = pd.DataFrame(rows).sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    frame = frame.set_index("timestamp")
    rule = _timeframe_rule(timeframe)

    price_resampled = frame["price"].resample(rule)
    candles = pd.DataFrame({
        "Open": price_resampled.first(),
        "High": price_resampled.max(),
        "Low": price_resampled.min(),
        "Close": price_resampled.last(),
    })
    candles["Volume"] = frame["volume"].resample(rule).sum()

    buy = frame["buy_qty"].fillna(0).resample(rule).sum()
    sell = frame["sell_qty"].fillna(0).resample(rule).sum()
    candles["Buy Volume"] = buy
    candles["Sell Volume"] = sell

    # When explicit buy/sell quantities are unavailable, estimate directional
    # volume from candle movement rather than inventing trade-level data.
    fallback_delta = candles["Buy Volume"] - candles["Sell Volume"]
    candles["Delta"] = fallback_delta
    candles["CVD"] = candles["Delta"].cumsum()

    typical = (candles["High"] + candles["Low"] + candles["Close"]) / 3.0
    vwap_denominator = candles["Volume"].cumsum().replace(0, float("nan")); candles["VWAP"] = (typical * candles["Volume"]).cumsum() / vwap_denominator; candles["VWAP"] = candles["VWAP"].fillna(candles["Close"])

    candles = candles.dropna(subset=["Open", "High", "Low", "Close"])
    candles = candles.tail(int(max(1, bars))).reset_index()
    candles["Bar"] = range(len(candles))
    candles = candles.rename(columns={"timestamp": "Timestamp"})
    return candles[columns]
