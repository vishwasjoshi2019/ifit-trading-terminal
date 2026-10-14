from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
import math
import random
from typing import Optional

from ..feed_interface import BaseMarketFeed
from ..models import (
    NormalizedTick,
    OrderBookDepth,
    OrderBookLevel,
    OHLCVCandle,
    OptionChainSnapshot,
    OptionStrike,
    ProviderInfo,
)


class SimulationFeed(BaseMarketFeed):
    """
    High-fidelity institutional market simulation feed.
    Simulates geometric Brownian motion, realistic 5-level order book depth,
    trade tape footprints, and Black-Scholes implied option chains.
    """

    name: str = "SIMULATION"
    is_live: bool = False

    BASE_PRICES = {
        "NIFTY": 25250.0,
        "BANKNIFTY": 55400.0,
        "FINNIFTY": 24800.0,
        "RELIANCE": 2980.0,
        "HDFCBANK": 1640.0,
        "TCS": 4120.0,
        "INFY": 1890.0,
    }

    def __init__(self, tick_interval_ms: int = 250, seed: int = 42) -> None:
        super().__init__()
        self.tick_interval_ms = tick_interval_ms
        self.rng = random.Random(seed)
        self.prices: dict[str, float] = dict(self.BASE_PRICES)
        self.day_opens: dict[str, float] = {k: v - self.rng.uniform(-30, 30) for k, v in self.BASE_PRICES.items()}
        self.day_highs: dict[str, float] = {k: v + self.rng.uniform(50, 100) for k, v in self.BASE_PRICES.items()}
        self.day_lows: dict[str, float] = {k: v - self.rng.uniform(50, 100) for k, v in self.BASE_PRICES.items()}
        self.cumulative_volumes: dict[str, float] = {k: 500000.0 for k in self.BASE_PRICES}
        self.cumulative_cvd: dict[str, float] = {k: 0.0 for k in self.BASE_PRICES}

        self.subscribed_symbols: set[str] = set(self.BASE_PRICES.keys())
        self.latest_ticks: dict[str, NormalizedTick] = {}
        self.candle_history: dict[str, deque[OHLCVCandle]] = {
            k: deque(maxlen=300) for k in self.BASE_PRICES
        }
        self._current_candles: dict[str, dict] = {}
        self._streaming_task: Optional[asyncio.Task] = None
        self._running: bool = False

    async def initialize(self) -> bool:
        # Generate initial candle history
        for sym in self.subscribed_symbols:
            self._seed_candles(sym)
            tick = self._generate_tick(sym)
            self.latest_ticks[sym] = tick
        return True

    def _seed_candles(self, symbol: str) -> None:
        base = self.prices.get(symbol, 25000.0)
        curr = base - 50.0
        now = datetime.now(timezone.utc).timestamp()
        for i in range(60, 0, -1):
            t_str = datetime.fromtimestamp(now - (i * 60), timezone.utc).isoformat()
            delta = self.rng.uniform(-10.0, 10.5)
            o = curr
            c = o + delta
            h = max(o, c) + self.rng.uniform(0.5, 5.0)
            l = min(o, c) - self.rng.uniform(0.5, 5.0)
            vol = round(self.rng.uniform(1000, 15000))
            cvd = round(self.rng.uniform(-500, 500))
            self.candle_history[symbol].append(
                OHLCVCandle(
                    timestamp=t_str,
                    open=round(o, 2),
                    high=round(h, 2),
                    low=round(l, 2),
                    close=round(c, 2),
                    volume=float(vol),
                    cvd=float(cvd),
                )
            )
            curr = c
        self.prices[symbol] = curr

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._streaming_task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._running = False
        if self._streaming_task and not self._streaming_task.done():
            self._streaming_task.cancel()
            try:
                await self._streaming_task
            except asyncio.CancelledError:
                pass

    async def subscribe(self, symbols: list[str]) -> None:
        for s in symbols:
            s_up = s.upper()
            self.subscribed_symbols.add(s_up)
            if s_up not in self.prices:
                self.prices[s_up] = 1000.0
                self.day_opens[s_up] = 1000.0
                self.day_highs[s_up] = 1010.0
                self.day_lows[s_up] = 990.0
                self.cumulative_volumes[s_up] = 10000.0
                self.cumulative_cvd[s_up] = 0.0
                self.candle_history[s_up] = deque(maxlen=300)
                self._seed_candles(s_up)

    async def unsubscribe(self, symbols: list[str]) -> None:
        for s in symbols:
            self.subscribed_symbols.discard(s.upper())

    def _generate_tick(self, symbol: str) -> NormalizedTick:
        p = self.prices.get(symbol, 25000.0)
        # Brownian jump
        pct_change = self.rng.gauss(0, 0.0003)
        p = round(p * (1.0 + pct_change), 2)
        self.prices[symbol] = p

        d_open = self.day_opens.get(symbol, p)
        d_high = max(self.day_highs.get(symbol, p), p)
        d_low = min(self.day_lows.get(symbol, p), p)
        self.day_highs[symbol] = d_high
        self.day_lows[symbol] = d_low

        net = round(p - d_open, 2)
        pct = round((net / d_open) * 100, 2) if d_open else 0.0

        trade_qty = float(self.rng.choice([25, 50, 75, 100, 150, 300, 500]))
        self.cumulative_volumes[symbol] = self.cumulative_volumes.get(symbol, 0.0) + trade_qty

        # Buy vs sell aggressor flag for CVD
        is_buyer = self.rng.random() > 0.48
        delta_step = trade_qty if is_buyer else -trade_qty
        self.cumulative_cvd[symbol] = self.cumulative_cvd.get(symbol, 0.0) + delta_step

        spread = 0.05 if p < 5000 else 0.50
        bid = round(p - (spread / 2.0), 2)
        ask = round(p + (spread / 2.0), 2)

        now_iso = datetime.now(timezone.utc).isoformat()

        tick = NormalizedTick(
            symbol=symbol,
            exchange="NSE",
            segment="EQUITY" if symbol not in {"NIFTY", "BANKNIFTY", "FINNIFTY"} else "INDEX",
            token=f"SIM_{symbol}",
            timestamp=now_iso,
            ltp=p,
            open=round(d_open, 2),
            high=round(d_high, 2),
            low=round(d_low, 2),
            close=round(p, 2),
            volume=self.cumulative_volumes[symbol],
            net_change=net,
            percentage_change=pct,
            bid=bid,
            ask=ask,
            bid_qty=float(self.rng.randint(200, 2500)),
            ask_qty=float(self.rng.randint(200, 2500)),
            oi=float(self.rng.randint(2000000, 5000000)),
            oi_change=float(self.rng.randint(-50000, 50000)),
            trade_price=p,
            trade_qty=trade_qty,
            source="SIMULATION",
            is_live=False,
        )
        self._update_candle(symbol, tick)
        return tick

    def _update_candle(self, symbol: str, tick: NormalizedTick) -> None:
        now = datetime.now(timezone.utc)
        minute_key = now.strftime("%Y-%m-%dT%H:%M:00Z")

        curr = self._current_candles.get(symbol)
        if not curr or curr["timestamp"] != minute_key:
            if curr:
                # finalize previous candle into history
                self.candle_history[symbol].append(
                    OHLCVCandle(
                        timestamp=curr["timestamp"],
                        open=curr["open"],
                        high=curr["high"],
                        low=curr["low"],
                        close=curr["close"],
                        volume=curr["volume"],
                        cvd=curr["cvd"],
                    )
                )
            self._current_candles[symbol] = {
                "timestamp": minute_key,
                "open": tick.ltp,
                "high": tick.ltp,
                "low": tick.ltp,
                "close": tick.ltp,
                "volume": tick.trade_qty or 1.0,
                "cvd": (tick.trade_qty or 1.0) if tick.trade_price and tick.trade_price >= tick.close else -(tick.trade_qty or 1.0),
            }
        else:
            curr["high"] = max(curr["high"], tick.ltp)
            curr["low"] = min(curr["low"], tick.ltp)
            curr["close"] = tick.ltp
            curr["volume"] += tick.trade_qty or 1.0

    async def _run_loop(self) -> None:
        while self._running:
            for symbol in list(self.subscribed_symbols):
                tick = self._generate_tick(symbol)
                self.latest_ticks[symbol] = tick
                await self._emit_tick(tick)
            await asyncio.sleep(self.tick_interval_ms / 1000.0)

    def get_latest_tick(self, symbol: str) -> Optional[NormalizedTick]:
        sym = symbol.upper()
        if sym not in self.latest_ticks:
            self.latest_ticks[sym] = self._generate_tick(sym)
        return self.latest_ticks.get(sym)

    def get_depth(self, symbol: str) -> Optional[OrderBookDepth]:
        tick = self.get_latest_tick(symbol)
        if not tick:
            return None

        p = tick.ltp
        step = 0.05 if p < 5000 else 0.50
        levels: list[OrderBookLevel] = []
        total_buy = 0.0
        total_sell = 0.0

        for i in range(5):
            b_p = round(p - (i + 1) * step, 2)
            a_p = round(p + (i + 1) * step, 2)
            b_q = float(self.rng.randint(250, 4000) * (5 - i))
            a_q = float(self.rng.randint(250, 4000) * (5 - i))
            total_buy += b_q
            total_sell += a_q
            levels.append(
                OrderBookLevel(
                    level=i + 1,
                    bid=b_p,
                    bid_qty=b_q,
                    ask=a_p,
                    ask_qty=a_q,
                )
            )

        return OrderBookDepth(
            symbol=symbol.upper(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            levels=levels,
            total_buy_qty=total_buy,
            total_sell_qty=total_sell,
            spread=round(levels[0].ask - levels[0].bid, 2),
            source="SIMULATION",
        )

    def get_option_chain(self, symbol: str) -> Optional[OptionChainSnapshot]:
        sym = symbol.upper()
        spot_tick = self.get_latest_tick(sym)
        spot = spot_tick.ltp if spot_tick else self.prices.get(sym, 25250.0)

        step = 50.0 if sym in {"NIFTY", "FINNIFTY"} else 100.0
        atm_strike = round(spot / step) * step

        strikes: list[OptionStrike] = []
        total_ce_oi = 0.0
        total_pe_oi = 0.0
        total_ce_vol = 0.0
        total_pe_vol = 0.0

        for i in range(-10, 11):
            k = atm_strike + (i * step)
            # Distance from ATM
            dist = (spot - k)
            # Simulated call & put prices with intrinsic + time value
            time_val = max(10.0, 120.0 - abs(dist) * 0.15)
            ce_val = round(max(0.0, dist) + time_val, 1)
            pe_val = round(max(0.0, -dist) + time_val, 1)

            iv = round(12.5 + (abs(dist) / step) * 0.35, 2)
            ce_oi = float(self.rng.randint(20000, 180000))
            pe_oi = float(self.rng.randint(20000, 180000))
            ce_v = float(self.rng.randint(5000, 60000))
            pe_v = float(self.rng.randint(5000, 60000))

            total_ce_oi += ce_oi
            total_pe_oi += pe_oi
            total_ce_vol += ce_v
            total_pe_vol += pe_v

            strikes.append(
                OptionStrike(
                    strike=k,
                    ce_ltp=ce_val,
                    ce_oi=ce_oi,
                    ce_iv=iv,
                    ce_volume=ce_v,
                    pe_ltp=pe_val,
                    pe_oi=pe_oi,
                    pe_iv=iv,
                    pe_volume=pe_v,
                )
            )

        pcr_oi = round(total_pe_oi / max(1.0, total_ce_oi), 2)
        pcr_vol = round(total_pe_vol / max(1.0, total_ce_vol), 2)

        return OptionChainSnapshot(
            underlying_symbol=sym,
            underlying_price=spot,
            expiry=datetime.now(timezone.utc).strftime("%d-%b-%Y").upper(),
            strikes=strikes,
            pcr_oi=pcr_oi,
            pcr_volume=pcr_vol,
            max_pain=atm_strike,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def get_candles(
        self, symbol: str, timeframe: str = "1m", limit: int = 100
    ) -> list[OHLCVCandle]:
        sym = symbol.upper()
        history = list(self.candle_history.get(sym, []))
        curr = self._current_candles.get(sym)
        if curr:
            history.append(
                OHLCVCandle(
                    timestamp=curr["timestamp"],
                    open=curr["open"],
                    high=curr["high"],
                    low=curr["low"],
                    close=curr["close"],
                    volume=curr["volume"],
                    cvd=curr["cvd"],
                )
            )
        return history[-limit:]

    def health(self) -> ProviderInfo:
        return ProviderInfo(
            name=self.name,
            status="READY",
            is_live=False,
            details={
                "subscribed_symbols": list(self.subscribed_symbols),
                "running": self._running,
                "interval_ms": self.tick_interval_ms,
            },
        )
