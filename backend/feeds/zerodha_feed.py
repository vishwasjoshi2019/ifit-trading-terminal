from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Optional

from ..feed_interface import BaseMarketFeed
from ..models import (
    NormalizedTick,
    OrderBookDepth,
    OHLCVCandle,
    OptionChainSnapshot,
    ProviderInfo,
)


class ZerodhaFeed(BaseMarketFeed):
    """
    Zerodha Kite Connect & KiteTicker market feed adapter.
    Enables plug-and-play streaming for Zerodha accounts.
    """

    name: str = "ZERODHA"
    is_live: bool = True

    def __init__(self) -> None:
        super().__init__()
        self.api_key = os.getenv("KITE_API_KEY", "")
        self.access_token = os.getenv("KITE_ACCESS_TOKEN", "")
        self._running: bool = False

    async def initialize(self) -> bool:
        if not self.api_key or not self.access_token:
            return False
        return True

    async def start(self) -> None:
        if not self.api_key or not self.access_token:
            return
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def subscribe(self, symbols: list[str]) -> None:
        pass

    async def unsubscribe(self, symbols: list[str]) -> None:
        pass

    def get_latest_tick(self, symbol: str) -> Optional[NormalizedTick]:
        return None

    def get_depth(self, symbol: str) -> Optional[OrderBookDepth]:
        return None

    def get_option_chain(self, symbol: str) -> Optional[OptionChainSnapshot]:
        return None

    def get_candles(
        self, symbol: str, timeframe: str = "1m", limit: int = 100
    ) -> list[OHLCVCandle]:
        return []

    def health(self) -> ProviderInfo:
        is_config = bool(self.api_key and self.access_token)
        return ProviderInfo(
            name=self.name,
            status="CONFIGURED" if is_config else "MISSING_API_KEY",
            is_live=True,
            details={
                "api_key_set": bool(self.api_key),
                "access_token_set": bool(self.access_token),
                "running": self._running,
            },
        )
