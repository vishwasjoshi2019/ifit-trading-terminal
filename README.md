# IFIT — Indian Financial Intelligence Terminal 🇮🇳
### Institutional-Grade Multi-Asset Quantitative Research & High-Frequency Execution Terminal

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/vishwasjoshi2019/ifit-trading-terminal)
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=vishwasjoshi2019/ifit-trading-terminal&branch=main&mainModule=app.py)
[![Vercel Live Terminal](https://img.shields.io/badge/Vercel-Live_React_Terminal-black?logo=vercel)](https://ifit-trading-terminal.vercel.app)

---

## 🏛️ System Overview

IFIT is a dual-engine Indian financial terminal modeled after institutional platforms (Bloomberg Terminal, Refinitiv Eikon, and TradingView Pro), combining deep quantitative research with real-time exchange streaming.

```
┌────────────────────────────────────────────────────────┐   ┌────────────────────────────────────────────────────────┐
│   Dual-Engine Architecture                             │   │   16 Institutional Quantitative Workspaces             │
├────────────────────────────────────────────────────────┤   ├────────────────────────────────────────────────────────┤
│ 1. Engine A: 16-Workspace Quant Terminal (Streamlit)   │   │  1. Command Center      9. AI Intelligence             │
│    • In-memory stochastic engines, Black-Scholes, VaR  │   │  2. Markets             10. Bonds / Fixed Income       │
│    • Sovereign G-Sec Yield Curves, Monte Carlo         │   │  3. Equities            11. MCX / Commodities          │
│                                                        │   │  4. Screener            12. Cross-Asset                │
│ 2. Engine B: React 18 Bloomberg Execution (Vite/TS)   │   │  5. Options Matrix      13. Forex (USDINR)             │
│    • TradingView Lightweight Charts Canvas (60 FPS)    │   │  6. Technical Charts    14. Crypto                     │
│    • L2 Depth (5 Bids / 5 Asks), Tick-by-Tick Tape     │   │  7. Portfolio Analytics 15. Global Markets (DXY/US10Y) │
│    • Broker-Agnostic Streaming Backend (FastAPI / WS)  │   │  8. Risk Engine (VaR)   16. Mutual Funds               │
└────────────────────────────────────────────────────────┘   └────────────────────────────────────────────────────────┘
```

---

## 🚀 1-Click Cloud Deployments

### 1. Deploy Quant Trading Terminal to Render (Persistent Docker Container)
Click the badge below to deploy the full 16-workspace Python terminal to Render with automated Docker builds and zero setup:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/vishwasjoshi2019/ifit-trading-terminal)

### 2. Deploy to Streamlit Community Cloud (100% Free Hosting)
Click the badge below to deploy directly to Streamlit Community Cloud:

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=vishwasjoshi2019/ifit-trading-terminal&branch=main&mainModule=app.py)

### 3. Live React Execution Terminal on Vercel
* **URL**: [https://ifit-trading-terminal.vercel.app](https://ifit-trading-terminal.vercel.app)
* High-frequency TradingView candlestick canvas, Level-2 depth book, and trade tape.

---

## 🛠️ Local Setup & Development

### 1. Clone Repository
```bash
git clone https://github.com/vishwasjoshi2019/ifit-trading-terminal.git
cd ifit-trading-terminal
```

### 2. Python Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Launching Engines

#### Launch Complete Quant Research Terminal:
```bash
streamlit run app.py --server.port 8501
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

#### Launch High-Frequency Streaming Backend:
```bash
uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
```
Open [http://localhost:8000](http://localhost:8000) for the compiled React Bloomberg Terminal & WebSocket feed (`ws://localhost:8000/ws/market`).

---

## 🔌 Broker Adapters & Live Feeds

The backend is broker-agnostic (`BaseMarketFeed` interface). Set credentials in your `.env` file:

```env
# Simulation Mode (No broker credentials required)
MARKET_FEED_PROVIDER=SIMULATION

# Live Dhan Feed
DHAN_CLIENT_ID=your_client_id
DHAN_ACCESS_TOKEN=your_token

# Live Zerodha Feed
KITE_API_KEY=your_key
KITE_ACCESS_TOKEN=your_token
```

---

## 🧪 Automated Test Suite

```bash
# Run backend streaming and workspace test suites
python3 -m unittest discover -s tests -p "test_*.py"
```

## 📜 License
MIT License. Built for Indian institutional traders, financial researchers, and quantitative analysts.
