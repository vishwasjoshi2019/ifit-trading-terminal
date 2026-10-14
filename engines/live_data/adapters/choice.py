import os, requests
from .base import LiveDataAdapter

class ChoiceAdapter(LiveDataAdapter):
    name="CHOICE"
    def __init__(self):
        self.api_key=os.getenv("CHOICE_API_KEY")
        self.base_url=os.getenv("CHOICE_BASE_URL","https://finx.choiceindia.com/api/OpenAPI").rstrip("/")
        self.ws_url=os.getenv("CHOICE_WS_URL","wss://finxsocket.choiceindia.com/ws/")
        self.timeout=int(os.getenv("CHOICE_TIMEOUT","15"))
        self.session=requests.Session()
    def health(self):
        return {"provider":self.name,"status":"CONFIGURED" if self.api_key else "MISSING_API_KEY",
                "mode":"TYPE_A_DIRECT_CLIENT","api_key_set":bool(self.api_key),
                "api_key_length":len(self.api_key) if self.api_key else 0,
                "base_url":self.base_url,"ws_url":self.ws_url}
    def _headers(self):
        if not self.api_key: raise RuntimeError("CHOICE_API_KEY is not set.")
        return {"X-API-Key":self.api_key,"Accept":"application/json","Content-Type":"application/json"}
    def get_instruments(self, query=""):
        raise NotImplementedError("Populate from Choice's exact current Type-A schema.")
    def get_quote(self, instrument):
        raise NotImplementedError("Populate from Choice's exact current Type-A schema.")
    def get_depth(self, instrument):
        raise NotImplementedError("Populate from Choice's exact current Type-A schema.")
    def get_ohlc(self, instrument, timeframe="1m"):
        raise NotImplementedError("Populate from Choice's exact current Type-A schema.")
    def request_raw(self, endpoint, method="POST", payload=None):
        u=f"{self.base_url}/{endpoint.lstrip('/')}"
        kw={"headers":self._headers(),"timeout":self.timeout}
        if payload is not None: kw["json"]=payload
        r=self.session.request(method.upper(),u,**kw)
        try: body=r.json()
        except: body=r.text
        return {"url":u,"status_code":r.status_code,"ok":r.ok,"body":body}
