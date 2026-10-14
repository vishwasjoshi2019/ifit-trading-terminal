import type { SystemHealth, MarketSnapshot, OptionChainSnapshot, OHLCVCandle } from '../types';

const API_BASE = 'http://localhost:8000';

export async function fetchHealth(): Promise<SystemHealth> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchSnapshot(symbol: string): Promise<MarketSnapshot> {
  const res = await fetch(`${API_BASE}/api/snapshot/${encodeURIComponent(symbol)}`);
  if (!res.ok) throw new Error(`Failed to fetch snapshot for ${symbol}`);
  return res.json();
}

export async function fetchOptionChain(symbol: string): Promise<OptionChainSnapshot> {
  const res = await fetch(`${API_BASE}/api/option-chain/${encodeURIComponent(symbol)}`);
  if (!res.ok) throw new Error(`Failed to fetch option chain for ${symbol}`);
  return res.json();
}

export async function fetchCandles(symbol: string, timeframe: string = '1m', limit: number = 100): Promise<OHLCVCandle[]> {
  const res = await fetch(`${API_BASE}/api/candles/${encodeURIComponent(symbol)}?timeframe=${timeframe}&limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch candles for ${symbol}`);
  return res.json();
}

export async function switchProvider(provider: string): Promise<{ status: string; active_provider: string; is_live: boolean }> {
  const res = await fetch(`${API_BASE}/api/providers/switch`, {
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
