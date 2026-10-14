
import math
import cmath
import numpy as np
import pandas as pd

from engines.greeks_engine import calculate_higher_order_greeks

def _heston_cf(u, S, T, r, q, v0, kappa, theta, sigma_v, rho):
    """Little-Heston-Trap characteristic function."""
    x = math.log(S)
    a = kappa * theta
    iu = 1j * u
    d = cmath.sqrt((rho * sigma_v * iu - kappa)**2 + sigma_v**2 * (iu + u*u))
    # Stable branch
    if d.real < 0:
        d = -d
    g = (kappa - rho*sigma_v*iu - d) / (kappa - rho*sigma_v*iu + d)
    exp_dT = cmath.exp(-d*T)
    C = (r-q)*iu*T + (a/(sigma_v**2))*(
        (kappa-rho*sigma_v*iu-d)*T
        - 2*cmath.log((1-g*exp_dT)/(1-g))
    )
    D = ((kappa-rho*sigma_v*iu-d)/(sigma_v**2))*(
        (1-exp_dT)/(1-g*exp_dT)
    )
    return cmath.exp(C + D*v0 + iu*x)

def heston_call_price(S, K, T, r, q, v0, kappa, theta, sigma_v, rho, n=900):
    """Numerical Heston call price via probability integrals."""
    T=max(float(T),1e-8)
    S=max(float(S),1e-8); K=max(float(K),1e-8)
    # Simpson grid, avoid u=0 singularity.
    umax=120.0
    xs=np.linspace(1e-5, umax, n+1)
    dx=xs[1]-xs[0]
    phi_mi= _heston_cf(-1j,S,T,r,q,v0,kappa,theta,sigma_v,rho)
    p1_vals=[]; p2_vals=[]
    logK=math.log(K)
    for u in xs:
        cf_u=_heston_cf(u,S,T,r,q,v0,kappa,theta,sigma_v,rho)
        denom=1j*u
        p2=(cmath.exp(-1j*u*logK)*cf_u/denom).real
        cf_shift=_heston_cf(u-1j,S,T,r,q,v0,kappa,theta,sigma_v,rho)
        p1=(cmath.exp(-1j*u*logK)*cf_shift/(1j*u*phi_mi)).real
        p1_vals.append(p1); p2_vals.append(p2)
    # scipy-free Simpson
    def simp(y):
        y=np.asarray(y)
        return dx/3.0*(y[0]+y[-1]+4*np.sum(y[1:-1:2])+2*np.sum(y[2:-1:2]))
    P1=0.5+simp(p1_vals)/math.pi
    P2=0.5+simp(p2_vals)/math.pi
    return float(S*math.exp(-q*T)*P1-K*math.exp(-r*T)*P2)

def heston_price(S,K,days,params,option="CE"):
    r=params["r"]; q=params["q"]; T=max(days/365.0,1e-8)
    call=heston_call_price(S,K,T,r,q,params["v0"],params["kappa"],params["theta"],
                           params["sigma_v"],params["rho"])
    if option.upper() in ("CE","CALL","C"):
        return call
    return call-S*math.exp(-q*T)+K*math.exp(-r*T)

def bsm_price(S,K,days,iv_percent,r_percent,q_percent,option):
    g=calculate_higher_order_greeks(S,K,days,iv_percent,r_percent,q_percent,option)
    return g["price"]

def implied_vol_bsm(price,S,K,days,r_percent,q_percent,option):
    """Bisection IV in percent, with no external optimizer dependency."""
    T=max(days/365.0,1e-8); r=r_percent/100.0; q=q_percent/100.0
    intrinsic=max(0.0, S*math.exp(-q*T)-K*math.exp(-r*T)) if option=="CE" else max(0.0,K*math.exp(-r*T)-S*math.exp(-q*T))
    if price < intrinsic-1e-7:
        return np.nan
    lo,hi=0.001,5.0
    for _ in range(90):
        mid=(lo+hi)/2
        p=bsm_price(S,K,days,mid*100,r_percent,q_percent,option)
        if p>price: hi=mid
        else: lo=mid
    return mid*100

def heston_to_bsm_iv_surface(S,strikes,expiries,params,r_percent,q_percent,option="CE"):
    rows=[]
    for K in strikes:
        row={"Strike":K}
        for d in expiries:
            hp=heston_price(S,K,d,params,option)
            iv=implied_vol_bsm(hp,S,K,d,r_percent,q_percent,option)
            row[f"{int(d)}D"]=iv
        rows.append(row)
    return pd.DataFrame(rows).set_index("Strike")

def model_dislocation(S,K,days,market_iv,r_percent,q_percent,params,option="CE"):
    hp=heston_price(S,K,days,params,option)
    h_iv=implied_vol_bsm(hp,S,K,days,r_percent,q_percent,option)
    bsm_p=bsm_price(S,K,days,market_iv,r_percent,q_percent,option)
    return {
        "market_iv":float(market_iv),
        "heston_iv":float(h_iv),
        "iv_gap":float(h_iv-market_iv),
        "bsm_price":float(bsm_p),
        "heston_price":float(hp),
        "price_gap":float(hp-bsm_p)
    }
