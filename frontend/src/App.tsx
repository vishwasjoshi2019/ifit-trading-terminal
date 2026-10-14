import React, { useState, useEffect } from 'react';
import { CommandHeader } from './components/CommandHeader';
import { TradingViewChart } from './components/TradingViewChart';
import { OrderBookDepthPanel } from './components/OrderBookDepthPanel';
import { TimeAndSalesTape } from './components/TimeAndSalesTape';
import { OptionChainMatrix } from './components/OptionChainMatrix';
import { BrokerSettingsModal } from './components/BrokerSettingsModal';
import { useWebSocketMarket } from './hooks/useWebSocketMarket';
import { fetchSnapshot } from './services/api';
import type { OrderBookDepth } from './types';
import { Radio, BarChart2, Clock, Activity, Cpu } from 'lucide-react';

export const App: React.FC = () => {
  const [activeSymbol, setActiveSymbol] = useState<string>('NIFTY');
  const [timeframe, setTimeframe] = useState<string>('1m');
  const [depth, setDepth] = useState<OrderBookDepth | null>(null);
  const [rightTab, setRightTab] = useState<'TAPE' | 'OPTIONS'>('TAPE');
  const [settingsOpen, setSettingsOpen] = useState<boolean>(false);
  const [clock, setClock] = useState<string>('');

  const { ticks, currentTick, tape, status, latencyMs, activeProvider } = useWebSocketMarket(activeSymbol);

  // Periodic depth polling
  useEffect(() => {
    let active = true;

    const loadDepth = () => {
      fetchSnapshot(activeSymbol)
        .then((snap) => {
          if (active && snap.depth) {
            setDepth(snap.depth);
          }
        })
        .catch(() => {});
    };

    loadDepth();
    const interval = setInterval(loadDepth, 1500);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [activeSymbol]);

  // Clock
  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setClock(now.toLocaleTimeString('en-IN', { hour12: false }) + ' IST');
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-terminal-bg text-terminal-text overflow-hidden font-sans select-none">
      {/* 1. Institutional Command Bar */}
      <CommandHeader
        activeSymbol={activeSymbol}
        onSelectSymbol={setActiveSymbol}
        timeframe={timeframe}
        onSelectTimeframe={setTimeframe}
        ticks={ticks}
        status={status}
        latencyMs={latencyMs}
        activeProvider={activeProvider}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      {/* 2. Main Terminal Grid */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Left: TradingView Chart Pane */}
        <div className="flex-1 h-full min-h-[400px]">
          <TradingViewChart
            symbol={activeSymbol}
            timeframe={timeframe}
            currentTick={currentTick}
          />
        </div>

        {/* Right: Institutional Order Book & Microstructure Panels */}
        <div className="w-full md:w-[380px] lg:w-[420px] flex flex-col h-full bg-terminal-panel border-l border-terminal-border">
          {/* Top Half: Order Book Depth */}
          <div className="h-1/2 flex flex-col">
            <OrderBookDepthPanel depth={depth} symbol={activeSymbol} />
          </div>

          {/* Bottom Half: Tabs for Time & Sales vs Option Chain */}
          <div className="h-1/2 flex flex-col">
            {/* Tab Header */}
            <div className="flex items-center bg-terminal-header border-b border-terminal-border text-xs font-mono">
              <button
                onClick={() => setRightTab('TAPE')}
                className={`flex-1 py-1.5 text-center font-bold transition-colors ${
                  rightTab === 'TAPE'
                    ? 'bg-terminal-panel text-blue-400 border-b-2 border-blue-500'
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                TIME & SALES (TAPE)
              </button>
              <button
                onClick={() => setRightTab('OPTIONS')}
                className={`flex-1 py-1.5 text-center font-bold transition-colors ${
                  rightTab === 'OPTIONS'
                    ? 'bg-terminal-panel text-amber-400 border-b-2 border-amber-500'
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                OPTION CHAIN MATRIX
              </button>
            </div>

            {/* Tab Body */}
            <div className="flex-1 overflow-hidden">
              {rightTab === 'TAPE' ? (
                <TimeAndSalesTape tape={tape} symbol={activeSymbol} />
              ) : (
                <OptionChainMatrix symbol={activeSymbol} />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 3. Terminal Footer Status Bar */}
      <footer className="flex items-center justify-between px-3 py-1 bg-terminal-header border-t border-terminal-border text-[11px] font-mono text-gray-400 select-none">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <span
              className={`w-2 h-2 rounded-full ${
                status === 'CONNECTED' ? 'bg-terminal-green shadow-[0_0_6px_#22c55e]' : 'bg-terminal-red'
              }`}
            />
            <span className="font-semibold text-gray-200">
              FASTAPI STREAM: {status === 'CONNECTED' ? 'ONLINE' : 'OFFLINE'}
            </span>
          </div>
          <span className="text-gray-600">|</span>
          <div>
            ENGINE: <span className="text-gray-200">ASYNCIO EVENT LOOP (:8000)</span>
          </div>
          <span className="text-gray-600">|</span>
          <div>
            PROVIDER: <span className="text-amber-400 font-bold">{activeProvider}</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-gray-300">
            <Clock className="w-3 h-3 text-gray-400" />
            <span>{clock}</span>
          </div>
          <span className="text-gray-600">|</span>
          <span className="text-gray-500">IFIT v1.0 PRO TERMINAL</span>
        </div>
      </footer>

      {/* 4. Broker Switching Modal */}
      <BrokerSettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        activeProvider={activeProvider}
      />
    </div>
  );
};

export default App;
