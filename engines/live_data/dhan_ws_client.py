from __future__ import annotations

import json
import threading
from typing import Callable, Iterable

import websocket

from .dhan_ws import DhanWebSocketTick, decode_packet
from .normalized import Instrument, NormalizedTick


class DhanWebSocketClient:
    """
    Dhan V2 WebSocket client.

    Connects to the authenticated Dhan feed, subscribes to instruments,
    decodes binary packets, and converts live market packets into
    IFIT NormalizedTick objects.
    """

    REQUEST_CODE = 21
    AUTH_VERSION = "2"
    AUTH_TYPE = "2"

    # Dhan packet types that represent actual live market updates.
    LIVE_PACKET_CODES = {2, 4, 5, 8}

    def __init__(
        self,
        client_id: str,
        access_token: str,
        ws_url: str,
        instruments: Iterable[Instrument],
        on_tick: Callable[[NormalizedTick], None],
    ):
        self.client_id = client_id
        self.access_token = access_token
        self.ws_url = ws_url.rstrip("/")
        self.instruments = list(instruments)
        self.on_tick = on_tick

        self.ws = None
        self._thread = None
        self._running = False

    @staticmethod
    def _exchange_segment_code(instrument: Instrument):
        segment = str(
            instrument.metadata.get(
                "dhan_segment",
                instrument.segment,
            )
        ).upper()

        mapping = {
            "IDX_I": 0,
            "NSE_EQ": 1,
            "NSE_FNO": 2,
            "NSE_CURRENCY": 3,
            "BSE_EQ": 4,
            "BSE_FNO": 5,
            "BSE_CURRENCY": 6,
            "MCX_COMM": 7,
        }

        return mapping.get(segment)

    def _url(self):
        return (
            f"{self.ws_url}"
            f"?version={self.AUTH_VERSION}"
            f"&token={self.access_token}"
            f"&clientId={self.client_id}"
            f"&authType={self.AUTH_TYPE}"
        )

    def _subscription_payload(self):
        instrument_list = []

        for instrument in self.instruments:
            segment = str(
                instrument.metadata.get(
                    "dhan_segment",
                    instrument.segment,
                )
            ).upper()

            if not instrument.token:
                continue

            instrument_list.append(
                {
                    "ExchangeSegment": segment,
                    "SecurityId": str(instrument.token),
                }
            )

        if not instrument_list:
            raise ValueError(
                "No valid instruments supplied for Dhan WebSocket"
            )

        return {
            "RequestCode": self.REQUEST_CODE,
            "InstrumentCount": len(instrument_list),
            "InstrumentList": instrument_list,
        }

    def _find_instrument(self, packet: DhanWebSocketTick):
        security_id = str(packet.security_id)

        candidates = [
            instrument
            for instrument in self.instruments
            if str(instrument.token) == security_id
        ]

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        for instrument in candidates:
            if (
                self._exchange_segment_code(instrument)
                == packet.exchange_segment
            ):
                return instrument

        return candidates[0]

    def _normalize_tick(
        self,
        packet: DhanWebSocketTick,
        instrument: Instrument,
    ) -> NormalizedTick:
        return NormalizedTick(
            symbol=instrument.symbol,
            exchange=instrument.exchange,
            segment=instrument.segment,
            token=instrument.token,
            timestamp=packet.last_trade_time,
            ltp=packet.ltp,
            open=packet.open,
            high=packet.high,
            low=packet.low,
            previous_close=packet.close,
            volume=packet.volume,
            average_price=packet.average_price,
            last_quantity=packet.last_quantity,
            last_trade_time=packet.last_trade_time,
            oi=packet.oi,
            oi_day_high=getattr(packet, "oi_day_high", None),
            oi_day_low=getattr(packet, "oi_day_low", None),
            source="DHAN",
            is_live=True,
            depth={
                "levels": packet.depth or [],
            },            
            raw={
                "response_code": packet.response_code,
                "message_length": packet.message_length,
                "exchange_segment_code": packet.exchange_segment,
                "security_id": packet.security_id,
                "raw_packet_hex": packet.raw.hex(),
            },
        )

    def connect(self):
        if self._running:
            return self

        if not self.client_id or not self.access_token:
            print("[DHAN WS] Cannot connect: missing client_id or access_token")
            return self

        try:
            self.ws = websocket.create_connection(
                self._url(),
                timeout=10,
            )

            self.ws.send(
                json.dumps(
                    self._subscription_payload()
                )
            )

            self._running = True

            self._thread = threading.Thread(
                target=self._receive_loop,
                name="IFIT-DHAN-WebSocket",
                daemon=True,
            )
            self._thread.start()
        except Exception as exc:
            self._running = False
            self.ws = None
            print(f"[DHAN WS] Connection attempt failed: {exc}")

        return self

    def _receive_loop(self):
        while self._running and self.ws is not None:
            try:
                data = self.ws.recv()

                if not data:
                    continue

                if isinstance(data, str):
                    continue

                if data[0] == 50:
                    disconnect_code = int.from_bytes(data[8:10], "little", signed=True)
                    print(f"[DHAN WS] FEED DISCONNECT code={disconnect_code} raw={data.hex()}")
                    break

                packet = decode_packet(data)

                # Previous-close packets are reference data, not live ticks.
                if packet.response_code not in self.LIVE_PACKET_CODES:
                    continue

                instrument = self._find_instrument(packet)

                if instrument is None:
                    continue

                normalized = self._normalize_tick(
                    packet,
                    instrument,
                )

                self.on_tick(normalized)

            except Exception as exc:
                if self._running:
                    print(
                        f"[DHAN WS] receive error: {exc}"
                    )
                break

        self._running = False

    def stop(self):
        self._running = False

        if self.ws is not None:
            try:
                self.ws.close()
            except Exception:
                pass

        self.ws = None

    def close(self):
        self.stop()

    @property
    def is_running(self):
        return self._running