import React, { useState, useEffect } from 'react';
import { fetchMonteCarlo } from '../services/api';
import type { MonteCarloResult } from '../types';

interface RiskQuantWorkspaceProps {
  currentSpot: number;
  symbol: string;
}

export const RiskQuantWorkspace: React.FC<RiskQuantWorkspaceProps> = ({ currentSpot, symbol }) => {
  const [spot, setSpot] = useState<number>(currentSpot || 24800);
  const [days, setDays] = useState<number>(30);
  const [paths, setPaths] = useState<number>(1000);
  const [loading, setLoading] = useState<boolean>(false);
  const [mcData, setMcData] = useState<MonteCarloResult | null>(null);

  useEffect(() => {
    if (currentSpot && currentSpot > 0 && Math.abs(currentSpot - spot) > 500) {
      setSpot(Math.round(currentSpot));
    }
  }, [currentSpot]);

  const runSimulation = async () => {
    setLoading(true);
    try {
      const data = await fetchMonteCarlo(spot, days, paths);
      setMcData(data);
    } catch (e) {
      console.error('Monte carlo simulation failed:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSimulation();
  }, [days, paths]);

  // Stress testing scenarios
  const stressScenarios = [
    { name: 'COVID Crash Replay', shock: -12.5, type: 'EXTREME', desc: 'Circuit down spike with VIX > 40' },
    { name: 'RBI Sudden +50bp Hike', shock: -3.8, type: 'POLICY', desc: 'Unscheduled rate tightening' },
    { name: 'Crude Surge (+$25/bbl)', shock: -4.2, type: 'COMMODITY', desc: 'Current account deficit pressure' },
    { name: 'Global Tech Selloff', shock: -5.5, type: 'GLOBAL', desc: 'Nasdaq -4% overnight contagion' },
    { name: 'FII Mega Inflow (+3.5%)', shock: +3.5, type: 'INFLOW', desc: 'Massive foreign institutional buy' },
  ];

  // SVG Chart Dimensions
  const chartWidth = 720;
  const chartHeight = 280;
  const padding = { top: 20, right: 30, bottom: 30, left: 60 };

  const innerW = chartWidth - padding.left - padding.right;
  const innerH = chartHeight - padding.top - padding.bottom;

  let minVal = spot * 0.85;
  let maxVal = spot * 1.15;
  if (mcData && mcData.p5.length > 0) {
    const allVals = [...mcData.p5, ...mcData.p95];
    minVal = Math.min(...allVals) * 0.98;
    maxVal = Math.max(...allVals) * 1.02;
  }

  const getX = (idx: number, total: number) => padding.left + (idx / Math.max(1, total - 1)) * innerW;
  const getY = (val: number) => padding.top + innerH - ((val - minVal) / Math.max(1, maxVal - minVal)) * innerH;

  const buildPath = (arr: number[]) => {
    if (!arr || arr.length === 0) return '';
    return arr.map((v, i) => `${i === 0 ? 'M' : 'L'} ${getX(i, arr.length)} ${getY(v)}`).join(' ');
  };

  const buildAreaPath = (topArr: number[], botArr: number[]) => {
    if (!topArr || !botArr || topArr.length === 0) return '';
    const top = topArr.map((v, i) => `${i === 0 ? 'M' : 'L'} ${getX(i, topArr.length)} ${getY(v)}`).join(' ');
    const bot = [...botArr].reverse().map((v, i) => `L ${getX(botArr.length - 1 - i, botArr.length)} ${getY(v)}`).join(' ');
    return `${top} ${bot} Z`;
  };

  return (
    <div className="flex-1 flex flex-col bg-[#06080B] text-slate-200 overflow-y-auto font-sans p-3 gap-3">
      {/* Top Bar: Risk Cockpit Controls */}
      <div className="flex flex-wrap items-center justify-between bg-[#0B0E14] border border-[#1E2638] rounded px-4 py-2.5 gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-100">Institutional Risk Engine</span>
          </div>
          <span className="text-[11px] text-slate-400 font-mono px-2 py-0.5 bg-[#141A26] border border-[#1E2638] rounded">
            {symbol} @ ₹{spot.toLocaleString('en-IN')}
          </span>
          <span className="text-[10px] text-amber-400 font-mono bg-amber-950/40 border border-amber-800/50 px-2 py-0.5 rounded">
            GBM / Jump-Diffusion Model
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <label className="text-slate-400">Spot:</label>
            <input
              type="number"
              value={spot}
              onChange={(e) => setSpot(Number(e.target.value))}
              className="w-24 bg-[#141A26] border border-[#1E2638] rounded px-2 py-1 text-slate-100 text-right focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="flex items-center gap-1.5">
            <label className="text-slate-400">Horizon:</label>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="bg-[#141A26] border border-[#1E2638] rounded px-2 py-1 text-slate-100 focus:outline-none focus:border-cyan-500"
            >
              <option value={7}>7 Days (1W)</option>
              <option value={14}>14 Days (2W)</option>
              <option value={30}>30 Days (1M)</option>
              <option value={60}>60 Days (2M)</option>
              <option value={90}>90 Days (1Q)</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <label className="text-slate-400">Paths:</label>
            <select
              value={paths}
              onChange={(e) => setPaths(Number(e.target.value))}
              className="bg-[#141A26] border border-[#1E2638] rounded px-2 py-1 text-slate-100 focus:outline-none focus:border-cyan-500"
            >
              <option value={500}>500 paths</option>
              <option value={1000}>1,000 paths</option>
              <option value={5000}>5,000 paths</option>
            </select>
          </div>

          <button
            onClick={runSimulation}
            disabled={loading}
            className="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-semibold rounded text-xs transition-colors flex items-center gap-1.5"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-3 w-3 text-white" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                Simulating...
              </>
            ) : (
              'Run Monte Carlo'
            )}
          </button>
        </div>
      </div>

      {/* KPI Cards: VaR, CVaR, Expected Shortfall */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Parametric VaR (95%)</span>
            <span className="text-[10px] text-red-400 bg-red-950/40 border border-red-800/40 px-1.5 py-0.2 rounded font-mono">1-Tail</span>
          </div>
          <div className="my-1.5">
            <div className="text-xl font-mono font-bold text-red-400">
              {mcData ? `-${mcData.var_95.toFixed(2)}%` : '--'}
            </div>
            <div className="text-[10px] font-mono text-slate-500">
              Max loss @ 95% confidence over {days}D
            </div>
          </div>
          <div className="text-[10px] text-slate-400 font-mono">
            Downside Limit: ₹{mcData ? (spot * (1 - mcData.var_95 / 100)).toFixed(0) : '--'}
          </div>
        </div>

        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Tail Risk VaR (99%)</span>
            <span className="text-[10px] text-amber-400 bg-amber-950/40 border border-amber-800/40 px-1.5 py-0.2 rounded font-mono">Extreme</span>
          </div>
          <div className="my-1.5">
            <div className="text-xl font-mono font-bold text-amber-400">
              {mcData ? `-${mcData.var_99.toFixed(2)}%` : '--'}
            </div>
            <div className="text-[10px] font-mono text-slate-500">
              Tail boundary (99th percentile)
            </div>
          </div>
          <div className="text-[10px] text-slate-400 font-mono">
            Downside Limit: ₹{mcData ? (spot * (1 - mcData.var_99 / 100)).toFixed(0) : '--'}
          </div>
        </div>

        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Expected Shortfall (CVaR)</span>
            <span className="text-[10px] text-rose-400 bg-rose-950/40 border border-rose-800/40 px-1.5 py-0.2 rounded font-mono">Avg Beyond VaR</span>
          </div>
          <div className="my-1.5">
            <div className="text-xl font-mono font-bold text-rose-400">
              {mcData ? `-${mcData.cvar_95.toFixed(2)}%` : '--'}
            </div>
            <div className="text-[10px] font-mono text-slate-500">
              Conditional expectation if tail breaches
            </div>
          </div>
          <div className="text-[10px] text-slate-400 font-mono">
            Avg Tail Loss: ₹{mcData ? (spot * (mcData.cvar_95 / 100)).toFixed(0) : '--'}
          </div>
        </div>

        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Mean Terminal Price</span>
            <span className="text-[10px] text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-1.5 py-0.2 rounded font-mono">Expected</span>
          </div>
          <div className="my-1.5">
            <div className="text-xl font-mono font-bold text-emerald-400">
              ₹{mcData ? mcData.mean_final_price.toLocaleString('en-IN') : '--'}
            </div>
            <div className="text-[10px] font-mono text-slate-500">
              {mcData ? `${(((mcData.mean_final_price - spot) / spot) * 100).toFixed(2)}% drift over horizon` : '--'}
            </div>
          </div>
          <div className="text-[10px] text-slate-400 font-mono">
            P50 Median: ₹{mcData && mcData.p50.length > 0 ? mcData.p50[mcData.p50.length - 1].toFixed(0) : '--'}
          </div>
        </div>
      </div>

      {/* Main Grid: Simulation Cone Visualization & Stress-Testing Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 flex-1 min-h-[360px]">
        {/* Left: Monte Carlo Trajectory Cone */}
        <div className="lg:col-span-8 bg-[#0B0E14] border border-[#1E2638] rounded p-3 flex flex-col">
          <div className="flex items-center justify-between border-b border-[#1E2638] pb-2 mb-2">
            <div>
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
                Monte Carlo Simulation Fan Chart ({paths.toLocaleString()} Paths)
              </h3>
              <p className="text-[10px] text-slate-400">
                Confidence intervals over {days} trading days with geometric Brownian motion
              </p>
            </div>
            <div className="flex items-center gap-3 text-[10px] font-mono">
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-1.5 bg-cyan-900/40 border border-cyan-700/60 inline-block"></span> 5% - 95% Band
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-1.5 bg-cyan-700/40 border border-cyan-500/80 inline-block"></span> 25% - 75% IQR
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-0.5 bg-emerald-400 inline-block"></span> P50 Median
              </span>
            </div>
          </div>

          <div className="flex-1 flex items-center justify-center relative overflow-hidden">
            {mcData ? (
              <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full h-full max-h-[300px]">
                {/* Horizontal Grid lines */}
                {[0.2, 0.4, 0.6, 0.8].map((ratio) => {
                  const val = minVal + ratio * (maxVal - minVal);
                  const y = getY(val);
                  return (
                    <g key={ratio}>
                      <line x1={padding.left} y1={y} x2={chartWidth - padding.right} y2={y} stroke="#1E2638" strokeDasharray="3 3" />
                      <text x={padding.left - 8} y={y + 3} fill="#64748B" fontSize="9" textAnchor="end" fontFamily="monospace">
                        ₹{Math.round(val)}
                      </text>
                    </g>
                  );
                })}

                {/* Days axis */}
                {mcData.days
                  .filter((_, i) => i % Math.ceil(mcData.days.length / 6) === 0 || i === mcData.days.length - 1)
                  .map((d, i, arr) => {
                    const x = getX(d, mcData.days.length);
                    return (
                      <g key={d}>
                        <line x1={x} y1={padding.top} x2={x} y2={chartHeight - padding.bottom} stroke="#141A26" />
                        <text x={x} y={chartHeight - padding.bottom + 14} fill="#64748B" fontSize="9" textAnchor="middle" fontFamily="monospace">
                          D+{d}
                        </text>
                      </g>
                    );
                  })}

                {/* 5% to 95% Confidence Band Area */}
                <path d={buildAreaPath(mcData.p95, mcData.p5)} fill="rgba(6, 182, 212, 0.08)" stroke="rgba(6, 182, 212, 0.3)" strokeWidth="1" />

                {/* 25% to 75% IQR Area */}
                <path d={buildAreaPath(mcData.p75, mcData.p25)} fill="rgba(6, 182, 212, 0.16)" stroke="rgba(6, 182, 212, 0.5)" strokeWidth="1" />

                {/* Individual Percentile Lines */}
                <path d={buildPath(mcData.p95)} fill="none" stroke="#06B6D4" strokeWidth="1" strokeDasharray="2 2" />
                <path d={buildPath(mcData.p5)} fill="none" stroke="#EF4444" strokeWidth="1" strokeDasharray="2 2" />
                <path d={buildPath(mcData.p50)} fill="none" stroke="#10B981" strokeWidth="2" />

                {/* Current Spot Baseline */}
                <line
                  x1={padding.left}
                  y1={getY(spot)}
                  x2={chartWidth - padding.right}
                  y2={getY(spot)}
                  stroke="#F59E0B"
                  strokeWidth="1"
                  strokeDasharray="4 4"
                />
                <text x={chartWidth - padding.right + 4} y={getY(spot) + 3} fill="#F59E0B" fontSize="9" fontFamily="monospace">
                  Spot
                </text>
              </svg>
            ) : (
              <div className="text-slate-500 font-mono text-xs">Computing Monte Carlo simulation...</div>
            )}
          </div>

          <div className="grid grid-cols-5 gap-2 pt-2 border-t border-[#1E2638] text-[10px] font-mono text-center">
            <div className="bg-[#141A26] p-1.5 rounded">
              <span className="text-rose-400 block font-bold">5th %ile (Bear)</span>
              <span className="text-slate-300">₹{mcData && mcData.p5.length > 0 ? mcData.p5[mcData.p5.length - 1].toFixed(0) : '--'}</span>
            </div>
            <div className="bg-[#141A26] p-1.5 rounded">
              <span className="text-cyan-400 block font-bold">25th %ile</span>
              <span className="text-slate-300">₹{mcData && mcData.p25.length > 0 ? mcData.p25[mcData.p25.length - 1].toFixed(0) : '--'}</span>
            </div>
            <div className="bg-[#141A26] p-1.5 rounded border border-emerald-500/30">
              <span className="text-emerald-400 block font-bold">Median (P50)</span>
              <span className="text-emerald-300">₹{mcData && mcData.p50.length > 0 ? mcData.p50[mcData.p50.length - 1].toFixed(0) : '--'}</span>
            </div>
            <div className="bg-[#141A26] p-1.5 rounded">
              <span className="text-cyan-400 block font-bold">75th %ile</span>
              <span className="text-slate-300">₹{mcData && mcData.p75.length > 0 ? mcData.p75[mcData.p75.length - 1].toFixed(0) : '--'}</span>
            </div>
            <div className="bg-[#141A26] p-1.5 rounded">
              <span className="text-emerald-400 block font-bold">95th %ile (Bull)</span>
              <span className="text-slate-300">₹{mcData && mcData.p95.length > 0 ? mcData.p95[mcData.p95.length - 1].toFixed(0) : '--'}</span>
            </div>
          </div>
        </div>

        {/* Right: Macro Stress Testing Matrix */}
        <div className="lg:col-span-4 bg-[#0B0E14] border border-[#1E2638] rounded p-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#1E2638] pb-2 mb-2">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wide">Macro Stress-Test Matrix</h3>
              <span className="text-[10px] text-slate-400 font-mono">Capital Impact</span>
            </div>
            <p className="text-[10px] text-slate-400 mb-3">
              Simulated portfolio shock testing under institutional crisis scenarios:
            </p>

            <div className="space-y-2">
              {stressScenarios.map((sc, i) => {
                const shockedPrice = spot * (1 + sc.shock / 100);
                const isPositive = sc.shock >= 0;
                return (
                  <div key={i} className="p-2 bg-[#141A26] border border-[#1E2638] rounded hover:border-slate-600 transition-colors">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-bold text-slate-200">{sc.name}</span>
                      <span
                        className={`text-xs font-mono font-bold px-1.5 py-0.5 rounded ${
                          isPositive ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800' : 'bg-red-950/60 text-red-400 border border-red-800'
                        }`}
                      >
                        {isPositive ? `+${sc.shock}%` : `${sc.shock}%`}
                      </span>
                    </div>
                    <div className="flex items-center justify-between mt-1 text-[10px] font-mono text-slate-400">
                      <span>{sc.desc}</span>
                      <span className="text-slate-200 font-bold">₹{shockedPrice.toFixed(0)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-3 p-2.5 bg-[#141A26]/80 border border-[#1E2638] rounded">
            <div className="flex items-center justify-between text-[11px] font-mono mb-1">
              <span className="text-slate-400">Portfolio Margin Buffer:</span>
              <span className="text-emerald-400 font-bold">342% (Robust)</span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-emerald-500 h-full w-4/5"></div>
            </div>
            <span className="text-[9px] text-slate-500 font-mono block mt-1">
              Zero margin call risk up to -18.4% instantaneous market gap.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
