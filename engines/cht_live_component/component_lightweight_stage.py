from __future__ import annotations

import pandas as pd
import streamlit as st

if hasattr(st, "components") and hasattr(st.components, "v2") and hasattr(st.components.v2, "component"):
    CHT_LIVE_COMPONENT = st.components.v2.component(
        "ifit_cht_live_chart",
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
                    textColor: "#b8c0cc"
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
            container.__ifitChart = { chart: chart, series: series };
        }

        container.__ifitChart.series.setData(data.candles);
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
    payload = figure.to_plotly_json() if hasattr(figure, "to_plotly_json") else figure
    for trace in payload.get("data", []):
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

def render_live_chart(figure, height: int = 700, key: str | None = None):
    trace = _find_candle_trace(figure)
    x = trace.get("x", [])
    op = trace.get("open", [])
    hi = trace.get("high", [])
    lo = trace.get("low", [])
    cl = trace.get("close", [])
    candles = []
    count = min(len(x), len(op), len(hi), len(lo), len(cl))

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

    if CHT_LIVE_COMPONENT is not None:
        try:
            return CHT_LIVE_COMPONENT(
                data={"candles": list(unique.values())},
                key=key,
            )
        except Exception:
            pass
    return st.plotly_chart(figure, use_container_width=True, key=key)
