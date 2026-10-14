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
