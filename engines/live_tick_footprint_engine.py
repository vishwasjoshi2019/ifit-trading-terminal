from __future__ import annotations

from collections import defaultdict
import math
from typing import Iterable
import pandas as pd

REQUIRED_COLUMNS = ["Bar", "Price", "Bid Volume", "Ask Volume", "Total Volume", "Delta"]


def _safe_float(value, default=None):
    try:
        if value is None:
            return default
        value = float(value)
        if not math.isfinite(value):
            return default
        return value
    except (TypeError, ValueError, OverflowError):
        return default


def _floor_price(price, tick_size):
    return round(math.floor((price / tick_size) + 1e-9) * tick_size, 10)


def build_live_tick_footprint(ticks: Iterable, tick_size: float = 0.05, bars: int = 60):
    """Build a real Dhan tick-derived 1-minute price-level footprint.

    Dhan does not expose a per-trade aggressor flag in the retained tick.
    Side is therefore inferred with the tick rule: price up = BUY/Ask,
    price down = SELL/Bid, unchanged = previous classified side.
    """
    tick_size = _safe_float(tick_size, 0.05)
    if tick_size is None or tick_size <= 0:
        tick_size = 0.05
    bars = max(int(bars), 1)

    prepared = []
    for tick in ticks or []:
        price = _safe_float(getattr(tick, "ltp", None))
        qty = _safe_float(getattr(tick, "last_quantity", None), 0.0)
        ts = getattr(tick, "last_trade_time", None)
        if price is None or price <= 0 or qty is None or qty <= 0 or ts is None:
            continue
        try:
            ts = pd.Timestamp(ts)
            if ts.tzinfo is None:
                ts = ts.tz_localize("UTC")
            else:
                ts = ts.tz_convert("UTC")
        except Exception:
            continue
        prepared.append((ts, price, qty))

    if not prepared:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    prepared.sort(key=lambda x: x[0])
    previous_price = None
    previous_side = None
    rows = []

    for ts, price, qty in prepared:
        if previous_price is None:
            side = None
        elif price > previous_price:
            side = "BUY"
        elif price < previous_price:
            side = "SELL"
        else:
            side = previous_side
        previous_price = price
        previous_side = side
        if side is None:
            continue
        bucket = ts.floor("1min")
        level = _floor_price(price, tick_size)
        rows.append((bucket, level, qty, side))

    if not rows:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    latest_bucket = max(row[0] for row in rows)
    first_bucket = latest_bucket - pd.Timedelta(minutes=bars - 1)
    grouped = defaultdict(lambda: {"Bid Volume": 0.0, "Ask Volume": 0.0})

    for bucket, level, qty, side in rows:
        if bucket < first_bucket or bucket > latest_bucket:
            continue
        key = (bucket, level)
        if side == "BUY":
            grouped[key]["Ask Volume"] += qty
        else:
            grouped[key]["Bid Volume"] += qty

    buckets = sorted({key[0] for key in grouped})
    bar_map = {bucket: i for i, bucket in enumerate(buckets)}
    output = []

    for (bucket, price), values in sorted(grouped.items(), key=lambda x: (x[0][0], x[0][1])):
        bid = float(values["Bid Volume"])
        ask = float(values["Ask Volume"])
        output.append({"Bar": int(bar_map[bucket]), "Price": float(price), "Bid Volume": bid, "Ask Volume": ask, "Total Volume": bid + ask, "Delta": ask - bid})

    return pd.DataFrame(output, columns=REQUIRED_COLUMNS)
