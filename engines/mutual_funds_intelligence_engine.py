from __future__ import annotations
import numpy as np
import pandas as pd

MF_UNIVERSE = [
("HDFC Flexi Cap Fund","Flexi Cap","Equity","HDFC Mutual Fund"),
("Parag Parikh Flexi Cap Fund","Flexi Cap","Equity","PPFAS Mutual Fund"),
("Mirae Asset Large & Midcap Fund","Large & Mid Cap","Equity","Mirae Asset Mutual Fund"),
("ICICI Prudential Bluechip Fund","Large Cap","Equity","ICICI Prudential Mutual Fund"),
("SBI Small Cap Fund","Small Cap","Equity","SBI Mutual Fund"),
("Nippon India Growth Fund","Mid Cap","Equity","Nippon India Mutual Fund"),
("Motilal Oswal Midcap Fund","Mid Cap","Equity","Motilal Oswal Mutual Fund"),
("Kotak Emerging Equity Fund","Mid Cap","Equity","Kotak Mahindra Mutual Fund"),
("Axis Balanced Advantage Fund","Balanced Advantage","Hybrid","Axis Mutual Fund"),
("ICICI Prudential Balanced Advantage Fund","Balanced Advantage","Hybrid","ICICI Prudential Mutual Fund"),
("HDFC Corporate Bond Fund","Corporate Bond","Debt","HDFC Mutual Fund"),
("SBI Magnum Gilt Fund","Gilt","Debt","SBI Mutual Fund"),
("Parag Parikh ELSS Tax Saver Fund","ELSS","Equity","PPFAS Mutual Fund"),
("Nippon India Liquid Fund","Liquid","Debt","Nippon India Mutual Fund"),
("Quant Small Cap Fund","Small Cap","Equity","Quant Mutual Fund"),
]

def build_mf_universe(periods=180, seed=42):
    rng=np.random.default_rng(seed); rows=[]
    for name,cat,asset,amc in MF_UNIVERSE:
        bias={"Small Cap":3.5,"Mid Cap":2.5,"Flexi Cap":2.0,"Large & Mid Cap":1.5,
              "Large Cap":0.8,"ELSS":1.8,"Balanced Advantage":1.0,
              "Corporate Bond":0.5,"Gilt":0.2,"Liquid":0.0}.get(cat,0)
        r1=rng.normal(12.5+bias,6); r3=rng.normal(13+bias*.7,4); r5=rng.normal(12+bias*.5,3.2)
        vol=max(2.5,rng.normal(13 if asset=="Equity" else 5,2.8))
        dd=-abs(rng.normal(13 if asset=="Equity" else 5,3))
        exp=max(.15,rng.normal(.85 if asset=="Equity" else .55,.18))
        aum=max(500,rng.normal(22000,11000)); flow=rng.normal(180,500); alpha=rng.normal(1.2,2)
        sharpe=(r3-6)/max(vol,1)
        consistency=np.clip(72+rng.normal(0,9)-max(0,vol-14)*1.2,35,95)
        quality=np.clip(50+2.2*r3+1.3*sharpe+.12*consistency-5.5*exp-.18*abs(dd)+bias*1.5,20,95)
        score=np.clip(.32*quality+.20*np.clip(50+alpha*8,0,100)+.18*consistency+
                      .15*np.clip(50+flow/20,0,100)+.15*np.clip(55-vol,20,90),20,95)
        sig="BULLISH" if score>=68 else "BEARISH" if score<45 else "NEUTRAL"
        rows.append({"Fund":name,"Category":cat,"Asset Class":asset,"AMC":amc,
                     "1Y Return %":round(r1,2),"3Y Return %":round(r3,2),"5Y Return %":round(r5,2),
                     "Volatility %":round(vol,2),"Max Drawdown %":round(dd,2),"Expense Ratio %":round(exp,2),
                     "AUM ₹ Cr":round(aum,0),"Net Flow ₹ Cr":round(flow,1),"Alpha %":round(alpha,2),
                     "Sharpe":round(sharpe,2),"Consistency Score":round(consistency,2),
                     "MF Intelligence Score":round(float(score),2),"Signal":sig})
    return pd.DataFrame(rows)

def apply_mf_filters(df,categories=None,asset_classes=None,amcs=None,signals=None,min_score=0,min_return_1y=-999,max_expense=999):
    out=df.copy()
    if categories: out=out[out["Category"].isin(categories)]
    if asset_classes: out=out[out["Asset Class"].isin(asset_classes)]
    if amcs: out=out[out["AMC"].isin(amcs)]
    if signals: out=out[out["Signal"].isin(signals)]
    return out[(out["MF Intelligence Score"]>=float(min_score)) &
               (out["1Y Return %"]>=float(min_return_1y)) &
               (out["Expense Ratio %"]<=float(max_expense))].reset_index(drop=True)

def rank_mf(df,ascending=False):
    return df.sort_values("MF Intelligence Score",ascending=ascending).reset_index(drop=True)

def mf_intelligence_summary(df):
    if df.empty:
        return {"Funds":0,"Average Intelligence Score":0.0,"Bullish":0,"Bearish":0,"Neutral":0,
                "Average 1Y Return":0.0,"Average Expense":0.0,"Average Flow ₹ Cr":0.0,"Signal":"NO DATA"}
    avg=float(df["MF Intelligence Score"].mean())
    return {"Funds":len(df),"Average Intelligence Score":round(avg,2),
            "Bullish":int((df.Signal=="BULLISH").sum()),"Bearish":int((df.Signal=="BEARISH").sum()),
            "Neutral":int((df.Signal=="NEUTRAL").sum()),"Average 1Y Return":round(float(df["1Y Return %"].mean()),2),
            "Average Expense":round(float(df["Expense Ratio %"].mean()),2),
            "Average Flow ₹ Cr":round(float(df["Net Flow ₹ Cr"].mean()),1),
            "Signal":"BULLISH" if avg>=65 else "BEARISH" if avg<45 else "NEUTRAL"}

def build_mf_snapshot(periods=180,seed=42):
    df=build_mf_universe(periods,seed); return {"universe":df,"summary":mf_intelligence_summary(df)}

def build_mf_intelligence_snapshot(periods=180,seed=42): return build_mf_snapshot(periods,seed)

def mf_decision_snapshot(df=None):
    if df is None: df=build_mf_universe()
    s=mf_intelligence_summary(df)
    if df.empty:
        return {"Market State":"NO DATA","Signal":"NEUTRAL","Confidence":0.0,
                "Thesis":"No mutual-fund universe is available.","Confirmation":"No funds passed the current filters.",
                "Risk / Invalidation":"Prototype signal only; validate scheme data, NAV history, portfolio disclosures and authorized live sources before production use."}
    top=df.sort_values("MF Intelligence Score",ascending=False).iloc[0]
    bot=df.sort_values("MF Intelligence Score").iloc[0]
    return {"Market State":"POSITIVE MF REGIME" if s["Signal"]=="BULLISH" else "DEFENSIVE MF REGIME" if s["Signal"]=="BEARISH" else "MIXED MF REGIME",
            "Signal":s["Signal"],"Confidence":round(float(np.clip(abs(s["Average Intelligence Score"]-50)*1.8,5,95)),1),
            "Thesis":f"Mutual fund intelligence is {s['Signal'].lower()} with average intelligence score {s['Average Intelligence Score']:.2f}.",
            "Confirmation":f"Top fund: {top['Fund']}; bottom fund: {bot['Fund']}.",
            "Risk / Invalidation":"Prototype signal only; validate NAV history, portfolio disclosures, liquidity, scheme documents and authorized live data before production use."}

def available_mf_categories(): return sorted({x[1] for x in MF_UNIVERSE})
def available_mf_asset_classes(): return sorted({x[2] for x in MF_UNIVERSE})
def available_mf_amcs(): return sorted({x[3] for x in MF_UNIVERSE})
def available_mf_signals(): return ["BULLISH","NEUTRAL","BEARISH"]
