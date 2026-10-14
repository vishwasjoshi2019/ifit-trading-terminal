from __future__ import annotations

import threading
import time
import pandas as pd

from dotenv import load_dotenv
load_dotenv()

from engines.live_data.adapters.dhan import DhanAdapter


class DhanLiveService:
    OPTION_CHAIN_CACHE_SECONDS = 5.0
    HISTORICAL_CACHE_SECONDS = 15.0

    def __init__(self):
        self.adapter = DhanAdapter()
        self.instrument = self._resolve_nifty()
        self.client = None
        # Separate NIFTY futures depth feed; do not mix with index ticks.
        self.futures_instrument = None
        self.futures_client = None
        self._futures_latest = None
        self._futures_ticks = []
        self._futures_tick_count = 0
        self._max_futures_ticks = 20000
        self._lock = threading.Lock()
        self._latest = None
        self._tick_count = 0
        self._ticks = []
        self._max_ticks = 20000
        self._option_chain = None
        self._option_chain_expiry = None
        self._option_chain_fetched_at = 0.0
        self._option_chain_error = None
        self._historical_cache = {}
        self._historical_fetched_at = {}

        # Shared live OHLCV cache.
        self._live_ohlcv_cache = {}
        self._live_ohlcv_tick_count = {}
        self._incremental_candles = {}
        self._incremental_previous_volume = {}
        self._incremental_last_timestamp = {}
        self._incremental_candle_history = {}

    def _resolve_nifty(self):
        matches = [
            x for x in self.adapter.get_instruments("NIFTY")
            if x.symbol.upper() == "NIFTY"
            and x.instrument_type.upper() == "INDEX"
            and str(x.metadata.get("dhan_segment", "")).upper() == "IDX_I"
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"Expected exactly one Dhan NIFTY index instrument, found {len(matches)}"
            )
        return matches[0]
    def _resolve_nifty_future(self):
        from datetime import datetime

        matches = [
            x for x in self.adapter.get_instruments("NIFTY")
            if x.instrument_type.upper() == "FUTIDX"
            and x.symbol.upper().startswith("NIFTY-")
            and str(x.metadata.get("dhan_segment", "")).upper() == "NSE_FNO"
            and x.expiry
        ]

        now = datetime.now()
        valid = []

        for instrument in matches:
            try:
                expiry = pd.Timestamp(instrument.expiry)
                if expiry.tzinfo is not None:
                    expiry = expiry.tz_localize(None)

                if expiry.to_pydatetime() > now:
                    valid.append((expiry, instrument))
            except (TypeError, ValueError, OverflowError):
                continue

        if not valid:
            raise RuntimeError(
                "No unexpired NIFTY futures contract found for Dhan WebSocket"
            )

        valid.sort(key=lambda item: item[0])
        return valid[0][1]

    def _incremental_timeframe_rule(self, timeframe):
        return {
            "Intraday": "1min",
            "1 min": "1min",
            "5 min": "5min",
            "15 min": "15min",
            "1 hour": "1h",
            "Daily": "1D",
        }.get(str(timeframe), "1min")

    def _update_incremental_candle(self, tick):
        from engines.live_data.live_candles import _tick_time
        ts = _tick_time(tick)
        price = getattr(tick, "ltp", None)
        if ts is None or price is None:
            return
        try:
            price = float(price)
        except Exception:
            return
        if price <= 0:
            return
        cumulative_volume = getattr(tick, "volume", None)
        try:
            cumulative_volume = float(cumulative_volume) if cumulative_volume is not None else None
        except Exception:
            cumulative_volume = None
        last_qty = getattr(tick, "last_quantity", None)
        if last_qty is None:
            last_qty = getattr(tick, "trade_qty", None)
        try:
            last_qty = float(last_qty) if last_qty is not None else 0.0
        except Exception:
            last_qty = 0.0
        previous_volume = self._incremental_previous_volume.get("1min")
        if cumulative_volume is not None and previous_volume is not None:
            volume_delta = max(cumulative_volume - previous_volume, 0.0)
        else:
            volume_delta = max(last_qty, 0.0)
        if cumulative_volume is not None:
            self._incremental_previous_volume["1min"] = cumulative_volume
        bucket = ts.floor("1min")
        current = self._incremental_candles.get("1min")
        if current is None or current["timestamp"] != bucket:
            if current is not None:
                history = self._incremental_candle_history.setdefault("1min", [])
                history.append(current.copy())
                if len(history) > self._max_ticks:
                    del history[:-self._max_ticks]
            current = {
                "timestamp": bucket,
                "Open": price,
                "High": price,
                "Low": price,
                "Close": price,
                "Volume": volume_delta,
                "Buy Volume": float(getattr(tick, "buy_quantity", None) or 0.0),
                "Sell Volume": float(getattr(tick, "sell_quantity", None) or 0.0),
            }
            self._incremental_candles["1min"] = current
        else:
            current["High"] = max(current["High"], price)
            current["Low"] = min(current["Low"], price)
            current["Close"] = price
            current["Volume"] += volume_delta
            current["Buy Volume"] += float(getattr(tick, "buy_quantity", None) or 0.0)
            current["Sell Volume"] += float(getattr(tick, "sell_quantity", None) or 0.0)
        self._incremental_last_timestamp["1min"] = ts

    def _on_tick(self, tick):
        with self._lock:
            self._latest = tick
            self._tick_count += 1
            self._ticks.append(tick)
            if len(self._ticks) > self._max_ticks:
                del self._ticks[:-self._max_ticks]
            self._update_incremental_candle(tick)

    def _on_futures_tick(self, tick):
        with self._lock:
            self._futures_latest = tick
            self._futures_tick_count += 1
            self._futures_ticks.append(tick)

            if len(self._futures_ticks) > self._max_futures_ticks:
                del self._futures_ticks[:-self._max_futures_ticks]

    def start_futures_feed(self):
        if (
            self.futures_client is not None
            and self.futures_client.is_running
        ):
            return self

        self.futures_instrument = self._resolve_nifty_future()
        self.futures_client = self.adapter.subscribe_ticks(
            [self.futures_instrument],
            self._on_futures_tick,
        )
        return self

    def start(self):
        if self.client is not None and self.client.is_running:
            return self
        self.client = self.adapter.subscribe_ticks(
            [self.instrument],
            self._on_tick,
        )
        return self

    def historical_candles(self, timeframe="Intraday", bars=180, force=False):
        """Return cached Dhan intraday candles for the current trading day."""
        interval_map = {
            "Intraday": 1,
            "1 min": 1,
            "5 min": 5,
            "15 min": 15,
            "1 hour": 60,
        }
        interval = interval_map.get(str(timeframe), 1)
        cache_key = (str(timeframe), int(bars))
        now = time.time()

        with self._lock:
            fetched_at = self._historical_fetched_at.get(cache_key, 0.0)
            cached = self._historical_cache.get(cache_key)

        if cached is not None and not force and (now - fetched_at) < self.HISTORICAL_CACHE_SECONDS:
            return cached

        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        from_date = f"{today} 09:15:00"
        to_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        candles = self.adapter.get_intraday(
            self.instrument,
            from_date,
            to_date,
            interval=interval,
            oi=False,
        )

        candles = list(candles or [])[-int(max(1, bars)):]

        with self._lock:
            self._historical_cache[cache_key] = candles
            self._historical_fetched_at[cache_key] = now

        return candles

    def live_ohlcv(self, timeframe="Intraday", bars=180, force=False):
        """Return live OHLCV using incrementally maintained 1-minute candles."""
        if str(timeframe) not in {"Intraday", "1 min"}:
            cache_key = (str(timeframe), int(bars))
            with self._lock:
                current_tick_count = self._tick_count
                cached = self._live_ohlcv_cache.get(cache_key)
                cached_tick_count = self._live_ohlcv_tick_count.get(cache_key, -1)
                ticks = list(self._ticks)
            if cached is not None and not force and cached_tick_count == current_tick_count:
                return cached
            if not ticks:
                return pd.DataFrame()
            from engines.live_data.live_candles import build_live_ohlcv
            result = build_live_ohlcv(ticks, timeframe=timeframe, bars=bars)
            with self._lock:
                self._live_ohlcv_cache[cache_key] = result
                self._live_ohlcv_tick_count[cache_key] = current_tick_count
            return result

        cache_key = (str(timeframe), int(bars))
        with self._lock:
            current_tick_count = self._tick_count
            cached = self._live_ohlcv_cache.get(cache_key)
            cached_tick_count = self._live_ohlcv_tick_count.get(cache_key, -1)
            history = [x.copy() for x in self._incremental_candle_history.get("1min", [])]
            current = self._incremental_candles.get("1min")
            if current is not None:
                history.append(current.copy())
        if cached is not None and not force and cached_tick_count == current_tick_count:
            return cached
        columns = ["Bar", "Open", "High", "Low", "Close", "Volume", "Buy Volume", "Sell Volume", "Delta", "CVD", "VWAP", "Timestamp"]
        if not history:
            return pd.DataFrame(columns=columns)
        frame = pd.DataFrame(history).sort_values("timestamp").drop_duplicates("timestamp", keep="last")
        frame["Delta"] = frame["Buy Volume"] - frame["Sell Volume"]
        frame["CVD"] = frame["Delta"].cumsum()
        typical = (frame["High"] + frame["Low"] + frame["Close"]) / 3.0
        denominator = frame["Volume"].cumsum().replace(0, float("nan"))
        frame["VWAP"] = ((typical * frame["Volume"]).cumsum() / denominator).fillna(frame["Close"])
        frame = frame.dropna(subset=["Open", "High", "Low", "Close"])
        frame = frame.tail(int(max(1, bars))).reset_index(drop=True)
        frame["Bar"] = range(len(frame))
        frame = frame.rename(columns={"timestamp": "Timestamp"})
        result = frame[columns]
        with self._lock:
            self._live_ohlcv_cache[cache_key] = result
            self._live_ohlcv_tick_count[cache_key] = current_tick_count
        return result

    def _refresh_option_chain(self, force=False):
        now = time.time()

        with self._lock:
            fresh = (
                self._option_chain is not None
                and (now - self._option_chain_fetched_at)
                < self.OPTION_CHAIN_CACHE_SECONDS
            )

        if fresh and not force:
            return

        try:
            result = self.adapter.get_option_chain(self.instrument)
            with self._lock:
                self._option_chain = result.get("option_chain")
                self._option_chain_expiry = result.get("expiry")
                self._option_chain_fetched_at = now
                self._option_chain_error = None
        except Exception as exc:
            with self._lock:
                self._option_chain_error = str(exc)

    def futures_depth_snapshot(self):
        with self._lock:
            tick = self._futures_latest
            count = self._futures_tick_count

        if tick is None:
            return {
                "status": "CONNECTING",
                "provider": "DHAN",
                "symbol": (
                    self.futures_instrument.symbol
                    if self.futures_instrument is not None
                    else None
                ),
                "tick_count": count,
                "ltp": None,
                "depth": [],
                "timestamp": None,
            }

        depth_data = getattr(tick, "depth", None) or []

        return {
            "status": "LIVE",
            "provider": "DHAN",
            "symbol": tick.symbol,
            "security_id": tick.token,
            "tick_count": count,
            "ltp": tick.ltp,
            "volume": tick.volume,
            "oi": tick.oi,
            "depth": depth_data.get("levels", []) if isinstance(depth_data, dict) else depth_data,
            "timestamp": tick.timestamp,
        }

    def tick_history(self, limit=None):
        with self._lock:
            ticks = list(self._ticks)
        if limit is None:
            return ticks
        return ticks[-int(limit):]

    def live_tick_snapshot(self):
        with self._lock:
            tick = self._latest
            count = self._tick_count
        if tick is None:
            return {
                "status": "CONNECTING",
                "provider": "DHAN",
                "symbol": self.instrument.symbol,
                "security_id": self.instrument.token,
                "tick_count": count,
                "spot": None,
                "timestamp": None,
            }
        return {
            "status": "LIVE",
            "provider": "DHAN",
            "symbol": tick.symbol,
            "security_id": tick.token,
            "tick_count": count,
            "spot": tick.ltp,
            "open": tick.open,
            "high": tick.high,
            "low": tick.low,
            "previous_close": tick.previous_close,
            "volume": tick.volume,
            "last_trade_time": tick.last_trade_time,
            "timestamp": tick.timestamp,
        }

    def snapshot(self):
        self._refresh_option_chain()

        with self._lock:
            tick = self._latest
            count = self._tick_count
            option_chain = self._option_chain
            option_expiry = self._option_chain_expiry
            option_error = self._option_chain_error
            option_age = (
                time.time() - self._option_chain_fetched_at
                if self._option_chain_fetched_at
                else None
            )

        if tick is None:
            return {
                "status": "CONNECTING",
                "provider": "DHAN",
                "symbol": self.instrument.symbol,
                "security_id": self.instrument.token,
                "tick_count": count,
                "spot": None,
                "futures": 0.0,
                "option_chain": option_chain,
                "option_expiry": option_expiry,
                "option_chain_age": option_age,
                "option_chain_error": option_error,
                "timestamp": None,
            }

        return {
            "status": "LIVE",
            "provider": "DHAN",
            "symbol": tick.symbol,
            "security_id": tick.token,
            "tick_count": count,
            "spot": tick.ltp,
            "futures": 0.0,
            "option_chain": option_chain,
            "option_expiry": option_expiry,
            "option_chain_age": option_age,
            "option_chain_error": option_error,
            "open": tick.open,
            "high": tick.high,
            "low": tick.low,
            "previous_close": tick.previous_close,
            "volume": tick.volume,
            "last_trade_time": tick.last_trade_time,
            "timestamp": tick.timestamp,
        }

    def health(self):
        adapter_health = self.adapter.health()
        with self._lock:
            running = bool(self.client is not None and self.client.is_running)
            tick_count = self._tick_count
            has_option_chain = self._option_chain is not None
            option_expiry = self._option_chain_expiry
            option_error = self._option_chain_error
            option_age = (
                time.time() - self._option_chain_fetched_at
                if self._option_chain_fetched_at
                else None
            )
            has_tick = self._latest is not None

        return {
            "provider": "DHAN",
            "status": "LIVE" if running and has_tick else "CONNECTING",
            "websocket_running": running,
            "tick_count": tick_count,
            "option_chain_loaded": has_option_chain,
            "option_expiry": option_expiry,
            "option_chain_age": option_age,
            "option_chain_error": option_error,
            "adapter": adapter_health,
        }

    def close(self):
        if self.futures_client is not None:
            self.futures_client.close()
        self.futures_client = None

        if self.client is not None:
            self.client.close()
        self.client = None

        self.adapter.close()







