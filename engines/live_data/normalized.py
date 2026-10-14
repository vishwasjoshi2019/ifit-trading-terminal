from dataclasses import dataclass, asdict, field
from typing import Any, Optional


@dataclass
class Instrument:
    symbol: str
    exchange: str
    segment: str = ""
    token: str = ""
    instrument_type: str = ""
    expiry: str = ""
    strike: Optional[float] = None
    option_type: str = ""
    lot_size: Optional[int] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


@dataclass
class NormalizedTick:
    symbol: str
    exchange: str = ""
    segment: str = ""
    token: str = ""
    timestamp: Any = None

    # Price
    ltp: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    previous_close: Optional[float] = None
    net_change: Optional[float] = None

    # Volume / trade
    volume: Optional[float] = None
    average_price: Optional[float] = None
    last_quantity: Optional[float] = None
    last_trade_time: Any = None

    # Bid / Ask
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_qty: Optional[float] = None
    ask_qty: Optional[float] = None
    buy_quantity: Optional[float] = None
    sell_quantity: Optional[float] = None

    # Open Interest
    oi: Optional[float] = None
    oi_change: Optional[float] = None
    oi_day_high: Optional[float] = None
    oi_day_low: Optional[float] = None

    # Circuit limits
    upper_circuit_limit: Optional[float] = None
    lower_circuit_limit: Optional[float] = None

    # Trade-level fields
    trade_price: Optional[float] = None
    trade_qty: Optional[float] = None

    # Market depth
    depth: dict[str, Any] = field(default_factory=dict)

    # Source metadata
    source: str = ""
    is_live: bool = False
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

    @property
    def spread(self):
        if self.bid is None or self.ask is None:
            return None

        return self.ask - self.bid