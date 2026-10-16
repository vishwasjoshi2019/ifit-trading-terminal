export interface NormalizedTick {
  symbol: string;
  exchange: string;
  segment: string;
  token?: string;
  timestamp: string;
  ltp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  net_change: number;
  percentage_change: number;
  bid: number;
  ask: number;
  bid_qty: number;
  ask_qty: number;
  oi: number;
  oi_change: number;
  trade_price?: number;
  trade_qty?: number;
  source: string;
  is_live: boolean;
}

export interface OrderBookLevel {
  level: number;
  bid: number;
  bid_qty: number;
  ask: number;
  ask_qty: number;
}

export interface OrderBookDepth {
  symbol: string;
  timestamp: string;
  levels: OrderBookLevel[];
  total_buy_qty: number;
  total_sell_qty: number;
  spread: number;
  source: string;
}

export interface OHLCVCandle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  cvd: number;
  oi?: number;
}

export interface OptionStrike {
  strike: number;
  ce_ltp: number;
  ce_oi: number;
  ce_iv: number;
  ce_volume: number;
  pe_ltp: number;
  pe_oi: number;
  pe_iv: number;
  pe_volume: number;
}

export interface OptionChainSnapshot {
  underlying_symbol: string;
  underlying_price: number;
  expiry: string;
  strikes: OptionStrike[];
  pcr_oi: number;
  pcr_volume: number;
  max_pain: number;
  timestamp: string;
}

export interface MarketSnapshot {
  symbol: string;
  tick?: NormalizedTick;
  depth?: OrderBookDepth;
  recent_candles: OHLCVCandle[];
  cvd_total: number;
  timestamp: string;
}

export interface ProviderHealth {
  name: string;
  status: string;
  is_live: boolean;
  details?: Record<string, any>;
}

export interface SystemHealth {
  status: string;
  service: string;
  active_provider: string;
  connected_ws_clients: number;
  providers: ProviderHealth[];
}

export type WorkspaceTab = 'COCKPIT' | 'OPTIONS' | 'RISK' | 'BONDS' | 'SCREENER' | 'CROSS_ASSET';

export interface YieldCurvePoint {
  Tenor: string;
  'Maturity Years': number;
  'YTM %': number;
  'Yield Change bp': number;
  Duration: number;
  'Slope from 3M bp': number;
  'Curve Curvature bp': number;
  'Local Slope bp/Yr': number;
  'Curve Score': number;
}

export interface EquityScreenerRow {
  Symbol: string;
  Sector: string;
  Price: number;
  'Market Cap (Cr)': number;
  'P/E': number;
  'ROE %': number;
  'ROCE %': number;
  'Debt/Equity': number;
  'Revenue Growth %': number;
  'EPS Growth %': number;
  'FCF Yield %': number;
  'Avg Volume': number;
  'Delivery %': number;
  'RSI 14': number;
  'EMA Trend': string;
  'Momentum 1M %': number;
  'Volatility %': number;
  'Relative Strength': number;
  'Equity Score': number;
}

export interface CrossAssetRow {
  Symbol: string;
  'Asset Class': string;
  Price: number;
  'Return %': number;
  Score: number;
}

export interface CrossAssetSnapshot {
  risk_state: string;
  cross_asset_score: number;
  regime: string;
  leadership: string;
  lagging: string;
  correlation: Record<string, Record<string, number>>;
  asset_table: CrossAssetRow[];
}

export interface MonteCarloResult {
  days: number[];
  p5: number[];
  p25: number[];
  p50: number[];
  p75: number[];
  p95: number[];
  var_95: number;
  var_99: number;
  cvar_95: number;
  mean_final_price: number;
}

export interface OptionGreeksRow {
  strike: number;
  is_atm: boolean;
  ce_price: number;
  ce_delta: number;
  ce_gamma: number;
  ce_theta: number;
  ce_vega: number;
  pe_price: number;
  pe_delta: number;
  pe_gamma: number;
  pe_theta: number;
  pe_vega: number;
}

export interface PaperOrder {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  qty: number;
  price: number;
  orderType: 'MARKET' | 'LIMIT' | 'SL';
  status: 'FILLED' | 'PENDING' | 'CANCELLED';
  time: string;
}

export interface Position {
  symbol: string;
  side: 'BUY' | 'SELL';
  qty: number;
  avgPrice: number;
  currentPrice: number;
  unrealizedPnl: number;
  pnlPercentage: number;
}
