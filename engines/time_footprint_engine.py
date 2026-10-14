
import numpy as np
import pandas as pd

def build_time_footprint(spot, periods=12, levels_per_bar=7, seed=5606):
    """
    Simulated time-based footprint.
    Each row is a price level inside a time bucket, with Bid x Ask,
    delta, cumulative delta, imbalance and OHLC-style bar context.
    """
    rng = np.random.default_rng(seed)
    periods = max(4, min(int(periods), 30))
    levels_per_bar = max(5, min(int(levels_per_bar), 11))

    base_time = pd.Timestamp("2026-09-11 09:15")
    rows = []
    prev_close = float(spot)

    for bar in range(periods):
        t = base_time + pd.Timedelta(minutes=bar)
        direction = rng.normal(0, 1)
        open_px = prev_close
        close_px = open_px + direction * 8 + rng.normal(0, 4)
        high_px = max(open_px, close_px) + abs(rng.normal(0, 7))
        low_px = min(open_px, close_px) - abs(rng.normal(0, 7))

        center = (open_px + close_px) / 2
        tick_prices = center + np.linspace(
            -levels_per_bar // 2, levels_per_bar // 2, levels_per_bar
        ) * 5

        for level, price in enumerate(tick_prices):
            # Aggression follows bar direction with random microstructure.
            directional_bias = direction * 0.16
            bid_base = rng.lognormal(4.7, 0.55)
            ask_base = rng.lognormal(4.7, 0.55)
            ask = ask_base * (1 + directional_bias)
            bid = bid_base * (1 - directional_bias)

            # Inject occasional strong imbalances.
            if rng.random() < 0.11:
                ask *= rng.uniform(1.8, 2.8)
            elif rng.random() < 0.11:
                bid *= rng.uniform(1.8, 2.8)

            bid = max(1, int(round(bid)))
            ask = max(1, int(round(ask)))
            delta = ask - bid
            ratio = max(ask / bid, bid / ask)

            rows.append({
                "Time": t.strftime("%H:%M"),
                "Bar": bar + 1,
                "Level": level + 1,
                "Price": int(round(price / 5) * 5),
                "Bid": bid,
                "Ask": ask,
                "Total": bid + ask,
                "Delta": delta,
                "Ratio": ratio,
                "Open": open_px,
                "High": high_px,
                "Low": low_px,
                "Close": close_px,
            })

        prev_close = close_px

    df = pd.DataFrame(rows)

    # Mark imbalances after all levels exist.
    df["Imbalance"] = ""
    df.loc[df["Ask"] >= df["Bid"] * 1.5, "Imbalance"] = "BUY"
    df.loc[df["Bid"] >= df["Ask"] * 1.5, "Imbalance"] = "SELL"

    # Stacked imbalance: same-side consecutive levels within a bar.
    stack_ids = []
    current = 0
    for bar, group in df.groupby("Bar", sort=False):
        prev = ""
        for idx in group.index:
            side = df.at[idx, "Imbalance"]
            if side and side == prev:
                stack_ids.append((idx, str(current)))
            elif side:
                current += 1
                stack_ids.append((idx, str(current)))
            prev = side

    df["Stack"] = ""
    for idx, sid in stack_ids:
        df.at[idx, "Stack"] = sid

    # CVD is time-ordered, then displayed by time.
    df["CVD"] = df["Delta"].cumsum()

    # Per-bar summary.
    summary = (
        df.groupby(["Bar", "Time"], as_index=False)
          .agg(
              Open=("Open", "first"),
              High=("High", "max"),
              Low=("Low", "min"),
              Close=("Close", "first"),
              Volume=("Total", "sum"),
              Delta=("Delta", "sum"),
              BuyImbalance=("Imbalance", lambda x: int((x == "BUY").sum())),
              SellImbalance=("Imbalance", lambda x: int((x == "SELL").sum())),
          )
    )
    summary["CVD"] = summary["Delta"].cumsum()

    return df, summary

def time_footprint_metrics(df, summary, spot, threshold=1.5):
    buy = int((df["Imbalance"] == "BUY").sum())
    sell = int((df["Imbalance"] == "SELL").sum())
    cvd = int(df["Delta"].sum())

    poc_row = df.loc[df["Total"].idxmax()]
    poc = float(poc_row["Price"])

    latest = summary.iloc[-1]
    first_close = float(summary.iloc[0]["Close"])
    last_close = float(summary.iloc[-1]["Close"])
    price_change = last_close - first_close

    if cvd > 0 and price_change > 0:
        regime = "BULLISH"
    elif cvd < 0 and price_change < 0:
        regime = "BEARISH"
    else:
        regime = "BALANCED"

    # Flow score: intentionally transparent prototype formula.
    score = 50
    score += 15 if cvd > 0 else -15 if cvd < 0 else 0
    score += 10 if buy > sell else -10 if sell > buy else 0
    score += 10 if price_change > 0 else -10 if price_change < 0 else 0
    score = int(max(0, min(100, score)))

    max_delta_idx = df["Delta"].abs().idxmax()
    max_delta = int(df.loc[max_delta_idx, "Delta"])
    max_delta_time = df.loc[max_delta_idx, "Time"]

    return {
        "bars": int(summary["Bar"].nunique()),
        "cvd": cvd,
        "poc": poc,
        "buy_imbalances": buy,
        "sell_imbalances": sell,
        "regime": regime,
        "flow_score": score,
        "price_change": price_change,
        "latest_time": str(latest["Time"]),
        "max_delta": max_delta,
        "max_delta_time": max_delta_time,
    }
