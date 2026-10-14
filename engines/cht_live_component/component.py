from __future__ import annotations

import pandas as pd
import streamlit as st

if hasattr(st, "components") and hasattr(st.components, "v2") and hasattr(st.components.v2, "component"):
    CHT_LIVE_COMPONENT = st.components.v2.component(
        "ifit_cht_live_chart_lightweight_v1",
        html='<div id="ifit-cht-live-chart"></div>',
        css="#ifit-cht-live-chart { width: 100%; height: 620px; min-height: 620px; background: #0b0e11; }",
        js="""
export default function(component) {
    const { data, parentElement } = component;
    const container = parentElement.querySelector("#ifit-cht-live-chart");
    if (!container || !data || !data.candles) return;

    function render() {
        if (!window.LightweightCharts) return;

        if (!container.__ifitChart) {
            const chart = LightweightCharts.createChart(container, {
                autoSize: true,
                layout: {
                    background: { type: "solid", color: "#0b0e11" },
                    textColor: "#b8c0cc",
                    attributionLogo: false
                },
                grid: {
                    vertLines: { color: "#1e2328" },
                    horzLines: { color: "#1e2328" }
                },
                rightPriceScale: { borderColor: "#343a40" },
                timeScale: {
                    borderColor: "#343a40",
                    timeVisible: true,
                    secondsVisible: false,
                    rightOffset: 8,
                    barSpacing: 8
                },
                crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
                handleScroll: true,
                handleScale: true
            });

            const series = chart.addSeries(
                LightweightCharts.CandlestickSeries,
                {
                    upColor: "#26a641",
                    downColor: "#ef4544",
                    borderUpColor: "#26a641",
                    borderDownColor: "#ef4544",
                    wickUpColor: "#26a641",
                    wickDownColor: "#ef4544",
                    lastValueVisible: true,
                    priceLineVisible: true
                }
            );
            container.__ifitChart = { chart: chart, series: series, overlays: {} };
        }

        container.__ifitChart.series.setData(data.candles || []);

        // POC price line
        if (container.__ifitChart.pocLine) {
            try {
                container.__ifitChart.series.removePriceLine(container.__ifitChart.pocLine);
            } catch (e) {}
            container.__ifitChart.pocLine = null;
        }
        if (data.poc !== null && data.poc !== undefined && Number.isFinite(Number(data.poc))) {
            container.__ifitChart.pocLine = container.__ifitChart.series.createPriceLine({
                price: Number(data.poc),
                color: "#f59e0b",
                lineWidth: 2,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: "POC"
            });
        }

        // Volume Profile overlay
        if (!container.__ifitProfile) {
            container.style.position = "relative";
            container.__ifitProfile = document.createElement("div");
            container.__ifitProfile.style.position = "absolute";
            container.__ifitProfile.style.left = "0px";
            container.__ifitProfile.style.right = "70px";
            container.__ifitProfile.style.top = "0px";
            container.__ifitProfile.style.bottom = "0px";
            container.__ifitProfile.style.pointerEvents = "none";
            container.__ifitProfile.style.zIndex = "20";
            container.__ifitProfile.style.overflow = "hidden";
            container.appendChild(container.__ifitProfile);
        }

        const profile = Array.isArray(data.profile) ? data.profile : [];
        const profileEl = container.__ifitProfile;
        profileEl.innerHTML = "";

        if (profile.length) {
            let maxVolume = 1;

            profile.forEach(function(item) {
                const volume = Number(item.volume);
                if (Number.isFinite(volume) && volume > 0) {
                    maxVolume = Math.max(maxVolume, volume);
                }
            });

            profile.forEach(function(item) {
                const price = Number(item.price);
                const volume = Number(item.volume);

                if (!Number.isFinite(price) ||
                    !Number.isFinite(volume) ||
                    volume <= 0) {
                    return;
                }

                let y = null;

                try {
                    y = container.__ifitChart.series.priceToCoordinate(price);
                } catch (e) {
                    y = null;
                }

                if (y === null ||
                    y === undefined ||
                    !Number.isFinite(Number(y))) {
                    return;
                }

                const bar = document.createElement("div");
                bar.style.position = "absolute";
                bar.style.right = "0px";
                bar.style.top = Math.max(0, Number(y) - 3) + "px";
                bar.style.height = "6px";
                bar.style.minWidth = "2px";
                bar.style.width =
                    Math.max(8, Math.round(140 * volume / maxVolume)) + "px";
                bar.style.background = "rgba(59, 130, 246, 0.65)";
                bar.style.borderRadius = "3px 0 0 3px";
                bar.style.boxShadow =
                    "0 0 2px rgba(59, 130, 246, 0.35)";

                profileEl.appendChild(bar);
            });
        }

        // Native Order Flow Footprint overlay
        if (!container.__ifitFootprint) {
            container.style.position = "relative";
            container.__ifitFootprint = document.createElement("div");
            container.__ifitFootprint.style.position = "absolute";
            container.__ifitFootprint.style.left = "0px";
            container.__ifitFootprint.style.right = "70px";
            container.__ifitFootprint.style.top = "0px";
            container.__ifitFootprint.style.bottom = "0px";
            container.__ifitFootprint.style.pointerEvents = "none";
            container.__ifitFootprint.style.zIndex = "15";
            container.__ifitFootprint.style.overflow = "hidden";
            container.appendChild(container.__ifitFootprint);
        }

        const footprintEl = container.__ifitFootprint;
        footprintEl.innerHTML = "";
        const footprint = Array.isArray(data.footprint) ? data.footprint : [];

        function renderFootprint() {
            footprintEl.innerHTML = "";
            if (!footprint.length) return;

            const byTime = {};
            footprint.forEach(function(item) {
                const t = Number(item.time);
                if (!Number.isFinite(t)) return;
                if (!byTime[t]) byTime[t] = [];
                byTime[t].push(item);
            });

            const candleTimes = (data.candles || []).map(function(c) { return Number(c.time); });
            const candleByTime = {};
            (data.candles || []).forEach(function(c) { candleByTime[Number(c.time)] = c; });

            Object.keys(byTime).forEach(function(timeKey) {
                const rows = byTime[timeKey];
                const time = Number(timeKey);
                const x = container.__ifitChart.chart.timeScale().timeToCoordinate(time);
                if (x === null || x === undefined || !Number.isFinite(Number(x))) return;

                let barWidth = 10;
                const candleIndex = candleTimes.indexOf(time);
                if (candleIndex >= 0) {
                    let otherX = null;
                    if (candleIndex < candleTimes.length - 1) {
                        otherX = container.__ifitChart.chart.timeScale().timeToCoordinate(candleTimes[candleIndex + 1]);
                    }
                    if ((otherX === null || otherX === undefined) && candleIndex > 0) {
                        otherX = container.__ifitChart.chart.timeScale().timeToCoordinate(candleTimes[candleIndex - 1]);
                    }
                    if (otherX !== null && otherX !== undefined && Number.isFinite(Number(otherX))) {
                        barWidth = Math.max(12, Math.min(80, Math.abs(Number(otherX) - Number(x)) * 0.54));
                    }
                }

                rows.sort(function(a, b) { return Number(a.price) - Number(b.price); });
                let levelStep = 0;
                for (let i = 1; i < rows.length; i++) {
                    const d = Math.abs(Number(rows[i].price) - Number(rows[i - 1].price));
                    if (Number.isFinite(d) && d > 0 && (levelStep === 0 || d < levelStep)) levelStep = d;
                }
                if (!levelStep) levelStep = Math.max(0.01, Math.abs(Number(rows[0].price)) * 0.00005);

                let maxTotal = 1;
                rows.forEach(function(row) {
                    maxTotal = Math.max(maxTotal, Number(row.total) || 0);
                });

                rows.forEach(function(row) {
                    const price = Number(row.price);
                    const bid = Math.max(0, Number(row.bid) || 0);
                    const ask = Math.max(0, Number(row.ask) || 0);
                    const total = Math.max(1, bid + ask);
                    if (!Number.isFinite(price)) return;

                    const candle = candleByTime[time];
                    let mappedPrice = price;
                    if (candle) {
                        const o = Number(candle.open); const h = Number(candle.high); const l = Number(candle.low); const c = Number(candle.close);
                        if ([o,h,l,c].every(Number.isFinite)) {
                            const bodyHigh = Math.max(o, c);
                            const bodyLow = Math.min(o, c);
                            const bodyMid = (bodyHigh + bodyLow) / 2;
                            const candleRange = Math.max(h - l, 0.01);
                            const halfRange = Math.max(candleRange * 0.34, levelStep * 4);
                            const mappedLow = Math.max(l, bodyMid - halfRange);
                            const mappedHigh = Math.min(h, bodyMid + halfRange);
                            if (mappedHigh > mappedLow && rows.length > 1) {
                                const srcLow = Number(rows[0].price);
                                const srcHigh = Number(rows[rows.length - 1].price);
                                if (Number.isFinite(srcLow) && Number.isFinite(srcHigh) && srcHigh > srcLow) {
                                    mappedPrice = mappedLow + ((price - srcLow) / (srcHigh - srcLow)) * (mappedHigh - mappedLow);
                                }
                            }
                        }
                    }
                    const y = container.__ifitChart.series.priceToCoordinate(mappedPrice);
                    if (y === null || y === undefined || !Number.isFinite(Number(y))) return;

                    const mappedStep = (candleByTime[time] && rows.length > 1) ? Math.max(0.01, Math.abs(mappedPrice - (mappedPrice + (levelStep / Math.max(Number(rows[rows.length - 1].price) - Number(rows[0].price), 0.01)) * levelStep))) : levelStep;
                    const yUp = container.__ifitChart.series.priceToCoordinate(mappedPrice + mappedStep * 0.40);
                    const yDown = container.__ifitChart.series.priceToCoordinate(mappedPrice - mappedStep * 0.40);
                    let cellHeight = 12;
                    if (yUp !== null && yDown !== null && Number.isFinite(Number(yUp)) && Number.isFinite(Number(yDown))) {
                        cellHeight = Math.max(8, Math.min(34, Math.abs(Number(yDown) - Number(yUp))));
                    }

                    const imbalance = Math.max(bid / Math.max(ask, 1), ask / Math.max(bid, 1));
                    const isPoc = total >= maxTotal;
                    const border = isPoc ? "1.5px solid rgba(255,215,70,0.98)" : (imbalance >= 2 ? "1px solid rgba(255,255,255,0.92)" : "1px solid rgba(150,160,175,0.28)");
                    const intensity = Math.min(1, total / maxTotal);
                    const bidAlpha = Math.min(0.72, 0.18 + 0.48 * Math.max(bid / total, 0.18) * intensity);
                    const askAlpha = Math.min(0.72, 0.18 + 0.48 * Math.max(ask / total, 0.18) * intensity);

                    const cell = document.createElement("div");
                    cell.style.position = "absolute";
                    cell.style.left = (Number(x) - barWidth / 2) + "px";
                    cell.style.top = (Number(y) - cellHeight / 2) + "px";
                    cell.style.width = barWidth + "px";
                    cell.style.height = cellHeight + "px";
                    cell.style.display = "flex";
                    cell.style.boxSizing = "border-box";
                    cell.style.border = border;
                    cell.style.fontFamily = "Arial, sans-serif";
                    cell.style.fontSize = cellHeight >= 14 ? "9px" : "8px";
                    cell.style.lineHeight = cellHeight + "px";
                    cell.style.textAlign = "center";
                    cell.style.whiteSpace = "nowrap";
                    cell.style.color = "#f1f5f9";
                    cell.style.textShadow = "0 1px 2px rgba(0,0,0,0.9)";
                    cell.style.overflow = "hidden";

                    const bidEl = document.createElement("div");
                    bidEl.style.width = "50%";
                    bidEl.style.height = "100%";
                    bidEl.style.boxSizing = "border-box";
                    bidEl.style.background = "rgba(55,145,235," + bidAlpha.toFixed(3) + ")";
                    bidEl.textContent = Math.round(bid).toLocaleString();

                    const askEl = document.createElement("div");
                    askEl.style.width = "50%";
                    askEl.style.height = "100%";
                    askEl.style.boxSizing = "border-box";
                    askEl.style.background = "rgba(235,80,85," + askAlpha.toFixed(3) + ")";
                    askEl.textContent = Math.round(ask).toLocaleString();

                    cell.appendChild(bidEl);
                    cell.appendChild(askEl);
                    footprintEl.appendChild(cell);
                });
            });
        }

        renderFootprint();
        if (!container.__ifitFootprintBound) {
            container.__ifitFootprintBound = true;
            container.__ifitChart.chart.timeScale().subscribeVisibleLogicalRangeChange(function() {
                renderFootprint();
            });
        }

        const overlays = data.overlays || {};
        const overlayNames = ["EMA", "SMA", "VWAP"];
        overlayNames.forEach(function(name) {
            const values = overlays[name] || [];
            if (!container.__ifitChart.overlays[name]) {
                container.__ifitChart.overlays[name] = container.__ifitChart.chart.addSeries(
                    LightweightCharts.LineSeries,
                    {
                        lineWidth: 2,
                        priceLineVisible: false,
                        lastValueVisible: true,
                        crosshairMarkerVisible: true,
                        title: name,
                        priceScaleId: "right"
                    }
                );
            }
            container.__ifitChart.overlays[name].setData(values);
        });
    }

    if (!window.LightweightCharts) {
        if (!window.__ifitLightweightLoading) {
            window.__ifitLightweightLoading = true;
            const script = document.createElement("script");
            script.src = "https://unpkg.com/lightweight-charts@5.2.0/dist/lightweight-charts.standalone.production.js";
            script.onload = function() {
                window.__ifitLightweightLoading = false;
                render();
            };
            script.onerror = function() {
                window.__ifitLightweightLoading = false;
                console.error("IFIT Lightweight Charts failed to load");
            };
            document.head.appendChild(script);
        }
    } else {
        render();
    }
}
""",
    isolate_styles=False,
)
else:
    CHT_LIVE_COMPONENT = None

def _find_candle_trace(figure):
    if hasattr(figure, "data"):
        for trace in figure.data:
            if str(getattr(trace, "type", "")).lower() == "candlestick":
                return trace
    if isinstance(figure, dict):
        for trace in figure.get("data", []):
            if str(trace.get("type", "")).lower() == "candlestick":
                return trace
    raise ValueError("No candlestick trace found in CHT source figure")

def _to_timestamp(value):
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    return int(ts.timestamp())

def render_live_chart(figure, height: int = 700, key: str | None = None, timestamps=None, ohlcv=None, poc=None, profile=None, footprint_df=None):
    trace = _find_candle_trace(figure)
    x_raw = timestamps if timestamps is not None else getattr(trace, 'x', None)
    op_raw = getattr(trace, 'open', None)
    hi_raw = getattr(trace, 'high', None)
    lo_raw = getattr(trace, 'low', None)
    cl_raw = getattr(trace, 'close', None)
    x = list([] if x_raw is None else x_raw)
    op = list([] if op_raw is None else op_raw)
    hi = list([] if hi_raw is None else hi_raw)
    lo = list([] if lo_raw is None else lo_raw)
    cl = list([] if cl_raw is None else cl_raw)
    candles = []
    count = min(len(x), len(op), len(hi), len(lo), len(cl))
    for i in range(count):
        try:
            candles.append({'time': _to_timestamp(x[i]), 'open': float(op[i]), 'high': float(hi[i]), 'low': float(lo[i]), 'close': float(cl[i])})
        except (TypeError, ValueError, OverflowError):
            continue
    candles.sort(key=lambda item: item['time'])
    unique = {}
    for candle in candles:
        unique[candle['time']] = candle
    overlays = {}
    overlay_names = {'EMA', 'SMA', 'VWAP'}
    figure_data = getattr(figure, 'data', [])
    for item in figure_data:
        name = str(getattr(item, 'name', '') or '')
        if name not in overlay_names:
            continue
        values_raw = getattr(item, 'y', None)
        values = list([] if values_raw is None else values_raw)
        series = []
        limit = min(len(x), len(values))
        for i in range(limit):
            try:
                value = float(values[i])
                if pd.isna(value):
                    continue
                series.append({'time': _to_timestamp(x[i]), 'value': value})
            except (TypeError, ValueError, OverflowError):
                continue
        overlays[name] = series
    market_data = {}
    if ohlcv is not None and isinstance(ohlcv, pd.DataFrame):
        for column in ['Volume', 'Buy Volume', 'Sell Volume', 'Delta', 'CVD']:
            if column not in ohlcv.columns:
                continue
            values = list(ohlcv[column])
            series = []
            limit = min(len(x), len(values))
            for i in range(limit):
                try:
                    value = float(values[i])
                    if pd.isna(value):
                        continue
                    series.append({'time': _to_timestamp(x[i]), 'value': value})
                except (TypeError, ValueError, OverflowError):
                    continue
            market_data[column] = series
    profile_data = []
    if profile is not None and isinstance(profile, pd.DataFrame) and not profile.empty and {'Price', 'Volume'}.issubset(profile.columns):
        profile_data = [{'price': float(row['Price']), 'volume': float(row['Volume'])} for _, row in profile.iterrows()]
    footprint_data = []
    if footprint_df is not None and isinstance(footprint_df, pd.DataFrame) and not footprint_df.empty:
        required = {'Bar', 'Price', 'Bid Volume', 'Ask Volume'}
        if required.issubset(footprint_df.columns) and candles:
            source_bars = sorted(footprint_df['Bar'].dropna().unique().tolist())
            source_bars = source_bars[-len(candles):]
            target_candles = candles[-len(source_bars):]
            bar_time = {source_bar: target_candles[i]['time'] for i, source_bar in enumerate(source_bars)}
            for _, row in footprint_df.iterrows():
                try:
                    source_bar = row['Bar']
                    if source_bar not in bar_time:
                        continue
                    price = float(row['Price'])
                    bid = max(float(row['Bid Volume']), 0.0)
                    ask = max(float(row['Ask Volume']), 0.0)
                    footprint_data.append({'time': bar_time[source_bar], 'bar': float(source_bar), 'price': price, 'bid': bid, 'ask': ask, 'total': bid + ask, 'delta': ask - bid})
                except (TypeError, ValueError, OverflowError):
                    continue
    if CHT_LIVE_COMPONENT is not None:
        try:
            return CHT_LIVE_COMPONENT(data={'candles': list(unique.values()), 'overlays': overlays, 'market_data': market_data, 'poc': (None if poc is None else float(poc)), 'profile': profile_data, 'footprint': footprint_data}, key=key)
        except Exception:
            pass
    return st.plotly_chart(figure, use_container_width=True, key=key)


    for i in range(count):
        try:
            candles.append({
                "time": _to_timestamp(x[i]),
                "open": float(op[i]),
                "high": float(hi[i]),
                "low": float(lo[i]),
                "close": float(cl[i]),
            })
        except (TypeError, ValueError, OverflowError):
            continue

    candles.sort(key=lambda item: item["time"])
    unique = {}
    for candle in candles:
        unique[candle["time"]] = candle

    overlays = {}
    overlay_names = {"EMA", "SMA", "VWAP"}
    figure_data = getattr(figure, "data", [])
    for item in figure_data:
        name = str(getattr(item, "name", "") or "")
        if name not in overlay_names:
            continue
        values_raw = getattr(item, "y", None)
        values = list([] if values_raw is None else values_raw)
        series = []
        limit = min(len(x), len(values))
        for i in range(limit):
            try:
                value = float(values[i])
                if pd.isna(value):
                    continue
                series.append({"time": _to_timestamp(x[i]), "value": value})
            except (TypeError, ValueError, OverflowError):
                continue
        overlays[name] = series

    return CHT_LIVE_COMPONENT(
        data={"candles": list(unique.values()), "overlays": overlays},
        key=key,
    )










