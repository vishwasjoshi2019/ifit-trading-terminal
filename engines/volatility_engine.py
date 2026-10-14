
import math
import pandas as pd

def expected_move_table(spot,iv,days):
    one=spot*(iv/100)*math.sqrt(max(days,1)/365)
    rows=[]
    for z,label in [(0.5,"50%"),(1.0,"68%"),(1.28,"80%"),(1.645,"90%"),(1.96,"95%")]:
        m=one*z; rows.append([label,round(spot-m),round(spot+m),round(m)])
    return pd.DataFrame(rows,columns=["Band","Lower","Upper","Move"])

def volatility_snapshot(iv,hv):
    premium=iv-hv; ratio=iv/hv if hv else 0
    regime="IV PREMIUM" if premium>1 else ("IV DISCOUNT" if premium<-1 else "BALANCED")
    return {"premium":premium,"ratio":ratio,"regime":regime,"premium_score":min(1,max(0,.5+premium/10))}


def gamma_exposure(chain):
    def find_column(candidates, label):
        for name in candidates:
            if name in chain.columns:
                return name
        raise ValueError(
            f"Gamma exposure requires a {label} column. "
            f"Available columns: {list(chain.columns)}"
        )

    strike_col = find_column(["Strike", "strike"], "strike")
    ce_gamma_col = find_column(
        ["CE Γ", "CE_GAMMA", "CE GAMMA"], "call gamma"
    )
    pe_gamma_col = find_column(
        ["PE Γ", "PE_GAMMA", "PE GAMMA"], "put gamma"
    )
    ce_oi_col = find_column(["CE OI", "CE_OI"], "call open interest")
    pe_oi_col = find_column(["PE OI", "PE_OI"], "put open interest")

    ce_gamma = pd.to_numeric(chain[ce_gamma_col], errors="raise")
    pe_gamma = pd.to_numeric(chain[pe_gamma_col], errors="raise")
    ce_oi = pd.to_numeric(chain[ce_oi_col], errors="raise")
    pe_oi = pd.to_numeric(chain[pe_oi_col], errors="raise")

    ge = (ce_gamma * ce_oi * -1 + pe_gamma * pe_oi) * 100

    return pd.DataFrame({
        "Strike": chain[strike_col],
        "Gamma Exposure": ge.values,
    })

