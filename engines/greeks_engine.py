
import math
import numpy as np
import pandas as pd

SQRT_2PI = math.sqrt(2.0 * math.pi)

def _norm_pdf(x):
    return math.exp(-0.5 * x * x) / SQRT_2PI

def _norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def _bs_price_delta_gamma_theta_vega_rho(S, K, T, r, q, sigma, option="CE"):
    T = max(float(T), 1e-8)
    sigma = max(float(sigma), 1e-8)
    S = max(float(S), 1e-8)
    K = max(float(K), 1e-8)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma*sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    disc_r = math.exp(-r*T)
    disc_q = math.exp(-q*T)
    cp = 1.0 if option.upper() in ("CE", "CALL", "C") else -1.0

    if cp > 0:
        price = S*disc_q*_norm_cdf(d1) - K*disc_r*_norm_cdf(d2)
        delta = disc_q*_norm_cdf(d1)
        theta = (-(S*disc_q*_norm_pdf(d1)*sigma)/(2*math.sqrt(T))
                 - r*K*disc_r*_norm_cdf(d2)
                 + q*S*disc_q*_norm_cdf(d1))
        rho = K*T*disc_r*_norm_cdf(d2)
    else:
        price = K*disc_r*_norm_cdf(-d2) - S*disc_q*_norm_cdf(-d1)
        delta = disc_q*(_norm_cdf(d1)-1.0)
        theta = (-(S*disc_q*_norm_pdf(d1)*sigma)/(2*math.sqrt(T))
                 + r*K*disc_r*_norm_cdf(-d2)
                 - q*S*disc_q*_norm_cdf(-d1))
        rho = -K*T*disc_r*_norm_cdf(-d2)

    gamma = disc_q*_norm_pdf(d1)/(S*sigma*math.sqrt(T))
    vega = S*disc_q*_norm_pdf(d1)*math.sqrt(T) / 100.0  # per 1 vol-point
    return {
        "price": price, "delta": delta, "gamma": gamma,
        "theta": theta/365.0, "vega": vega, "rho": rho/100.0,
    }

def _surface_function(S, K, T, r, q, sigma, option, field):
    return _bs_price_delta_gamma_theta_vega_rho(S,K,T,r,q,sigma,option)[field]

def _derivative(fun, x, h):
    return (fun(x+h)-fun(x-h))/(2*h)

def _second_derivative(fun, x, h):
    return (fun(x+h)-2*fun(x)+fun(x-h))/(h*h)

def calculate_higher_order_greeks(S, K, days_to_expiry, iv_percent,
                                  r_percent=6.5, q_percent=0.0, option="CE"):
    """
    Black-Scholes-Merton higher-order Greeks.

    Primary:
      delta, gamma, theta, vega, rho
    Second-order:
      vanna = dDelta/dVol, vomma/volga = dVega/dVol,
      charm = dDelta/dTime, zomma = dGamma/dVol
    Third-order / higher:
      speed = dGamma/dSpot, color = dGamma/dTime,
      ultima = dVomma/dVol, veta = dVega/dTime

    Volatility derivatives use a decimal-volatility bump.
    Time derivatives are reported per calendar day.
    Vega/vomma/volga follow the engine's per-vol-point convention.
    """
    S=float(S); K=float(K); T=max(float(days_to_expiry)/365.0, 1e-8)
    sigma=max(float(iv_percent)/100.0, 1e-8)
    r=float(r_percent)/100.0; q=float(q_percent)/100.0

    base = _bs_price_delta_gamma_theta_vega_rho(S,K,T,r,q,sigma,option)

    # Numerically differentiate analytical BSM primitives. This is intentional:
    # it keeps the higher-order definitions consistent and easy to audit.
    hs = max(S*1e-4, 0.01)
    hv = 1e-4
    ht = min(max(T*1e-4, 1e-6), 1/3650)

    def greek_at_spot(field, s):
        return _surface_function(s,K,T,r,q,sigma,option,field)

    def greek_at_vol(field, v):
        return _surface_function(S,K,T,r,q,v,option,field)

    def greek_at_time(field, t):
        return _surface_function(S,K,max(t,1e-8),r,q,sigma,option,field)

    # Vanna: dDelta/dsigma
    vanna = _derivative(lambda v: greek_at_vol("delta", v), sigma, hv)

    # Vomma/Volga: dVega/dsigma. Vega is per vol-point, so result follows that scale.
    vomma = _derivative(lambda v: greek_at_vol("vega", v), sigma, hv)

    # Charm: dDelta/d(calendar time) represented as forward time decay.
    charm = -_derivative(lambda t: greek_at_time("delta", t), T, ht) / 365.0

    # Zomma: dGamma/dsigma
    zomma = _derivative(lambda v: greek_at_vol("gamma", v), sigma, hv)

    # Speed: dGamma/dS
    speed = _derivative(lambda s: greek_at_spot("gamma", s), S, hs)

    # Color: dGamma/d(calendar time)
    color = -_derivative(lambda t: greek_at_time("gamma", t), T, ht) / 365.0

    # Ultima: dVomma/dsigma
    ultima = _second_derivative(lambda v: greek_at_vol("vega", v), sigma, hv)

    # Veta: dVega/d(calendar time)
    veta = -_derivative(lambda t: greek_at_time("vega", t), T, ht) / 365.0

    return {
        **base,
        "vanna": vanna,
        "vomma": vomma,
        "volga": vomma,
        "charm": charm,
        "zomma": zomma,
        "speed": speed,
        "color": color,
        "ultima": ultima,
        "veta": veta,
    }

def greek_snapshot_dataframe(spot, strikes, days_to_expiry, ivs,
                              r_percent=6.5, q_percent=0.0):
    rows=[]
    for K, iv in zip(strikes, ivs):
        ce=calculate_higher_order_greeks(spot,K,days_to_expiry,iv,r_percent,q_percent,"CE")
        pe=calculate_higher_order_greeks(spot,K,days_to_expiry,iv,r_percent,q_percent,"PE")
        rows.append({
            "Strike": K, "IV": iv,
            "CE Δ": ce["delta"], "CE Γ": ce["gamma"], "CE Θ/day": ce["theta"],
            "CE Vega": ce["vega"], "CE Vanna": ce["vanna"], "CE Vomma": ce["vomma"],
            "CE Charm": ce["charm"], "CE Zomma": ce["zomma"],
            "CE Speed": ce["speed"], "CE Color": ce["color"],
            "CE Ultima": ce["ultima"], "CE Veta": ce["veta"],
            "PE Δ": pe["delta"], "PE Γ": pe["gamma"], "PE Θ/day": pe["theta"],
            "PE Vega": pe["vega"], "PE Vanna": pe["vanna"], "PE Vomma": pe["vomma"],
            "PE Charm": pe["charm"], "PE Zomma": pe["zomma"],
            "PE Speed": pe["speed"], "PE Color": pe["color"],
            "PE Ultima": pe["ultima"], "PE Veta": pe["veta"],
        })
    return pd.DataFrame(rows)

def greek_risk_interpretation(g):
    vol_delta = abs(g["vanna"]) / max(abs(g["delta"]), 0.05)
    gamma_accel = abs(g["zomma"]) + abs(g["speed"])*max(g.get("spot", 1),1)
    time_delta = abs(g["charm"])
    vol_convexity = abs(g["vomma"])

    return {
        "vol_delta_risk": "HIGH" if vol_delta > 0.35 else ("MEDIUM" if vol_delta > 0.15 else "LOW"),
        "gamma_acceleration": "HIGH" if gamma_accel > 0.001 else ("MEDIUM" if gamma_accel > 0.0003 else "LOW"),
        "time_delta_drift": "HIGH" if time_delta > 0.01 else ("MEDIUM" if time_delta > 0.003 else "LOW"),
        "vol_convexity": "HIGH" if vol_convexity > 10 else ("MEDIUM" if vol_convexity > 3 else "LOW"),
    }


def build_greek_surface(spot, strikes, expiries, iv_percent, greek,
                        r_percent=6.5, q_percent=0.0, option="CE"):
    """Return a strike x expiry DataFrame for a selected Greek."""
    aliases = {
        "Delta": "delta", "Gamma": "gamma", "Theta": "theta",
        "Vega": "vega", "Rho": "rho", "Vanna": "vanna",
        "Vomma / Volga": "vomma", "Charm": "charm", "Zomma": "zomma",
        "Speed": "speed", "Color": "color", "Ultima": "ultima", "Veta": "veta",
    }
    field = aliases.get(greek, greek.lower())
    data = {}
    for exp in expiries:
        vals = []
        for k in strikes:
            g = calculate_higher_order_greeks(
                spot, k, exp, iv_percent, r_percent, q_percent, option
            )
            vals.append(g[field])
        data[f"{int(exp)}D"] = vals
    return pd.DataFrame(data, index=[float(x) for x in strikes])

def greek_surface_summary(surface, greek):
    arr = surface.to_numpy(dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return {"min": np.nan, "max": np.nan, "mean": np.nan, "abs_max": np.nan}
    return {
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
        "mean": float(np.mean(finite)),
        "abs_max": float(np.max(np.abs(finite))),
    }
