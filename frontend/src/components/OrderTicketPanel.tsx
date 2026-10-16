import React, { useState } from 'react';
import type { NormalizedTick, PaperOrder, Position } from '../types';
import { ArrowUpRight, ArrowDownRight, CheckCircle2, TrendingUp, DollarSign } from 'lucide-react';

interface OrderTicketPanelProps {
  symbol: string;
  currentTick: NormalizedTick | null;
  onSendOrder: (order: {
    symbol: string;
    side: 'BUY' | 'SELL';
    qty: number;
    price: number;
    orderType: 'MARKET' | 'LIMIT' | 'SL';
  }) => void;
  orders: PaperOrder[];
}

export const OrderTicketPanel: React.FC<OrderTicketPanelProps> = ({
  symbol,
  currentTick,
  onSendOrder,
  orders,
}) => {
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT' | 'SL'>('MARKET');
  const [lots, setLots] = useState<number>(1);
  const [limitPrice, setLimitPrice] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'TICKET' | 'POSITIONS' | 'ORDERS'>('TICKET');
  const [positions, setPositions] = useState<Position[]>([]);
  const [orderNotice, setOrderNotice] = useState<string | null>(null);

  const lotSize = symbol === 'BANKNIFTY' ? 15 : symbol === 'FINNIFTY' ? 25 : symbol === 'NIFTY' ? 25 : 1;
  const totalQty = lots * lotSize;
  const ltp = currentTick?.ltp || 0;
  const effectivePrice = orderType === 'MARKET' ? (side === 'BUY' ? currentTick?.ask || ltp : currentTick?.bid || ltp) : parseFloat(limitPrice) || ltp;
  const orderValue = totalQty * effectivePrice;
  const marginRequired = Math.round(orderValue / 5); // 5x intraday margin

  const handlePlaceOrder = () => {
    if (effectivePrice <= 0) return;

    onSendOrder({
      symbol,
      side,
      qty: totalQty,
      price: effectivePrice,
      orderType,
    });

    // Update internal paper positions
    setPositions((prev) => {
      const existing = prev.find((p) => p.symbol === symbol && p.side === side);
      if (existing) {
        const newQty = existing.qty + totalQty;
        const newAvg = (existing.avgPrice * existing.qty + effectivePrice * totalQty) / newQty;
        return prev.map((p) =>
          p.symbol === symbol && p.side === side
            ? {
                ...p,
                qty: newQty,
                avgPrice: +newAvg.toFixed(2),
                currentPrice: ltp,
                unrealizedPnl: +((ltp - newAvg) * newQty * (side === 'BUY' ? 1 : -1)).toFixed(2),
                pnlPercentage: +(((ltp - newAvg) / newAvg) * 100 * (side === 'BUY' ? 1 : -1)).toFixed(2),
              }
            : p
        );
      } else {
        const pnl = +((ltp - effectivePrice) * totalQty * (side === 'BUY' ? 1 : -1)).toFixed(2);
        return [
          ...prev,
          {
            symbol,
            side,
            qty: totalQty,
            avgPrice: effectivePrice,
            currentPrice: ltp,
            unrealizedPnl: pnl,
            pnlPercentage: +(((ltp - effectivePrice) / effectivePrice) * 100 * (side === 'BUY' ? 1 : -1)).toFixed(2),
          },
        ];
      }
    });

    setOrderNotice(`${side} ${totalQty} ${symbol} @ ₹${effectivePrice.toLocaleString('en-IN')}`);
    setTimeout(() => setOrderNotice(null), 3000);
  };

  const closePosition = (pos: Position) => {
    onSendOrder({
      symbol: pos.symbol,
      side: pos.side === 'BUY' ? 'SELL' : 'BUY',
      qty: pos.qty,
      price: ltp,
      orderType: 'MARKET',
    });
    setPositions((prev) => prev.filter((p) => !(p.symbol === pos.symbol && p.side === pos.side)));
    setOrderNotice(`CLOSED ${pos.side} ${pos.qty} ${pos.symbol} @ ₹${ltp.toLocaleString('en-IN')}`);
    setTimeout(() => setOrderNotice(null), 3000);
  };

  const totalPnl = positions.reduce((acc, p) => acc + (ltp - p.avgPrice) * p.qty * (p.side === 'BUY' ? 1 : -1), 0);

  return (
    <div className="flex flex-col h-full bg-terminal-panel font-mono text-terminal-text border-t border-terminal-border select-none">
      {/* Tab Navigation */}
      <div className="flex items-center justify-between border-b border-terminal-border bg-terminal-header text-xs">
        <div className="flex">
          <button
            onClick={() => setActiveTab('TICKET')}
            className={`px-3 py-1.5 font-bold transition-colors ${
              activeTab === 'TICKET' ? 'bg-terminal-panel text-blue-400 border-b-2 border-blue-500' : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            ORDER TICKET
          </button>
          <button
            onClick={() => setActiveTab('POSITIONS')}
            className={`px-3 py-1.5 font-bold transition-colors flex items-center gap-1.5 ${
              activeTab === 'POSITIONS' ? 'bg-terminal-panel text-blue-400 border-b-2 border-blue-500' : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <span>POSITIONS ({positions.length})</span>
            {positions.length > 0 && (
              <span className={`text-[10px] font-bold ${totalPnl >= 0 ? 'text-terminal-green' : 'text-terminal-red'}`}>
                {totalPnl >= 0 ? '+' : ''}₹{Math.round(totalPnl).toLocaleString('en-IN')}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('ORDERS')}
            className={`px-3 py-1.5 font-bold transition-colors ${
              activeTab === 'ORDERS' ? 'bg-terminal-panel text-blue-400 border-b-2 border-blue-500' : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            LOG ({orders.length})
          </button>
        </div>

        {orderNotice && (
          <div className="mr-3 text-[10px] text-terminal-green font-bold flex items-center gap-1 bg-green-950/40 border border-green-800/40 px-2 py-0.5 rounded animate-fade-in">
            <CheckCircle2 className="w-3 h-3" />
            {orderNotice}
          </div>
        )}
      </div>

      {/* Tab 1: Ticket Execution */}
      {activeTab === 'TICKET' && (
        <div className="p-3 space-y-3 flex-1 overflow-y-auto">
          {/* Side Selector: Buy vs Sell */}
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => setSide('BUY')}
              className={`py-1.5 rounded font-bold text-xs flex items-center justify-center gap-1 transition-all ${
                side === 'BUY'
                  ? 'bg-terminal-green text-black shadow-md'
                  : 'bg-terminal-bg text-gray-400 hover:bg-terminal-hover border border-terminal-border'
              }`}
            >
              <ArrowUpRight className="w-4 h-4" />
              BUY / LONG
            </button>
            <button
              onClick={() => setSide('SELL')}
              className={`py-1.5 rounded font-bold text-xs flex items-center justify-center gap-1 transition-all ${
                side === 'SELL'
                  ? 'bg-terminal-red text-white shadow-md'
                  : 'bg-terminal-bg text-gray-400 hover:bg-terminal-hover border border-terminal-border'
              }`}
            >
              <ArrowDownRight className="w-4 h-4" />
              SELL / SHORT
            </button>
          </div>

          {/* Order Type & Lots */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-[10px] text-gray-400 uppercase font-semibold">Order Type</label>
              <div className="flex rounded border border-terminal-border bg-terminal-bg mt-1">
                {(['MARKET', 'LIMIT', 'SL'] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setOrderType(t)}
                    className={`flex-1 py-1 text-[11px] font-bold transition-colors ${
                      orderType === t ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-gray-200'
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-[10px] text-gray-400 uppercase font-semibold">Lots ({lotSize}/lot)</label>
              <div className="flex items-center border border-terminal-border rounded bg-terminal-bg mt-1">
                <button
                  onClick={() => setLots((prev) => Math.max(1, prev - 1))}
                  className="px-2.5 py-1 text-gray-400 hover:text-gray-100 font-bold"
                >
                  -
                </button>
                <input
                  type="number"
                  value={lots}
                  onChange={(e) => setLots(Math.max(1, parseInt(e.target.value) || 1))}
                  className="w-full text-center bg-transparent text-xs text-gray-100 font-bold focus:outline-none"
                />
                <button
                  onClick={() => setLots((prev) => prev + 1)}
                  className="px-2.5 py-1 text-gray-400 hover:text-gray-100 font-bold"
                >
                  +
                </button>
              </div>
            </div>
          </div>

          {/* Limit Price Input if LIMIT or SL */}
          {orderType !== 'MARKET' && (
            <div>
              <label className="text-[10px] text-gray-400 uppercase font-semibold">Limit Price (₹)</label>
              <input
                type="number"
                placeholder={ltp ? ltp.toFixed(2) : '0.00'}
                value={limitPrice}
                onChange={(e) => setLimitPrice(e.target.value)}
                className="w-full mt-1 bg-terminal-bg border border-terminal-border px-2.5 py-1.5 rounded text-xs text-gray-100 focus:outline-none focus:border-blue-500 font-mono"
              />
            </div>
          )}

          {/* Order Summary Pill */}
          <div className="p-2 bg-terminal-bg rounded border border-terminal-border/60 text-[11px] space-y-1">
            <div className="flex justify-between text-gray-400">
              <span>Total Quantity:</span>
              <span className="text-gray-200 font-bold">{totalQty} units</span>
            </div>
            <div className="flex justify-between text-gray-400">
              <span>Exec Price:</span>
              <span className="text-gray-200 font-bold">₹{effectivePrice.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
            </div>
            <div className="flex justify-between text-gray-400">
              <span>Margin Required (5x):</span>
              <span className="text-blue-400 font-bold">₹{marginRequired.toLocaleString('en-IN')}</span>
            </div>
          </div>

          {/* Primary Action Button */}
          <button
            onClick={handlePlaceOrder}
            className={`w-full py-2 rounded font-bold text-xs tracking-wider transition-all shadow-md active:scale-[0.98] ${
              side === 'BUY'
                ? 'bg-terminal-green hover:bg-green-400 text-black'
                : 'bg-terminal-red hover:bg-red-400 text-white'
            }`}
          >
            EXECUTE {side} ({totalQty} QTY)
          </button>
        </div>
      )}

      {/* Tab 2: Live Positions */}
      {activeTab === 'POSITIONS' && (
        <div className="p-2 flex-1 overflow-y-auto space-y-1.5 text-xs">
          {positions.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-500 text-[11px] py-8">
              <TrendingUp className="w-6 h-6 mb-1 opacity-40" />
              <span>No active positions. Execute orders to build book.</span>
            </div>
          ) : (
            positions.map((pos, idx) => {
              const pnl = (ltp - pos.avgPrice) * pos.qty * (pos.side === 'BUY' ? 1 : -1);
              const pnlPct = ((ltp - pos.avgPrice) / pos.avgPrice) * 100 * (pos.side === 'BUY' ? 1 : -1);
              const isWin = pnl >= 0;

              return (
                <div key={idx} className="p-2 bg-terminal-bg rounded border border-terminal-border flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className={`px-1 py-0.2 rounded text-[10px] font-bold ${pos.side === 'BUY' ? 'bg-green-950 text-terminal-green' : 'bg-red-950 text-terminal-red'}`}>
                        {pos.side}
                      </span>
                      <span className="font-bold text-gray-200">{pos.symbol}</span>
                      <span className="text-gray-400 text-[11px]">x{pos.qty}</span>
                    </div>
                    <div className="text-[10px] text-gray-400 mt-0.5">
                      Avg: ₹{pos.avgPrice.toLocaleString('en-IN')} | LTP: ₹{ltp.toLocaleString('en-IN')}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <div className="text-right">
                      <div className={`font-bold text-xs ${isWin ? 'text-terminal-green' : 'text-terminal-red'}`}>
                        {isWin ? '+' : ''}₹{Math.round(pnl).toLocaleString('en-IN')}
                      </div>
                      <div className={`text-[10px] ${isWin ? 'text-terminal-green' : 'text-terminal-red'}`}>
                        {isWin ? '+' : ''}{pnlPct.toFixed(2)}%
                      </div>
                    </div>
                    <button
                      onClick={() => closePosition(pos)}
                      className="px-2 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 text-[10px] rounded border border-gray-700 transition-colors"
                    >
                      Exit
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Tab 3: Order History Log */}
      {activeTab === 'ORDERS' && (
        <div className="p-2 flex-1 overflow-y-auto space-y-1 text-xs">
          {orders.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-500 text-[11px] py-8">
              <DollarSign className="w-6 h-6 mb-1 opacity-40" />
              <span>No orders executed yet in this session.</span>
            </div>
          ) : (
            orders.map((o) => (
              <div key={o.id} className="p-1.5 bg-terminal-bg rounded border border-terminal-border/60 flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-1.5">
                  <span className={`px-1 rounded text-[9px] font-bold ${o.side === 'BUY' ? 'text-terminal-green bg-green-950/60' : 'text-terminal-red bg-red-950/60'}`}>
                    {o.side}
                  </span>
                  <span className="text-gray-300 font-semibold">{o.symbol}</span>
                  <span className="text-gray-500">x{o.qty}</span>
                </div>
                <div className="flex items-center gap-2 text-[10px]">
                  <span className="text-gray-200">₹{o.price.toLocaleString('en-IN')}</span>
                  <span className="text-terminal-green font-bold">FILLED</span>
                  <span className="text-gray-500">{o.time}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
