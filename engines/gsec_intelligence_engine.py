"""IFIT G-Secs Intelligence Engine V0.1 - simulation-first."""
from __future__ import annotations
import pandas as pd

_GSECS = [
    ("GSEC 2028", 2028, 1.8, 6.82, 6.84, 1.55, 96.0),
    ("GSEC 2030", 2030, 3.8, 6.95, 6.97, 3.15, 94.0),
    ("GSEC 2032", 2032, 5.8, 7.03, 7.01, 4.62, 92.0),
    ("GSEC 2035", 2035, 8.8, 7.14, 7.12, 6.71, 89.0),
    ("GSEC 2040", 2040, 13.8, 7.27, 7.24, 9.35, 84.0),
    ("GSEC 2044", 2044, 17.8, 7.33, 7.30, 11.55, 80.0),
    ("GSEC 2050", 2050, 23.8, 7.39, 7.36, 14.05, 75.0),
    ("GSEC 2055", 2055, 28.8, 7.43, 7.40, 16.20, 71.0),
]

def build_gsec_intelligence() -> pd.DataFrame:
    rows=[]
    for bond, maturity, years, coupon, ytm, duration, liquidity in _GSECS:
        yield_score=max(0.0,min(100.0,60.0+(ytm-7.0)*90.0))
        duration_score=max(0.0,min(100.0,92.0-duration*2.0))
        relative_value_score=max(0.0,min(100.0,65.0+(ytm-6.95)*110.0-max(duration-8.0,0)*0.8))
        curve_position_score=max(0.0,min(100.0,78.0+(ytm-7.10)*85.0))
        score=round(yield_score*.30+duration_score*.15+liquidity*.20+relative_value_score*.20+curve_position_score*.15,2)
        signal="STRONG BUY" if score>=75 else "BUY" if score>=66 else "NEUTRAL" if score>=52 else "SELL" if score>=42 else "STRONG SELL"
        if duration>=10:
            thesis=f"{bond} offers long-duration exposure at {ytm:.2f}% YTM; higher duration increases sensitivity to rate and curve moves."
        elif ytm>=7.0:
            thesis=f"{bond} combines {ytm:.2f}% YTM with moderate duration and strong secondary-market liquidity characteristics."
        else:
            thesis=f"{bond} provides shorter-duration sovereign exposure with lower rate sensitivity and high liquidity."
        rows.append({"Bond":bond,"Maturity Year":maturity,"Maturity Years":years,"Coupon %":coupon,"YTM %":ytm,"Duration":duration,"Liquidity Score":liquidity,"Yield Score":round(yield_score,2),"Duration Score":round(duration_score,2),"Relative Value Score":round(relative_value_score,2),"Curve Position Score":round(curve_position_score,2),"G-Sec Intelligence Score":score,"Signal":signal,"Thesis":thesis})
    return pd.DataFrame(rows)

def apply_gsec_intelligence_filters(df, signals=None, min_ytm=0.0, max_ytm=15.0, min_duration=0.0, max_duration=100.0, min_score=0.0):
    out=df.copy()
    if signals: out=out[out["Signal"].isin(signals)]
    return out[out["YTM %"].between(float(min_ytm),float(max_ytm)) & out["Duration"].between(float(min_duration),float(max_duration)) & (out["G-Sec Intelligence Score"]>=float(min_score))].reset_index(drop=True)

def rank_gsec_intelligence(df, ascending=False):
    return df.sort_values(["G-Sec Intelligence Score","YTM %"],ascending=[ascending,ascending]).reset_index(drop=True)

def gsec_intelligence_summary(df=None):
    if df is None: df=build_gsec_intelligence()
    if df.empty: return {"G-Secs":0,"Average YTM":0.0,"Average Duration":0.0,"Average Liquidity":0.0,"Average Intelligence Score":0.0,"Buy":0,"Sell":0,"Signal":"NEUTRAL"}
    buy=int(df["Signal"].isin(["BUY","STRONG BUY"]).sum()); sell=int(df["Signal"].isin(["SELL","STRONG SELL"]).sum())
    return {"G-Secs":int(len(df)),"Average YTM":round(float(df["YTM %"].mean()),3),"Average Duration":round(float(df["Duration"].mean()),2),"Average Liquidity":round(float(df["Liquidity Score"].mean()),2),"Average Intelligence Score":round(float(df["G-Sec Intelligence Score"].mean()),2),"Buy":buy,"Sell":sell,"Signal":"BUY" if buy>sell else "SELL" if sell>buy else "NEUTRAL"}

def available_gsec_signals(): return ["STRONG BUY","BUY","NEUTRAL","SELL","STRONG SELL"]
def build_gsec_intelligence_snapshot():
    df=build_gsec_intelligence(); return {"data":df,"summary":gsec_intelligence_summary(df)}

__all__=["build_gsec_intelligence","apply_gsec_intelligence_filters","rank_gsec_intelligence","gsec_intelligence_summary","available_gsec_signals","build_gsec_intelligence_snapshot"]
