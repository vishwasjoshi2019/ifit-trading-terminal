import React, { useState, useEffect } from 'react';
import { fetchCrossAsset } from '../services/api';
import type { CrossAssetSnapshot } from '../types';

export const CrossAssetWorkspace: React.FC = () => {
  const [data, setData] = useState<CrossAssetSnapshot | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [hoveredPair, setHoveredPair] = useState<{ assetA: string; assetB: string; value: number } | null>(null);

  useEffect(() => {
    let isMounted = true;
    fetchCrossAsset()
      .then((snapshot) => {
        if (isMounted) {
          setData(snapshot);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error('Failed to load cross asset data:', err);
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const getHeatmapColor = (val: number) => {
    if (val === 1) return 'bg-cyan-900/60 text-cyan-200 font-bold';
    if (val > 0.5) return 'bg-emerald-900/70 text-emerald-200 font-semibold';
    if (val > 0.15) return 'bg-emerald-950/50 text-emerald-300';
    if (val >= -0.15 && val <= 0.15) return 'bg-[#141A26] text-slate-400';
    if (val >= -0.5) return 'bg-rose-950/50 text-rose-300';
    return 'bg-red-900/70 text-red-200 font-semibold';
  };

  const getPairInsight = (a: string, b: string) => {
    if (a === b) return `${a} self-correlation is perfectly unitary (1.00).`;
    const pair = [a, b].sort().join(' & ');
    if (pair.includes('CRUDE') && pair.includes('USDINR')) {
      return 'Crude Oil & USDINR (+0.52): High positive correlation. Higher oil imports directly expand India trade deficit, depreciating INR.';
    }
    if (pair.includes('CRUDE') && (pair.includes('NIFTY') || pair.includes('BANKNIFTY'))) {
      return 'Crude Oil & NIFTY (-0.32): Inverse transmission. Energy input cost inflation squeezes corporate EBITDA margins.';
    }
    if (pair.includes('GOLD') && pair.includes('US 10Y')) {
      return 'Gold & US 10Y (-0.40): Opportunity cost dynamics. Rising real Treasury yields dampen non-yielding precious metals.';
    }
    if (pair.includes('USDINR') && pair.includes('NIFTY')) {
      return 'USDINR & NIFTY (-0.42): FII repatriation cycle. Currency weakness coincides with foreign portfolio capital outflows.';
    }
    return `Cross-asset interaction between ${a} and ${b} reflects current macro liquidity regime.`;
  };

  const assets = data && data.correlation ? Object.keys(data.correlation) : [];

  return (
    <div className="flex-1 flex flex-col bg-[#06080B] text-slate-200 overflow-y-auto font-sans p-3 gap-3">
      {/* Top Banner: Macro Regime & State */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2.5">
        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-2.5">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Global Macro Regime</span>
          <div className="text-base font-mono font-bold text-emerald-400 mt-1">
            {data ? data.regime : 'EXPANSIONARY'}
          </div>
          <span className="text-[9px] text-emerald-500 font-mono">Equity & Credit Outperformance</span>
        </div>

        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-2.5">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Cross-Asset Sentiment</span>
          <div className="text-base font-mono font-bold text-cyan-400 mt-1">
            {data ? `${data.cross_asset_score.toFixed(1)} / 100` : '74.2'}
          </div>
          <span className="text-[9px] text-cyan-500 font-mono">Risk-On Constructive</span>
        </div>

        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-2.5">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Asset Leadership</span>
          <div className="text-sm font-mono font-bold text-slate-200 mt-1 truncate">
            {data ? data.leadership : 'EQUITIES & GOLD'}
          </div>
          <span className="text-[9px] text-slate-500 font-mono">Strongest Relative Strength</span>
        </div>

        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-2.5">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Lagging Sectors</span>
          <div className="text-sm font-mono font-bold text-rose-400 mt-1 truncate">
            {data ? data.lagging : 'RATES & FX'}
          </div>
          <span className="text-[9px] text-slate-500 font-mono">Yield Pressure / FX Consolidation</span>
        </div>

        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-2.5">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">RBI FX Buffer</span>
          <div className="text-base font-mono font-bold text-emerald-400 mt-1">$704 Billion</div>
          <span className="text-[9px] text-emerald-500 font-mono">All-time High Currency Defense</span>
        </div>
      </div>

      {/* Main Grid: Correlation Heatmap Matrix & Asset Class Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 flex-1 min-h-[380px]">
        {/* Left: Correlation Heatmap Matrix */}
        <div className="lg:col-span-7 bg-[#0B0E14] border border-[#1E2638] rounded p-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#1E2638] pb-2 mb-2">
              <div>
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
                  Cross-Asset Correlation Matrix (90-Day Rolling)
                </h3>
                <p className="text-[10px] text-slate-400">
                  Spearman rank correlations across Equities, Commodities, Rates, and Currencies
                </p>
              </div>
              <div className="flex items-center gap-2 text-[9px] font-mono">
                <span className="px-1.5 py-0.5 bg-emerald-900/70 text-emerald-200 rounded">+1.0 Positive</span>
                <span className="px-1.5 py-0.5 bg-[#141A26] text-slate-400 rounded">0.0 Neutral</span>
                <span className="px-1.5 py-0.5 bg-red-900/70 text-red-200 rounded">-1.0 Negative</span>
              </div>
            </div>

            {loading || !data ? (
              <div className="py-16 text-center text-slate-500 font-mono text-xs">Loading correlation matrix...</div>
            ) : (
              <div className="overflow-x-auto mt-2">
                <table className="w-full text-[11px] font-mono text-center border-collapse">
                  <thead>
                    <tr>
                      <th className="py-2 px-1 text-left text-slate-400 text-[10px]"></th>
                      {assets.map((a) => (
                        <th key={a} className="py-2 px-1 text-slate-300 font-bold text-[10px] max-w-[70px] truncate">
                          {a}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {assets.map((rowAsset) => (
                      <tr key={rowAsset}>
                        <td className="py-1.5 px-2 text-left font-bold text-slate-300 text-[10px] whitespace-nowrap">
                          {rowAsset}
                        </td>
                        {assets.map((colAsset) => {
                          const val = data.correlation[rowAsset]?.[colAsset] ?? 0;
                          return (
                            <td
                              key={colAsset}
                              onMouseEnter={() => setHoveredPair({ assetA: rowAsset, assetB: colAsset, value: val })}
                              className={`py-1.5 px-1 border border-[#0B0E14] cursor-pointer transition-all hover:scale-105 ${getHeatmapColor(
                                val
                              )}`}
                            >
                              {val.toFixed(2)}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Interactive Pair Transmission Readout */}
          <div className="mt-3 p-2.5 bg-[#141A26] border border-[#1E2638] rounded">
            <span className="text-[10px] text-cyan-400 font-mono uppercase tracking-wider block font-bold mb-0.5">
              Macro Transmission Insight:
            </span>
            <p className="text-[11px] text-slate-300 font-sans leading-relaxed">
              {hoveredPair
                ? getPairInsight(hoveredPair.assetA, hoveredPair.assetB)
                : 'Hover over any cell in the correlation matrix above to inspect the macro transmission channel and economic linkage.'}
            </p>
          </div>
        </div>

        {/* Right: Asset Universe Table */}
        <div className="lg:col-span-5 bg-[#0B0E14] border border-[#1E2638] rounded p-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#1E2638] pb-2 mb-2">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wide">Cross-Asset Universe Monitor</h3>
              <span className="text-[10px] text-slate-400 font-mono">Live Benchmarks</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-[11px] font-mono text-left">
                <thead>
                  <tr className="border-b border-[#1E2638] text-slate-400 text-[10px] uppercase">
                    <th className="py-1.5 px-2">Asset</th>
                    <th className="py-1.5 px-2">Class</th>
                    <th className="py-1.5 px-2 text-right">Price</th>
                    <th className="py-1.5 px-2 text-right">Return %</th>
                    <th className="py-1.5 px-2 text-right">Score</th>
                  </tr>
                </thead>
                <tbody>
                  {data &&
                    data.asset_table.map((row) => (
                      <tr key={row.Symbol} className="border-b border-[#141A26] hover:bg-[#141A26] transition-colors">
                        <td className="py-1.5 px-2 font-bold text-slate-200">{row.Symbol}</td>
                        <td className="py-1.5 px-2 text-slate-400 text-[10px]">{row['Asset Class']}</td>
                        <td className="py-1.5 px-2 text-right text-slate-100 font-mono">
                          {row['Asset Class'] === 'Bonds'
                            ? `${row.Price.toFixed(2)}%`
                            : row.Price > 1000
                            ? row.Price.toLocaleString('en-IN')
                            : row.Price.toFixed(2)}
                        </td>
                        <td
                          className={`py-1.5 px-2 text-right font-bold ${
                            row['Return %'] >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {row['Return %'] >= 0 ? `+${row['Return %'].toFixed(2)}%` : `${row['Return %'].toFixed(2)}%`}
                        </td>
                        <td className="py-1.5 px-2 text-right">
                          <span
                            className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                              row.Score >= 80
                                ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800'
                                : row.Score >= 65
                                ? 'bg-cyan-950/60 text-cyan-300 border border-cyan-800'
                                : 'bg-slate-800 text-slate-400'
                            }`}
                          >
                            {row.Score.toFixed(0)}
                          </span>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="p-2.5 bg-[#141A26]/80 border border-[#1E2638] rounded mt-3">
            <span className="text-[11px] font-bold text-slate-300 block mb-1">Macro Strategic Takeaway</span>
            <p className="text-[10px] text-slate-400 leading-relaxed">
              Equities and Bullion continue simultaneous accumulation. USDINR remains tightly defended in the 83.90–84.05
              band by the RBI, isolating Indian financial assets from global currency swings.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
