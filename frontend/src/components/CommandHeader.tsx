import type { NormalizedTick } from '../types';
import { Activity, ShieldCheck, Settings, ExternalLink, Zap } from 'lucide-react';

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
}

const TICKER_SYMBOLS = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'RELIANCE', 'HDFCBANK', 'TCS'];
const TIMEFRAMES = ['1m', '5m', '15m', '1h', '1D'];

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
}) => {
  return (
    <header className="bg-terminal-header border-b border-terminal-border text-terminal-text select-none sticky top-0 z-50">
      {/* Top Bar: Brand, Tape, Connection Status */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-terminal-border/60">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 font-bold tracking-wider text-sm">
            <span className="text-xl">🇮🇳</span>
            <span className="bg-amber-500/20 text-amber-400 border border-amber-500/40 px-1.5 py-0.5 rounded text-xs font-mono font-black">
              IFIT
            </span>
            <span className="tracking-widest text-xs text-gray-300 font-mono">TERMINAL</span>
          </div>

          <div className="h-4 w-[1px] bg-terminal-border" />

          {/* Active Broker Pill */}
          <button
            onClick={onOpenSettings}
            className="flex items-center gap-1.5 bg-terminal-panel hover:bg-terminal-hover border border-terminal-border px-2 py-0.5 rounded text-[11px] font-mono transition-colors"
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
            <span>{status === 'CONNECTED' ? `${latencyMs}ms` : 'RECONNECTING'}</span>
          </div>
        </div>

        {/* Global Live Ticker Tape */}
        <div className="flex items-center gap-4 overflow-x-auto text-[11px] font-mono no-scrollbar">
          {TICKER_SYMBOLS.map((sym) => {
            const tick = ticks[sym];
            const ltp = tick ? tick.ltp : 0;
            const pct = tick ? tick.percentage_change : 0;
            const isPos = pct >= 0;

            return (
              <div
                key={sym}
                onClick={() => onSelectSymbol(sym)}
                className={`flex items-center gap-1.5 cursor-pointer px-2 py-0.5 rounded transition-colors ${
                  activeSymbol === sym ? 'bg-blue-950/40 border border-blue-500/30' : 'hover:bg-terminal-hover'
                }`}
              >
                <span className="font-bold text-gray-300">{sym}</span>
                <span className="text-gray-100">
                  {ltp > 0 ? ltp.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '...'}
                </span>
                <span className={`text-[10px] ${isPos ? 'text-terminal-green' : 'text-terminal-red'}`}>
                  {isPos ? '+' : ''}{pct.toFixed(2)}%
                </span>
              </div>
            );
          })}
        </div>

        {/* Quant Lab Link */}
        <div className="flex items-center gap-3">
          <a
            href="http://localhost:8501"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 text-[11px] font-mono text-blue-400 hover:text-blue-300 bg-blue-950/30 border border-blue-800/40 px-2.5 py-0.5 rounded transition-colors"
          >
            <span>Quant Lab</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      {/* Control Bar: Instrument Context & Timeframe Buttons */}
      <div className="flex items-center justify-between px-4 py-1.5 bg-terminal-bg text-xs font-mono">
        <div className="flex items-center gap-3">
          <span className="text-gray-400 uppercase tracking-wider text-[11px]">Symbol:</span>
          <div className="flex items-center gap-1">
            {['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'RELIANCE', 'HDFCBANK'].map((s) => (
              <button
                key={s}
                onClick={() => onSelectSymbol(s)}
                className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-all ${
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

          {/* Timeframe Selector */}
          <span className="text-gray-400 uppercase tracking-wider text-[11px]">TF:</span>
          <div className="flex items-center gap-1">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf}
                onClick={() => onSelectTimeframe(tf)}
                className={`px-2 py-0.5 rounded text-[11px] transition-colors ${
                  timeframe === tf
                    ? 'bg-amber-600/30 text-amber-300 border border-amber-500/50 font-bold'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* Active Quote Quick Display */}
        {ticks[activeSymbol] && (
          <div className="flex items-center gap-4 text-[11px]">
            <div>
              <span className="text-gray-500 mr-1">OPEN:</span>
              <span className="text-gray-300">₹{ticks[activeSymbol].open.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500 mr-1">HIGH:</span>
              <span className="text-terminal-green">₹{ticks[activeSymbol].high.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500 mr-1">LOW:</span>
              <span className="text-terminal-red">₹{ticks[activeSymbol].low.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500 mr-1">VOL:</span>
              <span className="text-gray-300 font-semibold">{ticks[activeSymbol].volume.toLocaleString()}</span>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
