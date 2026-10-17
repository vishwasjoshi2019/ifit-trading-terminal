import React, { useState, useEffect } from 'react';
import { fetchHealth, switchProvider, getBackendBaseUrl, setBackendBaseUrl } from '../services/api';
import type { SystemHealth } from '../types';
import { X, CheckCircle, AlertTriangle, Radio, Globe } from 'lucide-react';

interface BrokerSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeProvider: string;
}

export const BrokerSettingsModal: React.FC<BrokerSettingsModalProps> = ({
  isOpen,
  onClose,
  activeProvider,
}) => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [backendUrl, setBackendUrlState] = useState<string>(getBackendBaseUrl());
  const [urlSaved, setUrlSaved] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen) {
      setBackendUrlState(getBackendBaseUrl());
      fetchHealth().then(setHealth).catch(() => {});
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSaveUrl = () => {
    setBackendBaseUrl(backendUrl);
    setUrlSaved(true);
    setTimeout(() => setUrlSaved(false), 2000);
    fetchHealth().then(setHealth).catch(() => {});
  };

  const handleSwitch = async (provider: string) => {
    setLoading(true);
    setError(null);
    try {
      await switchProvider(provider);
      const updated = await fetchHealth();
      setHealth(updated);
    } catch (err: any) {
      setError(err.message || 'Failed to switch provider');
    } finally {
      setLoading(false);
    }
  };

  const providers = [
    {
      id: 'CHOICE_FINX',
      title: 'Choice FinX (OpenAPI & Live Feed)',
      desc: 'Live tick-by-tick NSE/BSE feeds & execution adapter configured for User UFA113.',
    },
    {
      id: 'SIMULATION',
      title: 'Institutional Simulation (Brownian Motion)',
      desc: 'Synthetic ticks, L2 depth, CVD, and Black-Scholes Greeks. Zero broker credentials required.',
    },
    {
      id: 'DHAN',
      title: 'Dhan HQ (Direct WebSocket & REST)',
      desc: 'Live tick-by-tick feed for NSE Indices, Futures, and Equity options.',
    },
    {
      id: 'ZERODHA',
      title: 'Zerodha Kite Connect',
      desc: 'KiteTicker WebSocket streaming adapter for retail trading accounts.',
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
      <div className="bg-terminal-header border border-terminal-border rounded-lg w-full max-w-lg shadow-2xl overflow-hidden font-mono text-terminal-text">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-terminal-border bg-terminal-panel">
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-bold text-gray-100">DATA FEED & BROKER CONFIGURATION</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-terminal-hover rounded text-gray-400 hover:text-gray-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {error && (
            <div className="p-2.5 bg-red-950/40 border border-red-500/40 rounded text-red-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Backend Streaming Server URL */}
          <div className="space-y-1.5 p-3 bg-terminal-bg rounded border border-terminal-border">
            <div className="flex items-center justify-between">
              <label className="text-xs text-gray-300 font-semibold flex items-center gap-1.5">
                <Globe className="w-3.5 h-3.5 text-blue-400" />
                Backend Streaming Endpoint (Render / Local)
              </label>
              {urlSaved && (
                <span className="text-[10px] text-terminal-green font-semibold flex items-center gap-1">
                  <CheckCircle className="w-3 h-3" /> Saved
                </span>
              )}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={backendUrl}
                onChange={(e) => setBackendUrlState(e.target.value)}
                placeholder="e.g. https://your-terminal.onrender.com or http://localhost:8000"
                className="flex-1 bg-terminal-panel border border-terminal-border px-2.5 py-1.5 text-xs rounded text-gray-200 focus:outline-none focus:border-blue-500 font-mono"
              />
              <button
                type="button"
                onClick={handleSaveUrl}
                className="px-3 py-1 bg-blue-600/80 hover:bg-blue-600 text-white text-xs rounded font-semibold transition-colors"
              >
                Connect
              </button>
            </div>
            <div className="text-[10px] text-gray-500">
              Leave blank to use default <span className="text-gray-400">http://localhost:8000</span> or enter your Render URL.
            </div>
          </div>

          <div className="space-y-2.5">
            <label className="text-xs text-gray-400 font-semibold uppercase tracking-wider">
              Active Provider Adapter
            </label>

            {providers.map((p) => {
              const isSelected = (health?.active_provider || activeProvider) === p.id;
              const provHealth = health?.providers.find((item) => item.name === p.id);

              return (
                <div
                  key={p.id}
                  onClick={() => !loading && handleSwitch(p.id)}
                  className={`p-3 rounded border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-blue-950/30 border-blue-500 shadow-md'
                      : 'bg-terminal-panel border-terminal-border hover:bg-terminal-hover'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-sm text-gray-200">{p.title}</span>
                    {isSelected ? (
                      <span className="flex items-center gap-1 text-[11px] text-terminal-green font-semibold">
                        <CheckCircle className="w-3.5 h-3.5" />
                        ACTIVE
                      </span>
                    ) : (
                      <span className="text-[10px] text-gray-500">
                        {provHealth?.status || 'READY'}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-gray-400 leading-relaxed">{p.desc}</p>
                </div>
              );
            })}
          </div>

          {/* Instructions */}
          <div className="p-3 bg-terminal-bg rounded border border-terminal-border/60 text-[11px] text-gray-400 space-y-1">
            <div className="font-semibold text-gray-300">Live Credentials Setup:</div>
            <div>To activate live exchange feeds, populate your credentials in <code className="text-amber-400">.env</code>:</div>
            <pre className="text-[10px] bg-black/40 p-1.5 rounded text-gray-300 mt-1">
              CHOICE_FINX_USER_ID=UFA113{'\n'}
              CHOICE_FINX_TOKEN=your_jwt_token{'\n'}
              DHAN_CLIENT_ID=your_client_id{'\n'}
              DHAN_ACCESS_TOKEN=your_token
            </pre>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end px-4 py-2.5 bg-terminal-panel border-t border-terminal-border">
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
