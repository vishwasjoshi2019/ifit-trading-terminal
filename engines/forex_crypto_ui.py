import streamlit as st

from engines.forex_intelligence_engine import (
    build_forex_snapshot, apply_forex_filters, rank_forex,
    forex_intelligence_summary, available_forex_groups,
    available_forex_signals, forex_decision_snapshot,
)
from engines.crypto_intelligence_engine import (
    build_crypto_snapshot, apply_crypto_filters, rank_crypto,
    crypto_intelligence_summary, available_crypto_signals,
    available_crypto_volatility_regimes, crypto_decision_snapshot,
)


def _fc_metric_row(summary, crypto=False):
    if crypto:
        labels = [
            ("Assets", summary.get("Assets", 0)),
            ("Top Asset", summary.get("Top Asset", "N/A")),
            ("Bottom Asset", summary.get("Bottom Asset", "N/A")),
            ("Avg Funding", summary.get("Average Funding", 0)),
            ("Avg OI Change", summary.get("Average OI Change", 0)),
            ("Signal", summary.get("Signal", "N/A")),
        ]
    else:
        labels = [
            ("Pairs", summary.get("Pairs", 0)),
            ("Top Pair", summary.get("Top Pair", "N/A")),
            ("Bottom Pair", summary.get("Bottom Pair", "N/A")),
            ("Avg Volatility", summary.get("Average Volatility", 0)),
            ("Avg Momentum", summary.get("Average Momentum", 0)),
            ("Signal", summary.get("Signal", "N/A")),
        ]
    cols = st.columns(6)
    for col, (label, value) in zip(cols, labels):
        col.metric(label, value)


def _forex_table(df):
    preferred = [
        "Symbol", "Pair", "Group", "Price", "1D Return %",
        "Momentum", "Liquidity", "Volatility", "Volatility Score",
        "Forex Intelligence Score", "Signal", "Forward Bias",
    ]
    cols = [c for c in preferred if c in df.columns]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)


def _crypto_table(df):
    preferred = [
        "Symbol", "Asset", "Price", "1D Return %",
        "Open Interest", "OI Change %", "Funding", "Basis",
        "Volatility", "Crypto Intelligence Score", "Volatility Regime",
        "Signal", "Liquidation Risk",
    ]
    cols = [c for c in preferred if c in df.columns]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)


def _ifit_forex_page(ctx):
    snapshot = build_forex_snapshot()
    universe = snapshot["Universe"]
    summary = snapshot["Summary"]
    view = getattr(ctx, "subview", "Overview") or "Overview"

    st.markdown("## FOREX INTELLIGENCE V0.1")
    st.caption("Simulation / proxy data — Forex Intelligence")

    if view == "Overview":
        _fc_metric_row({
            **summary,
            "Top Pair": snapshot.get("Top Pair", "N/A"),
            "Bottom Pair": snapshot.get("Bottom Pair", "N/A"),
        })
        st.divider()
        st.markdown("### Forex Universe")
        _forex_table(universe)
        st.markdown("### FX Correlation Matrix")
        st.dataframe(snapshot["Correlation"], use_container_width=True)

    elif view == "Intelligence":
        st.markdown("### Currency Intelligence Ranking")
        ranked = rank_forex(universe.copy())
        _forex_table(ranked)
        st.markdown("### Intelligence Distribution")
        st.bar_chart(ranked.set_index("Symbol")["Forex Intelligence Score"])

    elif view == "Screener":
        st.markdown("### Forex Screener")
        c1, c2, c3 = st.columns(3)
        groups = c1.multiselect("Group", available_forex_groups())
        signals = c2.multiselect("Signal", available_forex_signals())
        min_score = c3.slider("Minimum Intelligence Score", 0.0, 100.0, 0.0, 1.0)
        filtered = apply_forex_filters(
            universe.copy(),
            groups=groups or None,
            signals=signals or None,
            min_score=min_score,
        )
        _forex_table(rank_forex(filtered))

    elif view == "Derivatives":
        st.markdown("### FX Derivatives Intelligence")
        cols = [c for c in [
            "Symbol", "Pair", "Group", "Price", "Momentum",
            "Liquidity", "Forward Bias", "Forex Intelligence Score", "Signal",
        ] if c in universe.columns]
        st.dataframe(universe[cols], use_container_width=True, hide_index=True)
        st.info("Prototype derivatives view combines forward bias, momentum, liquidity and intelligence scoring. Production deployment requires authorized live FX/derivatives data.")

    elif view == "Volatility":
        st.markdown("### FX Volatility Intelligence")
        cols = [c for c in [
            "Symbol", "Pair", "Price", "Volatility",
            "Volatility Score", "Momentum", "Forex Intelligence Score", "Signal",
        ] if c in universe.columns]
        st.dataframe(universe[cols].sort_values("Volatility Score", ascending=False), use_container_width=True, hide_index=True)

    elif view == "Decision Intelligence":
        decision = forex_decision_snapshot(universe)
        st.markdown("### Forex Decision Intelligence")
        c1, c2, c3 = st.columns(3)
        c1.metric("Market State", decision.get("Market State", "N/A"))
        c2.metric("Signal", decision.get("Signal", "N/A"))
        c3.metric("Confidence", f'{decision.get("Confidence", 0):.1f}')
        st.markdown("### Decision Thesis")
        st.info(decision.get("Thesis", "No decision thesis available."))
        st.markdown("### Confirmation")
        st.write(decision.get("Confirmation", "No confirmation available."))
        st.markdown("### Risk / Invalidation")
        st.warning(decision.get("Risk / Invalidation", "No risk framework available."))

    st.caption("IFIT Forex Intelligence V0.1 — prototype simulation / proxy data.")


def _ifit_crypto_page(ctx):
    snapshot = build_crypto_snapshot()
    universe = snapshot["Universe"]
    summary = snapshot["Summary"]
    view = getattr(ctx, "subview", "Overview") or "Overview"

    st.markdown("## CRYPTO INTELLIGENCE V0.1")
    st.caption("Simulation / proxy data — Crypto Intelligence")

    if view == "Overview":
        _fc_metric_row({
            **summary,
            "Top Asset": snapshot.get("Top Asset", "N/A"),
            "Bottom Asset": snapshot.get("Bottom Asset", "N/A"),
        }, crypto=True)
        st.divider()
        st.markdown("### Crypto Universe")
        _crypto_table(universe)
        st.markdown("### Crypto Correlation Matrix")
        st.dataframe(snapshot["Correlation"], use_container_width=True)

    elif view == "Intelligence":
        st.markdown("### Digital Asset Intelligence Ranking")
        ranked = rank_crypto(universe.copy())
        _crypto_table(ranked)
        st.markdown("### Intelligence Distribution")
        st.bar_chart(ranked.set_index("Symbol")["Crypto Intelligence Score"])

    elif view == "Screener":
        st.markdown("### Crypto Screener")
        c1, c2, c3, c4 = st.columns(4)
        signals = c1.multiselect("Signal", available_crypto_signals())
        regimes = c2.multiselect("Volatility Regime", available_crypto_volatility_regimes())
        min_score = c3.slider("Minimum Intelligence Score", 0.0, 100.0, 0.0, 1.0)
        min_oi = c4.number_input("Minimum OI Change %", value=-999.0, step=1.0)
        filtered = apply_crypto_filters(
            universe.copy(),
            signals=signals or None,
            vol_regimes=regimes or None,
            min_score=min_score,
            min_oi_change=min_oi,
        )
        _crypto_table(rank_crypto(filtered))

    elif view == "Derivatives":
        st.markdown("### Crypto Derivatives Intelligence")
        cols = [c for c in [
            "Symbol", "Asset", "Price", "Open Interest",
            "OI Change %", "Funding", "Basis", "Liquidation Risk",
            "Crypto Intelligence Score", "Signal",
        ] if c in universe.columns]
        st.dataframe(universe[cols], use_container_width=True, hide_index=True)
        st.info("Prototype derivatives view combines open interest, funding, basis and liquidation-risk signals. Production deployment requires authorized exchange feeds and derivatives data.")

    elif view == "Volatility":
        st.markdown("### Crypto Volatility Intelligence")
        cols = [c for c in [
            "Symbol", "Asset", "Price", "Volatility",
            "Volatility Regime", "Liquidation Risk",
            "Crypto Intelligence Score", "Signal",
        ] if c in universe.columns]
        st.dataframe(universe[cols].sort_values("Crypto Intelligence Score", ascending=False), use_container_width=True, hide_index=True)

    elif view == "Decision Intelligence":
        decision = crypto_decision_snapshot(universe)
        st.markdown("### Crypto Decision Intelligence")
        c1, c2, c3 = st.columns(3)
        c1.metric("Market State", decision.get("Market State", "N/A"))
        c2.metric("Signal", decision.get("Signal", "N/A"))
        c3.metric("Confidence", f'{decision.get("Confidence", 0):.1f}')
        st.markdown("### Decision Thesis")
        st.info(decision.get("Thesis", "No decision thesis available."))
        st.markdown("### Confirmation")
        st.write(decision.get("Confirmation", "No confirmation available."))
        st.markdown("### Risk / Invalidation")
        st.warning(decision.get("Risk / Invalidation", "No risk framework available."))

    st.caption("IFIT Crypto Intelligence V0.1 — prototype simulation / proxy data.")
