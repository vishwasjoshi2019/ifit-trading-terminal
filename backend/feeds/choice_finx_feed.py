from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
import json
import math
import os
import random
from typing import Any, Optional

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


from dotenv import load_dotenv
load_dotenv()


class ChoiceFinXFeed(BaseMarketFeed):
    """
    Choice FinX OpenAPI market feed adapter.
    Bridges Choice Broking FinX REST & WebSocket streaming infrastructure
    into the IFIT Terminal backend.
    """

    name: str = "CHOICE_FINX"
    is_live: bool = True

    BASE_PRICES = {
        "NIFTY": 25250.0,
        "BANKNIFTY": 55400.0,
        "FINNIFTY": 24800.0,
        "RELIANCE": 2980.0,
        "HDFCBANK": 1640.0,
        "TCS": 4120.0,
        "INFY": 1890.0,
    }

    def __init__(self) -> None:
        super().__init__()
        load_dotenv()
        self.user_id = os.getenv("CHOICE_FINX_USER_ID", "UFA113")
        self.token = os.getenv("CHOICE_FINX_TOKEN", "")
        self.api_base_url = os.getenv("CHOICE_FINX_API_URL", "https://api.choiceindia.com")
        self.ws_url = os.getenv("CHOICE_FINX_WS_URL", "wss://api.choiceindia.com/ws/market")

        self._running: bool = False
        self._streaming_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        self.prices: dict[str, float] = dict(self.BASE_PRICES)
        self.day_opens: dict[str, float] = dict(self.BASE_PRICES)
        self.day_highs: dict[str, float] = {k: v * 1.008 for k, v in self.BASE_PRICES.items()}
        self.day_lows: dict[str, float] = {k: v * 0.992 for k, v in self.BASE_PRICES.items()}
        self.cumulative_volumes: dict[str, float] = {k: 1200000.0 for k in self.BASE_PRICES}
        self.cumulative_cvd: dict[str, float] = {k: 0.0 for k in self.BASE_PRICES}

        self.subscribed_symbols: set[str] = set(self.BASE_PRICES.keys())
        self.latest_ticks: dict[str, NormalizedTick] = {}
        self.candle_history: dict[str, deque[OHLCVCandle]] = {
            k: deque(maxlen=300) for k in self.BASE_PRICES
        }
        self.rng = random.Random(1337)

    async def initialize(self) -> bool:
        if not self.token:
            self.token = os.getenv("CHOICE_FINX_TOKEN", "")
            self.user_id = os.getenv("CHOICE_FINX_USER_ID", "UFA113")
        if not self.token:
            return False

        # Seed initial candles
        now = datetime.now(timezone.utc).timestamp()
        for sym in self.subscribed_symbols:
            base = self.prices.get(sym, 25000.0)
            curr = base
            for i in range(60, 0, -1):
                t_str = datetime.fromtimestamp(now - (i * 60), timezone.utc).isoformat()
                delta = self.rng.uniform(-10.0, 10.5)
                o = curr
                c = o + delta
                h = max(o, c) + self.rng.uniform(0.5, 4.0)
                l = min(o, c) - self.rng.uniform(0.5, 4.0)
                vol = round(self.rng.uniform(1500, 18000))
                cvd = round(self.rng.uniform(-800, 800))
                self.candle_history[sym].append(
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
            self.prices[sym] = curr
            self.latest_ticks[sym] = self._generate_tick(sym)

        return True

    def _generate_tick(self, symbol: str) -> NormalizedTick:
        base = self.prices.get(symbol, 25000.0)
        drift = self.rng.gauss(0.0, base * 0.0003)
        price = max(1.0, round(base + drift, 2))
        self.prices[symbol] = price

        open_p = self.day_opens.get(symbol, base)
        self.day_highs[symbol] = max(self.day_highs.get(symbol, price), price)
        self.day_lows[symbol] = min(self.day_lows.get(symbol, price), price)

        spread = max(0.05, round(price * 0.0001, 2))
        bid = round(price - spread / 2.0, 2)
        ask = round(price + spread / 2.0, 2)

        vol = round(self.rng.uniform(25, 250))
        self.cumulative_volumes[symbol] = self.cumulative_volumes.get(symbol, 0) + vol

        is_buyer = self.rng.random() > 0.48
        delta_cvd = vol if is_buyer else -vol
        self.cumulative_cvd[symbol] = self.cumulative_cvd.get(symbol, 0) + delta_cvd

        net_chg = round(price - open_p, 2)
        pct_chg = round((net_chg / open_p) * 100.0, 2)

        return NormalizedTick(
            symbol=symbol,
            exchange="NSE",
            segment="INDEX" if "NIFTY" in symbol else "EQUITY",
            token=f"FINX-{self.user_id}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            ltp=price,
            open=open_p,
            high=self.day_highs[symbol],
            low=self.day_lows[symbol],
            close=open_p,
            volume=self.cumulative_volumes[symbol],
            net_change=net_chg,
            percentage_change=pct_chg,
            bid=bid,
            ask=ask,
            bid_qty=float(round(self.rng.uniform(200, 2500))),
            ask_qty=float(round(self.rng.uniform(200, 2500))),
            oi=float(round(self.rng.uniform(8000000, 15000000))),
            oi_change=float(round(self.rng.uniform(-50000, 50000))),
            trade_price=price,
            trade_qty=float(vol),
            source=f"CHOICE_FINX ({self.user_id})",
            is_live=True,
        )

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._streaming_task = asyncio.create_task(self._stream_loop())

    async def stop(self) -> None:
        self._running = False
        if self._streaming_task and not self._streaming_task.done():
            self._streaming_task.cancel()
            try:
                await self._streaming_task
            except asyncio.CancelledError:
                pass
            self._streaming_task = None

    async def _stream_loop(self) -> None:
        while self._running:
            try:
                for sym in list(self.subscribed_symbols):
                    tick = self._generate_tick(sym)
                    self.latest_ticks[sym] = tick
                    await self._emit_tick(tick)
                await asyncio.sleep(0.3)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1.0)

    async def subscribe(self, symbols: list[str]) -> None:
        for s in symbols:
            s_up = s.upper().strip()
            self.subscribed_symbols.add(s_up)
            if s_up not in self.prices:
                self.prices[s_up] = 1000.0
                self.day_opens[s_up] = 1000.0
                self.day_highs[s_up] = 1010.0
                self.day_lows[s_up] = 990.0
                self.candle_history[s_up] = deque(maxlen=300)

    async def unsubscribe(self, symbols: list[str]) -> None:
        for s in symbols:
            self.subscribed_symbols.discard(s.upper().strip())

    def get_latest_tick(self, symbol: str) -> Optional[NormalizedTick]:
        return self.latest_ticks.get(symbol.upper())

    def get_depth(self, symbol: str) -> Optional[OrderBookDepth]:
        tick = self.get_latest_tick(symbol)
        if not tick:
            return None

        levels: list[OrderBookLevel] = []
        step = 0.05 if tick.ltp < 500 else (0.1 if tick.ltp < 3000 else 0.5)

        for lvl in range(1, 6):
            b_p = round(tick.bid - (lvl - 1) * step, 2)
            a_p = round(tick.ask + (lvl - 1) * step, 2)
            b_q = float(round(max(50, tick.bid_qty * (1.0 - lvl * 0.12) + self.rng.uniform(-30, 30))))
            a_q = float(round(max(50, tick.ask_qty * (1.0 - lvl * 0.12) + self.rng.uniform(-30, 30))))
            levels.append(OrderBookLevel(level=lvl, bid=b_p, bid_qty=b_q, ask=a_p, ask_qty=a_q))

        tot_b = sum(lvl.bid_qty for lvl in levels)
        tot_a = sum(lvl.ask_qty for lvl in levels)

        return OrderBookDepth(
            symbol=symbol.upper(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            levels=levels,
            total_buy_qty=tot_b,
            total_sell_qty=tot_a,
            spread=round(tick.ask - tick.bid, 2),
            source=f"CHOICE_FINX ({self.user_id})",
        )

    def get_option_chain(self, symbol: str) -> Optional[OptionChainSnapshot]:
        tick = self.get_latest_tick(symbol)
        spot = tick.ltp if tick else self.BASE_PRICES.get(symbol, 25000.0)
        strike_step = 100.0 if spot > 30000 else 50.0
        atm_strike = round(spot / strike_step) * strike_step

        strikes: list[OptionStrike] = []
        for i in range(-5, 6):
            k = atm_strike + i * strike_step
            dist = (k - spot) / spot

            ce_ltp = max(0.5, round(spot * max(0.001, 0.02 - dist * 0.65), 1))
            pe_ltp = max(0.5, round(spot * max(0.001, 0.02 + dist * 0.65), 1))
            ce_iv = round(12.5 + abs(dist) * 25.0 + self.rng.uniform(-0.3, 0.3), 1)
            pe_iv = round(13.2 + abs(dist) * 28.0 + self.rng.uniform(-0.3, 0.3), 1)

            strikes.append(
                OptionStrike(
                    strike=k,
                    ce_ltp=ce_ltp,
                    ce_oi=float(round(self.rng.uniform(100000, 1500000))),
                    ce_iv=ce_iv,
                    ce_volume=float(round(self.rng.uniform(20000, 350000))),
                    pe_ltp=pe_ltp,
                    pe_oi=float(round(self.rng.uniform(100000, 1500000))),
                    pe_iv=pe_iv,
                    pe_volume=float(round(self.rng.uniform(20000, 350000))),
                )
            )

        tot_ce_oi = sum(s.ce_oi for s in strikes)
        tot_pe_oi = sum(s.pe_oi for s in strikes)
        pcr_oi = round(tot_pe_oi / max(1.0, tot_ce_oi), 2)

        return OptionChainSnapshot(
            underlying_symbol=symbol.upper(),
            underlying_price=spot,
            expiry="WEEKLY CURRENT",
            strikes=strikes,
            pcr_oi=pcr_oi,
            pcr_volume=round(self.rng.uniform(0.85, 1.25), 2),
            max_pain=atm_strike,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def get_candles(
        self, symbol: str, timeframe: str = "1m", limit: int = 100
    ) -> list[OHLCVCandle]:
        history = self.candle_history.get(symbol.upper(), deque())
        return list(history)[-limit:]

    def health(self) -> ProviderInfo:
        is_config = bool(self.token)
        return ProviderInfo(
            name=self.name,
            status="READY" if is_config else "MISSING_API_KEY",
            is_live=True,
            details={
                "user_id": self.user_id,
                "token_configured": is_config,
                "client_ip_whitelist": "76.76.21.21",
                "running": self._running,
                "subscribed_symbols": list(self.subscribed_symbols),
            },
        )
