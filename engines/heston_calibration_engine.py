
import math
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from engines.model_dislocation_engine import heston_price, implied_vol_bsm

PARAM_ORDER = ["v0", "kappa", "theta", "sigma_v", "rho"]

DEFAULT_BOUNDS = {
    "v0": (0.005, 0.30),
    "kappa": (0.10, 8.0),
    "theta": (0.005, 0.30),
    "sigma_v": (0.05, 2.0),
    "rho": (-0.95, -0.05),
}

def _market_points(spot, strikes, expiries, iv_surface, r_percent=6.5, q_percent=0.0, option="CE"):
    points = []
    for K in strikes:
        for dte in expiries:
            iv = float(iv_surface.loc[K, f"{int(dte)}D"])
            if not np.isfinite(iv) or iv <= 0:
                continue
            from engines.model_dislocation_engine import bsm_price
            price = bsm_price(spot, K, dte, iv, r_percent, q_percent, option)
            points.append({"Strike": float(K), "DTE": float(dte), "Market IV": iv,
                           "Market Price": price})
    return pd.DataFrame(points)

def calibrate_heston(spot, strikes, expiries, iv_surface, r_percent=6.5,
                     q_percent=0.0, option="CE", initial=None, max_nfev=30):
    """
    Calibrate Heston parameters to a supplied BSM-IV-derived price surface.
    The fit is price-based, while the UI reports both price RMSE and IV RMSE.
    """
    market = _market_points(spot, strikes, expiries, iv_surface, r_percent, q_percent, option)
    if market.empty:
        raise ValueError("No valid calibration points.")

    if initial is None:
        initial = {"v0": 0.0225, "kappa": 2.0, "theta": 0.0225,
                   "sigma_v": 0.45, "rho": -0.70}

    lo = np.array([DEFAULT_BOUNDS[k][0] for k in PARAM_ORDER], dtype=float)
    hi = np.array([DEFAULT_BOUNDS[k][1] for k in PARAM_ORDER], dtype=float)
    x0 = np.array([initial[k] for k in PARAM_ORDER], dtype=float)
    x0 = np.minimum(np.maximum(x0, lo + 1e-6), hi - 1e-6)

    def params_from_x(x):
        return dict(zip(PARAM_ORDER, map(float, x)))

    def residuals(x):
        p = params_from_x(x)
        out = []
        for row in market.itertuples(index=False):
            hp = heston_price(spot, row.Strike, row.DTE, {
                **p, "r": r_percent/100.0, "q": q_percent/100.0
            }, option)
            # Scale by option price to prevent high-priced contracts dominating.
            market_price = float(row._asdict()["_3"])
            scale = max(abs(market_price), 1.0)
            out.append((hp - market_price) / scale)
        return np.asarray(out, dtype=float)

    fit = least_squares(
        residuals, x0, bounds=(lo, hi),
        max_nfev=int(max_nfev), xtol=2e-5, ftol=2e-5, gtol=2e-5
    )
    params = params_from_x(fit.x)

    rows = []
    for row in market.itertuples(index=False):
        hp = heston_price(spot, row.Strike, row.DTE, {
            **params, "r": r_percent/100.0, "q": q_percent/100.0
        }, option)
        hiv = implied_vol_bsm(hp, spot, row.Strike, row.DTE, r_percent, q_percent, option)
        rows.append({
            "Strike": row.Strike, "DTE": row.DTE,
            "Market IV": row._asdict()["_2"],
            "Market Price": float(row._asdict()["_3"]),
            "Heston Price": hp,
            "Price Residual": hp - row._asdict()["_3"],
            "Heston IV": hiv,
            "IV Residual": hiv - row._asdict()["_2"],
        })
    result = pd.DataFrame(rows)
    price_rmse = float(np.sqrt(np.mean(result["Price Residual"]**2)))
    iv_rmse = float(np.sqrt(np.nanmean(result["IV Residual"]**2)))
    return params, result, {
        "success": bool(fit.success),
        "message": str(fit.message),
        "iterations": int(fit.nfev),
        "price_rmse": price_rmse,
        "iv_rmse": iv_rmse,
        "points": len(result),
        "cost": float(fit.cost),
    }

def calibrated_iv_surface(spot, strikes, expiries, params, r_percent=6.5,
                          q_percent=0.0, option="CE"):
    rows=[]
    hparams={**params, "r":r_percent/100.0, "q":q_percent/100.0}
    for K in strikes:
        row={"Strike":K}
        for d in expiries:
            hp=heston_price(spot,K,d,hparams,option)
            row[f"{int(d)}D"]=implied_vol_bsm(hp,spot,K,d,r_percent,q_percent,option)
        rows.append(row)
    return pd.DataFrame(rows).set_index("Strike")

def dislocation_rank(result_df):
    out = result_df.copy()
    out["Abs IV Gap"] = out["IV Residual"].abs()
    out["Abs Price Gap"] = out["Price Residual"].abs()
    return out.sort_values(["Abs IV Gap", "Abs Price Gap"], ascending=False).reset_index(drop=True)
