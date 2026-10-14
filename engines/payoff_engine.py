"""
IFIT Payoff Engine V0.1
Reusable strategy payoff / MTM / stress calculations.
Prototype outputs are analytical diagnostics, not trading instructions.
"""
from __future__ import annotations
import math
from typing import Iterable, Mapping
import numpy as np
import pandas as pd

def _f(x, default=0.0):
    try:
        v=float(x)
        return v if math.isfinite(v) else default
    except Exception:
        return default

def _norm_option(x):
    s=str(x or "").upper().strip()
    return "PE" if s in ("PE","PUT","P") else "CE"

def _side_sign(x):
    s=str(x or "").upper().strip()
    return -1.0 if s in ("SELL","SHORT","SHORT CALL","SHORT PUT","-1","-") else 1.0

def _norm_legs(legs):
    rows=[]
    for i, raw in enumerate(legs or [], 1):
        r=dict(raw) if isinstance(raw, Mapping) else {}
        opt=_norm_option(r.get("Option", r.get("Option Type", r.get("Type","CE"))))
        side=_side_sign(r.get("Side", r.get("Position", r.get("Direction","BUY"))))
        qty=abs(_f(r.get("Qty", r.get("Quantity", r.get("Lots",1))),1.0))
        mult=abs(_f(r.get("Multiplier", r.get("Lot Size",50)),50.0))
        strike=_f(r.get("Strike",r.get("strike",0.0)))
        premium=_f(r.get("Premium",r.get("LTP",r.get("Entry Price",0.0))))
        iv=_f(r.get("IV",r.get("iv",15.0)),15.0)
        dte=_f(r.get("DTE",14.0),14.0)
        rows.append({
            "Leg": r.get("Leg", f"LEG {i}"),
            "Instrument": r.get("Instrument", f"NIFTY {strike:.0f} {opt}"),
            "Side": "SELL" if side < 0 else "BUY",
            "Option": opt,
            "Qty": qty,
            "Multiplier": mult,
            "Strike": strike,
            "Premium": premium,
            "IV": iv,
            "DTE": dte,
            "_sign": side,
        })
    return pd.DataFrame(rows)

def _intrinsic(spot, strike, option):
    return max(spot-strike,0.0) if option=="CE" else max(strike-spot,0.0)

def leg_expiry_pnl(spot, leg):
    return leg["_sign"] * leg["Qty"] * leg["Multiplier"] * (_intrinsic(spot,leg["Strike"],leg["Option"]) - leg["Premium"])

def strategy_expiry_payoff(legs, spots):
    df=_norm_legs(legs)
    out=pd.DataFrame({"Spot":np.asarray(spots,dtype=float)})
    out["Combined P&L"]=0.0
    for _,leg in df.iterrows():
        out[f'{leg["Leg"]} P&L']=[leg_expiry_pnl(s,leg) for s in out["Spot"]]
        out["Combined P&L"] += out[f'{leg["Leg"]} P&L']
    return out, df

def _norm_cdf(x):
    return 0.5*(1.0+math.erf(x/math.sqrt(2.0)))

def bsm_price(spot,strike,dte_days,iv_pct,rate_pct,option):
    S=max(_f(spot),1e-12); K=max(_f(strike),1e-12); T=max(_f(dte_days)/365.0,1e-10)
    sig=max(_f(iv_pct)/100.0,1e-8); r=_f(rate_pct)/100.0
    d1=(math.log(S/K)+(r+0.5*sig*sig)*T)/(sig*math.sqrt(T))
    d2=d1-sig*math.sqrt(T)
    discK=K*math.exp(-r*T)
    if option=="CE":
        return S*_norm_cdf(d1)-discK*_norm_cdf(d2)
    return discK*_norm_cdf(-d2)-S*_norm_cdf(-d1)

def strategy_mtm(legs, spot, days_passed=0, rate_pct=6.0, iv_shift=0.0):
    df=_norm_legs(legs)
    total=0.0
    rows=[]
    for _,leg in df.iterrows():
        remaining=max(0.0,leg["DTE"]-_f(days_passed))
        current=bsm_price(spot,leg["Strike"],remaining,leg["IV"]+iv_shift,rate_pct,leg["Option"])
        pnl=leg["_sign"]*leg["Qty"]*leg["Multiplier"]*(current-leg["Premium"])
        total += pnl
        rows.append({**{k:leg[k] for k in ["Leg","Instrument","Side","Option","Qty","Multiplier","Strike","Premium","IV","DTE"]},
                     "Remaining DTE":remaining,"Model Price":current,"MTM P&L":pnl})
    return float(total), pd.DataFrame(rows)

def breakevens(payoff):
    x=payoff["Spot"].to_numpy(float); y=payoff["Combined P&L"].to_numpy(float)
    roots=[]
    for i in range(1,len(x)):
        if y[i]==0: roots.append(x[i])
        elif y[i-1]*y[i]<0:
            roots.append(x[i-1] + (0-y[i-1])*(x[i]-x[i-1])/(y[i]-y[i-1]))
    return sorted({round(float(r),2) for r in roots})

def payoff_summary(payoff, spot):
    y=payoff["Combined P&L"].astype(float)
    roots=breakevens(payoff)
    maxp=float(y.max()); minp=float(y.min())
    if maxp>0 and minp<0:
        zone="MIXED"
    elif maxp>=0:
        zone="PROFIT / FLAT"
    else:
        zone="LOSS"
    return {"Current Spot":float(spot),"Breakevens":roots,"Max Profit (Grid)":maxp,
            "Max Loss (Grid)":minp,"Profit/Loss Zone":zone}

def scenario_grid(legs, spot, spot_moves=(-10,-5,-2,0,2,5,10), iv_moves=(-4,0,4), dte_days=(0,1,3,7)):
    rows=[]
    for sm in spot_moves:
        for iv in iv_moves:
            for d in dte_days:
                s=spot*(1+sm/100.0)
                mtm,_=strategy_mtm(legs,s,d,6.0,iv)
                rows.append({"Spot Shock %":sm,"IV Shock pt":iv,"Days Passed":d,"Scenario Spot":s,"Approx P&L":mtm})
    return pd.DataFrame(rows)

def payoff_decision_snapshot(summary, scenario):
    worst=scenario.loc[scenario["Approx P&L"].idxmin()] if not scenario.empty else {}
    best=scenario.loc[scenario["Approx P&L"].idxmax()] if not scenario.empty else {}
    return {
        "Market State":"PAYOFF PROFILE",
        "Signal":"DEFINED BY STRATEGY STRUCTURE",
        "Thesis":f'Payoff profile has {len(summary["Breakevens"])} modeled breakeven level(s) on the selected grid.',
        "Confirmation":f'Grid best P&L {float(best.get("Approx P&L",0)):,.2f}; grid worst P&L {float(worst.get("Approx P&L",0)):,.2f}.',
        "Risk / Invalidation":"Prototype payoff model; validate live prices, contract specifications, corporate actions, liquidity and authorized market data before production use.",
        "Source":"IFIT Payoff Engine V0.1",
    }

def build_default_payoff_legs(spot=24782.35):
    atm=round(float(spot)/100.0)*100.0
    return [
        {"Leg":"LONG CALL","Instrument":f"NIFTY {atm+200:.0f} CE","Side":"BUY","Option":"CE","Qty":1,"Multiplier":50,"Strike":atm+200,"Premium":120.0,"IV":14.5,"DTE":14},
        {"Leg":"LONG PUT","Instrument":f"NIFTY {atm-100:.0f} PE","Side":"BUY","Option":"PE","Qty":1,"Multiplier":50,"Strike":atm-100,"Premium":105.0,"IV":14.8,"DTE":14},
        {"Leg":"SHORT CALL","Instrument":f"NIFTY {atm+100:.0f} CE","Side":"SELL","Option":"CE","Qty":1,"Multiplier":50,"Strike":atm+100,"Premium":85.0,"IV":14.7,"DTE":14},
    ]
