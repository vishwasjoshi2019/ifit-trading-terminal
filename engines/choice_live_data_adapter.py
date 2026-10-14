from __future__ import annotations
import json, os
from dataclasses import dataclass, asdict
from typing import Any, Optional, Callable
import requests

@dataclass
class IFITTick:
    symbol: str
    exchange: str = ""
    timestamp: Any = None
    ltp: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_volume: Optional[float] = None
    ask_volume: Optional[float] = None
    oi: Optional[float] = None
    oi_change: Optional[float] = None
    raw: Optional[dict] = None
    def to_dict(self): return asdict(self)

class ChoiceLiveDataAdapter:
    def __init__(self):
        self.api_key=os.getenv("CHOICE_API_KEY")
        self.base_url=os.getenv("CHOICE_BASE_URL","https://finx.choiceindia.com/api/OpenAPI").rstrip("/")
        self.api_key_header=os.getenv("CHOICE_API_KEY_HEADER","X-API-Key")
        self.ws_url=os.getenv("CHOICE_WS_URL","wss://finxsocket.choiceindia.com/ws/")
        self.timeout=int(os.getenv("CHOICE_TIMEOUT","15"))
        self.session=requests.Session()

    def health(self):
        return {"provider":"Choice","mode":"Type A - Direct Client",
                "api_key_set":bool(self.api_key),
                "api_key_length":len(self.api_key) if self.api_key else 0,
                "base_url":self.base_url,"ws_url":self.ws_url}

    def _headers(self):
        if not self.api_key: raise RuntimeError("CHOICE_API_KEY is not set.")
        return {self.api_key_header:self.api_key,"Accept":"application/json","Content-Type":"application/json"}

    def request(self, endpoint, method="POST", payload=None):
        url=f"{self.base_url}/{endpoint.lstrip('/')}"
        kw={"headers":self._headers(),"timeout":self.timeout}
        if payload is not None: kw["json"]=payload
        r=self.session.request(method.upper(),url,**kw)
        try: body=r.json()
        except Exception: body=r.text
        return {"url":url,"status_code":r.status_code,"ok":r.ok,"body":body}

    def get_instruments(self,payload=None,method="POST"): return self.request("/instruments",method,payload)
    def get_quote(self,payload=None,method="POST"): return self.request("/quote",method,payload)
    def get_ohlc(self,payload=None,method="POST"): return self.request("/ohlc",method,payload)
    def get_depth(self,payload=None,method="POST"): return self.request("/depth",method,payload)

    def websocket_url(self,jwt=None):
        token=jwt or os.getenv("CHOICE_JWT")
        if not token: raise RuntimeError("CHOICE_JWT is not set. Obtain it from Choice Logon/2FA.")
        return f"{self.ws_url}{'&' if '?' in self.ws_url else '?'}token={token}"

    def websocket_connect(self,on_message:Callable[[dict],None],jwt=None):
        import websocket
        def msg(ws,m):
            try: on_message(json.loads(m))
            except Exception: on_message({"raw_message":m})
        ws=websocket.WebSocketApp(self.websocket_url(jwt),on_message=msg)
        ws.run_forever(ping_interval=20,ping_timeout=10)
        return ws

def normalize_tick(data:dict,symbol=""):
    def p(*names):
        for n in names:
            if n in data and data[n] not in (None,""): return data[n]
    def f(v):
        try: return float(v) if v is not None else None
        except: return None
    return IFITTick(
        symbol=str(p("symbol","Symbol","tradingsymbol","TradingSymbol") or symbol),
        exchange=str(p("exchange","Exchange","segment","Segment") or ""),
        timestamp=p("timestamp","Timestamp","time","Time"),
        ltp=f(p("ltp","LTP","last","LastPrice")),
        open=f(p("open","Open")), high=f(p("high","High")), low=f(p("low","Low")),
        close=f(p("close","Close","prev_close","PreviousClose")),
        volume=f(p("volume","Volume","total_volume","TotalVolume")),
        bid=f(p("bid","Bid","best_bid","BestBid")), ask=f(p("ask","Ask","best_ask","BestAsk")),
        bid_volume=f(p("bid_volume","BidVolume")), ask_volume=f(p("ask_volume","AskVolume")),
        oi=f(p("oi","OI","open_interest","OpenInterest")),
        oi_change=f(p("oi_change","OIChange","open_interest_change")),
        raw=data)
