"""IFIT Footprint V0.4 - Advanced Auction Intelligence."""
from __future__ import annotations
from typing import Any, Dict, Optional, List
import math

AUCTION_STATES = [
    "BALANCED", "INITIATIVE BUYING", "INITIATIVE SELLING", "ABSORPTION",
    "EXHAUSTION", "FAILED AUCTION", "IMBALANCE EXPANSION", "ROTATION"
]

def _n(v, d=0.0):
    try:
        x=float(v)
        return x if math.isfinite(x) else d
    except (TypeError, ValueError):
        return d

def _rows(data):
    if data is None: return []
    if hasattr(data, "to_dict"):
        try: return list(data.to_dict("records"))
        except Exception: pass
    if isinstance(data, dict):
        for k in ("rows","data","levels","footprint"):
            if isinstance(data.get(k), (list,tuple)):
                return [dict(x) for x in data[k] if isinstance(x,dict)]
        return [dict(data)]
    if isinstance(data,(list,tuple)):
        return [dict(x) for x in data if isinstance(x,dict)]
    return []

def _v(r, *keys):
    for k in keys:
        if k in r: return _n(r[k])
    return 0.0

def detect_poc_migration(current_poc, previous_poc, tolerance=0.0):
    cur, prev = _n(current_poc), _n(previous_poc)
    diff=cur-prev
    direction="STABLE" if abs(diff)<=_n(tolerance) else ("UP" if diff>0 else "DOWN")
    strength=min(100.0, abs(diff)/max(abs(prev),1)*10000)
    return {"Current POC":cur,"Previous POC":prev,"POC Migration":direction,
            "POC Change":diff,"POC Migration Strength":round(strength,2)}

def _pct(values,p):
    if not values: return 0.0
    a=sorted(values); pos=(len(a)-1)*max(0,min(100,p))/100
    lo,hi=int(pos),math.ceil(pos)
    return a[lo] if lo==hi else a[lo]+(a[hi]-a[lo])*(pos-lo)

def identify_hvn_lvn(data,hvn_percentile=75,lvn_percentile=25):
    rows=_rows(data); pairs=[(r,_v(r,"Total Volume","total_volume","Volume","volume")) for r in rows]
    vols=[v for _,v in pairs]
    hi,lo=_pct(vols,hvn_percentile),_pct(vols,lvn_percentile)
    hvn=[{"Price":_v(r,"Price","price","level"),"Volume":round(v,2)} for r,v in pairs if v>=hi]
    lvn=[{"Price":_v(r,"Price","price","level"),"Volume":round(v,2)} for r,v in pairs if v<=lo]
    return {"HVN Zones":hvn,"LVN Zones":lvn,"HVN Count":len(hvn),"LVN Count":len(lvn),
            "HVN Threshold":round(hi,2),"LVN Threshold":round(lo,2)}

def detect_absorption_zones(data,volume_percentile=70):
    rows=_rows(data); cut=_pct([_v(r,"Total Volume","Volume","volume") for r in rows],volume_percentile)
    out=[]
    for r in rows:
        vol=_v(r,"Total Volume","Volume","volume"); delta=_v(r,"Delta","delta")
        if vol>=cut and abs(delta)<=max(vol/1.5,1):
            out.append({"Price":_v(r,"Price","price","level"),"Volume":round(vol,2),
                        "Delta":round(delta,2),
                        "Type":"BUY ABSORPTION" if delta<0 else "SELL ABSORPTION"})
    return out

def detect_exhaustion_zones(data,relative_delta_threshold=.75,volume_percentile=70):
    rows=_rows(data); cut=_pct([_v(r,"Total Volume","Volume","volume") for r in rows],volume_percentile)
    out=[]
    for r in rows:
        vol=_v(r,"Total Volume","Volume","volume"); delta=_v(r,"Delta","delta")
        ratio=abs(delta)/max(vol,1)
        if vol>=cut and ratio>=relative_delta_threshold:
            out.append({"Price":_v(r,"Price","price","level"),"Volume":round(vol,2),
                        "Delta":round(delta,2),
                        "Type":"BUYER EXHAUSTION" if delta>0 else "SELLER EXHAUSTION",
                        "Delta/Volume":round(ratio,3)})
    return out

def detect_stacked_imbalances(data,minimum_stack=3):
    rows=sorted(_rows(data),key=lambda r:_v(r,"Price","price","level"))
    flags=[]
    for r in rows:
        bid=_v(r,"Bid Volume","bid_volume","Bid"); ask=_v(r,"Ask Volume","ask_volume","Ask")
        ratio=max(bid,ask)/max(min(bid,ask),1)
        flags.append((r,ratio,"BUY" if ask>=bid else "SELL"))
    out=[]; start=None
    for i in range(len(flags)+1):
        strong=i<len(flags) and flags[i][1]>=2
        if strong and start is None: start=i
        if (not strong or i==len(flags)) and start is not None:
            end=i
            if end-start>=minimum_stack:
                z=flags[start:end]
                out.append({"Start Price":_v(z[0][0],"Price","price","level"),
                            "End Price":_v(z[-1][0],"Price","price","level"),
                            "Direction":z[0][2],"Levels":end-start,
                            "Max Imbalance Ratio":round(max(x[1] for x in z),2)})
            start=None
    return out

def detect_failed_auctions(current,previous=None):
    c=current or {}; p=previous or {}
    h=_v(c,"High","high"); l=_v(c,"Low","low"); close=_v(c,"Close","close")
    ph=_v(p,"High","high"); pl=_v(p,"Low","low"); d=_v(c,"Delta","delta")
    failed="NONE"
    if ph and h>ph and close<ph and d<0: failed="FAILED HIGH AUCTION"
    elif pl and l<pl and close>pl and d>0: failed="FAILED LOW AUCTION"
    return {"Failed Auction":failed,"Breakout High":bool(ph and h>ph),
            "Breakout Low":bool(pl and l<pl)}

def detect_delta_flip(previous_delta,current_delta):
    p,c=_n(previous_delta),_n(current_delta)
    flip=(p<0<=c) or (p>0>=c)
    direction="BULLISH FLIP" if p<0<=c else ("BEARISH FLIP" if p>0>=c else "NONE")
    return {"Delta Flip":direction,"Delta Flip Detected":flip,
            "Previous Delta":p,"Current Delta":c}

def detect_cvd_divergence(price_change,cvd_change):
    p,c=_n(price_change),_n(cvd_change)
    d="BEARISH CVD DIVERGENCE" if p>0 and c<0 else ("BULLISH CVD DIVERGENCE" if p<0 and c>0 else "NONE")
    return {"CVD Divergence":d,"Price Change":p,"CVD Change":c}

def classify_auction_state(poc_migration="STABLE",dominant_side="NEUTRAL",
                           absorption_count=0,exhaustion_count=0,
                           stacked_imbalance_count=0,failed_auction="NONE",
                           delta_flip="NONE",cvd_divergence="NONE"):
    side=str(dominant_side).upper()
    if str(failed_auction).upper()!="NONE": state="FAILED AUCTION"
    elif absorption_count: state="ABSORPTION"
    elif exhaustion_count and not stacked_imbalance_count: state="EXHAUSTION"
    elif stacked_imbalance_count: state="IMBALANCE EXPANSION"
    elif "BULLISH" in str(delta_flip).upper() or (poc_migration=="UP" and side in ("BUY","BUYING")): state="INITIATIVE BUYING"
    elif "BEARISH" in str(delta_flip).upper() or (poc_migration=="DOWN" and side in ("SELL","SELLING")): state="INITIATIVE SELLING"
    elif "DIVERGENCE" in str(cvd_divergence).upper(): state="ROTATION"
    elif poc_migration=="STABLE": state="BALANCED"
    else: state="ROTATION"
    score=min(100,25+stacked_imbalance_count*5+absorption_count*5+exhaustion_count*5+
              (15 if failed_auction!="NONE" else 0)+(10 if delta_flip!="NONE" else 0))
    return {"Auction State":state,"Auction Confidence":round(score,2),
            "Dominant Side":side,"POC Migration":poc_migration}

def build_advanced_auction_snapshot(footprint_levels,current_bar=None,previous_bar=None,
                                    previous_poc=None,current_poc=None,
                                    price_change=None,cvd_change=None):
    c=current_bar or {}; p=previous_bar or {}
    poc=detect_poc_migration(current_poc,previous_poc)
    nodes=identify_hvn_lvn(footprint_levels)
    absorption=detect_absorption_zones(footprint_levels)
    exhaustion=detect_exhaustion_zones(footprint_levels)
    stacked=detect_stacked_imbalances(footprint_levels)
    failed=detect_failed_auctions(c,p)
    flip=detect_delta_flip(_v(p,"Delta","delta"),_v(c,"Delta","delta"))
    cvd=detect_cvd_divergence(price_change,cvd_change)
    state=classify_auction_state(poc["POC Migration"],str(c.get("Dominant Side","NEUTRAL")),
                                  len(absorption),len(exhaustion),len(stacked),
                                  failed["Failed Auction"],flip["Delta Flip"],cvd["CVD Divergence"])
    return {"POC Intelligence":poc,"Volume Nodes":nodes,"Absorption Zones":absorption,
            "Exhaustion Zones":exhaustion,"Stacked Imbalance Zones":stacked,
            "Failed Auction":failed,"Delta Flip":flip,"CVD Divergence":cvd,
            "Auction State":state}

def auction_intelligence_summary(snapshot):
    s=snapshot or {}; n=s.get("Volume Nodes",{}); a=s.get("Auction State",{})
    return {"Auction State":a.get("Auction State","BALANCED"),
            "Auction Confidence":a.get("Auction Confidence",0),
            "POC Migration":s.get("POC Intelligence",{}).get("POC Migration","STABLE"),
            "HVN Count":n.get("HVN Count",0),"LVN Count":n.get("LVN Count",0),
            "Absorption Zones":len(s.get("Absorption Zones",[])),
            "Exhaustion Zones":len(s.get("Exhaustion Zones",[])),
            "Stacked Imbalance Zones":len(s.get("Stacked Imbalance Zones",[])),
            "Failed Auction":s.get("Failed Auction",{}).get("Failed Auction","NONE"),
            "Delta Flip":s.get("Delta Flip",{}).get("Delta Flip","NONE"),
            "CVD Divergence":s.get("CVD Divergence",{}).get("CVD Divergence","NONE")}

def available_auction_states():
    return list(AUCTION_STATES)
