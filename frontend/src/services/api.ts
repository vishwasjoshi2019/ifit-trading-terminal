import type { SystemHealth, MarketSnapshot, OptionChainSnapshot, OHLCVCandle } from '../types';

export function getBackendBaseUrl(): string {
  if (typeof window !== 'undefined') {
    const custom = localStorage.getItem('ifit_backend_url');
    if (custom) return custom.replace(/\/$/, '');
    if (import.meta.env.VITE_BACKEND_URL) return import.meta.env.VITE_BACKEND_URL.replace(/\/$/, '');
    // If running on a dedicated cloud host (Render, Fly, Railway) that serves this frontend
    if (window.location.hostname !== 'localhost' && !window.location.hostname.endsWith('vercel.app')) {
      return window.location.origin;
    }
  }
  return 'http://localhost:8000';
}

export function setBackendBaseUrl(url: string): void {
  if (typeof window !== 'undefined') {
    if (!url || url.trim() === '') {
      localStorage.removeItem('ifit_backend_url');
    } else {
      localStorage.setItem('ifit_backend_url', url.trim());
    }
  }
}

// Resilient fallback candle generator for standalone cloud previews (e.g. Vercel)
function generateFallbackCandles(symbol: string, limit: number = 100): OHLCVCandle[] {
  const basePrice = symbol === 'BANKNIFTY' ? 48500 : symbol === 'FINNIFTY' ? 21800 : 22500;
  const candles: OHLCVCandle[] = [];
  const now = Date.now();
  let current = basePrice;
  let runningCvd = 0;

  for (let i = limit; i >= 0; i--) {
    const time = new Date(now - i * 60 * 1000).toISOString();
    const change = (Math.random() - 0.49) * (basePrice * 0.0015);
    const open = current;
    const close = +(open + change).toFixed(2);
    const high = +(Math.max(open, close) + Math.random() * (basePrice * 0.0008)).toFixed(2);
    const low = +(Math.min(open, close) - Math.random() * (basePrice * 0.0008)).toFixed(2);
    const volume = Math.floor(1000 + Math.random() * 5000);
    runningCvd += (close >= open ? 1 : -1) * (volume * (0.3 + Math.random() * 0.4));

    candles.push({
      timestamp: time,
      open,
      high,
      low,
      close,
      volume,
      cvd: Math.round(runningCvd),
    });
    current = close;
  }
  return candles;
}

function generateFallbackOptionChain(symbol: string): OptionChainSnapshot {
  const spot = symbol === 'BANKNIFTY' ? 48500 : symbol === 'FINNIFTY' ? 21800 : 22500;
  const step = symbol === 'BANKNIFTY' ? 100 : 50;
  const atm = Math.round(spot / step) * step;
  const strikes = [];

  for (let i = -7; i <= 7; i++) {
    const strike = atm + i * step;
    const diff = (strike - spot) / spot;
    const ce_ltp = Math.max(1, +(spot * Math.max(0.001, 0.02 - diff * 0.8)).toFixed(2));
    const pe_ltp = Math.max(1, +(spot * Math.max(0.001, 0.02 + diff * 0.8)).toFixed(2));
    const distWeight = Math.exp(-Math.pow(i / 4, 2));

    strikes.push({
      strike,
      ce_ltp,
      ce_oi: Math.round(2500000 * distWeight + Math.random() * 500000),
      ce_iv: +(13.5 + Math.abs(i) * 0.3).toFixed(2),
      ce_volume: Math.round(150000 * distWeight),
      pe_ltp,
      pe_oi: Math.round(2700000 * distWeight + Math.random() * 500000),
      pe_iv: +(14.2 + Math.abs(i) * 0.3).toFixed(2),
      pe_volume: Math.round(160000 * distWeight),
    });
  }

  return {
    underlying_symbol: symbol,
    underlying_price: spot,
    expiry: 'CURRENT_WEEKLY',
    strikes,
    pcr_oi: 1.08,
    pcr_volume: 1.05,
    max_pain: atm,
    timestamp: new Date().toISOString(),
  };
}

export async function fetchHealth(): Promise<SystemHealth> {
  const base = getBackendBaseUrl();
  try {
    const res = await fetch(`${base}/api/health`, { signal: AbortSignal.timeout(3000) });
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return await res.json();
  } catch {
    return {
      status: 'FALLBACK_SIMULATION',
      service: 'IFIT Standalone Cloud Mode',
      active_provider: 'SIMULATION (Client-Side)',
      connected_ws_clients: 1,
      providers: [
        { name: 'SIMULATION', status: 'ACTIVE', is_live: true },
        { name: 'DHAN', status: 'STANDBY', is_live: false },
        { name: 'ZERODHA', status: 'STANDBY', is_live: false },
      ],
    };
  }
}

export async function fetchSnapshot(symbol: string): Promise<MarketSnapshot> {
  const base = getBackendBaseUrl();
  try {
    const res = await fetch(`${base}/api/snapshot/${encodeURIComponent(symbol)}`, { signal: AbortSignal.timeout(3000) });
    if (!res.ok) throw new Error(`Failed to fetch snapshot for ${symbol}`);
    return await res.json();
  } catch {
    const candles = generateFallbackCandles(symbol, 60);
    return {
      symbol,
      recent_candles: candles,
      cvd_total: candles[candles.length - 1]?.cvd || 0,
      timestamp: new Date().toISOString(),
    };
  }
}

export async function fetchOptionChain(symbol: string): Promise<OptionChainSnapshot> {
  const base = getBackendBaseUrl();
  try {
    const res = await fetch(`${base}/api/option-chain/${encodeURIComponent(symbol)}`, { signal: AbortSignal.timeout(3000) });
    if (!res.ok) throw new Error(`Failed to fetch option chain for ${symbol}`);
    return await res.json();
  } catch {
    return generateFallbackOptionChain(symbol);
  }
}

export async function fetchCandles(symbol: string, timeframe: string = '1m', limit: number = 100): Promise<OHLCVCandle[]> {
  const base = getBackendBaseUrl();
  try {
    const res = await fetch(`${base}/api/candles/${encodeURIComponent(symbol)}?timeframe=${timeframe}&limit=${limit}`, { signal: AbortSignal.timeout(3000) });
    if (!res.ok) throw new Error(`Failed to fetch candles for ${symbol}`);
    return await res.json();
  } catch {
    return generateFallbackCandles(symbol, limit);
  }
}

export async function switchProvider(provider: string): Promise<{ status: string; active_provider: string; is_live: boolean }> {
  const base = getBackendBaseUrl();
  const res = await fetch(`${base}/api/providers/switch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to switch provider');
  }
  return res.json();
}
