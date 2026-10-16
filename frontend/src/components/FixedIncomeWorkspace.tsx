import React, { useState, useEffect } from 'react';
import { fetchYieldCurve } from '../services/api';
import type { YieldCurvePoint } from '../types';

export const FixedIncomeWorkspace: React.FC = () => {
  const [curve, setCurve] = useState<YieldCurvePoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedTenor, setSelectedTenor] = useState<string>('10Y');

  useEffect(() => {
    let isMounted = true;
    fetchYieldCurve()
      .then((data) => {
        if (isMounted) {
          setCurve(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error('Failed to load yield curve:', err);
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  // Benchmarks
  const point3M = curve.find((c) => c.Tenor === '3M');
  const point2Y = curve.find((c) => c.Tenor === '2Y');
  const point10Y = curve.find((c) => c.Tenor === '10Y');
  const point30Y = curve.find((c) => c.Tenor === '30Y');

  const spread10_2 = point10Y && point2Y ? +((point10Y['YTM %'] - point2Y['YTM %']) * 100).toFixed(1) : 31;
  const spread10_3M = point10Y && point3M ? +((point10Y['YTM %'] - point3M['YTM %']) * 100).toFixed(1) : 50;
  const spread30_10 = point30Y && point10Y ? +((point30Y['YTM %'] - point10Y['YTM %']) * 100).toFixed(1) : 19;

  // SVG Chart Setup
  const chartW = 760;
  const chartH = 260;
  const pad = { top: 25, right: 35, bottom: 35, left: 55 };
  const innerW = chartW - pad.left - pad.right;
  const innerH = chartH - pad.top - pad.bottom;

  const minY = 6.4;
  const maxY = 7.6;

  const getY = (ytm: number) => pad.top + innerH - ((ytm - minY) / (maxY - minY)) * innerH;
  const getX = (idx: number, total: number) => pad.left + (idx / Math.max(1, total - 1)) * innerW;

  const pathStr = curve.length > 0 ? curve.map((pt, i) => `${i === 0 ? 'M' : 'L'} ${getX(i, curve.length)} ${getY(pt['YTM %'])}`).join(' ') : '';
  const areaStr =
    curve.length > 0
      ? `${pathStr} L ${getX(curve.length - 1, curve.length)} ${chartH - pad.bottom} L ${pad.left} ${chartH - pad.bottom} Z`
      : '';

  return (
    <div className="flex-1 flex flex-col bg-[#06080B] text-slate-200 overflow-y-auto font-sans p-3 gap-3">
      {/* Top Banner: RBI Policy Rates & Yield Curve Status */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-2.5">
        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-2.5">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Policy Repo Rate</span>
          <div className="text-lg font-mono font-bold text-cyan-400 mt-1">6.50%</div>
          <span className="text-[9px] text-slate-500 font-mono">RBI MPC Neutral Stance</span>
        </div>

        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-2.5">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">SDF Rate</span>
          <div className="text-lg font-mono font-bold text-slate-200 mt-1">6.25%</div>
          <span className="text-[9px] text-slate-500 font-mono">Floor of LAF Corridor</span>
        </div>

        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-2.5">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">MSF / Bank Rate</span>
          <div className="text-lg font-mono font-bold text-slate-200 mt-1">6.75%</div>
          <span className="text-[9px] text-slate-500 font-mono">Ceiling of LAF Corridor</span>
        </div>

        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-2.5">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">10Y Benchmark (7.18 GS 2033)</span>
          <div className="text-lg font-mono font-bold text-emerald-400 mt-1">
            {point10Y ? `${point10Y['YTM %'].toFixed(2)}%` : '7.22%'}
          </div>
          <span className="text-[9px] text-emerald-500 font-mono">+0.4 bp Daily Shift</span>
        </div>

        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-2.5">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">10Y - 2Y Term Spread</span>
          <div className="text-lg font-mono font-bold text-cyan-400 mt-1">+{spread10_2} bp</div>
          <span className="text-[9px] text-slate-500 font-mono">Healthy Normal Slope</span>
        </div>

        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-2.5">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">System Liquidity</span>
          <div className="text-lg font-mono font-bold text-emerald-400 mt-1">+₹1.15 T</div>
          <span className="text-[9px] text-emerald-500 font-mono">RBI Net Absorber (Surplus)</span>
        </div>
      </div>

      {/* Main Split: Yield Curve Chart & Spread Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 flex-1 min-h-[360px]">
        {/* Left: SVG Sovereign Yield Curve Chart */}
        <div className="lg:col-span-8 bg-[#0B0E14] border border-[#1E2638] rounded p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-[#1E2638] pb-2 mb-2">
            <div>
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wide flex items-center gap-2">
                India Sovereign G-Sec Yield Curve (NDS-OM Fitted)
                <span className="text-[10px] text-emerald-400 font-normal px-1.5 py-0.2 bg-emerald-950/40 border border-emerald-800 rounded">
                  UPWARD SLOPING
                </span>
              </h3>
              <p className="text-[10px] text-slate-400">Nelson-Siegel-Svensson zero-coupon yield curve estimation</p>
            </div>
            <div className="flex items-center gap-3 text-[10px] font-mono">
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-0.5 bg-cyan-400 inline-block"></span> Sovereign G-Sec
              </span>
              <span className="flex items-center gap-1 text-slate-400">
                <span className="w-2.5 h-0.5 bg-amber-400 inline-block"></span> Policy Rate (6.50%)
              </span>
            </div>
          </div>

          <div className="flex-1 flex items-center justify-center relative overflow-hidden">
            {loading ? (
              <div className="text-xs font-mono text-slate-500">Loading sovereign debt data...</div>
            ) : (
              <svg viewBox={`0 0 ${chartW} ${chartH}`} className="w-full h-full max-h-[280px]">
                {/* Horizontal Yield Grid */}
                {[6.6, 6.8, 7.0, 7.2, 7.4, 7.6].map((rate) => {
                  const y = getY(rate);
                  return (
                    <g key={rate}>
                      <line x1={pad.left} y1={y} x2={chartW - pad.right} y2={y} stroke="#1E2638" strokeDasharray="3 3" />
                      <text x={pad.left - 8} y={y + 3} fill="#64748B" fontSize="9" textAnchor="end" fontFamily="monospace">
                        {rate.toFixed(1)}%
                      </text>
                    </g>
                  );
                })}

                {/* Repo Rate Reference Line */}
                <line
                  x1={pad.left}
                  y1={getY(6.50)}
                  x2={chartW - pad.right}
                  y2={getY(6.50)}
                  stroke="#F59E0B"
                  strokeWidth="1.2"
                  strokeDasharray="4 4"
                />
                <text x={chartW - pad.right + 4} y={getY(6.50) + 3} fill="#F59E0B" fontSize="9" fontFamily="monospace">
                  Repo 6.50%
                </text>

                {/* Curve Area & Line */}
                <path d={areaStr} fill="rgba(6, 182, 212, 0.08)" />
                <path d={pathStr} fill="none" stroke="#06B6D4" strokeWidth="2.5" />

                {/* Interactive Points on Curve */}
                {curve.map((pt, i) => {
                  const cx = getX(i, curve.length);
                  const cy = getY(pt['YTM %']);
                  const isSelected = selectedTenor === pt.Tenor;
                  return (
                    <g key={pt.Tenor} className="cursor-pointer" onClick={() => setSelectedTenor(pt.Tenor)}>
                      <circle
                        cx={cx}
                        cy={cy}
                        r={isSelected ? 6 : 4}
                        fill={isSelected ? '#38BDF8' : '#0B0E14'}
                        stroke="#06B6D4"
                        strokeWidth="2"
                      />
                      <text
                        x={cx}
                        y={chartH - pad.bottom + 14}
                        fill={isSelected ? '#38BDF8' : '#64748B'}
                        fontWeight={isSelected ? 'bold' : 'normal'}
                        fontSize="9"
                        textAnchor="middle"
                        fontFamily="monospace"
                      >
                        {pt.Tenor}
                      </text>
                      {isSelected && (
                        <g>
                          <rect x={cx - 24} y={cy - 24} width={48} height={16} rx="2" fill="#1E293B" stroke="#06B6D4" strokeWidth="0.5" />
                          <text x={cx} y={cy - 13} fill="#FFFFFF" fontSize="9" fontWeight="bold" textAnchor="middle" fontFamily="monospace">
                            {pt['YTM %'].toFixed(2)}%
                          </text>
                        </g>
                      )}
                    </g>
                  );
                })}
              </svg>
            )}
          </div>

          {/* Tenor Quick Strip */}
          <div className="flex items-center justify-between pt-2 border-t border-[#1E2638] text-[10px] font-mono">
            <span className="text-slate-400">Selected Tenor: <strong className="text-cyan-400">{selectedTenor}</strong></span>
            <div className="flex items-center gap-4">
              <span>Duration: <strong className="text-slate-200">{curve.find(c => c.Tenor === selectedTenor)?.Duration.toFixed(2) || '--'} yrs</strong></span>
              <span>Slope from 3M: <strong className="text-emerald-400">+{curve.find(c => c.Tenor === selectedTenor)?.['Slope from 3M bp'] || 0} bp</strong></span>
              <span>Curvature: <strong className="text-slate-200">{curve.find(c => c.Tenor === selectedTenor)?.['Curve Curvature bp'] || 0} bp</strong></span>
            </div>
          </div>
        </div>

        {/* Right: Credit Spread Matrix & Key Spreads */}
        <div className="lg:col-span-4 bg-[#0B0E14] border border-[#1E2638] rounded p-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#1E2638] pb-2 mb-2">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wide">Credit & Term Spreads</h3>
              <span className="text-[10px] text-slate-400 font-mono">NDS-OM / CCIL</span>
            </div>

            <div className="space-y-2 mb-3">
              <div className="p-2 bg-[#141A26] border border-[#1E2638] rounded">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-300 font-medium">10Y G-Sec vs 3M T-Bill</span>
                  <span className="font-mono font-bold text-cyan-400">+{spread10_3M} bp</span>
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">Steepness premium reflecting duration risk</div>
              </div>

              <div className="p-2 bg-[#141A26] border border-[#1E2638] rounded">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-300 font-medium">30Y G-Sec vs 10Y G-Sec</span>
                  <span className="font-mono font-bold text-cyan-400">+{spread30_10} bp</span>
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">Ultra-long institutional appetite (EPFO / LIC)</div>
              </div>

              <div className="p-2 bg-[#141A26] border border-[#1E2638] rounded">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-300 font-medium">SDL (State Dev Loans) Spread</span>
                  <span className="font-mono font-bold text-amber-400">+38 bp</span>
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">Average spread over central government benchmark</div>
              </div>

              <div className="p-2 bg-[#141A26] border border-[#1E2638] rounded">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-300 font-medium">AAA PSU Corporate Bond (10Y)</span>
                  <span className="font-mono font-bold text-emerald-400">7.62% (+40 bp)</span>
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">REC, PFC, NABARD, PowerGrid Tier-1 yields</div>
              </div>
            </div>
          </div>

          <div className="p-2.5 bg-[#141A26]/80 border border-[#1E2638] rounded">
            <span className="text-[11px] font-bold text-slate-300 block mb-1">Fixed Income Macro Outlook</span>
            <p className="text-[10px] text-slate-400 leading-relaxed">
              Curve exhibits normal upward slope. Heavy foreign institutional inflows via JP Morgan GBI-EM Index inclusion
              anchor long-end yields below 7.25%. Front-end remains tied to RBI SDF liquidity operations.
            </p>
          </div>
        </div>
      </div>

      {/* Bottom Table: Full Sovereign Curve Details */}
      <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-3">
        <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wide mb-2">
          Government of India Benchmark Securities Ladder
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-[11px] font-mono text-left">
            <thead>
              <tr className="border-b border-[#1E2638] text-slate-400 text-[10px] uppercase">
                <th className="py-1 px-2">Tenor</th>
                <th className="py-1 px-2 text-right">Maturity (Yrs)</th>
                <th className="py-1 px-2 text-right">YTM (%)</th>
                <th className="py-1 px-2 text-right">Day Chg (bp)</th>
                <th className="py-1 px-2 text-right">Modified Duration</th>
                <th className="py-1 px-2 text-right">Slope vs 3M (bp)</th>
                <th className="py-1 px-2 text-right">Curvature (bp)</th>
                <th className="py-1 px-2 text-right">Curve Score</th>
              </tr>
            </thead>
            <tbody>
              {curve.map((row) => (
                <tr
                  key={row.Tenor}
                  onClick={() => setSelectedTenor(row.Tenor)}
                  className={`border-b border-[#141A26] hover:bg-[#141A26] cursor-pointer transition-colors ${
                    selectedTenor === row.Tenor ? 'bg-[#141A26] font-semibold text-cyan-400' : 'text-slate-300'
                  }`}
                >
                  <td className="py-1 px-2 font-bold">{row.Tenor}</td>
                  <td className="py-1 px-2 text-right">{row['Maturity Years'].toFixed(2)}</td>
                  <td className="py-1 px-2 text-right font-bold text-slate-100">{row['YTM %'].toFixed(2)}%</td>
                  <td className="py-1 px-2 text-right text-emerald-400">+{row['Yield Change bp'].toFixed(1)}</td>
                  <td className="py-1 px-2 text-right">{row.Duration.toFixed(2)}</td>
                  <td className="py-1 px-2 text-right text-cyan-400">+{row['Slope from 3M bp'].toFixed(0)}</td>
                  <td className="py-1 px-2 text-right">{row['Curve Curvature bp'].toFixed(0)}</td>
                  <td className="py-1 px-2 text-right">
                    <span className="px-1.5 py-0.2 bg-cyan-950/60 border border-cyan-800 text-cyan-300 rounded text-[9px]">
                      {row['Curve Score'].toFixed(0)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
