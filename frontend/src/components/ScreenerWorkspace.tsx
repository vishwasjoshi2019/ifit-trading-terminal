import React, { useState, useEffect, useMemo } from 'react';
import { fetchScreener } from '../services/api';
import type { EquityScreenerRow } from '../types';

interface ScreenerWorkspaceProps {
  onSelectSymbol?: (symbol: string) => void;
}

export const ScreenerWorkspace: React.FC<ScreenerWorkspaceProps> = ({ onSelectSymbol }) => {
  const [data, setData] = useState<EquityScreenerRow[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [sectorFilter, setSectorFilter] = useState<string>('ALL');
  const [sortField, setSortField] = useState<keyof EquityScreenerRow>('Equity Score');
  const [sortAsc, setSortAsc] = useState<boolean>(false);
  const [preset, setPreset] = useState<string>('ALL');

  useEffect(() => {
    let isMounted = true;
    fetchScreener()
      .then((rows) => {
        if (isMounted) {
          setData(rows);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error('Failed to load screener data:', err);
        if (isMounted) setLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const sectors = useMemo(() => {
    const set = new Set<string>();
    data.forEach((r) => set.add(r.Sector));
    return ['ALL', ...Array.from(set)];
  }, [data]);

  const filteredData = useMemo(() => {
    return data
      .filter((r) => {
        if (sectorFilter !== 'ALL' && r.Sector !== sectorFilter) return false;
        if (search && !r.Symbol.toLowerCase().includes(search.toLowerCase())) return false;
        if (preset === 'MOMENTUM') return r['RSI 14'] >= 60 && r['EMA Trend'].includes('BULLISH');
        if (preset === 'VALUE') return r['P/E'] <= 22;
        if (preset === 'QUALITY') return r['ROE %'] >= 18 && r['Debt/Equity'] < 0.9;
        if (preset === 'GROWTH') return r['Revenue Growth %'] >= 12;
        return true;
      })
      .sort((a, b) => {
        const valA = a[sortField];
        const valB = b[sortField];
        if (typeof valA === 'number' && typeof valB === 'number') {
          return sortAsc ? valA - valB : valB - valA;
        }
        return sortAsc ? String(valA).localeCompare(String(valB)) : String(valB).localeCompare(String(valA));
      });
  }, [data, sectorFilter, search, preset, sortField, sortAsc]);

  const handleSort = (field: keyof EquityScreenerRow) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  // Summary Metrics
  const avgPe = data.length > 0 ? (data.reduce((acc, r) => acc + r['P/E'], 0) / data.length).toFixed(1) : '--';
  const avgRoe = data.length > 0 ? (data.reduce((acc, r) => acc + r['ROE %'], 0) / data.length).toFixed(1) : '--';
  const bullishCount = data.filter((r) => r['EMA Trend'].includes('BULLISH')).length;

  return (
    <div className="flex-1 flex flex-col bg-[#06080B] text-slate-200 overflow-y-auto font-sans p-3 gap-3">
      {/* Top Banner: Screener Metrics & Market Breadth */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-2.5">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Universe Breadth</span>
          <div className="text-lg font-mono font-bold text-emerald-400 mt-1">
            {bullishCount} / {data.length} Bullish
          </div>
          <span className="text-[9px] text-emerald-500 font-mono">Strong Technical Trend</span>
        </div>

        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-2.5">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Universe Avg P/E</span>
          <div className="text-lg font-mono font-bold text-slate-200 mt-1">{avgPe}x</div>
          <span className="text-[9px] text-slate-500 font-mono">Trailing Twelve Months</span>
        </div>

        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-2.5">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Average ROE</span>
          <div className="text-lg font-mono font-bold text-cyan-400 mt-1">{avgRoe}%</div>
          <span className="text-[9px] text-cyan-500 font-mono">Capital Efficiency</span>
        </div>

        <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-2.5">
          <span className="text-[10px] text-slate-400 font-mono uppercase tracking-wider block">Top Ranked Factor Score</span>
          <div className="text-lg font-mono font-bold text-emerald-400 mt-1">
            {data.length > 0 ? `${data[0].Symbol} (${data[0]['Equity Score'].toFixed(1)})` : '--'}
          </div>
          <span className="text-[9px] text-slate-500 font-mono">Multi-factor Composite Leader</span>
        </div>
      </div>

      {/* Control Bar: Filters, Presets, and Search */}
      <div className="flex flex-wrap items-center justify-between bg-[#0B0E14] border border-[#1E2638] rounded px-3 py-2 gap-3 text-xs">
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Search symbol (e.g. RELIANCE)…"
            aria-label="Search equities by symbol"
            autoComplete="off"
            spellCheck={false}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-[#141A26] border border-[#1E2638] rounded px-2.5 py-1 text-slate-100 placeholder-slate-400 text-xs w-48 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-cyan-500 font-mono"
          />

          <div className="flex items-center gap-1">
            <span className="text-slate-400 text-[11px]">Sector:</span>
            <select
              value={sectorFilter}
              aria-label="Filter equities by sector"
              onChange={(e) => setSectorFilter(e.target.value)}
              className="bg-[#141A26] border border-[#1E2638] rounded px-2 py-1 text-slate-200 text-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-cyan-500 font-mono"
            >
              {sectors.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Strategy Presets */}
        <div className="flex items-center gap-1.5" role="group" aria-label="Strategy screener presets">
          <span className="text-slate-400 text-[11px] mr-1">Presets:</span>
          {[
            { id: 'ALL', label: 'All Equities' },
            { id: 'MOMENTUM', label: 'Momentum (RSI>60)' },
            { id: 'VALUE', label: 'Value (P/E<22)' },
            { id: 'QUALITY', label: 'High Quality (ROE>18%)' },
            { id: 'GROWTH', label: 'Growth (>12%)' },
          ].map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setPreset(p.id)}
              className={`px-2 py-0.5 rounded text-[11px] font-mono transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-cyan-400 ${
                preset === p.id
                  ? 'bg-cyan-600 text-white font-bold'
                  : 'bg-[#141A26] text-slate-300 hover:bg-[#1E2638] border border-[#1E2638]'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Table: Multi-Factor Equity Screener */}
      <div className="bg-[#0B0E14] border border-[#1E2638] rounded p-3 flex-1 flex flex-col overflow-hidden">
        <div className="flex items-center justify-between border-b border-[#1E2638] pb-2 mb-2">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
            Institutional Factor Screener ({filteredData.length} matches)
          </h3>
          <span className="text-[10px] text-slate-400 font-mono">
            Click column header to sort | Click row to inspect in Cockpit
          </span>
        </div>

        <div className="overflow-x-auto flex-1">
          {loading ? (
            <div className="text-center py-12 text-slate-400 font-mono text-xs">Loading institutional screener data…</div>
          ) : (
            <table className="w-full text-[11px] font-mono text-left tabular-nums">
              <thead>
                <tr className="border-b border-[#1E2638] text-slate-400 text-[10px] uppercase select-none">
                  {(
                    [
                      ['Symbol', 'Symbol', 'text-left'],
                      ['Sector', 'Sector', 'text-left'],
                      ['Price', 'Price (₹)', 'text-right'],
                      ['P/E', 'P/E', 'text-right'],
                      ['ROE %', 'ROE %', 'text-right'],
                      ['ROCE %', 'ROCE %', 'text-right'],
                      ['Debt/Equity', 'D/E', 'text-right'],
                      ['Revenue Growth %', 'Rev Grw %', 'text-right'],
                      ['RSI 14', 'RSI 14', 'text-right'],
                      ['EMA Trend', 'EMA Trend', 'text-center'],
                      ['Equity Score', 'Composite Score', 'text-right'],
                    ] as const
                  ).map(([field, label, align]) => (
                    <th
                      key={field}
                      role="columnheader"
                      tabIndex={0}
                      aria-sort={sortField === field ? (sortAsc ? 'ascending' : 'descending') : 'none'}
                      onClick={() => handleSort(field as keyof StockFactor)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          handleSort(field as keyof StockFactor);
                        }
                      }}
                      className={`py-2 px-2 cursor-pointer hover:text-cyan-400 focus-visible:outline-none focus-visible:text-cyan-400 ${align}`}
                    >
                      {label} {sortField === field && (sortAsc ? '▲' : '▼')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredData.map((row) => (
                  <tr
                    key={row.Symbol}
                    role="row"
                    tabIndex={0}
                    aria-label={`Select ${row.Symbol} equity`}
                    onClick={() => onSelectSymbol && onSelectSymbol(row.Symbol)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        onSelectSymbol && onSelectSymbol(row.Symbol);
                      }
                    }}
                    className="border-b border-[#141A26] hover:bg-[#141A26] cursor-pointer transition-colors focus-visible:outline-none focus-visible:bg-[#141A26]"
                  >
                    <td className="py-1.5 px-2 font-bold text-cyan-400">{row.Symbol}</td>
                    <td className="py-1.5 px-2 text-slate-400">{row.Sector}</td>
                    <td className="py-1.5 px-2 text-right font-bold text-slate-100">₹{row.Price.toFixed(2)}</td>
                    <td className="py-1.5 px-2 text-right text-slate-300">{row['P/E'].toFixed(1)}</td>
                    <td className="py-1.5 px-2 text-right text-emerald-400">{row['ROE %'].toFixed(1)}%</td>
                    <td className="py-1.5 px-2 text-right text-emerald-400">{row['ROCE %'].toFixed(1)}%</td>
                    <td className="py-1.5 px-2 text-right text-slate-300">{row['Debt/Equity'].toFixed(2)}</td>
                    <td className="py-1.5 px-2 text-right text-cyan-400">+{row['Revenue Growth %'].toFixed(1)}%</td>
                    <td className="py-1.5 px-2 text-right font-bold">
                      <span
                        className={`px-1.5 py-0.2 rounded text-[10px] ${
                          row['RSI 14'] > 65
                            ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800'
                            : row['RSI 14'] < 40
                            ? 'bg-rose-950/60 text-rose-400 border border-rose-800'
                            : 'text-slate-300'
                        }`}
                      >
                        {row['RSI 14'].toFixed(1)}
                      </span>
                    </td>
                    <td className="py-1.5 px-2 text-center">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                          row['EMA Trend'].includes('STRONG')
                            ? 'bg-emerald-900/60 text-emerald-300 border border-emerald-700'
                            : row['EMA Trend'].includes('BULLISH')
                            ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-800'
                            : 'bg-slate-800 text-slate-400 border border-slate-700'
                        }`}
                      >
                        {row['EMA Trend']}
                      </span>
                    </td>
                    <td className="py-1.5 px-2 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-16 bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div
                            className="bg-cyan-400 h-full rounded-full"
                            style={{ width: `${Math.min(100, row['Equity Score'])}%` }}
                          ></div>
                        </div>
                        <span className="font-bold text-cyan-300 w-8">{row['Equity Score'].toFixed(1)}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
