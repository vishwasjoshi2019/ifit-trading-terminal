import { useState, useEffect, useRef, useCallback } from 'react';
import type { NormalizedTick } from '../types';

export interface TradePrint {
  id: string;
  symbol: string;
  price: number;
  qty: number;
  time: string;
  isBuyer: boolean;
}

function getWebSocketUrl(): string {
  if (typeof window !== 'undefined') {
    const custom = localStorage.getItem('ifit_backend_url');
    if (custom) {
      const clean = custom.replace(/^http/, 'ws').replace(/\/$/, '');
      return `${clean}/ws/market`;
    }
    if (import.meta.env.VITE_BACKEND_URL) {
      const clean = import.meta.env.VITE_BACKEND_URL.replace(/^http/, 'ws').replace(/\/$/, '');
      return `${clean}/ws/market`;
    }
    // Remote single-port deployment (Render / container)
    if (window.location.hostname !== 'localhost' && !window.location.hostname.endsWith('vercel.app')) {
      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${proto}//${window.location.host}/ws/market`;
    }
  }
  return 'ws://localhost:8000/ws/market';
}

export function useWebSocketMarket(activeSymbol: string = 'NIFTY') {
  const [ticks, setTicks] = useState<Record<string, NormalizedTick>>({});
  const [tape, setTape] = useState<TradePrint[]>([]);
  const [status, setStatus] = useState<'CONNECTING' | 'CONNECTED' | 'DISCONNECTED'>('CONNECTING');
  const [latencyMs, setLatencyMs] = useState<number>(4);
  const [activeProvider, setActiveProvider] = useState<string>('SIMULATION');
  const wsRef = useRef<WebSocket | null>(null);
  const pingStartRef = useRef<number>(0);
  const isConnectedRef = useRef<boolean>(false);

  const connect = useCallback(() => {
    try {
      const url = getWebSocketUrl();
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('CONNECTED');
        isConnectedRef.current = true;
      };

      ws.onmessage = (event) => {
        try {
          if (event.data === 'pong') {
            const rtt = Math.max(1, Math.round(performance.now() - pingStartRef.current));
            setLatencyMs(rtt);
            return;
          }

          const msg = JSON.parse(event.data);
          if (msg.type === 'handshake') {
            setActiveProvider(msg.active_provider || 'SIMULATION');
          } else if (msg.type === 'provider_changed') {
            setActiveProvider(msg.active_provider || 'SIMULATION');
          } else if (msg.type === 'tick' && msg.data) {
            const tick: NormalizedTick = msg.data;
            setTicks((prev) => ({ ...prev, [tick.symbol]: tick }));

            // Add trade to tape if matching active symbol
            if (tick.symbol === activeSymbol) {
              const tradePrice = tick.trade_price ?? tick.ltp;
              const tradeQty = tick.trade_qty ?? 50;
              const isBuyer = tick.bid && tradePrice >= (tick.ask + tick.bid) / 2;

              const print: TradePrint = {
                id: `${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
                symbol: tick.symbol,
                price: tradePrice,
                qty: tradeQty,
                time: new Date(tick.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
                isBuyer: Boolean(isBuyer),
              };

              setTape((prev) => [print, ...prev.slice(0, 49)]);
            }
          }
        } catch {
          // ignore parse error
        }
      };

      ws.onclose = () => {
        setStatus('DISCONNECTED');
        isConnectedRef.current = false;
        wsRef.current = null;
        setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        setStatus('DISCONNECTED');
        isConnectedRef.current = false;
      };
    } catch {
      setStatus('DISCONNECTED');
      isConnectedRef.current = false;
      setTimeout(connect, 4000);
    }
  }, [activeSymbol]);

  useEffect(() => {
    connect();

    // Ping interval to monitor socket latency when connected
    const pingInterval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        pingStartRef.current = performance.now();
        wsRef.current.send('ping');
      }
    }, 4000);

    // Client-side simulation fallback when disconnected (e.g. standalone Vercel preview)
    const fallbackTicker = setInterval(() => {
      if (!isConnectedRef.current) {
        const symbols = ['NIFTY', 'BANKNIFTY', 'FINNIFTY'];
        symbols.forEach((sym) => {
          const base = sym === 'BANKNIFTY' ? 48500 : sym === 'FINNIFTY' ? 21800 : 22500;
          setTicks((prev) => {
            const last = prev[sym]?.ltp || base;
            const delta = (Math.random() - 0.495) * (base * 0.0003);
            const ltp = +(last + delta).toFixed(2);
            const spread = +(base * 0.0001).toFixed(2);
            const isUp = delta >= 0;

            if (sym === activeSymbol && Math.random() > 0.4) {
              const print: TradePrint = {
                id: `${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
                symbol: sym,
                price: ltp,
                qty: Math.floor(25 + Math.random() * 100) * (sym === 'BANKNIFTY' ? 15 : 25),
                time: new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
                isBuyer: isUp,
              };
              setTape((tapePrev) => [print, ...tapePrev.slice(0, 49)]);
            }

            return {
              ...prev,
              [sym]: {
                symbol: sym,
                exchange: 'NSE',
                segment: 'INDEX',
                timestamp: new Date().toISOString(),
                ltp,
                open: +(base * 0.998).toFixed(2),
                high: Math.max(ltp, +(base * 1.004).toFixed(2)),
                low: Math.min(ltp, +(base * 0.995).toFixed(2)),
                close: base,
                volume: Math.floor(1500000 + Math.random() * 50000),
                net_change: +(ltp - base).toFixed(2),
                percentage_change: +(((ltp - base) / base) * 100).toFixed(2),
                bid: +(ltp - spread / 2).toFixed(2),
                ask: +(ltp + spread / 2).toFixed(2),
                bid_qty: Math.floor(500 + Math.random() * 2000),
                ask_qty: Math.floor(500 + Math.random() * 2000),
                oi: Math.floor(12000000 + Math.random() * 20000),
                oi_change: Math.floor(150000 + Math.random() * 5000),
                source: 'SIMULATION (Client Fallback)',
                is_live: false,
              },
            };
          });
        });
      }
    }, 400);

    return () => {
      clearInterval(pingInterval);
      clearInterval(fallbackTicker);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect, activeSymbol]);

  return {
    ticks,
    currentTick: ticks[activeSymbol] || null,
    tape,
    status,
    latencyMs,
    activeProvider: isConnectedRef.current ? activeProvider : 'SIMULATION (Standalone Preview)',
  };
}
