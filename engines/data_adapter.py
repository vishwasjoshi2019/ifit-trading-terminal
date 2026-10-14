
import os
import time
import json
import random
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd
import requests


@dataclass
class DataHealth:
    source: str
    status: str
    last_update: str
    age_seconds: float
    records: int
    latency_ms: float
    message: str
    mode: str

    def to_dict(self):
        return asdict(self)


class IFITDataAdapter:
    """
    Unified data interface for IFIT.

    Modes:
      - SIMULATION: safe local market-data simulator.
      - API: user-supplied authorized broker/vendor JSON endpoint.

    IFIT intentionally does not scrape NSE webpages. For production live data,
    configure an authorized NSE/vendor/broker feed in the environment.
    """

    def __init__(self, mode="SIMULATION", endpoint=None, api_key=None,
                 timeout=8, symbol="NIFTY"):
        self.mode = (mode or "SIMULATION").upper()
        self.endpoint = endpoint or os.getenv("IFIT_DATA_URL", "")
        self.api_key = api_key or os.getenv("IFIT_API_KEY", "")
        self.timeout = timeout
        self.symbol = symbol
        self._last_snapshot = None

    def fetch(self):
        started = time.perf_counter()
        if self.mode == "API":
            return self._fetch_api(started)
        return self._fetch_simulation(started)

    def _fetch_simulation(self, started):
        now = datetime.now(timezone.utc)
        base = 24782.35
        prev = self._last_snapshot.get("spot", base) if self._last_snapshot else base
        move = random.gauss(0, 3.2)
        spot = max(100.0, prev + move)
        futures = spot + random.uniform(-8, 8)

        strikes = np.arange(round(spot/50)*50 - 500,
                            round(spot/50)*50 + 501, 50)
        expiry = "2026-09-24"
        rows = []
        for k in strikes:
            m = (k-spot)/max(spot,1)
            base_iv = 14.5 + 3.0*abs(m)
            ce_ltp = max(0.5, max(spot-k,0)*0.10 + 120*np.exp(-abs(m)*10))
            pe_ltp = max(0.5, max(k-spot,0)*0.10 + 120*np.exp(-abs(m)*10))
            rows.append({
                "symbol": self.symbol, "expiry": expiry, "strike": float(k),
                "CE_LTP": round(float(ce_ltp),2), "PE_LTP": round(float(pe_ltp),2),
                "CE_OI": int(100000*max(0.2,1-abs(m)*2)+random.randint(-3000,3000)),
                "PE_OI": int(100000*max(0.2,1-abs(m)*2)+random.randint(-3000,3000)),
                "CE_IV": round(max(5,base_iv+random.uniform(-0.2,0.2)),2),
                "PE_IV": round(max(5,base_iv+random.uniform(-0.2,0.2)),2),
            })
        snapshot = {
            "timestamp": now.isoformat(),
            "spot": float(spot),
            "futures": float(futures),
            "option_chain": pd.DataFrame(rows),
            "source": "IFIT Simulation",
        }
        self._last_snapshot = snapshot
        latency=(time.perf_counter()-started)*1000
        health=DataHealth("IFIT Simulation","LIVE",snapshot["timestamp"],0,
                          len(rows)+2,latency,"Simulation heartbeat healthy","SIMULATION")
        return snapshot, health

    def _fetch_api(self, started):
        if not self.endpoint:
            health=DataHealth("Authorized API","ERROR","",float("inf"),0,
                              (time.perf_counter()-started)*1000,
                              "IFIT_DATA_URL is not configured","API")
            return None, health

        headers={"Accept":"application/json","User-Agent":"IFIT/0.6.0"}
        if self.api_key:
            headers["Authorization"]=f"Bearer {self.api_key}"
        try:
            r=requests.get(self.endpoint,headers=headers,timeout=self.timeout)
            latency=(time.perf_counter()-started)*1000
            r.raise_for_status()
            payload=r.json()
            snapshot=self._normalize_payload(payload)
            ts=snapshot.get("timestamp") or datetime.now(timezone.utc).isoformat()
            snapshot["timestamp"]=ts
            snapshot["source"]="Authorized API"
            records=len(snapshot.get("option_chain",[]))+2
            health=DataHealth("Authorized API","LIVE",ts,0,records,latency,
                              "API response normalized successfully","API")
            self._last_snapshot=snapshot
            return snapshot, health
        except Exception as exc:
            health=DataHealth("Authorized API","ERROR","",float("inf"),0,
                              (time.perf_counter()-started)*1000,
                              str(exc)[:180],"API")
            return None, health

    def _normalize_payload(self,payload):
        """
        Accept common normalized API shapes:
          {"spot": ..., "futures": ..., "timestamp": ..., "options":[...]}
          {"data": {"spot":..., "options":[...]}}
          {"records":{"data":[{"strikePrice":...,"CE":...,"PE":...}]}}
        """
        root=payload.get("data",payload) if isinstance(payload,dict) else {}
        if isinstance(root,list):
            root={"options":root}
        records=root.get("records",root) if isinstance(root,dict) else {}
        if isinstance(records,dict) and isinstance(records.get("data"),list):
            option_rows=records["data"]
        else:
            option_rows=root.get("options",[]) if isinstance(root,dict) else []

        spot=(root.get("spot") if isinstance(root,dict) else None)
        if spot is None and isinstance(root,dict):
            spot=root.get("underlyingValue",root.get("lastPrice"))
        if spot is None and isinstance(records,dict):
            spot=records.get("spot",records.get("underlyingValue",records.get("lastPrice")))
        futures=(root.get("futures") if isinstance(root,dict) else None)
        if futures is None and isinstance(records,dict):
            futures=records.get("futures")

        normalized=[]
        for item in option_rows or []:
            if not isinstance(item,dict): continue
            ce=item.get("CE") or item.get("ce") or {}
            pe=item.get("PE") or item.get("pe") or {}
            normalized.append({
                "symbol":item.get("symbol",self.symbol),
                "expiry":item.get("expiryDate",item.get("expiry")),
                "strike":float(item.get("strikePrice",item.get("strike",0)) or 0),
                "CE_LTP":float(ce.get("lastPrice",ce.get("ltp",0)) or 0),
                "PE_LTP":float(pe.get("lastPrice",pe.get("ltp",0)) or 0),
                "CE_OI":float(ce.get("openInterest",ce.get("oi",0)) or 0),
                "PE_OI":float(pe.get("openInterest",pe.get("oi",0)) or 0),
                "CE_IV":float(ce.get("impliedVolatility",ce.get("iv",0)) or 0),
                "PE_IV":float(pe.get("impliedVolatility",pe.get("iv",0)) or 0),
            })

        return {
            "timestamp":root.get("timestamp",root.get("time")) if isinstance(root,dict) else None,
            "spot":float(spot) if spot is not None else 0.0,
            "futures":float(futures) if futures is not None else 0.0,
            "option_chain":pd.DataFrame(normalized),
            "source":"Authorized API",
        }


def health_from_snapshot(snapshot, health):
    if snapshot is None:
        return health
    try:
        ts=datetime.fromisoformat(snapshot["timestamp"].replace("Z","+00:00"))
        age=max(0.0,(datetime.now(timezone.utc)-ts).total_seconds())
    except Exception:
        age=0.0
    health.age_seconds=age
    if age > 10:
        health.status="STALE"
        health.message=f"Data age {age:.1f}s exceeds 10s threshold"
    return health
