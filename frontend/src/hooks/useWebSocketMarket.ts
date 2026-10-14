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

export function useWebSocketMarket(activeSymbol: string = 'NIFTY') {
  const [ticks, setTicks] = useState<Record<string, NormalizedTick>>({});
  const [tape, setTape] = useState<TradePrint[]>([]);
  const [status, setStatus] = useState<'CONNECTING' | 'CONNECTED' | 'DISCONNECTED'>('CONNECTING');
  const [latencyMs, setLatencyMs] = useState<number>(4);
  const [activeProvider, setActiveProvider] = useState<string>('SIMULATION');
  const wsRef = useRef<WebSocket | null>(null);
  const pingStartRef = useRef<number>(0);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket('ws://localhost:8000/ws/market');
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('CONNECTED');
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
        } catch (e) {
          // ignore parse error
        }
      };

      ws.onclose = () => {
        setStatus('DISCONNECTED');
        wsRef.current = null;
        // Exponential backoff reconnect
        setTimeout(connect, 2000);
      };

      ws.onerror = () => {
        setStatus('DISCONNECTED');
      };
    } catch (err) {
      setStatus('DISCONNECTED');
      setTimeout(connect, 3000);
    }
  }, [activeSymbol]);

  useEffect(() => {
    connect();

    // Ping interval to monitor socket latency
    const pingInterval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        pingStartRef.current = performance.now();
        wsRef.current.send('ping');
      }
    }, 4000);

    return () => {
      clearInterval(pingInterval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    ticks,
    currentTick: ticks[activeSymbol] || null,
    tape,
    status,
    latencyMs,
    activeProvider,
  };
}
