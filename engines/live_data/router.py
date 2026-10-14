from __future__ import annotations

from typing import Any

from .engine import LiveDataEngine


class LiveDataRouter:
    def __init__(
        self,
        providers: dict[str, LiveDataEngine] | None = None,
        active_provider: str = "SIMULATION",
    ):
        self.providers: dict[str, LiveDataEngine] = providers or {}
        self.active_provider = active_provider.upper()

        if self.active_provider not in self.providers:
            raise ValueError(
                f"Provider not registered: {self.active_provider}"
            )

    @property
    def provider(self) -> str:
        return self.active_provider

    @property
    def engine(self) -> LiveDataEngine:
        return self.providers[self.active_provider]

    def register_provider(
        self,
        name: str,
        engine: LiveDataEngine,
        make_active: bool = False,
    ) -> None:
        key = str(name).upper()

        self.providers[key] = engine

        if make_active:
            self.active_provider = key

    def set_provider(self, name: str) -> None:
        key = str(name).upper()

        if key not in self.providers:
            raise KeyError(
                f"Unknown provider: {key}"
            )

        self.active_provider = key

    def available_providers(self) -> list[str]:
        return sorted(self.providers.keys())

    def health(self) -> dict[str, Any]:
        provider_health = self.engine.health()

        if callable(provider_health):
            provider_health = provider_health()

        return {
            "status": (
                "OK"
                if provider_health.get("status")
                in {"OK", "CONFIGURED"}
                else "DEGRADED"
            ),
            "active_provider": self.provider,
            "available_providers": self.available_providers(),
            "provider_health": provider_health,
        }

    def discover(self, **kwargs):
        return self.engine.discover(**kwargs)

    def _resolve_instrument(self, symbol, **kwargs):
        if not isinstance(symbol, str):
            return symbol

        requested = symbol.strip().upper()

        instruments = self.engine.discover(**kwargs)

        # 1. Exact trading-symbol match
        exact = [
            instrument
            for instrument in instruments
            if getattr(
                instrument,
                "symbol",
                "",
            ).upper()
            == requested
        ]

        if len(exact) == 1:
            return exact[0]

        if len(exact) > 1:
            raise KeyError(
                f"Multiple exact instruments found for "
                f"{symbol}: {len(exact)}"
            )

        # 2. Exact custom-symbol match
        custom_exact = [
            instrument
            for instrument in instruments
            if str(
                getattr(
                    instrument,
                    "metadata",
                    {},
                ).get("custom_symbol", "")
            ).upper()
            == requested
        ]

        if len(custom_exact) == 1:
            return custom_exact[0]

        if len(custom_exact) > 1:
            raise KeyError(
                f"Multiple custom-symbol matches found "
                f"for {symbol}: {len(custom_exact)}"
            )

        # 3. No exact match
        raise KeyError(
            f"Instrument not found for symbol: {symbol}"
        )

    def quote(self, symbol: str, **kwargs):
        instrument = self._resolve_instrument(
            symbol,
            **kwargs,
        )

        return self.engine.quote(instrument)

    def depth(self, symbol: str, **kwargs):
        instrument = self._resolve_instrument(
            symbol,
            **kwargs,
        )

        return self.engine.depth(instrument)

    def ohlc(self, symbol: str, **kwargs):
        instrument = self._resolve_instrument(
            symbol,
            **kwargs,
        )

        return self.engine.ohlc(instrument)

    def latest(self, symbol: str):
        return self.engine.latest(symbol)

    def history(
        self,
        symbol: str,
        limit: int | None = None,
    ):
        instrument = self._resolve_instrument(symbol)

        if limit is None:
            limit = 100

        return self.engine.history(
            instrument,
            limit=limit,
        )

    def snapshot(self):
        return self.engine.snapshot()

    def close(self) -> None:
        for engine in self.providers.values():
            engine.close()