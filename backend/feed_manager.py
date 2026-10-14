from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
import os
from typing import Any, Optional
from fastapi import WebSocket

from .feed_interface import BaseMarketFeed
from .feeds.simulation_feed import SimulationFeed
from .feeds.dhan_feed import DhanFeed
from .feeds.zerodha_feed import ZerodhaFeed
from .models import (
    NormalizedTick,
    OrderBookDepth,
    OptionChainSnapshot,
    OHLCVCandle,
    MarketSnapshot,
    ProviderInfo,
)


class FeedManager:
    """
    Central orchestration hub for broker feeds and WebSocket dispatching.
    Handles dynamic provider switching, subscriber multiplexing, and snapshot queries.
    """

    def __init__(self) -> None:
        self.providers: dict[str, BaseMarketFeed] = {
            "SIMULATION": SimulationFeed(),
            "DHAN": DhanFeed(),
            "ZERODHA": ZerodhaFeed(),
        }
        env_provider = os.getenv("MARKET_FEED_PROVIDER", "SIMULATION").upper()
        self.active_provider_name: str = env_provider if env_provider in self.providers else "SIMULATION"
        self._connected_clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._running: bool = False

    @property
    def active_feed(self) -> BaseMarketFeed:
        return self.providers[self.active_provider_name]

    async def initialize(self) -> None:
        for provider in self.providers.values():
            try:
                await provider.initialize()
            except Exception:
                pass

        # Wire tick callback to broadcast to WebSockets
        for provider in self.providers.values():
            provider.add_tick_listener(self._broadcast_tick)

    async def start(self) -> None:
        self._running = True
        await self.active_feed.start()

    async def stop(self) -> None:
        self._running = False
        for provider in self.providers.values():
            try:
                await provider.stop()
            except Exception:
                pass

    async def switch_provider(self, provider_name: str) -> bool:
        p_name = provider_name.upper().strip()
        if p_name not in self.providers:
            raise ValueError(f"Unknown provider: {p_name}. Available: {list(self.providers.keys())}")

        if p_name == self.active_provider_name:
            return True

        async with self._lock:
            # Stop currently active feed
            await self.active_feed.stop()
            self.active_provider_name = p_name

            # Initialize and start new feed
            await self.active_feed.initialize()
            if self._running:
                await self.active_feed.start()

            # Broadcast provider change event to all WebSocket clients
            await self._broadcast_event({
                "type": "provider_changed",
                "active_provider": self.active_provider_name,
                "is_live": self.active_feed.is_live,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        return True

    async def register_client(self, websocket: WebSocket) -> None:
        self._connected_clients.add(websocket)

    async def unregister_client(self, websocket: WebSocket) -> None:
        self._connected_clients.discard(websocket)

    async def _broadcast_tick(self, tick: NormalizedTick) -> None:
        if not self._connected_clients:
            return

        payload = {
            "type": "tick",
            "data": tick.model_dump(),
        }
        text = json.dumps(payload)
        dead = set()

        for ws in self._connected_clients:
            try:
                await ws.send_text(text)
            except Exception:
                dead.add(ws)

        for ws in dead:
            self._connected_clients.discard(ws)

    async def _broadcast_event(self, event: dict[str, Any]) -> None:
        if not self._connected_clients:
            return

        text = json.dumps(event)
        dead = set()
        for ws in self._connected_clients:
            try:
                await ws.send_text(text)
            except Exception:
                dead.add(ws)

        for ws in dead:
            self._connected_clients.discard(ws)

    def get_latest_tick(self, symbol: str) -> Optional[NormalizedTick]:
        return self.active_feed.get_latest_tick(symbol)

    def get_depth(self, symbol: str) -> Optional[OrderBookDepth]:
        return self.active_feed.get_depth(symbol)

    def get_option_chain(self, symbol: str) -> Optional[OptionChainSnapshot]:
        return self.active_feed.get_option_chain(symbol)

    def get_candles(self, symbol: str, timeframe: str = "1m", limit: int = 100) -> list[OHLCVCandle]:
        return self.active_feed.get_candles(symbol, timeframe=timeframe, limit=limit)

    def get_snapshot(self, symbol: str) -> MarketSnapshot:
        sym = symbol.upper()
        tick = self.get_latest_tick(sym)
        depth = self.get_depth(sym)
        candles = self.get_candles(sym, limit=60)
        cvd_sum = sum(c.cvd for c in candles) if candles else 0.0

        return MarketSnapshot(
            symbol=sym,
            tick=tick,
            depth=depth,
            recent_candles=candles,
            cvd_total=cvd_sum,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def get_providers_info(self) -> dict[str, Any]:
        return {
            "active_provider": self.active_provider_name,
            "connected_ws_clients": len(self._connected_clients),
            "providers": [p.health().model_dump() for p in self.providers.values()],
        }


# Global singleton instance
feed_manager = FeedManager()
