import pandas as pd
from engines.liquidity_execution_engine import build_liquidity_execution

def build_live_hedge_universe(service):
    columns = ["Instrument", "Type", "Strike", "Delta", "Gamma", "Vega", "Theta", "Cost", "Liquidity Score"]
    try:
        snapshot = service.snapshot()
        chain = snapshot.get("option_chain")
        spot = float(snapshot.get("spot") or 0.0)
        expiry = snapshot.get("option_expiry")
        if chain is None or not isinstance(chain, pd.DataFrame) or chain.empty or spot <= 0:
            return pd.DataFrame(columns=columns)
        live_chain = chain.copy()
        live_chain["strike"] = pd.to_numeric(live_chain["strike"], errors="coerce")
        live_chain = live_chain.dropna(subset=["strike"])
        strikes = sorted(live_chain["strike"].unique(), key=lambda x: abs(float(x) - spot))[:5]
        live_chain = live_chain[live_chain["strike"].isin(strikes)].copy()
        live_chain["Strike"] = live_chain["strike"]
        live_chain["CE LTP"] = live_chain["CE_LTP"]
        live_chain["PE LTP"] = live_chain["PE_LTP"]
        live_chain["CE OI"] = live_chain["CE_OI"]
        live_chain["PE OI"] = live_chain["PE_OI"]
        liquidity = build_liquidity_execution(chain_df=live_chain, spot=spot, multiplier=50)
        liquidity_map = {}
        contracts = liquidity.get("contracts", pd.DataFrame()) if isinstance(liquidity, dict) else pd.DataFrame()
        if isinstance(contracts, pd.DataFrame) and not contracts.empty:
            for _, row in contracts.iterrows():
                key = (round(float(row.get("Strike", 0.0)), 6), str(row.get("Option", "")).upper())
                liquidity_map[key] = float(row.get("Liquidity Score", 0.0))
        rows = []
        for _, row in live_chain.iterrows():
            strike = float(row["strike"])
            for option, prefix, option_type in [("CE", "CE", "CALL"), ("PE", "PE", "PUT")]:
                ltp = pd.to_numeric(row.get(f"{prefix}_LTP"), errors="coerce")
                delta = pd.to_numeric(row.get(f"{prefix}_DELTA"), errors="coerce")
                gamma = pd.to_numeric(row.get(f"{prefix}_GAMMA"), errors="coerce")
                vega = pd.to_numeric(row.get(f"{prefix}_VEGA"), errors="coerce")
                theta = pd.to_numeric(row.get(f"{prefix}_THETA"), errors="coerce")
                values = [ltp, delta, gamma, vega, theta]
                if any(pd.isna(v) for v in values) or float(ltp) <= 0:
                    continue
                score = liquidity_map.get((round(strike, 6), option), 0.0)
                if score <= 0:
                    continue
                expiry_text = str(expiry or row.get("expiry") or "LIVE")
                rows.append({"Instrument": f"NIFTY {expiry_text} {strike:.0f} {option_type}", "Type": option_type, "Strike": strike, "Delta": float(delta), "Gamma": float(gamma), "Vega": float(vega), "Theta": float(theta), "Cost": float(ltp), "Liquidity Score": score})
        return pd.DataFrame(rows, columns=columns)
    except Exception:
        return pd.DataFrame(columns=columns)
