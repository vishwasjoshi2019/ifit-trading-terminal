from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Optional
from .models import (
    NormalizedTick,
    OrderBookDepth,
    OptionChainSnapshot,
    OHLCVCandle,
    ProviderInfo,
)

TickListener = Callable[[NormalizedTick], Awaitable[None]]


class BaseMarketFeed(ABC):
    """
    Abstract interface for all market feed adapters (Simulation, Dhan, Zerodha, etc.).
    Ensures broker-agnostic, decoupled architecture across the quantitative terminal.
    """

    name: str = "BASE"
    is_live: bool = False

    def __init__(self) -> None:
        self._listeners: list[TickListener] = []

    def add_tick_listener(self, listener: TickListener) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_tick_listener(self, listener: TickListener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    async def _emit_tick(self, tick: NormalizedTick) -> None:
        for listener in list(self._listeners):
            try:
                await listener(tick)
            except Exception:
                pass

    @abstractmethod
    async def initialize(self) -> bool:
        """Validate credentials, prepare connection pools or symbols."""
        raise NotImplementedError

    @abstractmethod
    async def start(self) -> None:
        """Start the streaming loop / connection."""
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        """Gracefully disconnect and tear down resources."""
        raise NotImplementedError

    @abstractmethod
    async def subscribe(self, symbols: list[str]) -> None:
        """Subscribe to live ticks for the given symbols."""
        raise NotImplementedError

    @abstractmethod
    async def unsubscribe(self, symbols: list[str]) -> None:
        """Unsubscribe from the given symbols."""
        raise NotImplementedError

    @abstractmethod
    def get_latest_tick(self, symbol: str) -> Optional[NormalizedTick]:
        """Return the most recent tick for the symbol."""
        raise NotImplementedError

    @abstractmethod
    def get_depth(self, symbol: str) -> Optional[OrderBookDepth]:
        """Return the current 5-level or 20-level order book depth."""
        raise NotImplementedError

    @abstractmethod
    def get_option_chain(self, symbol: str) -> Optional[OptionChainSnapshot]:
        """Return the option chain snapshot with Greeks and IVs."""
        raise NotImplementedError

    @abstractmethod
    def get_candles(
        self, symbol: str, timeframe: str = "1m", limit: int = 100
    ) -> list[OHLCVCandle]:
        """Return historical/aggregated intraday candles."""
        raise NotImplementedError

    @abstractmethod
    def health(self) -> ProviderInfo:
        """Return the adapter's configuration and health status."""
        raise NotImplementedError
