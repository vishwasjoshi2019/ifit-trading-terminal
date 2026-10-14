from collections import deque
from datetime import datetime

class LiveDataEngine:
    def __init__(self, adapter, max_ticks_per_symbol=5000):
        self.adapter=adapter
        self.max_ticks_per_symbol=max_ticks_per_symbol
        self._instruments={}
        self._ticks={}
    @property
    def provider(self): return self.adapter.name
    def health(self): return self.adapter.health()
    def key(self, instrument): return f"{instrument.exchange}:{instrument.segment}:{instrument.symbol}:{instrument.token}"
    def register_instrument(self, instrument):
        k=self.key(instrument); self._instruments[k]=instrument
        self._ticks.setdefault(k,deque(maxlen=self.max_ticks_per_symbol))
    def discover(self, query=""):
        xs=self.adapter.get_instruments(query)
        for x in xs: self.register_instrument(x)
        return xs
    def quote(self, instrument):
        self.register_instrument(instrument)
        t=self.adapter.get_quote(instrument)
        if t is not None: self.ingest(t)
        return t
    def depth(self, instrument):
        self.register_instrument(instrument); return self.adapter.get_depth(instrument)
    def ohlc(self, instrument, timeframe="1m"):
        self.register_instrument(instrument); return self.adapter.get_ohlc(instrument,timeframe)
    def ingest(self, tick):
        k=f"{tick.exchange}:{tick.segment}:{tick.symbol}:{tick.token}"
        self._ticks.setdefault(k,deque(maxlen=self.max_ticks_per_symbol)).append(tick)
    def latest(self, instrument):
        x=self._ticks.get(self.key(instrument)); return x[-1] if x else None
    def history(self, instrument, limit=100):
        return list(self._ticks.get(self.key(instrument),()))[-limit:]
    def snapshot(self):
        return {"timestamp":datetime.now().isoformat(),"provider":self.provider,
                "instruments":len(self._instruments),
                "symbols_with_ticks":sum(bool(x) for x in self._ticks.values())}
    def close(self): self.adapter.close()
