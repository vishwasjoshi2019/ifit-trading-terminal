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
    timeframe: str = Query("1m", pattern="^(1m|5m|15m|1h|1d)$"),
    limit: int = Query(100, ge=1, le=500),
) -> list[OHLCVCandle]:
    return feed_manager.get_candles(symbol, timeframe=timeframe, limit=limit)


# -----------------------------------------------------------------------------
# Quant & Fixed Income Analytics Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/quant/yield-curve")
async def get_yield_curve() -> list[dict[str, Any]]:
    try:
        from engines.yield_curve_engine import build_yield_curve
        df = build_yield_curve()
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate yield curve: {e}")


@app.get("/api/quant/screener")
async def get_equity_screener() -> list[dict[str, Any]]:
    try:
        from engines.screener_engine import build_equity_universe, rank_equities
        df = rank_equities(build_equity_universe())
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build equity screener: {e}")


@app.get("/api/quant/cross-asset")
async def get_cross_asset() -> dict[str, Any]:
    try:
        from engines.cross_asset_intelligence_engine import build_cross_asset_snapshot
        snap = build_cross_asset_snapshot()
        corr_matrix = snap["Correlation"].to_dict()
        asset_table = snap["Asset Table"].to_dict(orient="records")
        return {
            "risk_state": snap["Risk State"],
            "cross_asset_score": snap["Cross-Asset Score"],
            "regime": snap["Regime"],
            "leadership": snap["Leadership"],
            "lagging": snap["Lagging"],
            "correlation": corr_matrix,
            "asset_table": asset_table,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build cross-asset analysis: {e}")


class MonteCarloRequest(BaseModel):
    spot: float = 24800.0
    mu: float = 0.12
    sigma: float = 0.15
    days: int = 30
    paths: int = 2000


@app.post("/api/quant/monte-carlo")
async def run_monte_carlo_simulation(req: MonteCarloRequest) -> dict[str, Any]:
    import numpy as np
    dt = 1.0 / 252.0
    drift = (req.mu - 0.5 * req.sigma**2) * dt
    shock = req.sigma * np.sqrt(dt) * np.random.normal(0, 1, (req.paths, req.days))
    log_returns = drift + shock
    log_prices = np.zeros((req.paths, req.days + 1))
    log_prices[:, 0] = np.log(req.spot)
    log_prices[:, 1:] = np.log(req.spot) + np.cumsum(log_returns, axis=1)
    price_paths = np.exp(log_prices)

    quantiles = np.percentile(price_paths, [5, 25, 50, 75, 95], axis=0)
    final_prices = price_paths[:, -1]
    final_returns = (final_prices - req.spot) / req.spot
    var_95 = -float(np.percentile(final_returns, 5) * 100)
    var_99 = -float(np.percentile(final_returns, 1) * 100)
    cvar_95 = -float(final_returns[final_returns <= -var_95 / 100].mean() * 100)

    return {
        "days": list(range(req.days + 1)),
        "p5": quantiles[0].round(2).tolist(),
        "p25": quantiles[1].round(2).tolist(),
        "p50": quantiles[2].round(2).tolist(),
        "p75": quantiles[3].round(2).tolist(),
        "p95": quantiles[4].round(2).tolist(),
        "var_95": round(var_95, 2),
        "var_99": round(var_99, 2),
        "cvar_95": round(cvar_95, 2),
        "mean_final_price": round(float(final_prices.mean()), 2),
    }


@app.get("/api/quant/options-greeks")
async def get_options_greeks(
    spot: float = 24800.0,
    r: float = 0.065,
    q: float = 0.012,
    dte: float = 7.0,
    iv: float = 0.14,
) -> list[dict[str, Any]]:
    from engines.greeks_engine import _bs_price_delta_gamma_theta_vega_rho
    T = max(dte / 365.0, 1e-4)
    step = 100 if spot > 30000 else 50
    atm = round(spot / step) * step
    results = []
    for i in range(-6, 7):
        K = atm + i * step
        ce = _bs_price_delta_gamma_theta_vega_rho(spot, K, T, r, q, iv, "CE")
        pe = _bs_price_delta_gamma_theta_vega_rho(spot, K, T, r, q, iv, "PE")
        results.append({
            "strike": K,
            "is_atm": K == atm,
            "ce_price": round(ce["price"], 2),
            "ce_delta": round(ce["delta"], 4),
            "ce_gamma": round(ce["gamma"], 6),
            "ce_theta": round(ce["theta"], 2),
            "ce_vega": round(ce["vega"], 2),
            "pe_price": round(pe["price"], 2),
            "pe_delta": round(pe["delta"], 4),
            "pe_gamma": round(pe["gamma"], 6),
            "pe_theta": round(pe["theta"], 2),
            "pe_vega": round(pe["vega"], 2),
        })
    return results


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
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            else:
                try:
                    import json
                    from datetime import datetime, timezone
                    msg = json.loads(data)
                    msg_type = msg.get("type")
                    if msg_type == "subscribe":
                        symbol = msg.get("symbol", "NIFTY")
                        snap = feed_manager.get_snapshot(symbol)
                        await websocket.send_json({"type": "snapshot", "data": snap.model_dump()})
                    elif msg_type == "order":
                        # Paper trade execution confirmation
                        order_id = f"ORD-{int(datetime.now().timestamp()*1000)}"
                        await websocket.send_json({
                            "type": "order_confirmed",
                            "order_id": order_id,
                            "symbol": msg.get("symbol"),
                            "side": msg.get("side"),
                            "qty": msg.get("qty"),
                            "price": msg.get("price"),
                            "order_type": msg.get("order_type", "MARKET"),
                            "status": "FILLED",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                except Exception:
                    pass
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

