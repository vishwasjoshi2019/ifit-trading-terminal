import type { TradePrint } from '../hooks/useWebSocketMarket';

interface TimeAndSalesTapeProps {
  tape: TradePrint[];
  symbol: string;
}

export const TimeAndSalesTape: React.FC<TimeAndSalesTapeProps> = ({ tape, symbol }) => {
  return (
    <div className="flex flex-col h-full bg-terminal-panel text-xs font-mono select-none">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-terminal-header border-b border-terminal-border">
        <span className="font-bold text-gray-200">TIME & SALES</span>
        <span className="text-[10px] text-gray-400">{tape.length} PRINTS</span>
      </div>

      {/* Columns Header */}
      <div className="grid grid-cols-3 px-3 py-1 text-[10px] text-gray-500 font-bold border-b border-terminal-border/40 bg-terminal-bg">
        <span>TIME</span>
        <span className="text-center">PRICE</span>
        <span className="text-right">SIZE</span>
      </div>

      {/* Prints List */}
      <div className="flex-1 overflow-y-auto px-2 divide-y divide-terminal-border/20">
        {tape.length === 0 ? (
          <div className="h-full flex items-center justify-center text-gray-500 text-[11px]">
            Waiting for live prints...
          </div>
        ) : (
          tape.map((print) => (
            <div
              key={print.id}
              className={`grid grid-cols-3 py-1 text-[11px] items-center transition-colors ${
                print.isBuyer ? 'text-terminal-green hover:bg-terminal-green/5' : 'text-terminal-red hover:bg-terminal-red/5'
              }`}
            >
              <span className="text-gray-400 font-normal">{print.time}</span>
              <span className="text-center font-semibold">₹{print.price.toFixed(2)}</span>
              <span className="text-right font-semibold">{print.qty}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
