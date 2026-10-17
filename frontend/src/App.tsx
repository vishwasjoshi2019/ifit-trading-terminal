import React, { useState, useEffect } from 'react';
import { CommandHeader } from './components/CommandHeader';
import { TradingViewChart } from './components/TradingViewChart';
import { OrderBookDepthPanel } from './components/OrderBookDepthPanel';
import { TimeAndSalesTape } from './components/TimeAndSalesTape';
import { OptionChainMatrix } from './components/OptionChainMatrix';
import { OrderTicketPanel } from './components/OrderTicketPanel';
import { OptionsLabWorkspace } from './components/OptionsLabWorkspace';
import { RiskQuantWorkspace } from './components/RiskQuantWorkspace';
import { FixedIncomeWorkspace } from './components/FixedIncomeWorkspace';
import { ScreenerWorkspace } from './components/ScreenerWorkspace';
import { CrossAssetWorkspace } from './components/CrossAssetWorkspace';
import { BrokerSettingsModal } from './components/BrokerSettingsModal';
import { useWebSocketMarket } from './hooks/useWebSocketMarket';
import { fetchSnapshot } from './services/api';
import type { OrderBookDepth, WorkspaceTab } from './types';
import { Clock } from 'lucide-react';

export const App: React.FC = () => {
  const [activeWorkspace, setActiveWorkspace] = useState<WorkspaceTab>('COCKPIT');
  const [activeSymbol, setActiveSymbol] = useState<string>('NIFTY');
  const [timeframe, setTimeframe] = useState<string>('1m');
  const [depth, setDepth] = useState<OrderBookDepth | null>(null);
  const [cockpitRightTab, setCockpitRightTab] = useState<'TICKET' | 'TAPE' | 'OPTIONS'>('TICKET');
  const [settingsOpen, setSettingsOpen] = useState<boolean>(false);
  const [clock, setClock] = useState<string>('');

  const {
    ticks,
    currentTick,
    currentDepth,
    tape,
    orders,
    sendOrder,
    status,
    latencyMs,
    activeProvider,
  } = useWebSocketMarket(activeSymbol);

  // Sync WebSocket depth into local state, fallback to periodic polling if WS depth is empty
  useEffect(() => {
    if (currentDepth) {
      setDepth(currentDepth);
    }
  }, [currentDepth]);

  useEffect(() => {
    let active = true;

    const loadDepth = () => {
      fetchSnapshot(activeSymbol)
        .then((snap) => {
          if (active && snap.depth && !currentDepth) {
            setDepth(snap.depth);
          }
        })
        .catch(() => {});
    };

    loadDepth();
    const interval = setInterval(loadDepth, 2000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [activeSymbol, currentDepth]);

  // Real-time IST Clock
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
      {/* 1. Institutional Command & Workspace Bar */}
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
        activeWorkspace={activeWorkspace}
        onSelectWorkspace={setActiveWorkspace}
      />

      {/* 2. Workspace View Routing */}
      <main className="flex-1 flex overflow-hidden">
        {activeWorkspace === 'COCKPIT' && (
          <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
            {/* Left: Interactive TradingView Chart */}
            <div className="flex-1 h-full min-h-[400px]">
              <TradingViewChart
                symbol={activeSymbol}
                timeframe={timeframe}
                currentTick={currentTick}
              />
            </div>

            {/* Right: Institutional Order Book & Microstructure Panels */}
            <div className="w-full md:w-[380px] lg:w-[440px] flex flex-col h-full bg-terminal-panel border-l border-terminal-border">
              {/* Top Half: Level-2 Order Book Depth */}
              <div className="h-[42%] flex flex-col border-b border-terminal-border">
                <OrderBookDepthPanel depth={depth} symbol={activeSymbol} />
              </div>

              {/* Bottom Half: Switchable Cockpit Tabs (Order Ticket / Tape / Option Chain) */}
              <div className="h-[58%] flex flex-col">
                {/* Cockpit Tab Switcher */}
                <div className="flex items-center bg-terminal-header border-b border-terminal-border text-[11px] font-mono" role="tablist" aria-label="Cockpit right utility panel tabs">
                  <button
                    type="button"
                    role="tab"
                    aria-selected={cockpitRightTab === 'TICKET'}
                    onClick={() => setCockpitRightTab('TICKET')}
                    className={`flex-1 py-1.5 text-center font-bold transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-cyan-500 ${
                      cockpitRightTab === 'TICKET'
                        ? 'bg-terminal-panel text-cyan-400 border-b-2 border-cyan-500'
                        : 'text-slate-400 hover:text-gray-300'
                    }`}
                  >
                    ORDER TICKET
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={cockpitRightTab === 'TAPE'}
                    onClick={() => setCockpitRightTab('TAPE')}
                    className={`flex-1 py-1.5 text-center font-bold transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-blue-500 ${
                      cockpitRightTab === 'TAPE'
                        ? 'bg-terminal-panel text-blue-400 border-b-2 border-blue-500'
                        : 'text-slate-400 hover:text-gray-300'
                    }`}
                  >
                    TAPE
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={cockpitRightTab === 'OPTIONS'}
                    onClick={() => setCockpitRightTab('OPTIONS')}
                    className={`flex-1 py-1.5 text-center font-bold transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-amber-500 ${
                      cockpitRightTab === 'OPTIONS'
                        ? 'bg-terminal-panel text-amber-400 border-b-2 border-amber-500'
                        : 'text-slate-400 hover:text-gray-300'
                    }`}
                  >
                    OPTIONS
                  </button>
                </div>

                {/* Cockpit Tab Body */}
                <div className="flex-1 overflow-hidden">
                  {cockpitRightTab === 'TICKET' ? (
                    <OrderTicketPanel
                      symbol={activeSymbol}
                      currentTick={currentTick}
                      onSendOrder={sendOrder}
                      orders={orders}
                    />
                  ) : cockpitRightTab === 'TAPE' ? (
                    <TimeAndSalesTape tape={tape} symbol={activeSymbol} />
                  ) : (
                    <OptionChainMatrix symbol={activeSymbol} />
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeWorkspace === 'OPTIONS' && (
          <OptionsLabWorkspace symbol={activeSymbol} currentTick={currentTick} />
        )}

        {activeWorkspace === 'RISK' && (
          <RiskQuantWorkspace currentSpot={currentTick?.ltp || 24800} symbol={activeSymbol} />
        )}

        {activeWorkspace === 'BONDS' && <FixedIncomeWorkspace />}

        {activeWorkspace === 'SCREENER' && (
          <ScreenerWorkspace
            onSelectSymbol={(sym) => {
              setActiveSymbol(sym);
              setActiveWorkspace('COCKPIT');
            }}
          />
        )}

        {activeWorkspace === 'CROSS_ASSET' && <CrossAssetWorkspace />}
      </main>

      {/* 3. Terminal Institutional Status Bar */}
      <footer className="flex items-center justify-between px-3 py-1 bg-terminal-header border-t border-terminal-border text-[11px] font-mono text-gray-400 select-none">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                status === 'CONNECTED' ? 'bg-terminal-green shadow-[0_0_6px_#22c55e]' : 'bg-amber-400'
              }`}
            />
            <span className="font-semibold text-gray-200">
              FASTAPI STREAM: {status === 'CONNECTED' ? 'ONLINE' : 'PREVIEW'}
            </span>
          </div>
          <span className="text-gray-600">|</span>
          <div>
            WS ENGINE: <span className="text-gray-200">ASYNCIO EVENT LOOP (:8000)</span>
          </div>
          <span className="text-gray-600">|</span>
          <div>
            FEED: <span className="text-amber-400 font-bold">{activeProvider}</span>
          </div>
          <span className="text-gray-600">|</span>
          <div>
            WORKSPACE: <span className="text-blue-400 font-bold">[{activeWorkspace}]</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-gray-300">
            <Clock className="w-3 h-3 text-gray-400" />
            <span>{clock}</span>
          </div>
          <span className="text-gray-600">|</span>
          <span className="text-gray-500 font-mono">IFIT PRO v2.0 BLOOMBERG EDITION</span>
        </div>
      </footer>

      {/* 4. Settings Modal */}
      <BrokerSettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
};
export default App;
