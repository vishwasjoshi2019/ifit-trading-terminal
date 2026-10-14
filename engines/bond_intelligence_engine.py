import numpy as np
import pandas as pd
from dataclasses import dataclass

@dataclass
class BondConfig:
    seed: int = 9107
    market_name: str = "INDIAN FIXED INCOME"

BOND_UNIVERSE = [
    ("T-BILL 91D", "T-BILL", "AAA", 91, 0.0),
    ("T-BILL 182D", "T-BILL", "AAA", 182, 0.0),
    ("T-BILL 364D", "T-BILL", "AAA", 364, 0.0),
    ("GSEC 2028", "G-SEC", "SOVEREIGN", 730, 7.10),
    ("GSEC 2030", "G-SEC", "SOVEREIGN", 1460, 6.95),
    ("GSEC 2032", "G-SEC", "SOVEREIGN", 2190, 7.05),
    ("GSEC 2035", "G-SEC", "SOVEREIGN", 3285, 7.20),
    ("GSEC 2040", "G-SEC", "SOVEREIGN", 5110, 7.25),
    ("SDL MH 2034", "SDL", "STATE", 2920, 7.55),
    ("SDL GJ 2035", "SDL", "STATE", 3285, 7.62),
    ("SDL KA 2036", "SDL", "STATE", 3650, 7.68),
    ("AAA PSU 2029", "CORPORATE", "AAA", 1095, 7.85),
    ("AAA PSU 2031", "CORPORATE", "AAA", 1825, 8.02),
    ("AAA BANK 2030", "CORPORATE", "AAA", 1460, 7.92),
    ("AA+ CORP 2029", "CORPORATE", "AA+", 1095, 8.35),
    ("AA CORP 2031", "CORPORATE", "AA", 1825, 8.72),
    ("AA CORP 2033", "CORPORATE", "AA", 2555, 8.91),
    ("A+ CORP 2030", "CORPORATE", "A+", 1460, 9.35),
]

def _signal(score):
    if score >= 72: return "STRONG BUY"
    if score >= 62: return "BUY"
    if score >= 39: return "NEUTRAL"
    if score >= 28: return "SELL"
    return "STRONG SELL"

def _credit_score(rating):
    return {"SOVEREIGN":95,"AAA":90,"AA+":80,"AA":72,"A+":62}.get(rating,50)

def build_bond_intelligence(bonds=None, seed=9107):
    rng = np.random.default_rng(seed)
    selected = bonds or [x[0] for x in BOND_UNIVERSE]
    rows=[]
    for name, asset_type, rating, days, coupon in BOND_UNIVERSE:
        if name not in selected: continue
        base_yield = coupon if coupon else (6.65 + days/3650*0.55)
        ytm = base_yield + rng.normal(0,0.10)
        price = 100 - (ytm-base_yield)*days/365*0.7 + rng.normal(0,0.25)
        duration = max(0.08, days/365 * (0.82 if asset_type=="T-BILL" else 0.88))
        yield_change = rng.normal(0,0.06)
        spread = ytm - (6.65 + min(days/365,10)*0.055)
        liquidity = float(np.clip(88 - days/365*1.8 + rng.normal(0,7),25,98))
        credit = _credit_score(rating)
        duration_score = float(np.clip(100 - duration*6,20,95))
        yield_score = float(np.clip(55 + (ytm-7.0)*18,20,95))
        relative_value = float(np.clip(55 + spread*12 + rng.normal(0,3),20,95))
        score = float(np.clip(
            yield_score*0.28 + credit*0.22 + liquidity*0.15 +
            duration_score*0.12 + relative_value*0.23,0,100))
        thesis = (
            f"{asset_type} with {rating} credit, {ytm:.2f}% YTM and "
            f"{duration:.2f}Y duration. Relative value score {relative_value:.1f}."
        )
        rows.append({
            "Market":"INDIAN FIXED INCOME", "Bond":name, "Asset Type":asset_type,
            "Rating":rating, "Days to Maturity":days, "Maturity Years":round(days/365,2),
            "Coupon %":round(coupon,2), "Price":round(price,3), "YTM %":round(ytm,3),
            "Yield Change bp":round(yield_change*100,2), "Duration":round(duration,3),
            "Credit Spread %":round(spread,3), "Liquidity Score":round(liquidity,2),
            "Credit Score":round(credit,2), "Yield Score":round(yield_score,2),
            "Duration Score":round(duration_score,2), "Relative Value Score":round(relative_value,2),
            "Bond Intelligence Score":round(score,2), "Signal":_signal(score), "Thesis":thesis
        })
    return pd.DataFrame(rows)

def apply_bond_intelligence_filters(df, asset_types=None, ratings=None, signals=None,
                                    min_ytm=0.0, max_ytm=999.0, min_duration=0.0,
                                    max_duration=999.0, min_score=0.0, min_liquidity=0.0):
    out=df.copy()
    if asset_types: out=out[out["Asset Type"].isin(asset_types)]
    if ratings: out=out[out["Rating"].isin(ratings)]
    if signals: out=out[out["Signal"].isin(signals)]
    out=out[(out["YTM %"]>=min_ytm)&(out["YTM %"]<=max_ytm)]
    out=out[(out["Duration"]>=min_duration)&(out["Duration"]<=max_duration)]
    out=out[out["Bond Intelligence Score"]>=min_score]
    out=out[out["Liquidity Score"]>=min_liquidity]
    return out.reset_index(drop=True)

def rank_bond_intelligence(df, ascending=False):
    return df.sort_values("Bond Intelligence Score", ascending=ascending).reset_index(drop=True)

def bond_intelligence_summary(df):
    if df is None or df.empty:
        return {"Bonds":0,"Buy":0,"Sell":0,"Average YTM":0.0,"Average Duration":0.0,"Average Spread":0.0,"Average Intelligence Score":0.0,"Signal":"NO DATA"}
    buy=int(df["Signal"].isin(["BUY","STRONG BUY"]).sum())
    sell=int(df["Signal"].isin(["SELL","STRONG SELL"]).sum())
    avg=df["Bond Intelligence Score"].mean()
    return {"Bonds":len(df),"Buy":buy,"Sell":sell,"Average YTM":round(df["YTM %"].mean(),3),"Average Duration":round(df["Duration"].mean(),2),"Average Spread":round(df["Credit Spread %"].mean(),3),"Average Intelligence Score":round(avg,2),"Signal":_signal(avg)}

def available_bond_asset_types():
    return sorted({x[1] for x in BOND_UNIVERSE})

def available_bond_ratings():
    return sorted({x[2] for x in BOND_UNIVERSE})

def available_bond_signals():
    return ["STRONG BUY","BUY","NEUTRAL","SELL","STRONG SELL"]

def build_bond_intelligence_snapshot(seed=9107):
    df=rank_bond_intelligence(build_bond_intelligence(seed=seed))
    return {"data":df,"summary":bond_intelligence_summary(df)}
