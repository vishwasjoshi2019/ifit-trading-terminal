from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import os
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


class DhanFeed(BaseMarketFeed):
    """
    Dhan HQ API and WebSocket live market feed adapter.
    Bridges DhanLiveService/DhanAdapter into the broker-agnostic backend.
    """

    name: str = "DHAN"
    is_live: bool = True

    def __init__(self) -> None:
        super().__init__()
        self.client_id = os.getenv("DHAN_CLIENT_ID", "")
        self.access_token = os.getenv("DHAN_ACCESS_TOKEN", "")
        self._service = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._queue: Optional[asyncio.Queue] = None
        self._dispatch_task: Optional[asyncio.Task] = None
        self._running: bool = False

    async def initialize(self) -> bool:
        if not self.client_id or not self.access_token:
            return False

        try:
            from engines.live_data.dhan_live_service import DhanLiveService
            self._service = DhanLiveService()
            return True
        except Exception:
            return False

    async def start(self) -> None:
        if self._running or not self._service:
            return

        self._running = True
        self._loop = asyncio.get_running_loop()
        self._queue = asyncio.Queue(maxsize=10000)

        # Wire callback from Dhan service background thread into asyncio queue
        def _on_tick_sync(tick_data):
            if self._loop and self._queue and not self._queue.full():
                self._loop.call_soon_threadsafe(self._queue.put_nowait, tick_data)

        # Start Dhan WebSocket service
        try:
            self._service.start(on_tick_callback=_on_tick_sync)
        except Exception:
            pass

        self._dispatch_task = asyncio.create_task(self._process_queue())

    async def _process_queue(self) -> None:
        while self._running and self._queue:
            try:
                raw = await self._queue.get()
                tick = self._normalize_tick(raw)
                if tick:
                    await self._emit_tick(tick)
            except asyncio.CancelledError:
                break
            except Exception:
                continue

    def _normalize_tick(self, raw: any) -> Optional[NormalizedTick]:
        if not raw:
            return None
        # Handle dict or Dhan normalized object
        if hasattr(raw, "symbol"):
            sym = getattr(raw, "symbol", "NIFTY")
            ltp = float(getattr(raw, "ltp", 0.0) or 0.0)
            bid = float(getattr(raw, "bid", 0.0) or 0.0)
            ask = float(getattr(raw, "ask", 0.0) or 0.0)
            vol = float(getattr(raw, "volume", 0.0) or 0.0)
            oi = float(getattr(raw, "oi", 0.0) or 0.0)
        elif isinstance(raw, dict):
            sym = raw.get("symbol", "NIFTY")
            ltp = float(raw.get("ltp", 0.0) or 0.0)
            bid = float(raw.get("bid", 0.0) or 0.0)
            ask = float(raw.get("ask", 0.0) or 0.0)
            vol = float(raw.get("volume", 0.0) or 0.0)
            oi = float(raw.get("oi", 0.0) or 0.0)
        else:
            return None

        return NormalizedTick(
            symbol=sym,
            exchange="NSE",
            segment="INDEX" if sym in {"NIFTY", "BANKNIFTY"} else "EQUITY",
            timestamp=datetime.now(timezone.utc).isoformat(),
            ltp=ltp,
            bid=bid,
            ask=ask,
            volume=vol,
            oi=oi,
            source="DHAN",
            is_live=True,
        )

    async def stop(self) -> None:
        self._running = False
        if self._dispatch_task and not self._dispatch_task.done():
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
        if self._service:
            try:
                self._service.stop()
            except Exception:
                pass

    async def subscribe(self, symbols: list[str]) -> None:
        pass

    async def unsubscribe(self, symbols: list[str]) -> None:
        pass

    def get_latest_tick(self, symbol: str) -> Optional[NormalizedTick]:
        if not self._service:
            return None
        raw = self._service.get_latest_tick() if hasattr(self._service, "get_latest_tick") else None
        return self._normalize_tick(raw)

    def get_depth(self, symbol: str) -> Optional[OrderBookDepth]:
        if not self._service or not hasattr(self._service, "get_futures_depth"):
            return None
        try:
            d = self._service.get_futures_depth()
            if not d or not isinstance(d, dict):
                return None
            levels = []
            raw_levels = d.get("levels", [])
            for lvl in raw_levels:
                levels.append(
                    OrderBookLevel(
                        level=lvl.get("level", 1),
                        bid=float(lvl.get("bid", 0.0)),
                        bid_qty=float(lvl.get("bid_qty", 0.0)),
                        ask=float(lvl.get("ask", 0.0)),
                        ask_qty=float(lvl.get("ask_qty", 0.0)),
                    )
                )
            return OrderBookDepth(
                symbol=symbol.upper(),
                timestamp=datetime.now(timezone.utc).isoformat(),
                levels=levels,
                total_buy_qty=float(d.get("total_buy_qty", 0.0)),
                total_sell_qty=float(d.get("total_sell_qty", 0.0)),
                spread=float(d.get("spread", 0.0)),
                source="DHAN",
            )
        except Exception:
            return None

    def get_option_chain(self, symbol: str) -> Optional[OptionChainSnapshot]:
        if not self._service or not hasattr(self._service, "get_option_chain"):
            return None
        try:
            df = self._service.get_option_chain()
            if df is None or (hasattr(df, "empty") and df.empty):
                return None
            strikes = []
            for _, row in df.iterrows():
                strikes.append(
                    OptionStrike(
                        strike=float(row.get("strike", 0.0)),
                        ce_ltp=float(row.get("ce_ltp", 0.0)),
                        ce_oi=float(row.get("ce_oi", 0.0)),
                        ce_iv=float(row.get("ce_iv", 0.0)),
                        ce_volume=float(row.get("ce_volume", 0.0)),
                        pe_ltp=float(row.get("pe_ltp", 0.0)),
                        pe_oi=float(row.get("pe_oi", 0.0)),
                        pe_iv=float(row.get("pe_iv", 0.0)),
                        pe_volume=float(row.get("pe_volume", 0.0)),
                    )
                )
            return OptionChainSnapshot(
                underlying_symbol=symbol.upper(),
                underlying_price=float(df.attrs.get("underlying_price", 25000.0)),
                expiry=str(df.attrs.get("expiry", "")),
                strikes=strikes,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception:
            return None

    def get_candles(
        self, symbol: str, timeframe: str = "1m", limit: int = 100
    ) -> list[OHLCVCandle]:
        if not self._service or not hasattr(self._service, "get_live_ohlcv"):
            return []
        try:
            df = self._service.get_live_ohlcv(limit=limit)
            if df is None or (hasattr(df, "empty") and df.empty):
                return []
            res = []
            for _, row in df.iterrows():
                res.append(
                    OHLCVCandle(
                        timestamp=str(row.get("timestamp", "")),
                        open=float(row.get("open", 0.0)),
                        high=float(row.get("high", 0.0)),
                        low=float(row.get("low", 0.0)),
                        close=float(row.get("close", 0.0)),
                        volume=float(row.get("volume", 0.0)),
                        cvd=float(row.get("cvd", 0.0)),
                    )
                )
            return res
        except Exception:
            return []

    def health(self) -> ProviderInfo:
        is_config = bool(self.client_id and self.access_token)
        return ProviderInfo(
            name=self.name,
            status="CONFIGURED" if is_config else "MISSING_API_KEY",
            is_live=True,
            details={
                "client_id_set": bool(self.client_id),
                "access_token_set": bool(self.access_token),
                "running": self._running,
            },
        )
