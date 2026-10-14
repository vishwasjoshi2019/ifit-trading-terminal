from __future__ import annotations
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

CROSS_ASSET_UNIVERSE = [
    "NIFTY 50", "BANKNIFTY", "NIFTY IT",
    "G-SEC 10Y", "SDL 10Y", "CORPORATE AAA",
    "GOLD", "SILVER", "CRUDE OIL", "USDINR",
    "INDIA VIX", "BTC", "ETH", "S&P 500", "NASDAQ 100",
]

ASSET_CLASSES = {
    "NIFTY 50": "Equity", "BANKNIFTY": "Equity", "NIFTY IT": "Equity",
    "G-SEC 10Y": "Bonds", "SDL 10Y": "Bonds", "CORPORATE AAA": "Credit",
    "GOLD": "Commodity", "SILVER": "Commodity", "CRUDE OIL": "Commodity",
    "USDINR": "FX", "INDIA VIX": "Volatility", "BTC": "Crypto", "ETH": "Crypto",
    "S&P 500": "Global Equity", "NASDAQ 100": "Global Equity",
}

def build_cross_asset_universe(periods: int = 180, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp.now().normalize(), periods=periods, freq="B")
    base = {
        "NIFTY 50":25000.0,"BANKNIFTY":56000.0,"NIFTY IT":40000.0,
        "G-SEC 10Y":6.85,"SDL 10Y":7.10,"CORPORATE AAA":7.55,
        "GOLD":73500.0,"SILVER":90000.0,"CRUDE OIL":72.0,"USDINR":88.0,
        "INDIA VIX":13.5,"BTC":110000.0,"ETH":4200.0,"S&P 500":6600.0,"NASDAQ 100":24000.0,
    }
    drift = {
        "NIFTY 50":.00025,"BANKNIFTY":.00030,"NIFTY IT":.00020,
        "G-SEC 10Y":-.00008,"SDL 10Y":-.00005,"CORPORATE AAA":-.00003,
        "GOLD":.00018,"SILVER":.00015,"CRUDE OIL":.00005,"USDINR":.00004,
        "INDIA VIX":-.00010,"BTC":.00035,"ETH":.00030,"S&P 500":.00022,"NASDAQ 100":.00028,
    }
    vol = {
        "NIFTY 50":.009,"BANKNIFTY":.012,"NIFTY IT":.011,
        "G-SEC 10Y":.003,"SDL 10Y":.0035,"CORPORATE AAA":.003,
        "GOLD":.008,"SILVER":.014,"CRUDE OIL":.020,"USDINR":.0035,
        "INDIA VIX":.035,"BTC":.025,"ETH":.030,"S&P 500":.010,"NASDAQ 100":.013,
    }
    common = rng.normal(0, 1, periods)
    rows: List[Dict[str, Any]] = []
    for symbol in CROSS_ASSET_UNIVERSE:
        shocks = .65 * common + .35 * rng.normal(0, 1, periods)
        if ASSET_CLASSES[symbol] == "Bonds":
            shocks *= -.45
        elif ASSET_CLASSES[symbol] == "Volatility":
            shocks *= -.70
        returns = drift[symbol] + vol[symbol] * shocks
        prices = base[symbol] * np.exp(np.cumsum(returns))
        for i, ts in enumerate(dates):
            rows.append({
                "Timestamp": ts, "Symbol": symbol, "Asset Class": ASSET_CLASSES[symbol],
                "Price": round(float(prices[i]), 4),
                "Return %": round(float(returns[i] * 100), 4),
                "Volume Proxy": round(float(abs(shocks[i]) * 100 + 50), 2),
            })
    return pd.DataFrame(rows)

def build_cross_asset_snapshot(df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    if df is None:
        df = build_cross_asset_universe()
    if df.empty:
        return {"Asset Count":0,"Risk State":"NEUTRAL","Cross-Asset Score":50.0,
                "Regime":"MIXED","Leadership":"N/A","Lagging":"N/A",
                "Divergence Count":0,"Correlation":pd.DataFrame(),"Asset Table":pd.DataFrame()}
    latest = df.sort_values("Timestamp").groupby("Symbol", as_index=False).tail(1).copy()
    latest["Score"] = np.clip(50.0 + latest["Return %"] * 18.0, 0, 100).round(2)
    def cls(name): return latest[latest["Asset Class"] == name]
    equity = latest[latest["Asset Class"].isin(["Equity","Global Equity"])]
    bonds, commodities, fx, crypto, vol_df = cls("Bonds"), cls("Commodity"), cls("FX"), cls("Crypto"), cls("Volatility")
    eq = float(equity["Score"].mean()) if len(equity) else 50.0
    bd = float(bonds["Score"].mean()) if len(bonds) else 50.0
    cm = float(commodities["Score"].mean()) if len(commodities) else 50.0
    fx_score = float(fx["Score"].mean()) if len(fx) else 50.0
    cr = float(crypto["Score"].mean()) if len(crypto) else 50.0
    risk = float(np.clip(.38*eq + .18*cr + .14*cm + .15*(100-bd) + .15*(50-(fx_score-50)), 0, 100))
    risk_state = "RISK-ON" if risk >= 62 else ("RISK-OFF" if risk <= 38 else "NEUTRAL / MIXED")
    regime = "GROWTH / RISK-ON" if eq >= 62 and bd <= 48 else (
        "DEFENSIVE / RISK-OFF" if eq <= 38 and bd >= 52 else "MIXED / ROTATION")
    leader = str(latest.sort_values("Score", ascending=False).iloc[0]["Symbol"])
    lagging = str(latest.sort_values("Score", ascending=True).iloc[0]["Symbol"])
    pivot = latest.set_index("Symbol")["Return %"]
    div = 0
    pairs = [("NIFTY 50","G-SEC 10Y",lambda a,b: np.sign(a)==np.sign(b)),
             ("GOLD","NIFTY 50",lambda a,b: np.sign(a)!=np.sign(b)),
             ("BTC","NIFTY 50",lambda a,b: np.sign(a)!=np.sign(b)),
             ("USDINR","NIFTY 50",lambda a,b: np.sign(a)==np.sign(b))]
    for a,b,rule in pairs:
        if a in pivot.index and b in pivot.index and rule(pivot[a], pivot[b]): div += 1
    wide = df.pivot_table(index="Timestamp", columns="Symbol", values="Return %", aggfunc="mean").tail(90)
    table = latest[["Symbol","Asset Class","Price","Return %","Score"]].sort_values("Score", ascending=False)
    return {
        "Asset Count":int(len(latest)), "Risk State":risk_state, "Cross-Asset Score":round(risk,2),
        "Regime":regime, "Leadership":leader, "Lagging":lagging, "Divergence Count":int(div),
        "Equity Score":round(eq,2), "Bond Score":round(bd,2), "Commodity Score":round(cm,2),
        "FX Score":round(fx_score,2), "Crypto Score":round(cr,2),
        "Volatility Proxy":round(float(vol_df["Return %"].mean()),4) if len(vol_df) else 0.0,
        "Correlation":wide.corr().round(2), "Asset Table":table.reset_index(drop=True),
    }

def cross_asset_summary(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "Assets":snapshot.get("Asset Count",0),"Risk State":snapshot.get("Risk State","N/A"),
        "Cross-Asset Score":snapshot.get("Cross-Asset Score",50.0),"Regime":snapshot.get("Regime","N/A"),
        "Leader":snapshot.get("Leadership","N/A"),"Lagging":snapshot.get("Lagging","N/A"),
        "Divergences":snapshot.get("Divergence Count",0),"Equity":snapshot.get("Equity Score",50.0),
        "Bonds":snapshot.get("Bond Score",50.0),"Commodities":snapshot.get("Commodity Score",50.0),
        "FX":snapshot.get("FX Score",50.0),"Crypto":snapshot.get("Crypto Score",50.0),
    }

def build_cross_asset_intelligence_snapshot(periods: int = 180, seed: int = 42) -> Dict[str, Any]:
    df = build_cross_asset_universe(periods=periods, seed=seed)
    snap = build_cross_asset_snapshot(df)
    snap["Summary"] = cross_asset_summary(snap)
    return snap
