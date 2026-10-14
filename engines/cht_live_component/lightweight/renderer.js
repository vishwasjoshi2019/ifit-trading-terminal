console.log('IFIT CHT Lightweight Charts renderer V1');

(function () {
    function loadLibrary(onReady) {
        if (window.LightweightCharts) {
            onReady();
            return;
        }
        if (window.__ifitLightweightLoading) { return; }
        window.__ifitLightweightLoading = true;
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/lightweight-charts@5.2.0/dist/lightweight-charts.standalone.production.js';
        script.onload = function () { window.__ifitLightweightLoading = false; console.log('IFIT CHT Lightweight Charts loaded'); onReady(); };
        script.onerror = function () { window.__ifitLightweightLoading = false; console.error('IFIT CHT Lightweight Charts failed to load'); };
        document.head.appendChild(script);
    }

    window.IFIT_CHT_LIGHTWEIGHT = { create: function (container, candles) {
        if (!container) return;
        loadLibrary(function () {
            if (!container.__ifitChart) {
                const chart = LightweightCharts.createChart(container, { autoSize: true, layout: { background: { type: 'solid', color: '#0b0e11' }, textColor: '#b8c0cc' }, grid: { vertLines: { color: '#1e2328' }, horzLines: { color: '#1e2328' } }, rightPriceScale: { borderColor: '#343a40' }, timeScale: { borderColor: '#343a40', timeVisible: true, secondsVisible: false, rightOffset: 8, barSpacing: 8 }, crosshair: { mode: LightweightCharts.CrosshairMode.Normal }, handleScroll: true, handleScale: true });
                const series = chart.addSeries(LightweightCharts.CandlestickSeries, { upColor: '#26a641', downColor: '#ef4544', borderUpColor: '#26a641', borderDownColor: '#ef4544', wickUpColor: '#26a641', wickDownColor: '#ef4544', lastValueVisible: true, priceLineVisible: true }); container.__ifitChart = { chart: chart, series: series };
            }
            container.__ifitChart.series.setData(candles || []);
        });
    } };
})();