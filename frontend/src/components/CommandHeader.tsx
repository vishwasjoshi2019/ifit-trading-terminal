import React, { useEffect } from 'react';
import type { NormalizedTick, WorkspaceTab } from '../types';
import { Settings, ExternalLink, Zap, Terminal, Activity, TrendingUp, ShieldAlert, DollarSign, Layers } from 'lucide-react';

interface CommandHeaderProps {
  activeSymbol: string;
  onSelectSymbol: (symbol: string) => void;
  timeframe: string;
  onSelectTimeframe: (tf: string) => void;
  ticks: Record<string, NormalizedTick>;
  status: 'CONNECTING' | 'CONNECTED' | 'DISCONNECTED';
  latencyMs: number;
  activeProvider: string;
  onOpenSettings: () => void;
  activeWorkspace: WorkspaceTab;
  onSelectWorkspace: (tab: WorkspaceTab) => void;
}

const TICKER_SYMBOLS = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'RELIANCE', 'HDFCBANK', 'TCS'];
const TIMEFRAMES = ['1m', '5m', '15m', '1h', '1D'];

const WORKSPACE_TABS: { id: WorkspaceTab; label: string; shortcut: string; icon: React.ReactNode }[] = [
  { id: 'COCKPIT', label: 'Cockpit', shortcut: 'F1', icon: <Terminal className="w-3.5 h-3.5" /> },
  { id: 'OPTIONS', label: 'Options Lab', shortcut: 'F2', icon: <Activity className="w-3.5 h-3.5" /> },
  { id: 'RISK', label: 'Risk Quant', shortcut: 'F3', icon: <ShieldAlert className="w-3.5 h-3.5" /> },
  { id: 'BONDS', label: 'Sovereign G-Sec', shortcut: 'F4', icon: <DollarSign className="w-3.5 h-3.5" /> },
  { id: 'SCREENER', label: 'Factor Screener', shortcut: 'F5', icon: <TrendingUp className="w-3.5 h-3.5" /> },
  { id: 'CROSS_ASSET', label: 'Cross-Asset', shortcut: 'F6', icon: <Layers className="w-3.5 h-3.5" /> },
];

export const CommandHeader: React.FC<CommandHeaderProps> = ({
  activeSymbol,
  onSelectSymbol,
  timeframe,
  onSelectTimeframe,
  ticks,
  status,
  latencyMs,
  activeProvider,
  onOpenSettings,
  activeWorkspace,
  onSelectWorkspace,
}) => {
  // Global Keyboard shortcuts F1-F6
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      if (e.key === 'F1') {
        e.preventDefault();
        onSelectWorkspace('COCKPIT');
      } else if (e.key === 'F2') {
        e.preventDefault();
        onSelectWorkspace('OPTIONS');
      } else if (e.key === 'F3') {
        e.preventDefault();
        onSelectWorkspace('RISK');
      } else if (e.key === 'F4') {
        e.preventDefault();
        onSelectWorkspace('BONDS');
      } else if (e.key === 'F5') {
        e.preventDefault();
        onSelectWorkspace('SCREENER');
      } else if (e.key === 'F6') {
        e.preventDefault();
        onSelectWorkspace('CROSS_ASSET');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onSelectWorkspace]);

  return (
    <header className="bg-terminal-header border-b border-terminal-border text-terminal-text select-none sticky top-0 z-50">
      {/* 1. Top Bar: Brand, Workspace Tabs, Feed Latency */}
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-terminal-border/60">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 font-bold tracking-wider text-sm">
            <span className="text-xl">🇮🇳</span>
            <span className="bg-amber-500/20 text-amber-400 border border-amber-500/40 px-1.5 py-0.5 rounded text-xs font-mono font-black">
              IFIT
            </span>
            <span className="tracking-widest text-xs text-gray-300 font-mono">TERMINAL</span>
          </div>

          <div className="h-4 w-[1px] bg-terminal-border" />

          {/* Institutional Workspace Tab Bar */}
          <nav className="flex items-center gap-1" role="tablist" aria-label="Institutional workspaces">
            {WORKSPACE_TABS.map((tab) => {
              const isActive = activeWorkspace === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => onSelectWorkspace(tab.id)}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 ${
                    isActive
                      ? 'bg-blue-600 text-white font-bold shadow-[0_0_12px_rgba(37,99,235,0.4)] border border-blue-400/50'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-terminal-panel border border-transparent'
                  }`}
                >
                  {tab.icon}
                  <span>{tab.label}</span>
                  <span
                    className={`text-[9px] px-1 py-0.2 rounded font-mono ${
                      isActive ? 'bg-blue-800 text-blue-200' : 'bg-gray-800 text-gray-400'
                    }`}
                  >
                    {tab.shortcut}
                  </span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Top Right: Active Broker Pill & Feed Latency */}
        <div className="flex items-center gap-2">
          {/* Active Broker Pill */}
          <button
            type="button"
            onClick={onOpenSettings}
            aria-label="Data feed and broker configuration"
            className="flex items-center gap-1.5 bg-terminal-panel hover:bg-terminal-hover border border-terminal-border px-2 py-0.5 rounded text-[11px] font-mono transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-500"
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                status === 'CONNECTED' ? 'bg-terminal-green shadow-[0_0_6px_#22c55e]' : 'bg-amber-500 animate-pulse'
              }`}
            />
            <span className="text-gray-400">FEED:</span>
            <span className="font-semibold text-gray-200">{activeProvider}</span>
            <Settings className="w-3 h-3 text-gray-400 ml-1" />
          </button>

          {/* Latency Meter */}
          <div className="flex items-center gap-1 text-[11px] font-mono text-gray-400 bg-terminal-panel/60 border border-terminal-border/60 px-2 py-0.5 rounded">
            <Zap className={`w-3 h-3 ${status === 'CONNECTED' ? 'text-terminal-green' : 'text-amber-400'}`} />
            <span>{status === 'CONNECTED' ? `${latencyMs}ms` : 'STANDALONE'}</span>
          </div>

          {/* Quant Lab External Link */}
          <a
            href={
              typeof window !== 'undefined' && localStorage.getItem('ifit_quant_url')
                ? localStorage.getItem('ifit_quant_url')!
                : typeof window !== 'undefined' && window.location.hostname === 'localhost'
                ? 'http://localhost:8501'
                : 'https://share.streamlit.io/vishwasjoshi2019/ifit-trading-terminal/main/app.py'
            }
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Open Legacy Quant Lab in new tab (external link)"
            className="flex items-center gap-1 text-[11px] font-mono text-cyan-400 hover:text-cyan-300 bg-cyan-950/40 border border-cyan-800/50 px-2 py-0.5 rounded transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-cyan-500"
          >
            <span>Legacy Lab</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      {/* 2. Global Live Ticker Tape Strip */}
      <div className="flex items-center justify-between px-3 py-1 bg-[#090C12] border-b border-terminal-border/40 text-[11px] font-mono overflow-x-auto no-scrollbar">
        <div className="flex items-center gap-4">
          <span className="text-slate-400 text-[10px] uppercase font-bold tracking-wider">INDICES & BLUECHIPS:</span>
          {TICKER_SYMBOLS.map((sym) => {
            const tick = ticks[sym];
            const ltp = tick ? tick.ltp : 0;
            const pct = tick ? tick.percentage_change : 0;
            const isPos = pct >= 0;

            return (
              <button
                key={sym}
                type="button"
                onClick={() => onSelectSymbol(sym)}
                aria-label={`Select ${sym} ticker quote`}
                className={`flex items-center gap-1.5 cursor-pointer px-2 py-0.5 rounded transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 ${
                  activeSymbol === sym ? 'bg-blue-950/60 border border-blue-500/40 font-bold' : 'hover:bg-terminal-hover border border-transparent'
                }`}
              >
                <span className="text-gray-300">{sym}</span>
                <span className="text-gray-100 tabular-nums">
                  {ltp > 0 ? ltp.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '…'}
                </span>
                <span className={`text-[10px] tabular-nums ${isPos ? 'text-terminal-green' : 'text-terminal-red'}`}>
                  {isPos ? '+' : ''}
                  {pct.toFixed(2)}%
                </span>
              </button>
            );
          })}
        </div>

        {/* Active Quote Quick Display */}
        {ticks[activeSymbol] && (
          <div className="hidden lg:flex items-center gap-4 text-[10px] text-gray-400 font-mono tabular-nums">
            <div>
              <span className="text-slate-400 mr-1">OPEN:</span>
              <span className="text-gray-300">₹{ticks[activeSymbol].open.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-slate-400 mr-1">HIGH:</span>
              <span className="text-terminal-green">₹{ticks[activeSymbol].high.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-slate-400 mr-1">LOW:</span>
              <span className="text-terminal-red">₹{ticks[activeSymbol].low.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-slate-400 mr-1">VOL:</span>
              <span className="text-gray-300 font-semibold">{ticks[activeSymbol].volume.toLocaleString()}</span>
            </div>
          </div>
        )}
      </div>

      {/* 3. Instrument Context Bar (For Cockpit & Options Lab) */}
      {(activeWorkspace === 'COCKPIT' || activeWorkspace === 'OPTIONS' || activeWorkspace === 'RISK') && (
        <div className="flex items-center justify-between px-3 py-1 bg-terminal-bg text-xs font-mono border-b border-terminal-border/30">
          <div className="flex items-center gap-3">
            <span className="text-slate-400 uppercase tracking-wider text-[10px]">Symbol:</span>
            <div className="flex items-center gap-1">
              {['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'RELIANCE', 'HDFCBANK'].map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => onSelectSymbol(s)}
                  className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 ${
                    activeSymbol === s
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'bg-terminal-panel text-gray-400 hover:text-gray-200 hover:bg-terminal-hover border border-terminal-border'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>

            <div className="h-3 w-[1px] bg-terminal-border mx-1" />

            {/* Timeframe Selector (Cockpit) */}
            {activeWorkspace === 'COCKPIT' && (
              <>
                <span className="text-slate-400 uppercase tracking-wider text-[10px]">TF:</span>
                <div className="flex items-center gap-1">
                  {TIMEFRAMES.map((tf) => (
                    <button
                      key={tf}
                      type="button"
                      onClick={() => onSelectTimeframe(tf)}
                      className={`px-2 py-0.5 rounded text-[11px] transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 ${
                        timeframe === tf
                          ? 'bg-amber-600/30 text-amber-300 border border-amber-500/50 font-bold'
                          : 'text-gray-400 hover:text-gray-200'
                      }`}
                    >
                      {tf}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>

          <div className="text-[10px] text-slate-400 font-mono">
            Press <kbd className="px-1 py-0.5 bg-gray-800 rounded border border-gray-700 text-gray-300">F1–F6</kbd> to switch workspaces instantly
          </div>
        </div>
      )}
    </header>
  );
};
