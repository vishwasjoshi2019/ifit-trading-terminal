import streamlit as st
from engines.global_markets_intelligence_engine import (
    build_global_markets_intelligence_snapshot, global_markets_summary
)

def _ifit_global_markets_intelligence_page():
    snapshot = build_global_markets_intelligence_snapshot()
    summary = global_markets_summary(snapshot)

    st.markdown("## GLOBAL MARKETS INTELLIGENCE V0.1")
    st.caption("Simulation / proxy data — Global Markets Intelligence")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Global Score", summary.get("Global Score", 0))
    c2.metric("Risk State", summary.get("Risk State", "N/A"))
    c3.metric("Regime", summary.get("Regime", "N/A"))
    c4.metric("Leader", summary.get("Leader", "N/A"))
    c5.metric("Lagging", summary.get("Lagging", "N/A"))
    c6.metric("Divergences", summary.get("Divergences", 0))

    st.divider()

    a, b, c, d, e, f, g = st.columns(7)
    a.metric("India", summary.get("India", 0))
    b.metric("US", summary.get("US", 0))
    c.metric("Asia", summary.get("Asia", 0))
    d.metric("Europe", summary.get("Europe", 0))
    e.metric("Rates", summary.get("Rates", 0))
    f.metric("FX", summary.get("FX", 0))
    g.metric("Commodities", summary.get("Commodities", 0))

    st.markdown("### Global Markets Universe")
    universe = snapshot.get("Asset Table")
    if universe is not None:
        st.dataframe(universe, width="stretch", hide_index=True)

    corr = snapshot.get("Correlation")
    if corr is not None:
        st.markdown("### Global Markets Correlation Matrix")
        st.dataframe(corr, width="stretch")

    st.info("Global Markets Intelligence combines Indian, US, Asian and European equities with rates, FX, commodities and volatility into a unified global regime and risk view. Data shown is simulation / proxy data for the current prototype.")


def render_global_markets(ctx=None):
    _ifit_global_markets_intelligence_page()
