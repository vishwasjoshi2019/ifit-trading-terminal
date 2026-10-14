
import numpy as np
import pandas as pd

def build_orderflow(spot, levels=50, imbalance_ratio=1.5):
    rng=np.random.default_rng(2026)
    # Synthetic bid/ask volume with localized aggressive buying/selling clusters.
    prices=np.arange(spot, spot-levels*5, -5.0)
    center=len(prices)//2
    base=rng.integers(40,500,len(prices)).astype(float)
    bid=base*rng.uniform(.65,1.35,len(prices))
    ask=base*rng.uniform(.65,1.35,len(prices))
    bid[center-8:center-3]*=1.9
    ask[center+3:center+9]*=2.1
    bid=np.maximum(1,np.rint(bid)).astype(int)
    ask=np.maximum(1,np.rint(ask)).astype(int)
    total=bid+ask
    delta=ask-bid
    ratio=np.maximum(ask/bid,bid/ask)
    side=np.where(ask>=bid,"BUY","SELL")
    cvd=np.cumsum(delta)
    return pd.DataFrame({
        "Price":prices,"Bid Volume":bid,"Ask Volume":ask,"Total Volume":total,
        "Delta":delta,"Bid/Ask Ratio":ratio,"Side":side,"CVD":cvd
    })

def classify_levels(flow, threshold=1.5):
    df=flow.copy()
    imbalance=[]
    for _,r in df.iterrows():
        if r["Ask Volume"] >= r["Bid Volume"]*threshold: imbalance.append("BUY")
        elif r["Bid Volume"] >= r["Ask Volume"]*threshold: imbalance.append("SELL")
        else: imbalance.append("")
    df["Imbalance"]=imbalance
    # stacked ID: consecutive same-side imbalances get the same identifier.
    ids=[]; current=0; prev=""
    for x in df["Imbalance"]:
        if x and x==prev:
            ids.append(str(current))
        elif x:
            current += 1
            ids.append(str(current))
        else:
            ids.append("")
        prev=x
    df["Stacked ID"]=ids
    return df

def orderflow_metrics(flow, spot):
    df=classify_levels(flow,1.5)
    cvd=int(df["Delta"].sum())
    poc=float(df.loc[df["Total Volume"].idxmax(),"Price"])

    # 70% value area approximation: expand around POC by descending volume.
    ranked=df.sort_values("Total Volume",ascending=False)
    target=df["Total Volume"].sum()*0.70
    used=0; selected=[]
    for idx,row in ranked.iterrows():
        selected.append(idx); used+=row["Total Volume"]
        if used>=target: break
    vah=float(df.loc[selected,"Price"].max()); val=float(df.loc[selected,"Price"].min())

    buys=int((df["Imbalance"]=="BUY").sum()); sells=int((df["Imbalance"]=="SELL").sum())
    stacked=0
    groups=df[df["Imbalance"]!=""]["Imbalance"].tolist()
    for i in range(1,len(groups)):
        if groups[i]==groups[i-1]: stacked+=1

    # Simple prototype diagnostics.
    recent=df.tail(max(5,len(df)//5))
    prior=df.head(max(5,len(df)//5))
    recent_delta=recent["Delta"].sum()
    price_change=float(recent["Price"].iloc[-1]-recent["Price"].iloc[0])
    cvd_div="BULLISH" if price_change<0 and recent_delta>0 else ("BEARISH" if price_change>0 and recent_delta<0 else "NONE")
    exhaustion="HIGH" if abs(recent_delta)<max(100,df["Total Volume"].mean()*.05) else "LOW"
    regime="BULLISH" if cvd>0 and buys>=sells else ("BEARISH" if cvd<0 and sells>buys else "BALANCED")

    score=50
    score += 15 if cvd>0 else -15 if cvd<0 else 0
    score += 10 if buys>sells else -10 if sells>buys else 0
    score += 10 if poc<spot and cvd>0 else -10 if poc>spot and cvd<0 else 0
    score += 10 if cvd_div=="BULLISH" else -10 if cvd_div=="BEARISH" else 0
    score=max(0,min(100,int(score)))

    return {
        "cvd":cvd,"poc":poc,"vah":vah,"val":val,
        "buy_imbalances":buys,"sell_imbalances":sells,
        "stacked_imbalance":stacked,"delta_exhaustion":exhaustion,
        "cvd_direction":"UP" if cvd>0 else "DOWN" if cvd<0 else "FLAT",
        "cvd_divergence":cvd_div,"regime":regime,"flow_score":score,
        "poc_position":"ABOVE SPOT" if poc>spot else "BELOW SPOT"
    }

def build_live_depth_orderflow(depth, spot=None):
    """
    Build a live displayed-liquidity view from Dhan's five-level depth.
    This is order-book liquidity, not trade-level footprint or CVD.
    """
    import pandas as pd

    levels = depth.get("levels", []) if isinstance(depth, dict) else depth

    if not levels:
        return pd.DataFrame(columns=[
            "Price", "Bid Volume", "Ask Volume",
            "Total Volume", "Delta", "Bid/Ask Ratio", "Side"
        ])

    rows = []

    for level in levels:
        bid_price = float(level.get("bid_price", 0) or 0)
        ask_price = float(level.get("ask_price", 0) or 0)
        bid_qty = int(level.get("bid_quantity", 0) or 0)
        ask_qty = int(level.get("ask_quantity", 0) or 0)

        if bid_price > 0:
            rows.append({
                "Price": bid_price,
                "Bid Volume": bid_qty,
                "Ask Volume": 0,
                "Total Volume": bid_qty,
                "Delta": 0,
                "Bid/Ask Ratio": (
                    bid_qty / ask_qty if ask_qty > 0 else None
                ),
                "Side": "BID",
            })

        if ask_price > 0:
            rows.append({
                "Price": ask_price,
                "Bid Volume": 0,
                "Ask Volume": ask_qty,
                "Total Volume": ask_qty,
                "Delta": 0,
                "Bid/Ask Ratio": (
                    bid_qty / ask_qty if ask_qty > 0 else None
                ),
                "Side": "ASK",
            })

    return pd.DataFrame(rows).sort_values(
        "Price", ascending=False
    ).reset_index(drop=True)