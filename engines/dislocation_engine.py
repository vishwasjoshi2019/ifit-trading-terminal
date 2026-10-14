
import numpy as np
import pandas as pd

from engines.greeks_engine import calculate_higher_order_greeks

def _scale_score(value, threshold):
    if not np.isfinite(value):
        return 0.0
    return float(np.clip(abs(value) / max(threshold, 1e-12) * 100.0, 0.0, 100.0))

def _expiry_score(dte):
    # Shorter expiries carry greater local model/convexity sensitivity.
    return float(np.clip(100.0 * np.sqrt(14.0 / max(float(dte), 1.0)), 0.0, 100.0))

def build_dislocation_rank(result_df, spot, calibration_stats,
                           r_percent=6.5, q_percent=0.0, top_n=15):
    """
    Build an explainable model-dislocation ranking.

    Components:
      - absolute market-vs-Heston IV gap
      - normalized price residual
      - expiry sensitivity
      - higher-order Greek sensitivity
      - calibration quality

    This is a research ranking, not an arbitrage/trade signal.
    """
    rows=[]
    iv_rmse=float(calibration_stats.get("iv_rmse", 0.0))
    quality=float(np.clip(100.0/(1.0+max(iv_rmse,0.0)),0.0,100.0))

    for _, row in result_df.iterrows():
        K=float(row["Strike"]); dte=float(row["DTE"]); iv=float(row["Market IV"])
        price_res=float(row["Price Residual"]); iv_res=float(row["IV Residual"])

        g=calculate_higher_order_greeks(
            spot,K,dte,iv,r_percent,q_percent,"CE"
        )
        greek_pressure=np.mean([
            _scale_score(g["gamma"],0.0005),
            _scale_score(g["vanna"],0.10),
            _scale_score(g["vomma"],0.50),
            _scale_score(g["zomma"],0.0003),
            _scale_score(g["ultima"],5.0),
        ])
        gap_score=_scale_score(iv_res,0.50)
        price_score=_scale_score(price_res,max(spot*0.002,1.0))
        expiry_score=_expiry_score(dte)

        # Weighted ranking, with calibration quality acting as a confidence gate.
        raw=(0.38*gap_score + 0.17*price_score +
             0.15*expiry_score + 0.20*greek_pressure + 0.10*quality)
        score=float(np.clip(raw,0,100))

        if score>=75:
            regime="HIGH DISLOCATION"
        elif score>=55:
            regime="ELEVATED"
        elif score>=35:
            regime="MODERATE"
        else:
            regime="LOW"

        rows.append({
            "Strike":K, "DTE":dte, "Market IV":iv,
            "Heston IV":float(row["Heston IV"]),
            "IV Gap":iv_res, "Abs IV Gap":abs(iv_res), "Price Gap":price_res,
            "Gap Score":gap_score, "Greek Risk":greek_pressure,
            "Expiry Score":expiry_score, "Calibration Quality":quality,
            "Dislocation Score":score, "Regime":regime
        })

    out=pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(
        ["Dislocation Score","Abs IV Gap" if "Abs IV Gap" in out.columns else "Gap Score"],
        ascending=False
    ).head(top_n).reset_index(drop=True)

def dislocation_summary(ranked):
    if ranked.empty:
        return {
            "top_score":0.0,"mean_score":0.0,"high_count":0,
            "max_gap":0.0,"top_strike":None,"top_dte":None
        }
    top=ranked.iloc[0]
    return {
        "top_score":float(top["Dislocation Score"]),
        "mean_score":float(ranked["Dislocation Score"].mean()),
        "high_count":int((ranked["Dislocation Score"]>=75).sum()),
        "max_gap":float(ranked["IV Gap"].abs().max()),
        "top_strike":float(top["Strike"]),
        "top_dte":float(top["DTE"])
    }
