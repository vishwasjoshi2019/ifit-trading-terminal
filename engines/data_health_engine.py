
import pandas as pd

def health_frame(health):
    return pd.DataFrame([{
        "Source": health.source,
        "Mode": health.mode,
        "Status": health.status,
        "Data Age (s)": health.age_seconds,
        "Records": health.records,
        "Latency (ms)": health.latency_ms,
        "Message": health.message,
    }])

def health_label(status):
    return {
        "LIVE":"● LIVE",
        "STALE":"● STALE",
        "ERROR":"● ERROR",
        "DISCONNECTED":"● DISCONNECTED",
    }.get(status,status)

def data_quality(snapshot):
    if snapshot is None:
        return {"score":0,"label":"NO DATA","issues":["No snapshot available."]}
    issues=[]
    spot=float(snapshot.get("spot",0) or 0)
    chain=snapshot.get("option_chain",pd.DataFrame())
    if spot<=0: issues.append("Spot missing or invalid.")
    if chain.empty: issues.append("Option chain empty.")
    else:
        for col in ["strike","CE_LTP","PE_LTP","CE_OI","PE_OI"]:
            if col not in chain.columns: issues.append(f"{col} missing.")
    score=max(0,100-len(issues)*20)
    return {"score":score,"label":"GOOD" if score>=80 else ("DEGRADED" if score>=50 else "POOR"),
            "issues":issues}
