"""IFIT Equities Intelligence Workspace."""
import streamlit as st
import pandas as pd
import numpy as np


def render_equities(ctx=None):
    """Render the Equities fundamentals and valuation workspace."""
    st.markdown("## Equities Intelligence")
    st.caption("Fundamental valuation, balance-sheet quality, capital return metrics, and peer benchmarking.")

    ticker = st.selectbox(
        "Security",
        ["RELIANCE", "HDFCBANK", "TCS", "INFY", "ICICIBANK", "LT"],
        key="ifit_equity_ticker_select"
    )

    data = {
        "RELIANCE": [1510, 24.1, 15.8, 19.4, 0.31, 14.2, 18.6],
        "HDFCBANK": [1840, 19.6, 16.2, 17.1, 0.20, 15.8, 16.9],
        "TCS": [4120, 28.2, 46.0, 51.3, 0.06, 11.4, 22.1],
        "INFY": [1740, 25.4, 31.8, 35.1, 0.08, 12.2, 19.8],
        "ICICIBANK": [1455, 18.4, 17.5, 18.2, 0.12, 14.5, 18.2],
        "LT": [3850, 34.5, 16.1, 18.7, 0.72, 12.8, 14.9],
    }[ticker]

    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    labels = ["Price (₹)", "P/E", "ROE %", "ROCE %", "Debt/Eq", "EPS Gr %", "FCF Yld %"]
    for col, name, val in zip([c1, c2, c3, c4, c5, c6, c7], labels, data):
        col.metric(name, f"{val:,.2f}")

    left, right = st.columns(2)
    with left:
        st.markdown("### Fundamental Diagnostic Map")
        st.dataframe(pd.DataFrame([
            ["Valuation", f"P/E {data[1]:.1f}x"],
            ["Quality", f"ROE {data[2]:.1f}% • ROCE {data[3]:.1f}%"],
            ["Growth", f"EPS Growth {data[5]:.1f}%"],
            ["Balance Sheet", f"Debt/Equity {data[4]:.2f}x"],
            ["Cash Generation", f"FCF Yield {data[6]:.1f}%"],
        ], columns=["Metric Layer", "Current Diagnostic"]), width="stretch", hide_index=True)

    with right:
        st.markdown("### Quantitative Factor Score")
        score = float(np.clip(50 + data[5] * 0.7 + data[2] * 0.5 + data[3] * 0.25 - data[1] * 0.35 - data[4] * 8, 0, 100))
        st.metric("Composite Equity Score", f"{score:.1f}/100")
        st.caption("Weighted factor model across growth, quality, profitability, leverage, and free-cash-flow yield.")
