import csv
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

from .base import LiveDataAdapter
from ..normalized import Instrument, NormalizedTick


class DhanAdapter(LiveDataAdapter):
    name = "DHAN"

    def __init__(
        self,
        client_id=None,
        access_token=None,
        base_url=None,
        ws_url=None,
        timeout=None,
        max_retries=2,
        default_retry_delay=2.0,
    ):
        self.client_id = client_id or os.getenv("DHAN_CLIENT_ID", "")
        self.access_token = access_token or os.getenv("DHAN_ACCESS_TOKEN", "")
        self.base_url = (
            base_url
            or os.getenv("DHAN_BASE_URL", "https://api.dhan.co")
        ).rstrip("/")
        self.ws_url = (
            ws_url
            or os.getenv("DHAN_WS_URL", "wss://api-feed.dhan.co")
        )
        self.timeout = int(timeout or os.getenv("DHAN_TIMEOUT", "15"))

        self.max_retries = int(max_retries)
        self.default_retry_delay = float(default_retry_delay)

        self._instrument_master = None
        self._instrument_master_loaded_at = None

    # ------------------------------------------------------------------
    # HEALTH
    # ------------------------------------------------------------------

    def health(self):
        return {
            "provider": self.name,
            "status": (
                "CONFIGURED"
                if self.client_id and self.access_token
                else "MISSING_API_KEY"
            ),
            "client_id_set": bool(self.client_id),
            "access_token_set": bool(self.access_token),
            "base_url": self.base_url,
            "ws_url": self.ws_url,
        }

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _headers(self):
        return {
            "access-token": self.access_token,
            "client-id": self.client_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _post_json(self, endpoint, payload):
        url = f"{self.base_url}{endpoint}"

        last_response = None

        for attempt in range(self.max_retries + 1):
            response = requests.post(
                url,
                headers=self._headers(),
                json=payload,
                timeout=self.timeout,
            )

            last_response = response

            if response.status_code == 429:
                if attempt >= self.max_retries:
                    response.raise_for_status()

                retry_after = response.headers.get("Retry-After")

                try:
                    delay = float(retry_after)
                except (TypeError, ValueError):
                    delay = self.default_retry_delay

                time.sleep(delay)
                continue

            response.raise_for_status()

            body = response.json()

            if isinstance(body, dict):
                if body.get("status") == "failure":
                    raise RuntimeError(
                        f"Dhan API failure: {body}"
                    )

            return body

        if last_response is not None:
            last_response.raise_for_status()

        raise RuntimeError("Dhan API request failed")

    # ------------------------------------------------------------------
    # INSTRUMENT MASTER
    # ------------------------------------------------------------------

    def _load_instrument_master(self):
        if self._instrument_master is not None:
            return self._instrument_master

        url = (
            "https://images.dhan.co/api-data/"
            "api-scrip-master.csv"
        )

        response = requests.get(
            url,
            timeout=self.timeout,
        )
        response.raise_for_status()

        text = response.content.decode(
            "utf-8",
            errors="replace",
        )

        rows = list(csv.DictReader(text.splitlines()))

        self._instrument_master = rows
        self._instrument_master_loaded_at = time.time()

        return rows

    # ------------------------------------------------------------------
    # INSTRUMENT DISCOVERY
    # ------------------------------------------------------------------

    def get_instruments(self, query=""):
        rows = self._load_instrument_master()

        query_upper = str(query or "").strip().upper()

        instruments = []

        for row in rows:
            exchange = str(
                row.get("SEM_EXM_EXCH_ID", "")
            ).strip()

            segment = str(
                row.get("SEM_SEGMENT", "")
            ).strip()

            security_id = str(
                row.get("SEM_SMST_SECURITY_ID", "")
            ).strip()

            instrument_name = str(
                row.get("SEM_INSTRUMENT_NAME", "")
            ).strip()

            trading_symbol = str(
                row.get("SEM_TRADING_SYMBOL", "")
            ).strip()

            custom_symbol = str(
                row.get("SEM_CUSTOM_SYMBOL", "")
            ).strip()

            symbol_name = str(
                row.get("SM_SYMBOL_NAME", "")
            ).strip()

            if query_upper:
                haystack = " ".join(
                    [
                        trading_symbol,
                        custom_symbol,
                        symbol_name,
                    ]
                ).upper()

                if query_upper not in haystack:
                    continue

            dhan_segment = self._map_segment(
                exchange=exchange,
                segment=segment,
                instrument_name=instrument_name,
            )

            expiry = str(
                row.get("SEM_EXPIRY_DATE", "")
            ).strip()

            strike_raw = str(
                row.get("SEM_STRIKE_PRICE", "")
            ).strip()

            try:
                strike = (
                    float(strike_raw)
                    if strike_raw
                    else None
                )
            except ValueError:
                strike = None

            option_type = str(
                row.get("SEM_OPTION_TYPE", "")
            ).strip()

            lot_raw = str(
                row.get("SEM_LOT_UNITS", "")
            ).strip()

            try:
                lot_size = (
                    int(float(lot_raw))
                    if lot_raw
                    else None
                )
            except ValueError:
                lot_size = None

            instrument_type = (
                instrument_name
                or str(
                    row.get(
                        "SEM_EXCH_INSTRUMENT_TYPE",
                        "",
                    )
                ).strip()
            )

            instrument = Instrument(
                symbol=trading_symbol
                or symbol_name
                or custom_symbol,
                exchange=exchange,
                segment=dhan_segment,
                token=security_id,
                instrument_type=instrument_type,
                expiry=expiry,
                strike=strike,
                option_type=option_type,
                lot_size=lot_size,
                metadata={
                    "dhan_segment": dhan_segment,
                    "trading_symbol": trading_symbol,
                    "custom_symbol": custom_symbol,
                    "symbol_name": symbol_name,
                    "instrument_name": instrument_name,
                    "exchange_instrument_type": row.get(
                        "SEM_EXCH_INSTRUMENT_TYPE",
                        "",
                    ),
                    "series": row.get(
                        "SEM_SERIES",
                        "",
                    ),
                    "expiry_code": row.get(
                        "SEM_EXPIRY_CODE",
                        "",
                    ),
                    "tick_size": row.get(
                        "SEM_TICK_SIZE",
                        "",
                    ),
                    "raw_master": row,
                },
            )

            instruments.append(instrument)

        return instruments

    # ------------------------------------------------------------------
    # DHAN SEGMENT MAPPING
    # ------------------------------------------------------------------

    @staticmethod
    def _map_segment(
        exchange,
        segment,
        instrument_name,
    ):
        if instrument_name.upper() == "INDEX":
            return "IDX_I"

        if segment.upper() == "D":
            return "NSE_FNO"

        return f"{exchange}_{segment}"

    # ------------------------------------------------------------------
    # MARKET QUOTE
    # ------------------------------------------------------------------

    @staticmethod
    def _instrument_payload(instrument):
        segment = instrument.metadata.get(
            "dhan_segment",
            instrument.segment,
        )

        security_id = str(instrument.token)

        return segment, security_id

    def get_quote(self, instrument):
        segment, security_id = self._instrument_payload(
            instrument
        )

        body = self._post_json(
            "/v2/marketfeed/ltp",
            {
                segment: [
                    int(security_id)
                ]
            },
        )

        data = body.get("data", {})

        segment_data = data.get(segment, {})
        quote = segment_data.get(
            security_id,
            {},
        )

        last_price = quote.get("last_price")

        tick = NormalizedTick(
            symbol=instrument.symbol,
            exchange=instrument.exchange,
            segment=instrument.segment,
            token=instrument.token,
            ltp=last_price,
            source=self.name,
            is_live=True,
            raw=quote,
        )

        self._last_quote = tick

        return tick

    # ------------------------------------------------------------------
    # OPTION CHAIN
    # ------------------------------------------------------------------

    def get_option_expiries(self, instrument):
        segment, security_id = self._instrument_payload(instrument)
        body = self._post_json(
            "/v2/optionchain/expirylist",
            {
                "UnderlyingScrip": int(security_id),
                "UnderlyingSeg": segment,
            },
        )
        return body.get("data", []) or []

    def get_option_chain(self, instrument, expiry=None):
        import pandas as pd

        expiries = self.get_option_expiries(instrument)
        if not expiries:
            raise RuntimeError("No option expiries returned for " + instrument.symbol)

        selected_expiry = str(expiry or expiries[0])
        if selected_expiry not in expiries:
            raise ValueError("Expiry " + selected_expiry + " not available for " + instrument.symbol)

        segment, security_id = self._instrument_payload(instrument)
        body = self._post_json(
            "/v2/optionchain",
            {
                "UnderlyingScrip": int(security_id),
                "UnderlyingSeg": segment,
                "Expiry": selected_expiry,
            },
        )

        data = body.get("data", {}) or {}
        option_chain = data.get("oc", {}) or {}
        rows = []

        for strike_raw, strike_data in option_chain.items():
            try:
                strike = float(strike_raw)
            except (TypeError, ValueError):
                continue

            ce = strike_data.get("ce") or {}
            pe = strike_data.get("pe") or {}
            ce_g = ce.get("greeks") or {}
            pe_g = pe.get("greeks") or {}

            rows.append({
                "symbol": instrument.symbol,
                "expiry": selected_expiry,
                "strike": strike,
                "CE_LTP": ce.get("last_price"), "PE_LTP": pe.get("last_price"),
                "CE_OI": ce.get("oi"), "PE_OI": pe.get("oi"),
                "CE_IV": ce.get("implied_volatility"), "PE_IV": pe.get("implied_volatility"),
                "CE_VOLUME": ce.get("volume"), "PE_VOLUME": pe.get("volume"),
                "CE_PREV_OI": ce.get("previous_oi"), "PE_PREV_OI": pe.get("previous_oi"),
                "CE_PREV_VOLUME": ce.get("previous_volume"), "PE_PREV_VOLUME": pe.get("previous_volume"),
                "CE_DELTA": ce_g.get("delta"), "PE_DELTA": pe_g.get("delta"),
                "CE_GAMMA": ce_g.get("gamma"), "PE_GAMMA": pe_g.get("gamma"),
                "CE_THETA": ce_g.get("theta"), "PE_THETA": pe_g.get("theta"),
                "CE_VEGA": ce_g.get("vega"), "PE_VEGA": pe_g.get("vega"),
                "CE_BID": ce.get("top_bid_price"), "PE_BID": pe.get("top_bid_price"),
                "CE_ASK": ce.get("top_ask_price"), "PE_ASK": pe.get("top_ask_price"),
                "CE_BID_QTY": ce.get("top_bid_quantity"), "PE_BID_QTY": pe.get("top_bid_quantity"),
                "CE_ASK_QTY": ce.get("top_ask_quantity"), "PE_ASK_QTY": pe.get("top_ask_quantity"),
                "CE_AVG_PRICE": ce.get("average_price"), "PE_AVG_PRICE": pe.get("average_price"),
                "CE_SECURITY_ID": ce.get("security_id"), "PE_SECURITY_ID": pe.get("security_id"),
                "CE_PREV_CLOSE": ce.get("previous_close_price"), "PE_PREV_CLOSE": pe.get("previous_close_price"),
            })

        frame = pd.DataFrame(rows)
        if not frame.empty:
            frame = frame.sort_values("strike").reset_index(drop=True)

        return {
            "symbol": instrument.symbol,
            "underlying_security_id": str(security_id),
            "underlying_segment": segment,
            "expiry": selected_expiry,
            "expiries": expiries,
            "last_price": data.get("last_price"),
            "option_chain": frame,
            "source": self.name,
            "is_live": True,
            "raw": body,
        }

    # ------------------------------------------------------------------
    # RICH QUOTE
    # ------------------------------------------------------------------

    def _normalize_rich_quote(
        self,
        instrument,
        body,
        segment,
        security_id,
    ):
        data = body.get("data", {})
        segment_data = data.get(segment, {})
        quote = segment_data.get(
            str(security_id),
            {},
        )

        ohlc = quote.get("ohlc") or {}
        depth = quote.get("depth") or {}

        buy_depth = depth.get("buy") or []
        sell_depth = depth.get("sell") or []

        bid = None
        ask = None
        bid_qty = None
        ask_qty = None

        if buy_depth:
            bid = buy_depth[0].get("price")
            bid_qty = buy_depth[0].get("quantity")

        if sell_depth:
            ask = sell_depth[0].get("price")
            ask_qty = sell_depth[0].get("quantity")

        tick = NormalizedTick(
            symbol=instrument.symbol,
            exchange=instrument.exchange,
            segment=instrument.segment,
            token=instrument.token,
            timestamp=quote.get(
                "last_trade_time"
            ),
            ltp=quote.get("last_price"),
            open=ohlc.get("open"),
            high=ohlc.get("high"),
            low=ohlc.get("low"),
            previous_close=ohlc.get("close"),
            net_change=quote.get("net_change"),
            volume=quote.get("volume"),
            average_price=quote.get(
                "average_price"
            ),
            last_quantity=quote.get(
                "last_quantity"
            ),
            last_trade_time=quote.get(
                "last_trade_time"
            ),
            bid=bid,
            ask=ask,
            bid_qty=bid_qty,
            ask_qty=ask_qty,
            buy_quantity=quote.get(
                "buy_quantity"
            ),
            sell_quantity=quote.get(
                "sell_quantity"
            ),
            oi=quote.get("oi"),
            oi_day_high=quote.get(
                "oi_day_high"
            ),
            oi_day_low=quote.get(
                "oi_day_low"
            ),
            upper_circuit_limit=quote.get(
                "upper_circuit_limit"
            ),
            lower_circuit_limit=quote.get(
                "lower_circuit_limit"
            ),
            trade_price=quote.get(
                "last_price"
            ),
            trade_qty=quote.get(
                "last_quantity"
            ),
            depth={
                "buy": buy_depth,
                "sell": sell_depth,
            },
            source=self.name,
            is_live=True,
            raw=quote,
        )

        return tick

    def get_rich_quote(self, instrument):
        segment, security_id = self._instrument_payload(
            instrument
        )

        body = self._post_json(
            "/v2/marketfeed/quote",
            {
                segment: [
                    int(security_id)
                ]
            },
        )

        return self._normalize_rich_quote(
            instrument,
            body,
            segment,
            security_id,
        )

    def get_rich_quotes(self, instruments):
        """
        Retrieve rich quotes for multiple instruments
        using the Dhan batch Market Quote endpoint.

        Instruments are grouped by Dhan segment.
        Requests are chunked to a maximum of 1000
        instruments per API request.
        """

        grouped = {}

        for instrument in instruments:
            segment, security_id = (
                self._instrument_payload(
                    instrument
                )
            )

            grouped.setdefault(
                segment,
                [],
            ).append(
                (instrument, security_id)
            )

        results = {}

        max_batch = 1000

        for segment, items in grouped.items():

            for start in range(
                0,
                len(items),
                max_batch,
            ):
                chunk = items[
                    start:start + max_batch
                ]

                security_ids = [
                    int(security_id)
                    for _, security_id in chunk
                ]

                body = self._post_json(
                    "/v2/marketfeed/quote",
                    {
                        segment: security_ids
                    },
                )

                for instrument, security_id in chunk:

                    tick = (
                        self._normalize_rich_quote(
                            instrument,
                            body,
                            segment,
                            security_id,
                        )
                    )

                    key = (
                        f"{instrument.exchange}:"
                        f"{instrument.segment}:"
                        f"{instrument.token}"
                    )

                    results[key] = tick

                # Dhan market quote API has a
                # 1 request/sec rate limit.
                if (
                    start + max_batch
                    < len(items)
                ):
                    time.sleep(1.05)

        return results

    # ------------------------------------------------------------------
    # DEPTH
    # ------------------------------------------------------------------

    def get_depth(self, instrument):
        tick = self.get_rich_quote(
            instrument
        )

        return {
            "buy": tick.depth.get(
                "buy",
                [],
            ),
            "sell": tick.depth.get(
                "sell",
                [],
            ),
            "levels": tick.depth,
            "source": tick.source,
            "is_live": tick.is_live,
        }

    # ------------------------------------------------------------------
    # QUOTE OHLC SNAPSHOT
    # ------------------------------------------------------------------

    def get_ohlc(self, instrument, timeframe="1m"):
        tick = self.get_rich_quote(
            instrument
        )

        return {
            "symbol": tick.symbol,
            "token": tick.token,
            "timeframe": timeframe,
            "timestamp": tick.last_trade_time,
            "open": tick.open,
            "high": tick.high,
            "low": tick.low,
            "close": tick.previous_close,
            "ltp": tick.ltp,
            "volume": tick.volume,
            "source": tick.source,
            "is_live": tick.is_live,
        }

    # ------------------------------------------------------------------
    # HISTORICAL DAILY CANDLES
    # ------------------------------------------------------------------

    def get_historical_daily(
        self,
        instrument,
        from_date,
        to_date,
        oi=False,
        expiry_code=0,
    ):
        """
        Retrieve daily OHLCV candles.

        from_date / to_date:
            YYYY-MM-DD

        to_date is non-inclusive according to
        Dhan historical-data API semantics.
        """

        segment, security_id = (
            self._instrument_payload(
                instrument
            )
        )

        instrument_type = (
            instrument.instrument_type
            or "EQUITY"
        )

        payload = {
            "securityId": str(security_id),
            "exchangeSegment": segment,
            "instrument": instrument_type,
            "expiryCode": int(expiry_code),
            "oi": bool(oi),
            "fromDate": str(from_date),
            "toDate": str(to_date),
        }

        body = self._post_json(
            "/v2/charts/historical",
            payload,
        )

        return self._normalize_candles(
            body,
            instrument,
            timeframe="1D",
        )

    # ------------------------------------------------------------------
    # INTRADAY CANDLES
    # ------------------------------------------------------------------

    def get_intraday(
        self,
        instrument,
        from_date,
        to_date,
        interval=1,
        oi=False,
    ):
        """
        Retrieve intraday OHLCV candles.

        Supported Dhan intervals:
            1, 5, 15, 25, 60

        from_date / to_date format:
            YYYY-MM-DD HH:MM:SS
        """

        interval = int(interval)

        if interval not in {
            1,
            5,
            15,
            25,
            60,
        }:
            raise ValueError(
                "Dhan intraday interval must be "
                "one of: 1, 5, 15, 25, 60"
            )

        segment, security_id = (
            self._instrument_payload(
                instrument
            )
        )

        instrument_type = (
            instrument.instrument_type
            or "EQUITY"
        )

        payload = {
            "securityId": str(security_id),
            "exchangeSegment": segment,
            "instrument": instrument_type,
            "interval": str(interval),
            "oi": bool(oi),
            "fromDate": str(from_date),
            "toDate": str(to_date),
        }

        body = self._post_json(
            "/v2/charts/intraday",
            payload,
        )

        return self._normalize_candles(
            body,
            instrument,
            timeframe=f"{interval}m",
        )

    # ------------------------------------------------------------------
    # CANDLE NORMALIZATION
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_candles(
        body,
        instrument,
        timeframe,
    ):
        opens = body.get("open", []) or []
        highs = body.get("high", []) or []
        lows = body.get("low", []) or []
        closes = body.get("close", []) or []
        volumes = body.get("volume", []) or []
        timestamps = body.get("timestamp", []) or []
        oi_values = body.get("oi", []) or []

        count = max(
            len(opens),
            len(highs),
            len(lows),
            len(closes),
            len(volumes),
            len(timestamps),
            len(oi_values),
            0,
        )

        candles = []

        for i in range(count):
            candles.append(
                {
                    "symbol": instrument.symbol,
                    "exchange": instrument.exchange,
                    "segment": instrument.segment,
                    "token": instrument.token,
                    "timeframe": timeframe,
                    "timestamp": (
                        timestamps[i]
                        if i < len(timestamps)
                        else None
                    ),
                    "open": (
                        opens[i]
                        if i < len(opens)
                        else None
                    ),
                    "high": (
                        highs[i]
                        if i < len(highs)
                        else None
                    ),
                    "low": (
                        lows[i]
                        if i < len(lows)
                        else None
                    ),
                    "close": (
                        closes[i]
                        if i < len(closes)
                        else None
                    ),
                    "volume": (
                        volumes[i]
                        if i < len(volumes)
                        else None
                    ),
                    "oi": (
                        oi_values[i]
                        if i < len(oi_values)
                        else None
                    ),
                    "source": "DHAN",
                }
            )

        return candles

    # ------------------------------------------------------------------
    # WEBSOCKET
    # ------------------------------------------------------------------

    def subscribe_ticks(self, instruments, on_tick):
        from ..dhan_ws_client import DhanWebSocketClient

        client = DhanWebSocketClient(
            client_id=self.client_id,
            access_token=self.access_token,
            ws_url=self.ws_url,
            instruments=instruments,
            on_tick=on_tick,
        )
        client.connect()
        return client

    # ------------------------------------------------------------------
    # CLOSE
    # ------------------------------------------------------------------

    def close(self):
        pass
