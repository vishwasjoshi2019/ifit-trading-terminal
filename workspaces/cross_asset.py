import streamlit as st
from engines.cross_asset_intelligence_engine import (
    build_cross_asset_intelligence_snapshot, cross_asset_summary
)

def _ifit_cross_asset_intelligence_page():
    snapshot = build_cross_asset_intelligence_snapshot()
    summary = cross_asset_summary(snapshot)

    st.markdown("## CROSS-ASSET INTELLIGENCE V0.1")
    st.caption("Simulation / proxy data — Cross-Asset Intelligence")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Cross-Asset Score", summary.get("Cross-Asset Score", 0))
    c2.metric("Risk State", summary.get("Risk State", "N/A"))
    c3.metric("Regime", summary.get("Regime", "N/A"))
    c4.metric("Leader", summary.get("Leader", "N/A"))
    c5.metric("Divergences", summary.get("Divergences", 0))

    st.divider()

    a, b, c, d, e = st.columns(5)
    a.metric("Equity", summary.get("Equity", 0))
    b.metric("Bonds", summary.get("Bonds", 0))
    c.metric("Commodities", summary.get("Commodities", 0))
    d.metric("FX", summary.get("FX", 0))
    e.metric("Crypto", summary.get("Crypto", 0))

    st.markdown("### Cross-Asset Universe")
    universe = snapshot.get("Asset Table", snapshot.get("Universe", []))
    if universe is not None:
        st.dataframe(universe, width="stretch", hide_index=True)

    corr = snapshot.get("Correlation")
    if corr is not None:
        st.markdown("### Cross-Asset Correlation Matrix")
        st.dataframe(corr, width="stretch")

    st.info("Cross-Asset Intelligence combines Equity, Bonds, Credit, Commodities, FX, Volatility, Crypto and Global Equity signals into a unified regime and risk view.")




def render_cross_asset(ctx=None):
    _ifit_cross_asset_intelligence_page()
