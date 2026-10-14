from __future__ import annotations

import struct
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class DhanWebSocketTick:
    response_code: int
    message_length: int
    exchange_segment: int
    security_id: int
    ltp: float | None = None
    last_trade_time: datetime | None = None
    last_quantity: int | None = None
    average_price: float | None = None
    volume: int | None = None
    total_sell_quantity: int | None = None
    total_buy_quantity: int | None = None
    open: float | None = None
    close: float | None = None
    high: float | None = None
    low: float | None = None
    oi: int | None = None
    depth: list[dict] | None = None
    raw: bytes = b""


def _epoch_to_datetime(value: int) -> datetime:
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _header(data: bytes):
    if len(data) < 8:
        raise ValueError(
            f"Dhan packet too short: {len(data)} bytes"
        )

    response_code = data[0]
    message_length = struct.unpack_from("<h", data, 1)[0]
    exchange_segment = data[3]
    security_id = struct.unpack_from("<i", data, 4)[0]

    return (
        response_code,
        message_length,
        exchange_segment,
        security_id,
    )


def decode_packet(data: bytes) -> DhanWebSocketTick:
    response_code, message_length, exchange_segment, security_id = (
        _header(data)
    )

    # Ticker packet
    # Header: 8 bytes
    # LTP: 4 bytes
    # LTT: 4 bytes
    if response_code == 2:
        if len(data) < 16:
            raise ValueError(
                f"Invalid ticker packet length: {len(data)}"
            )

        ltp = struct.unpack_from("<f", data, 8)[0]
        ltt = struct.unpack_from("<i", data, 12)[0]

        return DhanWebSocketTick(
            response_code=response_code,
            message_length=message_length,
            exchange_segment=exchange_segment,
            security_id=security_id,
            ltp=ltp,
            last_trade_time=_epoch_to_datetime(ltt),
            raw=data,
        )

    # Previous close packet
    if response_code == 6:
        if len(data) < 16:
            raise ValueError(
                f"Invalid previous-close packet length: {len(data)}"
            )

        previous_close = struct.unpack_from("<f", data, 8)[0]
        previous_oi = struct.unpack_from("<i", data, 12)[0]

        return DhanWebSocketTick(
            response_code=response_code,
            message_length=message_length,
            exchange_segment=exchange_segment,
            security_id=security_id,
            ltp=previous_close,
            oi=previous_oi,
            raw=data,
        )

    # OI packet
    if response_code == 5:
        if len(data) < 12:
            raise ValueError(
                f"Invalid OI packet length: {len(data)}"
            )

        oi = struct.unpack_from("<i", data, 8)[0]

        return DhanWebSocketTick(
            response_code=response_code,
            message_length=message_length,
            exchange_segment=exchange_segment,
            security_id=security_id,
            oi=oi,
            raw=data,
        )

    # Quote packet
    if response_code == 4:
        if len(data) < 50:
            raise ValueError(
                f"Invalid quote packet length: {len(data)}"
            )

        return DhanWebSocketTick(
            response_code=response_code,
            message_length=message_length,
            exchange_segment=exchange_segment,
            security_id=security_id,
            ltp=struct.unpack_from("<f", data, 8)[0],
            last_quantity=struct.unpack_from("<h", data, 12)[0],
            last_trade_time=_epoch_to_datetime(
                struct.unpack_from("<i", data, 14)[0]
            ),
            average_price=struct.unpack_from("<f", data, 18)[0],
            volume=struct.unpack_from("<i", data, 22)[0],
            total_sell_quantity=struct.unpack_from("<i", data, 26)[0],
            total_buy_quantity=struct.unpack_from("<i", data, 30)[0],
            open=struct.unpack_from("<f", data, 34)[0],
            close=struct.unpack_from("<f", data, 38)[0],
            high=struct.unpack_from("<f", data, 42)[0],
            low=struct.unpack_from("<f", data, 46)[0],
            raw=data,
        )

    
    # Full packet
    if response_code == 8:
        if len(data) < 162:
            raise ValueError(
                f"Invalid full packet length: {len(data)}"
            )

        depth = []

        for i in range(5):
            offset = 62 + i * 20
            bid_qty, ask_qty, bid_orders, ask_orders, bid_price, ask_price = (
                struct.unpack_from("<IIHHff", data, offset)
            )

            depth.append({
                "bid_quantity": bid_qty,
                "ask_quantity": ask_qty,
                "bid_orders": bid_orders,
                "ask_orders": ask_orders,
                "bid_price": bid_price,
                "ask_price": ask_price,
            })

        return DhanWebSocketTick(
            response_code=response_code,
            message_length=message_length,
            exchange_segment=exchange_segment,
            security_id=security_id,
            ltp=struct.unpack_from("<f", data, 8)[0],
            last_quantity=struct.unpack_from("<h", data, 12)[0],
            last_trade_time=_epoch_to_datetime(
                struct.unpack_from("<i", data, 14)[0]
            ),
            average_price=struct.unpack_from("<f", data, 18)[0],
            volume=struct.unpack_from("<i", data, 22)[0],
            total_sell_quantity=struct.unpack_from("<i", data, 26)[0],
            total_buy_quantity=struct.unpack_from("<i", data, 30)[0],
            oi=struct.unpack_from("<i", data, 34)[0],
            open=struct.unpack_from("<f", data, 46)[0],
            close=struct.unpack_from("<f", data, 50)[0],
            high=struct.unpack_from("<f", data, 54)[0],
            low=struct.unpack_from("<f", data, 58)[0],
            depth=depth,
            raw=data,
        )