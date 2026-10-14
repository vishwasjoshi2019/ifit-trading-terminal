import math
from dataclasses import dataclass, asdict
from datetime import date, datetime, timezone

@dataclass
class GreekResult:
    delta: float; gamma: float; theta: float; vega: float; rho: float
    vanna: float; vomma: float; charm: float; zomma: float
    speed: float; color: float; ultima: float; veta: float
    def as_dict(self): return asdict(self)

def _f(x, d=0.0):
    try: return float(x) if x not in (None, "") else d
    except (TypeError, ValueError): return d

def _pdf(x): return math.exp(-0.5*x*x)/math.sqrt(2*math.pi)
def _cdf(x): return 0.5*(1+math.erf(x/math.sqrt(2)))
def _iv(x):
    x=_f(x,0.2)
    return x/100 if x>3 else max(x,1e-8)

def years_to_expiry(expiry, now=None):
    if expiry in (None,""): return 30/365
    base=now or datetime.now(timezone.utc)
    if isinstance(base,date) and not isinstance(base,datetime):
        base=datetime.combine(base,datetime.min.time(),tzinfo=timezone.utc)
    if isinstance(expiry,datetime): dt=expiry
    elif isinstance(expiry,date): dt=datetime.combine(expiry,datetime.min.time())
    else:
        dt=None
        for fmt in ("%Y-%m-%d","%Y-%m-%dT%H:%M:%S","%Y-%m-%dT%H:%M:%S.%f","%d-%b-%Y","%d-%B-%Y"):
            try: dt=datetime.strptime(str(expiry),fmt); break
            except ValueError: pass
        if dt is None: return max(_f(expiry,30/365),1e-8)
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    return max((dt-base).total_seconds()/(365*86400),1e-8)

def bsm_greeks(spot,strike,years,rate,iv,option_type="CE"):
    S=max(_f(spot),1e-12); K=max(_f(strike),1e-12); T=max(_f(years),1e-8)
    r=_f(rate); r=r/100 if abs(r)>1 else r; sig=_iv(iv); st=math.sqrt(T)
    d1=(math.log(S/K)+(r+.5*sig*sig)*T)/(sig*st); d2=d1-sig*st
    p=_pdf(d1); disc=math.exp(-r*T); call=str(option_type).upper() in ("CE","C","CALL")
    delta=_cdf(d1) if call else _cdf(d1)-1
    gamma=p/(S*sig*st); vega=S*p*st
    theta=-(S*p*sig)/(2*st)-r*K*disc*_cdf(d2) if call else -(S*p*sig)/(2*st)+r*K*disc*_cdf(-d2)
    rho=K*T*disc*_cdf(d2) if call else -K*T*disc*_cdf(-d2)
    vanna=-p*d2/sig; vomma=vega*d1*d2/sig
    charm=-p*(2*r*T-d2*sig*st)/(2*T*sig*st)
    zomma=gamma*(d1*d2-1)/sig
    speed=-gamma/S*(1+d1/(sig*st))
    color=-gamma*(1/(2*T)+(2*r*T-d2*sig*st)*d1/(2*T*sig*st))
    d1s=-d1/sig+.5*st; d2s=d1s-st
    factor=((d1+d2)*d1s*d2+d1*d2*d2s)/sig-(d1*d2)/(sig*sig)
    ultima=vomma*(d1*d2/sig+factor)
    veta=vega*(1/(2*T)-d1*(r+.5*sig*sig)/(sig*st))
    return GreekResult(delta,gamma,theta,vega,rho,vanna,vomma,charm,zomma,speed,color,ultima,veta)

def chain_greek_rows(options,spot,risk_free_rate=.06,now=None):
    rows=[]
    for item in options:
        strike=_f(item.get("strikePrice",item.get("strike"))); expiry=item.get("expiryDate",item.get("expiry"))
        T=years_to_expiry(expiry,now)
        for side in ("CE","PE"):
            leg=item.get(side) or item.get(side.lower()) or item.get("call" if side=="CE" else "put")
            if not isinstance(leg,dict): continue
            iv=leg.get("impliedVolatility",leg.get("iv",leg.get("IV")))
            g=bsm_greeks(spot,strike,T,risk_free_rate,iv,side).as_dict()
            rows.append({"symbol":item.get("symbol","NIFTY"),"expiry":expiry,"strike":strike,"option":side,
                         "ltp":_f(leg.get("lastPrice",leg.get("ltp"))),"oi":_f(leg.get("openInterest",leg.get("oi"))),
                         "volume":_f(leg.get("volume")),"iv":_iv(iv)*100,**g})
    return rows
