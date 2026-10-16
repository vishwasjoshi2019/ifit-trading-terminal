import type {
  SystemHealth,
  MarketSnapshot,
  OptionChainSnapshot,
  OHLCVCandle,
  YieldCurvePoint,
  EquityScreenerRow,
  CrossAssetSnapshot,
  MonteCarloResult,
  OptionGreeksRow,
} from '../types';

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

// -----------------------------------------------------------------------------
// Quant, Fixed Income & Analytics API Services
// -----------------------------------------------------------------------------

export async function fetchYieldCurve(): Promise<YieldCurvePoint[]> {
  const base = getBackendBaseUrl();
  try {
    const res = await fetch(`${base}/api/quant/yield-curve`, { signal: AbortSignal.timeout(3000) });
    if (!res.ok) throw new Error('Failed to fetch yield curve');
    return await res.json();
  } catch {
    return [
      { Tenor: '3M', 'Maturity Years': 0.25, 'YTM %': 6.72, 'Yield Change bp': 3.0, Duration: 0.23, 'Slope from 3M bp': 0.0, 'Curve Curvature bp': -38.0, 'Local Slope bp/Yr': 24.0, 'Curve Score': 100.0 },
      { Tenor: '6M', 'Maturity Years': 0.50, 'YTM %': 6.78, 'Yield Change bp': 6.0, Duration: 0.46, 'Slope from 3M bp': 6.0, 'Curve Curvature bp': -32.0, 'Local Slope bp/Yr': 24.0, 'Curve Score': 98.0 },
      { Tenor: '1Y', 'Maturity Years': 1.00, 'YTM %': 6.84, 'Yield Change bp': 6.0, Duration: 0.92, 'Slope from 3M bp': 12.0, 'Curve Curvature bp': -26.0, 'Local Slope bp/Yr': 12.0, 'Curve Score': 96.0 },
      { Tenor: '2Y', 'Maturity Years': 2.00, 'YTM %': 6.91, 'Yield Change bp': 7.0, Duration: 1.70, 'Slope from 3M bp': 19.0, 'Curve Curvature bp': -19.0, 'Local Slope bp/Yr': 7.0, 'Curve Score': 95.0 },
      { Tenor: '3Y', 'Maturity Years': 3.00, 'YTM %': 7.00, 'Yield Change bp': 9.0, Duration: 2.53, 'Slope from 3M bp': 28.0, 'Curve Curvature bp': -10.0, 'Local Slope bp/Yr': 9.0, 'Curve Score': 94.0 },
      { Tenor: '5Y', 'Maturity Years': 5.00, 'YTM %': 7.10, 'Yield Change bp': 10.0, Duration: 4.23, 'Slope from 3M bp': 38.0, 'Curve Curvature bp': 0.0, 'Local Slope bp/Yr': 5.0, 'Curve Score': 93.0 },
      { Tenor: '7Y', 'Maturity Years': 7.00, 'YTM %': 7.18, 'Yield Change bp': 8.0, Duration: 5.93, 'Slope from 3M bp': 46.0, 'Curve Curvature bp': 8.0, 'Local Slope bp/Yr': 4.0, 'Curve Score': 92.0 },
      { Tenor: '10Y', 'Maturity Years': 10.00, 'YTM %': 7.22, 'Yield Change bp': 4.0, Duration: 8.50, 'Slope from 3M bp': 50.0, 'Curve Curvature bp': 12.0, 'Local Slope bp/Yr': 1.3, 'Curve Score': 91.0 },
      { Tenor: '15Y', 'Maturity Years': 15.00, 'YTM %': 7.28, 'Yield Change bp': 6.0, Duration: 12.75, 'Slope from 3M bp': 56.0, 'Curve Curvature bp': 18.0, 'Local Slope bp/Yr': 1.2, 'Curve Score': 89.0 },
      { Tenor: '20Y', 'Maturity Years': 20.00, 'YTM %': 7.34, 'Yield Change bp': 6.0, Duration: 17.00, 'Slope from 3M bp': 62.0, 'Curve Curvature bp': 24.0, 'Local Slope bp/Yr': 1.2, 'Curve Score': 87.0 },
      { Tenor: '30Y', 'Maturity Years': 30.00, 'YTM %': 7.41, 'Yield Change bp': 7.0, Duration: 25.50, 'Slope from 3M bp': 69.0, 'Curve Curvature bp': 31.0, 'Local Slope bp/Yr': 0.7, 'Curve Score': 85.0 },
    ];
  }
}

export async function fetchScreener(): Promise<EquityScreenerRow[]> {
  const base = getBackendBaseUrl();
  try {
    const res = await fetch(`${base}/api/quant/screener`, { signal: AbortSignal.timeout(3000) });
    if (!res.ok) throw new Error('Failed to fetch screener');
    return await res.json();
  } catch {
    return [
      { Symbol: 'RELIANCE', Sector: 'Energy', Price: 2940.50, 'Market Cap (Cr)': 1989000, 'P/E': 26.4, 'ROE %': 13.8, 'ROCE %': 11.2, 'Debt/Equity': 0.42, 'Revenue Growth %': 11.5, 'EPS Growth %': 9.8, 'FCF Yield %': 3.2, 'Avg Volume': 4800000, 'Delivery %': 58.2, 'RSI 14': 62.4, 'EMA Trend': 'BULLISH', 'Momentum 1M %': 4.2, 'Volatility %': 14.5, 'Relative Strength': 1.15, 'Equity Score': 88.5 },
      { Symbol: 'HDFCBANK', Sector: 'Banking', Price: 1682.00, 'Market Cap (Cr)': 1278000, 'P/E': 19.2, 'ROE %': 16.5, 'ROCE %': 14.8, 'Debt/Equity': 0.85, 'Revenue Growth %': 14.2, 'EPS Growth %': 16.1, 'FCF Yield %': 4.1, 'Avg Volume': 11200000, 'Delivery %': 64.5, 'RSI 14': 58.1, 'EMA Trend': 'BULLISH', 'Momentum 1M %': 3.1, 'Volatility %': 16.2, 'Relative Strength': 1.08, 'Equity Score': 89.2 },
      { Symbol: 'ICICIBANK', Sector: 'Banking', Price: 1245.80, 'Market Cap (Cr)': 874000, 'P/E': 18.1, 'ROE %': 18.2, 'ROCE %': 16.4, 'Debt/Equity': 0.78, 'Revenue Growth %': 18.5, 'EPS Growth %': 21.0, 'FCF Yield %': 4.5, 'Avg Volume': 8900000, 'Delivery %': 62.1, 'RSI 14': 66.8, 'EMA Trend': 'STRONG BULLISH', 'Momentum 1M %': 5.8, 'Volatility %': 15.8, 'Relative Strength': 1.24, 'Equity Score': 92.4 },
      { Symbol: 'INFY', Sector: 'IT', Price: 1885.30, 'Market Cap (Cr)': 782000, 'P/E': 28.5, 'ROE %': 31.2, 'ROCE %': 38.5, 'Debt/Equity': 0.08, 'Revenue Growth %': 7.8, 'EPS Growth %': 8.5, 'FCF Yield %': 3.8, 'Avg Volume': 5200000, 'Delivery %': 52.4, 'RSI 14': 54.2, 'EMA Trend': 'NEUTRAL', 'Momentum 1M %': 1.2, 'Volatility %': 18.4, 'Relative Strength': 0.96, 'Equity Score': 84.1 },
      { Symbol: 'TCS', Sector: 'IT', Price: 4220.00, 'Market Cap (Cr)': 1526000, 'P/E': 31.2, 'ROE %': 48.5, 'ROCE %': 58.2, 'Debt/Equity': 0.05, 'Revenue Growth %': 8.4, 'EPS Growth %': 10.2, 'FCF Yield %': 3.5, 'Avg Volume': 2100000, 'Delivery %': 61.8, 'RSI 14': 56.4, 'EMA Trend': 'BULLISH', 'Momentum 1M %': 2.5, 'Volatility %': 14.1, 'Relative Strength': 1.02, 'Equity Score': 87.8 },
      { Symbol: 'LT', Sector: 'Industrials', Price: 3680.00, 'Market Cap (Cr)': 506000, 'P/E': 33.4, 'ROE %': 15.4, 'ROCE %': 17.2, 'Debt/Equity': 0.65, 'Revenue Growth %': 16.8, 'EPS Growth %': 18.2, 'FCF Yield %': 2.8, 'Avg Volume': 1800000, 'Delivery %': 48.9, 'RSI 14': 64.2, 'EMA Trend': 'BULLISH', 'Momentum 1M %': 4.9, 'Volatility %': 17.2, 'Relative Strength': 1.18, 'Equity Score': 86.4 },
      { Symbol: 'BHARTIARTL', Sector: 'Telecom', Price: 1640.20, 'Market Cap (Cr)': 980000, 'P/E': 42.1, 'ROE %': 14.2, 'ROCE %': 13.5, 'Debt/Equity': 1.20, 'Revenue Growth %': 13.5, 'EPS Growth %': 24.5, 'FCF Yield %': 3.1, 'Avg Volume': 4200000, 'Delivery %': 56.4, 'RSI 14': 68.5, 'EMA Trend': 'STRONG BULLISH', 'Momentum 1M %': 6.4, 'Volatility %': 16.5, 'Relative Strength': 1.28, 'Equity Score': 91.0 },
      { Symbol: 'SBIN', Sector: 'Banking', Price: 825.40, 'Market Cap (Cr)': 736000, 'P/E': 11.5, 'ROE %': 17.4, 'ROCE %': 14.1, 'Debt/Equity': 1.10, 'Revenue Growth %': 12.4, 'EPS Growth %': 15.8, 'FCF Yield %': 5.2, 'Avg Volume': 14500000, 'Delivery %': 44.2, 'RSI 14': 59.8, 'EMA Trend': 'BULLISH', 'Momentum 1M %': 3.8, 'Volatility %': 19.5, 'Relative Strength': 1.12, 'Equity Score': 88.0 },
    ];
  }
}

export async function fetchCrossAsset(): Promise<CrossAssetSnapshot> {
  const base = getBackendBaseUrl();
  try {
    const res = await fetch(`${base}/api/quant/cross-asset`, { signal: AbortSignal.timeout(3000) });
    if (!res.ok) throw new Error('Failed to fetch cross-asset snapshot');
    return await res.json();
  } catch {
    return {
      risk_state: 'RISK-ON BALANCED',
      cross_asset_score: 74.2,
      regime: 'EXPANSIONARY EQUITIES',
      leadership: 'DOMESTIC EQUITIES & BULLION',
      lagging: 'RATES & CURRENCY',
      correlation: {
        'NIFTY 50': { 'NIFTY 50': 1.0, BANKNIFTY: 0.88, GOLD: -0.18, 'CRUDE OIL': -0.32, USDINR: -0.42, 'US 10Y': -0.24 },
        BANKNIFTY: { 'NIFTY 50': 0.88, BANKNIFTY: 1.0, GOLD: -0.22, 'CRUDE OIL': -0.28, USDINR: -0.45, 'US 10Y': -0.30 },
        GOLD: { 'NIFTY 50': -0.18, BANKNIFTY: -0.22, GOLD: 1.0, 'CRUDE OIL': 0.35, USDINR: 0.28, 'US 10Y': -0.40 },
        'CRUDE OIL': { 'NIFTY 50': -0.32, BANKNIFTY: -0.28, GOLD: 0.35, 'CRUDE OIL': 1.0, USDINR: 0.52, 'US 10Y': 0.25 },
        USDINR: { 'NIFTY 50': -0.42, BANKNIFTY: -0.45, GOLD: 0.28, 'CRUDE OIL': 0.52, USDINR: 1.0, 'US 10Y': 0.38 },
        'US 10Y': { 'NIFTY 50': -0.24, BANKNIFTY: -0.30, GOLD: -0.40, 'CRUDE OIL': 0.25, USDINR: 0.38, 'US 10Y': 1.0 },
      },
      asset_table: [
        { Symbol: 'NIFTY 50', 'Asset Class': 'Equity', Price: 24820.50, 'Return %': 0.45, Score: 78.5 },
        { Symbol: 'BANKNIFTY', 'Asset Class': 'Equity', Price: 51450.00, 'Return %': 0.62, Score: 81.2 },
        { Symbol: 'G-SEC 10Y', 'Asset Class': 'Bonds', Price: 7.22, 'Return %': -0.02, Score: 68.0 },
        { Symbol: 'GOLD MCX', 'Asset Class': 'Commodity', Price: 76200.00, 'Return %': 0.85, Score: 84.0 },
        { Symbol: 'CRUDE OIL', 'Asset Class': 'Commodity', Price: 72.40, 'Return %': -1.20, Score: 52.0 },
        { Symbol: 'USDINR', 'Asset Class': 'FX', Price: 83.95, 'Return %': 0.05, Score: 64.0 },
        { Symbol: 'S&P 500', 'Asset Class': 'Global', Price: 5850.00, 'Return %': 0.32, Score: 75.0 },
      ],
    };
  }
}

export async function fetchMonteCarlo(spot: number = 24800, days: number = 30, paths: number = 1000): Promise<MonteCarloResult> {
  const base = getBackendBaseUrl();
  try {
    const res = await fetch(`${base}/api/quant/monte-carlo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ spot, days, paths, mu: 0.12, sigma: 0.15 }),
      signal: AbortSignal.timeout(4000),
    });
    if (!res.ok) throw new Error('Monte carlo calculation failed');
    return await res.json();
  } catch {
    const daysArr = Array.from({ length: days + 1 }, (_, i) => i);
    const dt = 1 / 252;
    const vol = 0.15;
    const p5 = daysArr.map((d) => +(spot * Math.exp(-1.645 * vol * Math.sqrt(d * dt))).toFixed(2));
    const p25 = daysArr.map((d) => +(spot * Math.exp(-0.674 * vol * Math.sqrt(d * dt))).toFixed(2));
    const p50 = daysArr.map((d) => +(spot * Math.exp(0.10 * d * dt)).toFixed(2));
    const p75 = daysArr.map((d) => +(spot * Math.exp(0.674 * vol * Math.sqrt(d * dt))).toFixed(2));
    const p95 = daysArr.map((d) => +(spot * Math.exp(1.645 * vol * Math.sqrt(d * dt))).toFixed(2));

    return {
      days: daysArr,
      p5,
      p25,
      p50,
      p75,
      p95,
      var_95: 5.85,
      var_99: 8.92,
      cvar_95: 7.42,
      mean_final_price: +(spot * 1.015).toFixed(2),
    };
  }
}

export async function fetchOptionGreeks(spot: number = 24800): Promise<OptionGreeksRow[]> {
  const base = getBackendBaseUrl();
  try {
    const res = await fetch(`${base}/api/quant/options-greeks?spot=${spot}`, { signal: AbortSignal.timeout(3000) });
    if (!res.ok) throw new Error('Failed to fetch option greeks');
    return await res.json();
  } catch {
    const step = spot > 30000 ? 100 : 50;
    const atm = Math.round(spot / step) * step;
    const rows: OptionGreeksRow[] = [];
    for (let i = -6; i <= 6; i++) {
      const strike = atm + i * step;
      const d = (strike - spot) / spot;
      rows.push({
        strike,
        is_atm: i === 0,
        ce_price: Math.max(1, +(spot * Math.max(0.001, 0.018 - d * 0.7)).toFixed(2)),
        ce_delta: +(0.50 - i * 0.06).toFixed(4),
        ce_gamma: +(0.0008 * Math.exp(-Math.pow(i / 3, 2))).toFixed(6),
        ce_theta: +(-15.2 * Math.exp(-Math.pow(i / 3, 2))).toFixed(2),
        ce_vega: +(14.5 * Math.exp(-Math.pow(i / 3, 2))).toFixed(2),
        pe_price: Math.max(1, +(spot * Math.max(0.001, 0.018 + d * 0.7)).toFixed(2)),
        pe_delta: +(-0.50 - i * 0.06).toFixed(4),
        pe_gamma: +(0.0008 * Math.exp(-Math.pow(i / 3, 2))).toFixed(6),
        pe_theta: +(-14.8 * Math.exp(-Math.pow(i / 3, 2))).toFixed(2),
        pe_vega: +(14.5 * Math.exp(-Math.pow(i / 3, 2))).toFixed(2),
      });
    }
    return rows;
  }
}
