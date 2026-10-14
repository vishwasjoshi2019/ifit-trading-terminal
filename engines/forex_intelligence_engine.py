"""
IFIT Forex Intelligence Engine V0.1
Simulation/proxy data architecture. Replace generators with authorized live data adapters in production.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

FOREX_UNIVERSE = [
    ("USDINR", "INR", "USD/INR"),
    ("EURINR", "INR", "EUR/INR"),
    ("GBPINR", "INR", "GBP/INR"),
    ("JPYINR", "INR", "JPY/INR"),
    ("EURUSD", "G10", "EUR/USD"),
    ("GBPUSD", "G10", "GBP/USD"),
    ("USDJPY", "G10", "USD/JPY"),
    ("AUDUSD", "G10", "AUD/USD"),
    ("USDCAD", "G10", "USD/CAD"),
    ("USDCHF", "G10", "USD/CHF"),
    ("DXY", "Index", "Dollar Index"),
]

def build_forex_universe(periods: int = 180, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    base_prices = {
        "USDINR": 83.4, "EURINR": 90.7, "GBPINR": 106.1, "JPYINR": 0.56,
        "EURUSD": 1.08, "GBPUSD": 1.27, "USDJPY": 149.2, "AUDUSD": 0.66,
        "USDCAD": 1.35, "USDCHF": 0.88, "DXY": 104.0,
    }
    for symbol, group, name in FOREX_UNIVERSE:
        drift = rng.normal(0.00015, 0.00045)
        vol = rng.uniform(0.004, 0.012)
        shocks = rng.normal(drift, vol, periods)
        prices = base_prices[symbol] * np.exp(np.cumsum(shocks))
        ret_5 = (prices[-1] / prices[-6] - 1) * 100
        ret_20 = (prices[-1] / prices[-21] - 1) * 100
        ret_60 = (prices[-1] / prices[-61] - 1) * 100
        rv = np.std(np.diff(np.log(prices[-61:]))) * np.sqrt(252) * 100
        momentum = 50 + np.tanh(ret_20 / 8) * 28 + np.tanh(ret_5 / 3) * 12
        trend = np.clip(50 + ret_60 * 2.2, 0, 100)
        carry = np.clip(50 + rng.normal(0, 15), 0, 100)
        liquidity = np.clip(rng.normal(82, 7), 45, 98)
        positioning = np.clip(50 + ret_5 * 4 + rng.normal(0, 9), 0, 100)
        vol_score = np.clip(100 - rv * 2.0, 0, 100)
        fx_score = float(np.clip(0.32*momentum + 0.24*trend + 0.16*carry + 0.14*positioning + 0.14*vol_score, 0, 100))
        signal = "BULLISH" if fx_score >= 60 else "BEARISH" if fx_score <= 40 else "NEUTRAL"
        rows.append({
            "Symbol": symbol, "Pair": name, "Group": group, "Price": round(float(prices[-1]), 5),
            "5D Return %": round(float(ret_5), 3), "20D Return %": round(float(ret_20), 3),
            "60D Return %": round(float(ret_60), 3), "Realized Volatility %": round(float(rv), 2),
            "Momentum Score": round(float(momentum), 2), "Trend Score": round(float(trend), 2),
            "Carry Score": round(float(carry), 2), "Positioning Score": round(float(positioning), 2),
            "Liquidity Score": round(float(liquidity), 2), "Volatility Score": round(float(vol_score), 2),
            "Forex Intelligence Score": round(fx_score, 2), "Signal": signal,
            "Forward Bias": "Positive Carry" if carry >= 60 else "Negative Carry" if carry <= 40 else "Balanced",
        })
    return pd.DataFrame(rows)

def apply_forex_filters(df, groups=None, signals=None, min_score=0.0, min_momentum=-999.0, min_liquidity=0.0):
    out = df.copy()
    if groups: out = out[out["Group"].isin(groups)]
    if signals: out = out[out["Signal"].isin(signals)]
    out = out[(out["Forex Intelligence Score"] >= min_score) &
              (out["5D Return %"] >= min_momentum) &
              (out["Liquidity Score"] >= min_liquidity)]
    return out

def rank_forex(df, ascending=False):
    out = df.sort_values("Forex Intelligence Score", ascending=ascending).copy()
    out.insert(0, "Rank", range(1, len(out)+1))
    return out

def forex_intelligence_summary(df):
    if df is None or df.empty:
        return {"Pairs": 0, "Average Intelligence Score": 0.0, "Bullish": 0, "Bearish": 0,
                "Neutral": 0, "Average Volatility": 0.0, "Average Momentum": 0.0, "Signal": "NO DATA"}
    return {
        "Pairs": int(len(df)),
        "Average Intelligence Score": round(float(df["Forex Intelligence Score"].mean()), 2),
        "Bullish": int((df["Signal"] == "BULLISH").sum()),
        "Bearish": int((df["Signal"] == "BEARISH").sum()),
        "Neutral": int((df["Signal"] == "NEUTRAL").sum()),
        "Average Volatility": round(float(df["Realized Volatility %"].mean()), 2),
        "Average Momentum": round(float(df["5D Return %"].mean()), 3),
        "Signal": "BULLISH" if df["Forex Intelligence Score"].mean() >= 60 else "BEARISH" if df["Forex Intelligence Score"].mean() <= 40 else "NEUTRAL",
    }

def available_forex_pairs(): return [x[0] for x in FOREX_UNIVERSE]
def available_forex_groups(): return sorted({x[1] for x in FOREX_UNIVERSE})
def available_forex_signals(): return ["BULLISH", "NEUTRAL", "BEARISH"]

def build_forex_snapshot(periods=180, seed=42):
    df = build_forex_universe(periods, seed)
    corr = df.set_index("Symbol")[["5D Return %","20D Return %","60D Return %"]].T.corr().round(2)
    return {
        "Universe": df, "Correlation": corr,
        "Summary": forex_intelligence_summary(df),
        "Top Pair": df.loc[df["Forex Intelligence Score"].idxmax(), "Symbol"],
        "Bottom Pair": df.loc[df["Forex Intelligence Score"].idxmin(), "Symbol"],
    }

def build_forex_intelligence_snapshot(periods=180, seed=42):
    return build_forex_snapshot(periods, seed)

def forex_decision_snapshot(df=None):
    if df is None: df = build_forex_universe()
    s = forex_intelligence_summary(df)
    score = s["Average Intelligence Score"]
    state = "RISK-ON FX" if score >= 60 else "RISK-OFF FX" if score <= 40 else "MIXED FX"
    return {
        "Market State": state, "Signal": s["Signal"], "Confidence": round(abs(score-50)*2, 1),
        "Thesis": f"Forex intelligence is {state.lower()} with average intelligence score {score:.2f}.",
        "Confirmation": f"Top pair: {df.loc[df['Forex Intelligence Score'].idxmax(),'Symbol']}; bottom pair: {df.loc[df['Forex Intelligence Score'].idxmin(),'Symbol']}.",
        "Risk / Invalidation": "Prototype signal only; validate liquidity, macro events, spreads and authorized live pricing before production use.",
    }

def available_forex_views():
    return ["Overview", "Intelligence", "Screener", "Derivatives", "Volatility", "Decision Intelligence"]
