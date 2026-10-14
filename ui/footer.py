"""IFIT Terminal Data Health & System Architecture Footer."""
import streamlit as st
import pandas as pd
from engines.data_health_engine import health_frame, data_quality


def render_terminal_footer(health, snapshot) -> None:
    """Render the data health monitor and system architecture table."""
    st.markdown("---")
    st.markdown("### IFIT Data Health Monitor")
    
    if health is not None:
        st.dataframe(
            health_frame(health).style.format({"Data Age (s)": "{:.2f}", "Latency (ms)": "{:.0f}"}),
            width="stretch",
            hide_index=True
        )
        q = data_quality(snapshot)
        if q["issues"]:
            st.warning(" | ".join(q["issues"]))
        else:
            st.success("Data schema and core market fields passed adapter verification.")
            
    st.markdown("### Terminal Architecture Status")
    status_df = pd.DataFrame([
        ["Command Center", "ACTIVE", "Consolidated executive snapshot + IFIT score + conviction"],
        ["Markets", "ACTIVE", "Market state + breadth + volatility + futures + regime"],
        ["Equities", "ACTIVE", "Fundamentals + valuation + quality + growth + peers"],
        ["Screener", "ACTIVE", "Multi-factor equity, derivatives, market, order flow, & quant screening"],
        ["Cross-Asset", "ACTIVE", "Cross-asset regime intelligence + spillover analysis"],
        ["Global Markets", "ACTIVE", "US, European, Asian equities + global macro & rates"],
        ["Forex", "ACTIVE", "INR currency strength + FX derivatives & volatility"],
        ["Crypto", "ACTIVE", "Digital assets positioning + derivatives + CVD flow"],
        ["Mutual Funds", "ACTIVE", "AMFI mutual fund intelligence + risk-adjusted return screening"],
        ["Options", "ACTIVE", "Chain + Greeks (higher-order) + Heston + Gamma exposure + execution"],
        ["Charts", "ACTIVE", "Interactive TradingView-style candles + footprint + CVD + profile + drawing"],
        ["Portfolio", "ACTIVE", "Holdings + portfolio Greeks + concentration + stress testing"],
        ["Risk Engine", "ACTIVE", "Cross-engine risk drivers + tail diagnostics + scenario PnL"],
        ["AI Intelligence", "ACTIVE", "Grounded explanation + evidence ladder + methodology"],
        ["Bonds / Fixed Income", "ACTIVE", "G-Secs + SDLs + Corporate Bonds + T-Bills + Sovereign Yield Curve"],
        ["MCX / Commodities", "ACTIVE", "Crude, Gold, Silver + term structure + basis & roll intelligence"],
    ], columns=["Terminal Module", "Status", "Primary Capability"])
    st.dataframe(status_df, width="stretch", hide_index=True)
    st.caption("IFIT V0.8.4.1 • Institutional Financial Intelligence Terminal • Production-grade quantitative architecture.")
