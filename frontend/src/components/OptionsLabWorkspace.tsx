import React, { useState, useEffect } from 'react';
import type { NormalizedTick, OptionGreeksRow } from '../types';
import { fetchOptionGreeks } from '../services/api';
import { Zap, Activity, TrendingUp, Sliders, Layers } from 'lucide-react';

interface OptionsLabWorkspaceProps {
  symbol: string;
  currentTick: NormalizedTick | null;
}

type StrategyType = 'BULL_CALL_SPREAD' | 'BEAR_PUT_SPREAD' | 'LONG_STRADDLE' | 'IRON_CONDOR' | 'NAKED_CALL';

export const OptionsLabWorkspace: React.FC<OptionsLabWorkspaceProps> = ({ symbol, currentTick }) => {
  const spot = currentTick?.ltp || (symbol === 'BANKNIFTY' ? 51400 : 24800);
  const [greeks, setGreeks] = useState<OptionGreeksRow[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyType>('BULL_CALL_SPREAD');
  const [ivOverride, setIvOverride] = useState<number>(14.5);
  const [daysToExpiry, setDaysToExpiry] = useState<number>(7);

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchOptionGreeks(spot)
      .then((data) => {
        if (active) {
          setGreeks(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [spot]);

  // Strategy payoff calculation
  const step = symbol === 'BANKNIFTY' ? 100 : 50;
  const atm = Math.round(spot / step) * step;

  const getStrategyMetrics = () => {
    switch (selectedStrategy) {
      case 'BULL_CALL_SPREAD':
        return {
          title: 'Bull Call Spread (Debit)',
          description: `Buy ${atm} CE, Sell ${atm + step * 2} CE. Defined risk bullish strategy.`,
          legs: [
            { type: 'BUY', strike: atm, opt: 'CE', premium: +(spot * 0.012).toFixed(1) },
            { type: 'SELL', strike: atm + step * 2, opt: 'CE', premium: +(spot * 0.005).toFixed(1) },
          ],
          maxProfit: +((step * 2 - (spot * 0.012 - spot * 0.005)) * 25).toFixed(0),
          maxLoss: +((spot * 0.012 - spot * 0.005) * 25).toFixed(0),
          breakeven: +(atm + (spot * 0.012 - spot * 0.005)).toFixed(1),
          rrRatio: '1 : 2.4',
        };
      case 'BEAR_PUT_SPREAD':
        return {
          title: 'Bear Put Spread (Debit)',
          description: `Buy ${atm} PE, Sell ${atm - step * 2} PE. Defined risk bearish strategy.`,
          legs: [
            { type: 'BUY', strike: atm, opt: 'PE', premium: +(spot * 0.012).toFixed(1) },
            { type: 'SELL', strike: atm - step * 2, opt: 'PE', premium: +(spot * 0.005).toFixed(1) },
          ],
          maxProfit: +((step * 2 - (spot * 0.012 - spot * 0.005)) * 25).toFixed(0),
          maxLoss: +((spot * 0.012 - spot * 0.005) * 25).toFixed(0),
          breakeven: +(atm - (spot * 0.012 - spot * 0.005)).toFixed(1),
          rrRatio: '1 : 2.4',
        };
      case 'LONG_STRADDLE':
        return {
          title: 'Long Straddle (High Volatility Play)',
          description: `Buy ${atm} CE + Buy ${atm} PE. Profits from sharp breakout in either direction.`,
          legs: [
            { type: 'BUY', strike: atm, opt: 'CE', premium: +(spot * 0.011).toFixed(1) },
            { type: 'BUY', strike: atm, opt: 'PE', premium: +(spot * 0.011).toFixed(1) },
          ],
          maxProfit: 'UNLIMITED',
          maxLoss: +((spot * 0.022) * 25).toFixed(0),
          breakeven: `${(atm - spot * 0.022).toFixed(0)} / ${(atm + spot * 0.022).toFixed(0)}`,
          rrRatio: 'Dynamic',
        };
      case 'IRON_CONDOR':
        return {
          title: 'Iron Condor (Range-Bound / Non-Directional)',
          description: `Sell OTM Strangle + Buy Wings. High probability credit theta harvest.`,
          legs: [
            { type: 'BUY', strike: atm - step * 3, opt: 'PE', premium: +(spot * 0.003).toFixed(1) },
            { type: 'SELL', strike: atm - step, opt: 'PE', premium: +(spot * 0.008).toFixed(1) },
            { type: 'SELL', strike: atm + step, opt: 'CE', premium: +(spot * 0.008).toFixed(1) },
            { type: 'BUY', strike: atm + step * 3, opt: 'CE', premium: +(spot * 0.003).toFixed(1) },
          ],
          maxProfit: +((spot * 0.010) * 25).toFixed(0),
          maxLoss: +((step * 2 - spot * 0.010) * 25).toFixed(0),
          breakeven: `${(atm - step - spot * 0.010).toFixed(0)} / ${(atm + step + spot * 0.010).toFixed(0)}`,
          rrRatio: '1 : 1.8',
        };
      default:
        return {
          title: 'Naked Long Call',
          description: `Buy ${atm} CE. Directional upside leverage.`,
          legs: [{ type: 'BUY', strike: atm, opt: 'CE', premium: +(spot * 0.012).toFixed(1) }],
          maxProfit: 'UNLIMITED',
          maxLoss: +((spot * 0.012) * 25).toFixed(0),
          breakeven: +(atm + spot * 0.012).toFixed(1),
          rrRatio: 'Asymmetric',
        };
    }
  };

  const metrics = getStrategyMetrics();

  // Generate SVG Payoff curve points
  const points = [];
  const range = step * 6;
  const startPrice = spot - range;
  const endPrice = spot + range;
  const width = 600;
  const height = 180;

  for (let i = 0; i <= 20; i++) {
    const p = startPrice + (endPrice - startPrice) * (i / 20);
    let pnl = 0;
    if (selectedStrategy === 'BULL_CALL_SPREAD') {
      const longVal = Math.max(0, p - atm) - spot * 0.012;
      const shortVal = -(Math.max(0, p - (atm + step * 2)) - spot * 0.005);
      pnl = (longVal + shortVal) * 25;
    } else if (selectedStrategy === 'BEAR_PUT_SPREAD') {
      const longVal = Math.max(0, atm - p) - spot * 0.012;
      const shortVal = -(Math.max(0, atm - step * 2 - p) - spot * 0.005);
      pnl = (longVal + shortVal) * 25;
    } else if (selectedStrategy === 'LONG_STRADDLE') {
      const callVal = Math.max(0, p - atm);
      const putVal = Math.max(0, atm - p);
      pnl = (callVal + putVal - spot * 0.022) * 25;
    } else if (selectedStrategy === 'IRON_CONDOR') {
      const netCredit = spot * 0.010;
      let loss = 0;
      if (p > atm + step) loss = Math.min(step * 2, p - (atm + step));
      if (p < atm - step) loss = Math.min(step * 2, (atm - step) - p);
      pnl = (netCredit - loss) * 25;
    } else {
      pnl = (Math.max(0, p - atm) - spot * 0.012) * 25;
    }
    const x = (i / 20) * width;
    const maxBound = Math.max(1000, typeof metrics.maxProfit === 'number' ? metrics.maxProfit : 5000);
    const y = height / 2 - (pnl / maxBound) * (height / 2.4);
    points.push(`${x},${Math.max(10, Math.min(height - 10, y))}`);
  }

  const polylineStr = points.join(' ');

  return (
    <div className="flex flex-col h-full bg-terminal-bg text-terminal-text overflow-y-auto p-4 space-y-4 font-mono select-none">
      {/* Top Banner: Metrics & Strategy Selector */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 bg-terminal-panel p-3.5 rounded border border-terminal-border">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-bold text-gray-100">BLACK-SCHOLES OPTIONS LAB & STRATEGY ENGINE</h2>
            <span className="text-[11px] bg-blue-950/60 border border-blue-500/40 text-blue-300 px-2 py-0.5 rounded">
              {symbol} @ ₹{spot.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>
          <p className="text-[11px] text-gray-400 mt-0.5">
            Real-time analytical Greeks (Delta, Gamma, Vega, Theta), Volatility Smile, and Strategy Payoffs.
          </p>
        </div>

        {/* Strategy Presets */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {(
            [
              ['BULL_CALL_SPREAD', 'Bull Call'],
              ['BEAR_PUT_SPREAD', 'Bear Put'],
              ['LONG_STRADDLE', 'Straddle'],
              ['IRON_CONDOR', 'Iron Condor'],
              ['NAKED_CALL', 'Naked Call'],
            ] as const
          ).map(([stratKey, label]) => (
            <button
              key={stratKey}
              onClick={() => setSelectedStrategy(stratKey)}
              className={`px-2.5 py-1 rounded text-xs font-semibold transition-all ${
                selectedStrategy === stratKey
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-terminal-bg border border-terminal-border text-gray-400 hover:text-gray-100'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Strategy Summary & Payoff Visualizer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left: Strategy Specs */}
        <div className="bg-terminal-panel p-3.5 rounded border border-terminal-border space-y-3">
          <div className="flex items-center justify-between border-b border-terminal-border pb-2">
            <span className="text-xs font-bold text-gray-200">{metrics.title}</span>
            <span className="text-[10px] text-blue-400 font-semibold bg-blue-950/40 px-2 py-0.5 rounded border border-blue-800/40">
              R:R {metrics.rrRatio}
            </span>
          </div>
          <p className="text-[11px] text-gray-400 leading-relaxed">{metrics.description}</p>

          <div className="space-y-1.5">
            <span className="text-[10px] text-gray-400 uppercase font-semibold">Legs Breakdown:</span>
            {metrics.legs.map((leg, i) => (
              <div key={i} className="flex justify-between items-center text-xs p-1.5 bg-terminal-bg rounded border border-terminal-border/60">
                <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${leg.type === 'BUY' ? 'bg-green-950 text-terminal-green' : 'bg-red-950 text-terminal-red'}`}>
                  {leg.type}
                </span>
                <span className="font-bold text-gray-200">{symbol} {leg.strike} {leg.opt}</span>
                <span className="text-gray-400">₹{leg.premium}</span>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-3 gap-2 pt-1 text-center text-xs">
            <div className="p-2 bg-terminal-bg rounded border border-terminal-border/60">
              <div className="text-[10px] text-gray-500 uppercase">Max Profit</div>
              <div className="font-bold text-terminal-green text-xs mt-0.5">
                {typeof metrics.maxProfit === 'number' ? `₹${metrics.maxProfit.toLocaleString('en-IN')}` : metrics.maxProfit}
              </div>
            </div>
            <div className="p-2 bg-terminal-bg rounded border border-terminal-border/60">
              <div className="text-[10px] text-gray-500 uppercase">Max Loss</div>
              <div className="font-bold text-terminal-red text-xs mt-0.5">
                {typeof metrics.maxLoss === 'number' ? `₹${metrics.maxLoss.toLocaleString('en-IN')}` : metrics.maxLoss}
              </div>
            </div>
            <div className="p-2 bg-terminal-bg rounded border border-terminal-border/60">
              <div className="text-[10px] text-gray-500 uppercase">Breakeven</div>
              <div className="font-bold text-amber-400 text-xs mt-0.5">{metrics.breakeven}</div>
            </div>
          </div>
        </div>

        {/* Right: SVG Payoff Diagram */}
        <div className="lg:col-span-2 bg-terminal-panel p-3.5 rounded border border-terminal-border flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-terminal-border pb-2">
            <div className="flex items-center gap-1.5 text-xs font-bold text-gray-200">
              <TrendingUp className="w-3.5 h-3.5 text-terminal-green" />
              <span>DYNAMIC EXPIRY PAYOFF CURVE (MTM PROFILE)</span>
            </div>
            <div className="flex items-center gap-3 text-[10px] text-gray-400">
              <span>ATM: ₹{atm}</span>
              <span>IV: {ivOverride}%</span>
              <span>DTE: {daysToExpiry}D</span>
            </div>
          </div>

          <div className="relative w-full h-[180px] bg-[#05070a] rounded border border-terminal-border/50 my-2 overflow-hidden flex items-center justify-center">
            {/* Zero axis line */}
            <div className="absolute w-full h-[1px] bg-gray-700/80 top-1/2" />
            <span className="absolute left-2 top-[44%] text-[9px] text-gray-400 font-bold">PROFIT (+)</span>
            <span className="absolute left-2 top-[54%] text-[9px] text-gray-400 font-bold">LOSS (-)</span>

            <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible">
              <polyline fill="none" stroke="#22c55e" strokeWidth="2.5" points={polylineStr} />
            </svg>
          </div>

          <div className="flex justify-between text-[10px] text-gray-500 px-1">
            <span>₹{(startPrice).toFixed(0)} (-{(range / spot * 100).toFixed(1)}%)</span>
            <span className="text-blue-400 font-bold">SPOT: ₹{spot.toFixed(0)}</span>
            <span>₹{(endPrice).toFixed(0)} (+{(range / spot * 100).toFixed(1)}%)</span>
          </div>
        </div>
      </div>

      {/* Bottom: Black-Scholes Greeks Ladder */}
      <div className="bg-terminal-panel p-3.5 rounded border border-terminal-border">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-1.5 text-xs font-bold text-gray-200">
            <Layers className="w-3.5 h-3.5 text-blue-400" />
            <span>BLACK-SCHOLES GREEK RUNNER (DELTA / GAMMA / THETA / VEGA)</span>
          </div>
          <span className="text-[10px] text-gray-400">Risk-free Rate r=6.5% | Div Yield q=1.2%</span>
        </div>

        <div className="overflow-x-auto text-xs">
          <table className="w-full text-center border-collapse">
            <thead>
              <tr className="bg-terminal-header text-[11px] text-gray-400 border-b border-terminal-border">
                <th className="py-1.5 px-2 text-terminal-green">CE PRICE</th>
                <th className="py-1.5 px-2">CE DELTA</th>
                <th className="py-1.5 px-2">CE GAMMA</th>
                <th className="py-1.5 px-2">CE THETA</th>
                <th className="py-1.5 px-2">CE VEGA</th>
                <th className="py-1.5 px-3 bg-blue-950/40 text-blue-300 font-bold border-x border-blue-900/40">STRIKE</th>
                <th className="py-1.5 px-2">PE VEGA</th>
                <th className="py-1.5 px-2">PE THETA</th>
                <th className="py-1.5 px-2">PE GAMMA</th>
                <th className="py-1.5 px-2">PE DELTA</th>
                <th className="py-1.5 px-2 text-terminal-red">PE PRICE</th>
              </tr>
            </thead>
            <tbody>
              {greeks.map((row) => (
                <tr
                  key={row.strike}
                  className={`border-b border-terminal-border/40 hover:bg-terminal-hover transition-colors ${
                    row.is_atm ? 'bg-blue-950/20 font-bold text-amber-300' : 'text-gray-300'
                  }`}
                >
                  <td className="py-1.5 px-2 text-terminal-green font-semibold">₹{row.ce_price}</td>
                  <td className="py-1.5 px-2 font-mono">{row.ce_delta}</td>
                  <td className="py-1.5 px-2 font-mono text-gray-400">{row.ce_gamma}</td>
                  <td className="py-1.5 px-2 font-mono text-red-400">{row.ce_theta}</td>
                  <td className="py-1.5 px-2 font-mono text-blue-300">{row.ce_vega}</td>
                  <td className="py-1.5 px-3 bg-blue-950/30 text-gray-100 font-bold border-x border-blue-900/40 font-mono">
                    {row.strike} {row.is_atm && '★'}
                  </td>
                  <td className="py-1.5 px-2 font-mono text-blue-300">{row.pe_vega}</td>
                  <td className="py-1.5 px-2 font-mono text-red-400">{row.pe_theta}</td>
                  <td className="py-1.5 px-2 font-mono text-gray-400">{row.pe_gamma}</td>
                  <td className="py-1.5 px-2 font-mono">{row.pe_delta}</td>
                  <td className="py-1.5 px-2 text-terminal-red font-semibold">₹{row.pe_price}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
