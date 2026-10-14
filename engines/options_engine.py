
import math
import numpy as np
import pandas as pd

def cdf(x): return 0.5*(1+math.erf(x/math.sqrt(2)))
def pdf(x): return math.exp(-x*x/2)/math.sqrt(2*math.pi)

def bs_price(S,K,T,r,sigma,typ):
    T=max(T,1e-8); sigma=max(sigma,1e-8)
    d1=(math.log(S/K)+(r+.5*sigma*sigma)*T)/(sigma*math.sqrt(T)); d2=d1-sigma*math.sqrt(T)
    if typ=="CE": return S*cdf(d1)-K*math.exp(-r*T)*cdf(d2)
    return K*math.exp(-r*T)*cdf(-d2)-S*cdf(-d1)

def greeks(S,K,T,r,sigma,typ):
    T=max(T,1e-8); sigma=max(sigma,1e-8)
    d1=(math.log(S/K)+(r+.5*sigma*sigma)*T)/(sigma*math.sqrt(T))
    d2=d1-sigma*math.sqrt(T)
    delta=cdf(d1) if typ=="CE" else cdf(d1)-1
    gamma=pdf(d1)/(S*sigma*math.sqrt(T))
    theta=(-S*pdf(d1)*sigma/(2*math.sqrt(T))-r*K*math.exp(-r*T)*cdf(d2)) if typ=="CE" else (-S*pdf(d1)*sigma/(2*math.sqrt(T))+r*K*math.exp(-r*T)*cdf(-d2))
    vega=S*pdf(d1)*math.sqrt(T)/100
    return delta,gamma,theta/365,vega

def build_option_chain(spot,days,atm_iv):
    T=days/365; atm=round(spot/100)*100; strikes=np.arange(atm-1500,atm+1501,100)
    rng=np.random.default_rng(42); rows=[]
    for K in strikes:
        ceoi=int(max(5000,rng.lognormal(10.4,.48)*(1+2*math.exp(-((K-(spot+250))/350)**2))))
        peoi=int(max(5000,rng.lognormal(10.4,.48)*(1+2.3*math.exp(-((K-(spot-300))/350)**2))))
        cechg=int(rng.normal(ceoi*.035,max(500,ceoi*.07))); pechg=int(rng.normal(peoi*.035,max(500,peoi*.07)))
        smile=.00002*(K-spot)**2/10
        ceiv=atm_iv+smile+.30*max(0,(spot-K))/100
        peiv=atm_iv+smile+.30*max(0,(K-spot))/100
        cd,cg,ct,cv=greeks(spot,K,T,.065,ceiv/100,"CE"); pd_,pg,pt,pv=greeks(spot,K,T,.065,peiv/100,"PE")
        rows.append([K,ceoi,cechg,bs_price(spot,K,T,.065,ceiv/100,"CE"),ceiv,cd,cg,ct,cv,
                     bs_price(spot,K,T,.065,peiv/100,"PE"),peiv,pd_,pg,pt,pv,pechg,peoi])
    df=pd.DataFrame(rows,columns=["Strike","CE OI","CE ΔOI","CE LTP","CE IV","CE Δ","CE Γ","CE Θ/day","CE Vega","PE LTP","PE IV","PE Δ","PE Γ","PE Θ/day","PE Vega","PE ΔOI","PE OI"])
    df["Moneyness"]=np.where(df.Strike==atm,"ATM",np.where(df.Strike<spot,"CE ITM / PE OTM","CE OTM / PE ITM"))
    return df

def calculate_metrics(df,spot,days,iv):
    pcr=df["PE OI"].sum()/df["CE OI"].sum()
    pains=[]
    for settle in df["Strike"]:
        pains.append((settle,float((np.maximum(settle-df.Strike,0)*df["CE OI"]+np.maximum(df.Strike-settle,0)*df["PE OI"]).sum())))
    maxpain=min(pains,key=lambda x:x[1])[0]
    move=spot*(iv/100)*math.sqrt(days/365)
    ge=df["CE Γ"]*df["CE OI"]*(-1)+df["PE Γ"]*df["PE OI"]
    crossings=[]
    for i in range(1,len(df)):
        if ge.iloc[i-1]*ge.iloc[i]<0: crossings.append(float((df.Strike.iloc[i-1]+df.Strike.iloc[i])/2))
    flip=min(crossings,key=lambda x:abs(x-spot)) if crossings else None
    return {"atm":round(spot/100)*100,"pcr":pcr,"max_pain":maxpain,"move":move,"gamma_flip":flip,"regime":"IV PREMIUM"}
