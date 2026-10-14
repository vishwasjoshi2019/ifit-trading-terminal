from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class OrderBookLevel(BaseModel):
    level: int
    bid: float
    bid_qty: float
    ask: float
    ask_qty: float


class OrderBookDepth(BaseModel):
    symbol: str
    timestamp: str
    levels: list[OrderBookLevel] = Field(default_factory=list)
    total_buy_qty: float = 0.0
    total_sell_qty: float = 0.0
    spread: float = 0.0
    source: str = ""


class NormalizedTick(BaseModel):
    symbol: str
    exchange: str = "NSE"
    segment: str = "EQUITY"
    token: str = ""
    timestamp: str
    ltp: float
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    net_change: float = 0.0
    percentage_change: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    bid_qty: float = 0.0
    ask_qty: float = 0.0
    oi: float = 0.0
    oi_change: float = 0.0
    trade_price: Optional[float] = None
    trade_qty: Optional[float] = None
    source: str = ""
    is_live: bool = False


class OHLCVCandle(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    cvd: float = 0.0
    oi: float = 0.0


class OptionStrike(BaseModel):
    strike: float
    ce_ltp: float = 0.0
    ce_oi: float = 0.0
    ce_iv: float = 0.0
    ce_volume: float = 0.0
    pe_ltp: float = 0.0
    pe_oi: float = 0.0
    pe_iv: float = 0.0
    pe_volume: float = 0.0


class OptionChainSnapshot(BaseModel):
    underlying_symbol: str
    underlying_price: float
    expiry: str
    strikes: list[OptionStrike] = Field(default_factory=list)
    pcr_oi: float = 0.0
    pcr_volume: float = 0.0
    max_pain: float = 0.0
    timestamp: str


class ProviderInfo(BaseModel):
    name: str
    status: str
    is_live: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class MarketSnapshot(BaseModel):
    symbol: str
    tick: Optional[NormalizedTick] = None
    depth: Optional[OrderBookDepth] = None
    recent_candles: list[OHLCVCandle] = Field(default_factory=list)
    cvd_total: float = 0.0
    timestamp: str
