"""IFIT Terminal Configuration & Design Tokens.

Enforces UI/UX Pro Max Fintech tokens, dark-mode terminal palette,
and institutional typography.
"""

PAGE_CONFIG = {
    "page_title": "IFIT — Indian Financial Intelligence Terminal",
    "page_icon": "🇮🇳",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

INSTRUMENT_OPTIONS = [
    "NIFTY 50",
    "BANK NIFTY",
    "FIN NIFTY",
    "MIDCP NIFTY",
    "SENSEX",
    "USDINR",
    "EURINR",
    "GBPINR",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
]

TIMEFRAME_OPTIONS = [
    "Intraday",
    "1 min",
    "5 min",
    "15 min",
    "1 hour",
    "Daily",
]

DEFAULT_SPOT_PRICES = {
    "NIFTY 50": 24782.35,
    "BANK NIFTY": 51420.80,
    "FIN NIFTY": 23680.15,
    "MIDCP NIFTY": 12890.45,
    "SENSEX": 81340.20,
    "USDINR": 83.92,
    "EURINR": 91.45,
    "GBPINR": 109.20,
    "EURUSD": 1.0895,
    "GBPUSD": 1.3012,
    "USDJPY": 149.35,
    "BTCUSDT": 67450.00,
    "ETHUSDT": 2620.50,
    "SOLUSDT": 154.80,
}

FINTECH_CSS = """
<style>
/* =====================================================================
   IFIT Master Fintech Design Tokens (Bloomberg / Institutional Terminal)
   ===================================================================== */
:root {
    --bg-primary: #080B10;
    --bg-surface: #0E131F;
    --bg-card: #121826;
    --border-subtle: #1E293B;
    --border-active: #38BDF8;
    --text-primary: #F1F5F9;
    --text-muted: #94A3B8;
    --emerald-alpha: #10B981;
    --crimson-risk: #EF4444;
    --amber-warning: #F59E0B;
    --cyan-accent: #38BDF8;
}

.block-container {
    padding-top: 0.4rem;
    padding-bottom: 2rem;
    max-width: 1600px;
}

/* Tabular numbers for financial metrics and tickers */
body, [data-testid="stMetricValue"], [data-testid="stDataFrame"], table {
    font-variant-numeric: tabular-nums;
}

/* Metric card containers */
[data-testid="stMetric"] {
    background: #0E131F;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 0.65rem 0.85rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.35);
    transition: border-color 0.15s ease, transform 0.15s ease;
}
[data-testid="stMetric"]:hover {
    border-color: #334155;
}
[data-testid="stMetricLabel"] {
    font-size: 0.72rem;
    font-weight: 700;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
[data-testid="stMetricValue"] {
    font-size: 1.32rem;
    font-weight: 800;
    font-family: -apple-system, BlinkMacSystemFont, "SF Mono", "JetBrains Mono", monospace;
    letter-spacing: -0.02em;
    color: #F8FAFC;
}

/* Modern terminal command bar */
.ifit-terminal-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1.1rem;
    margin: 0.2rem 0 0.4rem;
    border: 1px solid #1E293B;
    border-radius: 8px;
    background: #0B0F17;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.45);
    position: sticky;
    top: 0;
    z-index: 99;
}
.ifit-logo {
    font-size: 1.35rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    color: #F8FAFC;
}
.ifit-logo-badge {
    background: linear-gradient(135deg, #FF9933 0%, #FFFFFF 50%, #138808 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 900;
}
.ifit-terminal-name {
    font-size: 1.05rem;
    font-weight: 700;
    color: #64748B;
    margin-left: 0.35rem;
}
.ifit-active-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    background: rgba(56, 189, 248, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.35);
    padding: 0.3rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 800;
    color: #38BDF8;
    letter-spacing: 0.06em;
}
.ifit-live-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: #10B981;
    box-shadow: 0 0 8px #10B981;
    animation: pulse-dot 1.8s infinite ease-in-out;
}
.ifit-sim-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: #F59E0B;
    box-shadow: 0 0 8px #F59E0B;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.85); }
}
.ifit-nav-note {
    font-size: 0.78rem;
    color: #94A3B8;
    margin: 0.2rem 0 0.85rem;
    padding: 0.35rem 0.65rem;
    background: #0E131F;
    border-left: 3px solid #38BDF8;
    border-radius: 0 6px 6px 0;
}

/* Radio buttons / Segments */
div[role="radiogroup"] {
    gap: 0.3rem;
}
div[role="radiogroup"] label {
    padding: 0.45rem 0.85rem;
    border-radius: 6px;
    border: 1px solid #1E293B;
    background: #0E131F;
    transition: all 0.15s ease;
}
div[role="radiogroup"] label:hover {
    border-color: #38BDF8;
}

/* Buttons */
.stButton button {
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.78rem;
    letter-spacing: 0.02em;
    transition: all 0.15s ease;
}
</style>
"""

TERMINAL_CSS = FINTECH_CSS
