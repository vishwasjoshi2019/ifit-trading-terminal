import random
from datetime import datetime
from ..normalized import Instrument, NormalizedTick
from .base import LiveDataAdapter

class SimulationAdapter(LiveDataAdapter):
    name="SIMULATION"
    def __init__(self, seed=42):
        self.rng=random.Random(seed)
        self.prices={"NIFTY":25000.0,"BANKNIFTY":55000.0,"SENSEX":82000.0}
    def health(self): return {"provider":self.name,"status":"OK","mode":"SIMULATION","is_live":False}
    def get_instruments(self, query=""):
        xs=[Instrument("NIFTY","NSE","NSE-CM","SIM-NIFTY","INDEX"),
            Instrument("BANKNIFTY","NSE","NSE-CM","SIM-BANKNIFTY","INDEX"),
            Instrument("SENSEX","BSE","BSE-CM","SIM-SENSEX","INDEX")]
        q=query.upper().strip()
        return [x for x in xs if not q or q in x.symbol]
    def get_quote(self, instrument):
        p=self.prices.get(instrument.symbol,1000.0)+self.rng.uniform(-15,15)
        self.prices[instrument.symbol]=p
        return NormalizedTick(symbol=instrument.symbol,exchange=instrument.exchange,
            segment=instrument.segment,token=instrument.token,timestamp=datetime.now().isoformat(),
            ltp=round(p,2),open=round(p-20,2),high=round(p+30,2),low=round(p-35,2),
            previous_close=round(p-10,2),volume=float(self.rng.randint(100000,1000000)),
            bid=round(p-.5,2),ask=round(p+.5,2),bid_qty=float(self.rng.randint(100,5000)),
            ask_qty=float(self.rng.randint(100,5000)),source="SIMULATION",is_live=False)
    def get_depth(self,instrument):
        q=self.get_quote(instrument)
        return {"symbol":instrument.symbol,"levels":[
            {"level":i+1,"bid":round(q.ltp-.5-i*.5,2),"bid_qty":int(q.bid_qty)+i*100,
             "ask":round(q.ltp+.5+i*.5,2),"ask_qty":int(q.ask_qty)+i*100} for i in range(5)],
            "source":"SIMULATION"}
