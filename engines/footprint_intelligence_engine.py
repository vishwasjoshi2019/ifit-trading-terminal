import numpy as np
import pandas as pd


def classify_footprint_intelligence(df):
    out = df.copy()

    out["Imbalance Signal"] = np.select(
        [
            out["Bid/Ask Imbalance"] >= 3.0,
            out["Bid/Ask Imbalance"] >= 2.0,
        ],
        ["STRONG", "MODERATE"],
        default="NORMAL",
    )

    out["Dominant Side"] = np.where(
        out["Delta"] > 0, "BUYERS",
        np.where(out["Delta"] < 0, "SELLERS", "BALANCED")
    )

    out["Absorption Signal"] = np.where(
        out["Absorption"], "ABSORPTION", "NONE"
    )
    out["Exhaustion Signal"] = np.where(
        out["Exhaustion"], "EXHAUSTION", "NONE"
    )
    out["Large Print Signal"] = np.where(
        out["Large Print"], "LARGE PRINT", "NONE"
    )

    out["Auction Signal"] = np.select(
        [
            out["Failed Auction"],
            out["Delta Flip"],
            out["CVD Divergence"],
        ],
        [
            "FAILED AUCTION",
            "DELTA FLIP",
            "CVD DIVERGENCE",
        ],
        default="NORMAL",
    )

    pressure = out["Aggression Pressure"]
    out["Aggression State"] = np.select(
        [
            pressure >= 25,
            pressure <= -25,
        ],
        ["BUY AGGRESSION", "SELL AGGRESSION"],
        default="BALANCED",
    )

    out["Footprint Intelligence Score"] = np.clip(
        50
        + out["Delta %"].abs() * 0.30
        + out["Aggression Pressure"].abs() * 0.25
        + out["Bid/Ask Imbalance"].clip(1, 5) * 5
        + out["Stacked Imbalance"] * 3
        + out["Large Print"] * 3
        + out["Absorption"] * 2
        + out["Exhaustion"] * 1
        - out["Failed Auction"] * 2,
        0,
        100,
    ).round(2)

    out["Intelligence State"] = np.select(
        [
            out["Footprint Intelligence Score"] >= 75,
            out["Footprint Intelligence Score"] >= 60,
            out["Footprint Intelligence Score"] >= 40,
        ],
        ["HIGH CONVICTION FLOW", "ACTIVE FLOW", "MIXED FLOW"],
        default="LOW CONVICTION FLOW",
    )

    return out


def footprint_intelligence_summary(df):
    out = classify_footprint_intelligence(df)
    latest = out.iloc[-1]

    return {
        "Score": float(latest["Footprint Intelligence Score"]),
        "State": latest["Intelligence State"],
        "Dominant Side": latest["Dominant Side"],
        "Aggression": latest["Aggression State"],
        "Imbalance": latest["Imbalance Signal"],
        "Absorption": int(out["Absorption"].sum()),
        "Exhaustion": int(out["Exhaustion"].sum()),
        "Failed Auctions": int(out["Failed Auction"].sum()),
        "Delta Flips": int(out["Delta Flip"].sum()),
        "CVD Divergences": int(out["CVD Divergence"].sum()),
        "Large Prints": int(out["Large Print"].sum()),
        "Stacked Imbalances": int(out["Stacked Imbalance"].sum()),
    }


def build_footprint_intelligence_snapshot(df):
    out = classify_footprint_intelligence(df)
    return {
        "data": out,
        "summary": footprint_intelligence_summary(out),
    }
