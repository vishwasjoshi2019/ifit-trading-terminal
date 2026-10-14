import numpy as np
import pandas as pd


def build_footprint_data(periods=60, levels=24, seed=42, start_price=25000.0):
    rng = np.random.default_rng(seed)
    rows = []
    base_time = pd.Timestamp.now().floor("min") - pd.Timedelta(minutes=periods)
    price = float(start_price)
    cvd = 0.0

    for bar in range(periods):
        ts = base_time + pd.Timedelta(minutes=bar)
        bar_move = rng.normal(0.0, 32.0)
        close = max(100.0, price + bar_move)
        low = min(price, close) - abs(rng.normal(0, 10))
        high = max(price, close) + abs(rng.normal(0, 10))
        levels_price = np.linspace(low, high, levels)

        total_bar_volume = int(rng.integers(90000, 180000))
        bar_delta = int(rng.normal(0, total_bar_volume * 0.16))
        bar_delta = max(-int(total_bar_volume * 0.65),
                        min(int(total_bar_volume * 0.65), bar_delta))
        cvd += bar_delta

        weights = rng.random(levels) + 0.2
        weights = weights / weights.sum()
        level_volumes = np.maximum(1, (weights * total_bar_volume).astype(int))
        level_deltas = np.array([
            int(rng.normal(bar_delta / levels,
                           max(50, abs(bar_delta) / levels + 150)))
            for _ in range(levels)
        ])
        level_deltas = level_deltas - int(
            (level_deltas.sum() - bar_delta) / levels
        )

        poc_idx = int(np.argmax(level_volumes))
        poc_price = float(levels_price[poc_idx])

        volume_p70 = np.percentile(level_volumes, 70)
        volume_p75 = np.percentile(level_volumes, 75)
        volume_p90 = np.percentile(level_volumes, 90)
        volume_p20 = np.percentile(level_volumes, 20)
        volume_p45 = np.percentile(level_volumes, 45)

        for i, px in enumerate(levels_price):
            total = int(level_volumes[i])
            delta = int(level_deltas[i])
            ask = max(1, int((total + delta) / 2))
            bid = max(1, total - ask)
            total = bid + ask
            delta = ask - bid
            delta_pct = delta / total * 100.0
            ratio = ask / bid if bid else float(ask)
            imbalance = max(ratio, 1.0 / ratio)

            rows.append({
                "Timestamp": ts,
                "Bar": bar + 1,
                "Price": round(float(px), 2),
                "Bid Volume": bid,
                "Ask Volume": ask,
                "Total Volume": total,
                "Delta": delta,
                "Delta %": round(delta_pct, 2),
                "Trade Count": int(max(1, total / rng.integers(80, 160))),
                "Buy/Sell Ratio": round(ratio, 3),
                "POC": poc_price,
                "Max Bid": bid >= int(total * 0.72),
                "Max Ask": ask >= int(total * 0.72),
                "Bid/Ask Imbalance": round(imbalance, 3),
                "Stacked Imbalance": imbalance >= 3.0,
                "Absorption": bool(
                    abs(delta) < total * 0.08 and total > volume_p70
                ),
                "Exhaustion": bool(
                    total < volume_p20 and abs(delta_pct) > 55
                ),
                "Delta Flip": bool(
                    i > 0
                    and np.sign(delta) != np.sign(level_deltas[i - 1])
                    and abs(delta) > 100
                ),
                "Failed Auction": bool(
                    i in (0, levels - 1)
                    and abs(delta_pct) > 45
                    and total < volume_p45
                ),
                "HVN": total >= volume_p75,
                "LVN": total <= volume_p20,
                "Volume Acceleration": round(float(rng.normal(0, 18)), 2),
                "Delta Acceleration": round(float(rng.normal(0, 12)), 2),
                "Relative Volume": round(
                    total / max(1, total_bar_volume / levels), 2
                ),
                "CVD": round(cvd, 2),
                "CVD Divergence": bool(
                    (close > price and bar_delta < 0)
                    or (close < price and bar_delta > 0)
                ),
                "Large Print": total >= volume_p90,
                "Aggression Pressure": round(
                    (ask - bid) / total * 100, 2
                ),
            })

        price = close

    return pd.DataFrame(rows)


def build_bar_footprint(periods=60, levels=24, seed=42):
    df = build_footprint_data(
        periods=periods, levels=levels, seed=seed
    )

    grouped = df.groupby(
        ["Timestamp", "Bar"], as_index=False
    ).agg(
        Price=("Price", "mean"),
        Bid_Volume=("Bid Volume", "sum"),
        Ask_Volume=("Ask Volume", "sum"),
        Total_Volume=("Total Volume", "sum"),
        Delta=("Delta", "sum"),
        Trade_Count=("Trade Count", "sum"),
        POC=("POC", "first"),
        Absorption=("Absorption", "sum"),
        Exhaustion=("Exhaustion", "sum"),
        Stacked_Imbalance=("Stacked Imbalance", "sum"),
        Large_Print=("Large Print", "sum"),
        Volume_Acceleration=("Volume Acceleration", "mean"),
        Delta_Acceleration=("Delta Acceleration", "mean"),
        Relative_Volume=("Relative Volume", "mean"),
        CVD=("CVD", "last"),
        CVD_Divergence=("CVD Divergence", "max"),
        Aggression_Pressure=("Aggression Pressure", "mean"),
    )

    grouped["Delta %"] = (
        grouped["Delta"] / grouped["Total_Volume"] * 100
    )
    grouped["Buy/Sell Ratio"] = (
        grouped["Ask_Volume"]
        / grouped["Bid_Volume"].replace(0, 1)
    )
    grouped["POC Migration"] = grouped["POC"].diff().fillna(0.0)

    grouped["Order Flow Score"] = np.clip(
        50
        + grouped["Delta %"].abs() * 0.35
        + grouped["Aggression_Pressure"].abs() * 0.20
        + grouped["Relative_Volume"].clip(0, 4) * 8
        + grouped["Stacked_Imbalance"] * 1.5
        + grouped["Large_Print"] * 1.0
        - grouped["Absorption"] * 0.5,
        0,
        100,
    )

    return grouped


def aggregate_footprint(df, timeframe="1m"):
    minutes = {
        "1m": 1, "3m": 3, "5m": 5, "15m": 15,
        "30m": 30, "1H": 60, "2H": 120, "Daily": 1440,
    }

    if timeframe not in minutes:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    if timeframe == "1m":
        return df.copy()

    out = df.copy()
    out["Group"] = ((out["Bar"] - 1) // minutes[timeframe]).astype(int)

    result = out.groupby("Group", as_index=False).agg(
        Timestamp=("Timestamp", "first"),
        Price=("Price", "last"),
        Bid_Volume=("Bid Volume", "sum"),
        Ask_Volume=("Ask Volume", "sum"),
        Total_Volume=("Total Volume", "sum"),
        Delta=("Delta", "sum"),
        Trade_Count=("Trade Count", "sum"),
        POC=("POC", "last"),
        Absorption=("Absorption", "sum"),
        Exhaustion=("Exhaustion", "sum"),
        Stacked_Imbalance=("Stacked Imbalance", "sum"),
        Large_Print=("Large Print", "sum"),
        CVD=("CVD", "last"),
        Relative_Volume=("Relative Volume", "mean"),
        Aggression_Pressure=("Aggression Pressure", "mean"),
    )

    result["Delta %"] = (
        result["Delta"] / result["Total_Volume"] * 100
    )
    result["Buy/Sell Ratio"] = (
        result["Ask_Volume"]
        / result["Bid_Volume"].replace(0, 1)
    )
    result["POC Migration"] = result["POC"].diff().fillna(0.0)

    return result.drop(columns=["Group"], errors="ignore")


def footprint_summary(df):
    bars = build_bar_footprint(
        periods=max(1, int(df["Bar"].max()))
    )
    latest = bars.iloc[-1]

    return {
        "Bars": int(len(bars)),
        "Price Levels": int(df["Price"].nunique()),
        "Total Volume": int(df["Total Volume"].sum()),
        "Delta": int(df["Delta"].sum()),
        "CVD": float(df["CVD"].iloc[-1]),
        "POC": float(latest["POC"]),
        "Buy/Sell Ratio": float(latest["Buy/Sell Ratio"]),
        "Absorption Events": int(df["Absorption"].sum()),
        "Exhaustion Events": int(df["Exhaustion"].sum()),
        "Stacked Imbalances": int(df["Stacked Imbalance"].sum()),
        "Large Prints": int(df["Large Print"].sum()),
        "Order Flow Score": float(latest["Order Flow Score"]),
    }


def available_footprint_timeframes():
    return [
        "1m", "3m", "5m", "15m",
        "30m", "1H", "2H", "Daily"
    ]


def build_footprint_snapshot(periods=60, levels=24, seed=42):
    df = build_footprint_data(
        periods=periods, levels=levels, seed=seed
    )
    return {
        "data": df,
        "bars": build_bar_footprint(
            periods=periods, levels=levels, seed=seed
        ),
        "summary": footprint_summary(df),
    }
