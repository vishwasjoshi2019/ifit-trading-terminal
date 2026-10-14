"""
IFIT Crypto Intelligence Engine V0.1
Simulation/proxy data architecture. Replace generators with authorized exchange/data adapters in production.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

CRYPTO_UNIVERSE = [
    ("BTCUSDT","Bitcoin"),("ETHUSDT","Ethereum"),("SOLUSDT","Solana"),("BNBUSDT","BNB"),
    ("XRPUSDT","XRP"),("ADAUSDT","Cardano"),("DOGEUSDT","Dogecoin"),("AVAXUSDT","Avalanche"),
    ("LINKUSDT","Chainlink"),("TRXUSDT","TRON"),("TONUSDT","Toncoin"),("DOTUSDT","Polkadot"),
]

def build_crypto_universe(periods=180, seed=42):
    rng=np.random.default_rng(seed); rows=[]
    bases={"BTCUSDT":65000,"ETHUSDT":3200,"SOLUSDT":145,"BNBUSDT":620,"XRPUSDT":0.58,"ADAUSDT":0.38,
           "DOGEUSDT":0.14,"AVAXUSDT":28,"LINKUSDT":14,"TRXUSDT":0.13,"TONUSDT":5.8,"DOTUSDT":4.6}
    for symbol,name in CRYPTO_UNIVERSE:
        drift=rng.normal(0.0003,0.0007); vol=rng.uniform(0.012,0.035)
        shocks=rng.normal(drift,vol,periods); prices=bases[symbol]*np.exp(np.cumsum(shocks))
        r1=(prices[-1]/prices[-2]-1)*100; r7=(prices[-1]/prices[-8]-1)*100
        r30=(prices[-1]/prices[-31]-1)*100; rv=np.std(np.diff(np.log(prices[-31:])))*np.sqrt(365)*100
        oi_change=rng.normal(r30*0.6,4.5); funding=rng.normal(0.008,0.012)
        basis=rng.normal(0.15,0.35); liq=np.clip(rng.normal(76,12),30,98)
        flow=np.clip(50+r7*2.8+rng.normal(0,8),0,100)
        positioning=np.clip(50+oi_change*2+rng.normal(0,8),0,100)
        vol_score=np.clip(100-rv*1.15,0,100)
        score=float(np.clip(0.25*(50+np.tanh(r30/12)*35)+0.20*flow+0.18*positioning+0.15*vol_score+0.12*liq+0.10*(50+np.tanh(basis/0.5)*30),0,100))
        signal="BULLISH" if score>=60 else "BEARISH" if score<=40 else "NEUTRAL"
        regime="EXPANSION" if rv>=75 else "COMPRESSED" if rv<=35 else "NORMAL"
        rows.append({
            "Symbol":symbol,"Asset":name,"Price":round(float(prices[-1]),4),"1D Return %":round(float(r1),3),
            "7D Return %":round(float(r7),3),"30D Return %":round(float(r30),3),"Realized Volatility %":round(float(rv),2),
            "Open Interest":round(float(abs(bases[symbol])*1000*(1+rng.normal(0,0.15))),2),
            "OI Change %":round(float(oi_change),2),"Funding %":round(float(funding),4),
            "Basis %":round(float(basis),3),"Flow Score":round(float(flow),2),"Positioning Score":round(float(positioning),2),
            "Liquidity Score":round(float(liq),2),"Volatility Score":round(float(vol_score),2),
            "Crypto Intelligence Score":round(score,2),"Volatility Regime":regime,"Signal":signal,
            "Liquidation Risk": "HIGH" if abs(oi_change)>8 or rv>85 else "NORMAL",
        })
    return pd.DataFrame(rows)

def apply_crypto_filters(df, signals=None, vol_regimes=None, min_score=0.0, min_oi_change=-999.0, max_oi_change=999.0, min_liquidity=0.0):
    out=df.copy()
    if signals: out=out[out["Signal"].isin(signals)]
    if vol_regimes: out=out[out["Volatility Regime"].isin(vol_regimes)]
    return out[(out["Crypto Intelligence Score"]>=min_score)&(out["OI Change %"]>=min_oi_change)&
               (out["OI Change %"]<=max_oi_change)&(out["Liquidity Score"]>=min_liquidity)]

def rank_crypto(df, ascending=False):
    out=df.sort_values("Crypto Intelligence Score",ascending=ascending).copy()
    out.insert(0,"Rank",range(1,len(out)+1)); return out

def crypto_intelligence_summary(df):
    if df is None or df.empty:
        return {"Assets":0,"Average Intelligence Score":0.0,"Bullish":0,"Bearish":0,"Neutral":0,
                "Average Funding":0.0,"Average OI Change":0.0,"Average Volatility":0.0,"Signal":"NO DATA"}
    score=df["Crypto Intelligence Score"].mean()
    return {"Assets":int(len(df)),"Average Intelligence Score":round(float(score),2),
            "Bullish":int((df.Signal=="BULLISH").sum()),"Bearish":int((df.Signal=="BEARISH").sum()),
            "Neutral":int((df.Signal=="NEUTRAL").sum()),"Average Funding":round(float(df["Funding %"].mean()),4),
            "Average OI Change":round(float(df["OI Change %"].mean()),2),"Average Volatility":round(float(df["Realized Volatility %"].mean()),2),
            "Signal":"BULLISH" if score>=60 else "BEARISH" if score<=40 else "NEUTRAL"}

def available_crypto_assets(): return [x[0] for x in CRYPTO_UNIVERSE]
def available_crypto_signals(): return ["BULLISH","NEUTRAL","BEARISH"]
def available_crypto_volatility_regimes(): return ["COMPRESSED","NORMAL","EXPANSION"]

def build_crypto_snapshot(periods=180,seed=42):
    df=build_crypto_universe(periods,seed)
    corr=df.set_index("Symbol")[["1D Return %","7D Return %","30D Return %"]].T.corr().round(2)
    return {"Universe":df,"Correlation":corr,"Summary":crypto_intelligence_summary(df),
            "Top Asset":df.loc[df["Crypto Intelligence Score"].idxmax(),"Symbol"],
            "Bottom Asset":df.loc[df["Crypto Intelligence Score"].idxmin(),"Symbol"]}

def build_crypto_intelligence_snapshot(periods=180,seed=42): return build_crypto_snapshot(periods,seed)

def crypto_decision_snapshot(df=None):
    if df is None: df=build_crypto_universe()
    s=crypto_intelligence_summary(df); score=s["Average Intelligence Score"]
    state="CRYPTO RISK-ON" if score>=60 else "CRYPTO RISK-OFF" if score<=40 else "MIXED CRYPTO"
    return {"Market State":state,"Signal":s["Signal"],"Confidence":round(abs(score-50)*2,1),
            "Thesis":f"Crypto intelligence is {state.lower()} with average intelligence score {score:.2f}.",
            "Confirmation":f"Top asset: {df.loc[df['Crypto Intelligence Score'].idxmax(),'Symbol']}.",
            "Risk / Invalidation":"Prototype signal only; validate exchange liquidity, funding, basis, liquidation and authorized live data before production use."}

def available_crypto_views():
    return ["Overview","Intelligence","Screener","Derivatives","Volatility","Decision Intelligence"]
