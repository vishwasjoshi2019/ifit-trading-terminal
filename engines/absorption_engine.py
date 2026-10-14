
import numpy as np
import pandas as pd

def detect_absorption_exhaustion(df, bars, spot, min_delta_ratio=1.8,
                                 exhaustion_window=3, price_tolerance=15):
    """
    Transparent prototype detector for absorption and exhaustion.

    Absorption:
      - unusually large aggressive delta/volume at a price/time level
      - while the corresponding bar closes without proportional follow-through.

    Exhaustion:
      - delta magnitude contracts for consecutive buckets near a local
        price extreme.

    This is an inference from simulated footprint statistics, not a claim
    about hidden dealer positioning.
    """
    x = df.copy()
    b = bars.copy()

    # Per-bar statistics.
    g = x.groupby("Bar")
    bar_stats = g.agg(
        Open=("Open", "first"),
        High=("High", "max"),
        Low=("Low", "min"),
        Close=("Close", "first"),
        Volume=("Total", "sum"),
        Delta=("Delta", "sum"),
        MaxAbsDelta=("Delta", lambda s: float(s.abs().max())),
        MaxPositiveDelta=("Delta", lambda s: float(s.max())),
        MaxNegativeDelta=("Delta", lambda s: float(s.min())),
        BuyImb=("Imbalance", lambda s: int((s == "BUY").sum())),
        SellImb=("Imbalance", lambda s: int((s == "SELL").sum())),
    ).reset_index()

    bar_stats["Range"] = (bar_stats["High"] - bar_stats["Low"]).clip(lower=1)
    bar_stats["Body"] = (bar_stats["Close"] - bar_stats["Open"]).abs()
    bar_stats["DeltaPerRange"] = bar_stats["Delta"].abs() / bar_stats["Range"]

    # Rolling baselines make the detector adaptive to the simulated sample.
    med_abs = bar_stats["MaxAbsDelta"].rolling(5, min_periods=2).median()
    med_abs = med_abs.fillna(bar_stats["MaxAbsDelta"].median()).replace(0, 1)

    bar_stats["DeltaSpike"] = bar_stats["MaxAbsDelta"] >= med_abs * min_delta_ratio

    # Absorption logic: large delta but small body relative to range.
    bar_stats["BuyAbsorption"] = (
        (bar_stats["MaxPositiveDelta"] >= med_abs * min_delta_ratio) &
        (bar_stats["Close"] <= bar_stats["High"] - bar_stats["Range"] * 0.35) &
        (bar_stats["Body"] <= bar_stats["Range"] * 0.45)
    )
    bar_stats["SellAbsorption"] = (
        (bar_stats["MaxNegativeDelta"].abs() >= med_abs * min_delta_ratio) &
        (bar_stats["Close"] >= bar_stats["Low"] + bar_stats["Range"] * 0.35) &
        (bar_stats["Body"] <= bar_stats["Range"] * 0.45)
    )

    # Exhaustion: absolute delta contracts for N buckets while price remains
    # close to the recent high/low.
    absd = bar_stats["MaxAbsDelta"]
    decline = absd < absd.shift(1)
    for i in range(1, exhaustion_window):
        decline = decline & (absd.shift(i) < absd.shift(i + 1))

    recent_high = bar_stats["High"].rolling(exhaustion_window, min_periods=1).max()
    recent_low = bar_stats["Low"].rolling(exhaustion_window, min_periods=1).min()

    bar_stats["BuyerExhaustion"] = (
        decline &
        (bar_stats["Close"] >= recent_high - price_tolerance) &
        (bar_stats["Delta"] >= 0)
    )
    bar_stats["SellerExhaustion"] = (
        decline &
        (bar_stats["Close"] <= recent_low + price_tolerance) &
        (bar_stats["Delta"] <= 0)
    )

    # Latest signal candidates.
    latest = bar_stats.iloc[-1]
    recent = bar_stats.tail(max(3, exhaustion_window))

    if bool(latest["BuyAbsorption"]):
        signal = "BUY ABSORPTION"
        interpretation = "Aggressive buying met resistance without proportional price follow-through."
    elif bool(latest["SellAbsorption"]):
        signal = "SELL ABSORPTION"
        interpretation = "Aggressive selling met support without proportional price follow-through."
    elif bool(latest["BuyerExhaustion"]):
        signal = "BUYER EXHAUSTION"
        interpretation = "Positive delta is contracting near a recent price high."
    elif bool(latest["SellerExhaustion"]):
        signal = "SELLER EXHAUSTION"
        interpretation = "Negative delta is contracting near a recent price low."
    else:
        signal = "NO MAJOR EVENT"
        interpretation = "No high-confidence absorption or exhaustion condition in the latest bucket."

    # Confidence is deliberately explainable and capped.
    confidence = 45
    if signal != "NO MAJOR EVENT":
        confidence += 15
        if latest["DeltaSpike"]:
            confidence += 15
        if latest["Body"] <= latest["Range"] * 0.30:
            confidence += 10
        if latest["BuyImb"] + latest["SellImb"] >= 3:
            confidence += 10
    confidence = int(max(0, min(100, confidence)))

    # Annotate the price-level rows for the latest bars.
    x["Event"] = ""
    latest_bar = int(latest["Bar"])
    if signal == "BUY ABSORPTION":
        candidates = x[(x["Bar"] == latest_bar) & (x["Delta"] > 0)]
        if len(candidates):
            x.loc[candidates["Delta"].abs().idxmax(), "Event"] = "BUY ABS"
    elif signal == "SELL ABSORPTION":
        candidates = x[(x["Bar"] == latest_bar) & (x["Delta"] < 0)]
        if len(candidates):
            x.loc[candidates["Delta"].abs().idxmax(), "Event"] = "SELL ABS"
    elif signal == "BUYER EXHAUSTION":
        candidates = x[x["Bar"].isin(recent["Bar"]) & (x["Delta"] > 0)]
        if len(candidates):
            x.loc[candidates["Delta"].abs().idxmax(), "Event"] = "BUY EXH"
    elif signal == "SELLER EXHAUSTION":
        candidates = x[x["Bar"].isin(recent["Bar"]) & (x["Delta"] < 0)]
        if len(candidates):
            x.loc[candidates["Delta"].abs().idxmax(), "Event"] = "SELL EXH"

    return x, bar_stats, {
        "signal": signal,
        "interpretation": interpretation,
        "confidence": confidence,
        "latest_bar": int(latest_bar),
        "latest_time": str(latest["Bar"]),
        "buy_absorption_bars": int(bar_stats["BuyAbsorption"].sum()),
        "sell_absorption_bars": int(bar_stats["SellAbsorption"].sum()),
        "buyer_exhaustion_bars": int(bar_stats["BuyerExhaustion"].sum()),
        "seller_exhaustion_bars": int(bar_stats["SellerExhaustion"].sum()),
    }
