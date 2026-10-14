import React, { useEffect, useRef, useState } from 'react';
import { createChart, LineStyle } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts';
import type { NormalizedTick } from '../types';
import { fetchCandles } from '../services/api';
import { Layers } from 'lucide-react';

interface TradingViewChartProps {
  symbol: string;
  timeframe: string;
  currentTick: NormalizedTick | null;
}

export const TradingViewChart: React.FC<TradingViewChartProps> = ({ symbol, timeframe, currentTick }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const ema9SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema21SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [showOverlays, setShowOverlays] = useState<boolean>(true);

  // Initialize TradingView Lightweight Charts Canvas
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      autoSize: true,
      layout: {
        background: { color: '#080a0c' },
        textColor: '#9ca3af',
      },
      grid: {
        vertLines: { color: '#13171f' },
        horzLines: { color: '#13171f' },
      },
      crosshair: {
        vertLine: { color: '#4b5563', width: 1, style: LineStyle.Dashed },
        horzLine: { color: '#4b5563', width: 1, style: LineStyle.Dashed },
      },
      rightPriceScale: {
        borderColor: '#1f2937',
        scaleMargins: { top: 0.1, bottom: 0.25 },
      },
      timeScale: {
        borderColor: '#1f2937',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });

    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    const ema9Series = chart.addLineSeries({
      color: '#3b82f6',
      lineWidth: 1.5,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    const ema21Series = chart.addLineSeries({
      color: '#f59e0b',
      lineWidth: 1.5,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    volumeSeriesRef.current = volumeSeries;
    ema9SeriesRef.current = ema9Series;
    ema21SeriesRef.current = ema21Series;

    const handleResize = () => {
      if (containerRef.current && chart) {
        chart.applyOptions({ width: containerRef.current.clientWidth, height: containerRef.current.clientHeight });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  // Fetch initial candles whenever symbol or timeframe changes
  useEffect(() => {
    let active = true;
    setLoading(true);

    fetchCandles(symbol, timeframe, 150)
      .then((candles) => {
        if (!active || !candleSeriesRef.current || !volumeSeriesRef.current) return;

        const candleData: CandlestickData<Time>[] = [];
        const volData: any[] = [];
        const ema9Data: any[] = [];
        const ema21Data: any[] = [];

        let prevEma9 = 0;
        let prevEma21 = 0;
        const k9 = 2 / (9 + 1);
        const k21 = 2 / (21 + 1);

        candles.forEach((c, idx) => {
          const t = Math.floor(new Date(c.timestamp).getTime() / 1000) as Time;
          candleData.push({
            time: t,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
          });

          volData.push({
            time: t,
            value: c.volume,
            color: c.close >= c.open ? 'rgba(34, 197, 94, 0.4)' : 'rgba(239, 68, 68, 0.4)',
          });

          // Moving averages
          if (idx === 0) {
            prevEma9 = c.close;
            prevEma21 = c.close;
          } else {
            prevEma9 = c.close * k9 + prevEma9 * (1 - k9);
            prevEma21 = c.close * k21 + prevEma21 * (1 - k21);
          }
          ema9Data.push({ time: t, value: prevEma9 });
          ema21Data.push({ time: t, value: prevEma21 });
        });

        candleSeriesRef.current.setData(candleData);
        volumeSeriesRef.current.setData(volData);
        if (ema9SeriesRef.current) ema9SeriesRef.current.setData(ema9Data);
        if (ema21SeriesRef.current) ema21SeriesRef.current.setData(ema21Data);

        if (chartRef.current) {
          chartRef.current.timeScale().fitContent();
        }
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [symbol, timeframe]);

  // Update chart in real-time when tick arrives
  useEffect(() => {
    if (!currentTick || currentTick.symbol !== symbol || !candleSeriesRef.current) return;

    const t = Math.floor(new Date(currentTick.timestamp).getTime() / 1000) as Time;
    candleSeriesRef.current.update({
      time: t,
      open: currentTick.open || currentTick.ltp,
      high: currentTick.high || currentTick.ltp,
      low: currentTick.low || currentTick.ltp,
      close: currentTick.ltp,
    });
  }, [currentTick, symbol]);

  return (
    <div className="relative w-full h-full bg-terminal-bg flex flex-col border-r border-terminal-border">
      {/* Chart Header Bar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-terminal-panel border-b border-terminal-border text-xs font-mono text-gray-300">
        <div className="flex items-center gap-2">
          <span className="font-bold text-gray-100">{symbol}</span>
          <span className="text-gray-500">•</span>
          <span className="text-amber-400 font-semibold">{timeframe}</span>
          <span className="text-gray-500">•</span>
          <span className="text-blue-400 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
            EMA 9
          </span>
          <span className="text-amber-400 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            EMA 21
          </span>
        </div>

        <div className="flex items-center gap-2">
          {loading && <span className="text-[11px] text-gray-500 animate-pulse">Loading candles...</span>}
          <button
            onClick={() => setShowOverlays(!showOverlays)}
            className={`px-2 py-0.5 rounded text-[11px] border flex items-center gap-1 ${
              showOverlays
                ? 'bg-blue-950/40 text-blue-300 border-blue-500/40'
                : 'bg-terminal-bg text-gray-500 border-terminal-border'
            }`}
          >
            <Layers className="w-3 h-3" />
            Indicators
          </button>
        </div>
      </div>

      {/* Canvas container */}
      <div ref={containerRef} className="flex-1 w-full min-h-[350px]" />
    </div>
  );
};
