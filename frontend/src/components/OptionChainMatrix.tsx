import React, { useEffect, useState } from 'react';
import type { OptionChainSnapshot } from '../types';
import { fetchOptionChain } from '../services/api';
import { Target, Activity, BarChart2 } from 'lucide-react';

interface OptionChainMatrixProps {
  symbol: string;
}

export const OptionChainMatrix: React.FC<OptionChainMatrixProps> = ({ symbol }) => {
  const [chain, setChain] = useState<OptionChainSnapshot | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let active = true;
    setLoading(true);

    const loadChain = () => {
      fetchOptionChain(symbol)
        .then((data) => {
          if (active) {
            setChain(data);
            setLoading(false);
          }
        })
        .catch(() => {
          if (active) setLoading(false);
        });
    };

    loadChain();
    const interval = setInterval(loadChain, 3000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [symbol]);

  if (loading && !chain) {
    return (
      <div className="h-full bg-terminal-panel flex items-center justify-center text-xs font-mono text-gray-500">
        Loading option chain matrix...
      </div>
    );
  }

  if (!chain || !chain.strikes || chain.strikes.length === 0) {
    return (
      <div className="h-full bg-terminal-panel flex items-center justify-center text-xs font-mono text-gray-500">
        No active option chain data available for {symbol}.
      </div>
    );
  }

  const spot = chain.underlying_price;

  return (
    <div className="flex flex-col h-full bg-terminal-panel text-xs font-mono select-none">
      {/* Header with PCR and Max Pain */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-terminal-header border-b border-terminal-border">
        <div className="flex items-center gap-2">
          <span className="font-bold text-gray-200">OPTION CHAIN MATRIX</span>
          <span className="text-[10px] text-gray-400">EXPIRY: {chain.expiry}</span>
        </div>

        <div className="flex items-center gap-4 text-[11px]">
          <div className="flex items-center gap-1">
            <span className="text-gray-400">PCR (OI):</span>
            <span className={`font-bold ${chain.pcr_oi >= 1.0 ? 'text-terminal-green' : 'text-terminal-red'}`}>
              {chain.pcr_oi.toFixed(2)}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Target className="w-3 h-3 text-amber-400" />
            <span className="text-gray-400">MAX PAIN:</span>
            <span className="text-amber-400 font-bold">₹{chain.max_pain.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Table Headers */}
      <div className="grid grid-cols-5 px-3 py-1 text-[10px] text-gray-500 font-bold border-b border-terminal-border/40 bg-terminal-bg text-center">
        <span className="text-left text-blue-400">CALL OI</span>
        <span className="text-blue-400">CALL LTP</span>
        <span className="text-amber-400 font-black">STRIKE</span>
        <span className="text-red-400">PUT LTP</span>
        <span className="text-right text-red-400">PUT OI</span>
      </div>

      {/* Strikes List */}
      <div className="flex-1 overflow-y-auto px-2 divide-y divide-terminal-border/20">
        {chain.strikes.map((s) => {
          const isAtm = Math.abs(s.strike - spot) <= 50;

          return (
            <div
              key={s.strike}
              className={`grid grid-cols-5 py-1 text-[11px] items-center text-center transition-colors ${
                isAtm ? 'bg-amber-500/10 border-y border-amber-500/30' : 'hover:bg-terminal-hover'
              }`}
            >
              {/* Call OI */}
              <span className="text-left text-gray-400 text-[10px]">{s.ce_oi.toLocaleString()}</span>
              {/* Call LTP */}
              <span className="text-terminal-green font-semibold">₹{s.ce_ltp.toFixed(1)}</span>
              {/* Strike */}
              <span className={`font-mono font-bold ${isAtm ? 'text-amber-300' : 'text-gray-200'}`}>
                {s.strike.toLocaleString()}
              </span>
              {/* Put LTP */}
              <span className="text-terminal-red font-semibold">₹{s.pe_ltp.toFixed(1)}</span>
              {/* Put OI */}
              <span className="text-right text-gray-400 text-[10px]">{s.pe_oi.toLocaleString()}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
