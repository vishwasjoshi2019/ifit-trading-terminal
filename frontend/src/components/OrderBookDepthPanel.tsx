import type { OrderBookDepth } from '../types';

interface OrderBookDepthPanelProps {
  depth: OrderBookDepth | null;
  symbol: string;
}

export const OrderBookDepthPanel: React.FC<OrderBookDepthPanelProps> = ({ depth, symbol }) => {
  if (!depth || !depth.levels || depth.levels.length === 0) {
    return (
      <div className="flex flex-col h-full bg-terminal-panel p-3 text-xs font-mono text-gray-500">
        <div className="font-semibold text-gray-400 mb-2">ORDER BOOK (L2)</div>
        <div className="flex-1 flex items-center justify-center">Connecting to depth feed...</div>
      </div>
    );
  }

  const maxQty = Math.max(
    ...depth.levels.map((l) => Math.max(l.bid_qty, l.ask_qty)),
    100
  );

  const totalBuy = depth.total_buy_qty || depth.levels.reduce((acc, l) => acc + l.bid_qty, 0);
  const totalSell = depth.total_sell_qty || depth.levels.reduce((acc, l) => acc + l.ask_qty, 0);
  const buyRatio = totalBuy + totalSell > 0 ? (totalBuy / (totalBuy + totalSell)) * 100 : 50;

  return (
    <div className="flex flex-col h-full bg-terminal-panel border-b border-terminal-border text-xs font-mono select-none">
      {/* Header & Spread */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-terminal-header border-b border-terminal-border">
        <span className="font-bold text-gray-200">MARKET DEPTH</span>
        <div className="flex items-center gap-2 text-[11px]">
          <span className="text-gray-400">SPREAD:</span>
          <span className="text-amber-400 font-semibold">₹{depth.spread.toFixed(2)}</span>
        </div>
      </div>

      {/* Buy/Sell Volume Ratio Bar */}
      <div className="px-3 py-1.5 border-b border-terminal-border/60 bg-terminal-bg">
        <div className="flex justify-between text-[10px] text-gray-400 mb-1">
          <span className="text-terminal-green">BUY: {totalBuy.toLocaleString()} ({buyRatio.toFixed(1)}%)</span>
          <span className="text-terminal-red">SELL: {totalSell.toLocaleString()} ({(100 - buyRatio).toFixed(1)}%)</span>
        </div>
        <div className="w-full h-1.5 bg-terminal-border rounded-full flex overflow-hidden">
          <div className="bg-terminal-green transition-all duration-300" style={{ width: `${buyRatio}%` }} />
          <div className="bg-terminal-red transition-all duration-300" style={{ width: `${100 - buyRatio}%` }} />
        </div>
      </div>

      {/* Levels Table */}
      <div className="flex-1 overflow-y-auto px-2 py-1">
        <div className="grid grid-cols-4 text-[10px] text-gray-500 font-bold border-b border-terminal-border/40 pb-1 mb-1">
          <span>QTY</span>
          <span>BID</span>
          <span className="text-right">ASK</span>
          <span className="text-right">QTY</span>
        </div>

        {depth.levels.map((lvl) => {
          const bidWidth = Math.min(100, Math.round((lvl.bid_qty / maxQty) * 100));
          const askWidth = Math.min(100, Math.round((lvl.ask_qty / maxQty) * 100));

          return (
            <div key={lvl.level} className="relative grid grid-cols-4 py-1 text-[11px] items-center">
              {/* Bid Volume fill */}
              <div
                className="absolute left-0 top-0 bottom-0 bg-terminal-green/10 pointer-events-none rounded-r"
                style={{ width: `${bidWidth / 2}%` }}
              />
              {/* Ask Volume fill */}
              <div
                className="absolute right-0 top-0 bottom-0 bg-terminal-red/10 pointer-events-none rounded-l"
                style={{ width: `${askWidth / 2}%` }}
              />

              <span className="text-gray-400 z-10">{lvl.bid_qty.toLocaleString()}</span>
              <span className="text-terminal-green font-semibold z-10">₹{lvl.bid.toFixed(2)}</span>
              <span className="text-terminal-red font-semibold text-right z-10">₹{lvl.ask.toFixed(2)}</span>
              <span className="text-gray-400 text-right z-10">{lvl.ask_qty.toLocaleString()}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
