from abc import ABC, abstractmethod

class LiveDataAdapter(ABC):
    name = "BASE"
    @abstractmethod
    def health(self): raise NotImplementedError
    @abstractmethod
    def get_instruments(self, query=""): raise NotImplementedError
    @abstractmethod
    def get_quote(self, instrument): raise NotImplementedError
    def get_depth(self, instrument): return {}
    def get_ohlc(self, instrument, timeframe="1m"): return None
    def subscribe_ticks(self, instruments, on_tick): raise NotImplementedError
    def close(self): pass
