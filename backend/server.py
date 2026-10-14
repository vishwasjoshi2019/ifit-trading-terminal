from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .feed_manager import feed_manager
from .models import MarketSnapshot, NormalizedTick, OrderBookDepth, OptionChainSnapshot, OHLCVCandle


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize feeds and start active streaming loop
    await feed_manager.initialize()
    await feed_manager.start()
    yield
    # Shutdown: Gracefully stop all feeds
    await feed_manager.stop()


app = FastAPI(
    title="IFIT Streaming Market Terminal Backend",
    description="High-frequency broker-agnostic market feed and WebSocket streaming server.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for local web terminals, Canvas, and external dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SwitchProviderRequest(BaseModel):
    provider: str


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    return {
        "status": "HEALTHY",
        "service": "IFIT Streaming Engine",
        **feed_manager.get_providers_info(),
    }


@app.get("/api/providers")
async def list_providers() -> dict[str, Any]:
    return feed_manager.get_providers_info()


@app.post("/api/providers/switch")
async def switch_provider(req: SwitchProviderRequest) -> dict[str, Any]:
    try:
        await feed_manager.switch_provider(req.provider)
        return {
            "status": "SUCCESS",
            "active_provider": feed_manager.active_provider_name,
            "is_live": feed_manager.active_feed.is_live,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to switch provider: {e}")


@app.get("/api/snapshot/{symbol}", response_model=MarketSnapshot)
async def get_snapshot(symbol: str) -> MarketSnapshot:
    return feed_manager.get_snapshot(symbol)


@app.get("/api/quote/{symbol}")
async def get_quote(symbol: str) -> Optional[NormalizedTick]:
    tick = feed_manager.get_latest_tick(symbol)
    if not tick:
        raise HTTPException(status_code=404, detail=f"Quote not available for {symbol}")
    return tick


@app.get("/api/depth/{symbol}")
async def get_depth(symbol: str) -> Optional[OrderBookDepth]:
    depth = feed_manager.get_depth(symbol)
    if not depth:
        raise HTTPException(status_code=404, detail=f"Depth not available for {symbol}")
    return depth


@app.get("/api/option-chain/{symbol}")
async def get_option_chain(symbol: str) -> Optional[OptionChainSnapshot]:
    chain = feed_manager.get_option_chain(symbol)
    if not chain:
        raise HTTPException(status_code=404, detail=f"Option chain not available for {symbol}")
    return chain


@app.get("/api/candles/{symbol}")
async def get_candles(
    symbol: str,
    timeframe: str = Query("1m", regex="^(1m|5m|15m|1h|1d)$"),
    limit: int = Query(100, ge=1, le=500),
) -> list[OHLCVCandle]:
    return feed_manager.get_candles(symbol, timeframe=timeframe, limit=limit)


@app.websocket("/ws/market")
async def websocket_market_endpoint(websocket: WebSocket):
    await websocket.accept()
    await feed_manager.register_client(websocket)

    # Send initial connection handshake with active provider info
    handshake = {
        "type": "handshake",
        "active_provider": feed_manager.active_provider_name,
        "is_live": feed_manager.active_feed.is_live,
        "supported_symbols": list(getattr(feed_manager.active_feed, "subscribed_symbols", ["NIFTY", "BANKNIFTY"])),
    }
    await websocket.send_json(handshake)

    try:
        while True:
            # Listen for client control messages (ping, subscribe, unsubscribe)
            data = await websocket.receive_text()
            # If client sends a ping or custom subscribe request
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await feed_manager.unregister_client(websocket)
    except Exception:
        await feed_manager.unregister_client(websocket)


# Mount compiled React frontend for single-port Bloomberg web terminal serving
import os
from fastapi.staticfiles import StaticFiles

_frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")

