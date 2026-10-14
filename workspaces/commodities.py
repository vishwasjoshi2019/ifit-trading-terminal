import streamlit as st
import pandas as pd
from engines.mcx_commodities_engine import (
    build_commodities_universe, apply_commodity_filters, rank_commodities,
    commodity_summary, available_commodities, available_commodity_signals,
    available_term_structures, available_roll_behaviours
)
from engines.mcx_intelligence_engine import (
    build_mcx_intelligence, apply_mcx_intelligence_filters, rank_mcx_intelligence,
    mcx_intelligence_summary, available_mcx_intelligence_commodities,
    available_mcx_intelligence_signals, available_positioning_states,
    available_volatility_regimes, available_mcx_term_structures, available_mcx_roll_behaviours
)

def _ifit_v085_mcx_page():
    subview = st.session_state.get("ifit_v082_subview", "Overview")

    st.markdown("## MCX / COMMODITIES INTELLIGENCE")
    st.caption(
        "Commodity price action, momentum, positioning, volatility, "
        "term structure, basis, roll and cross-commodity intelligence."
    )

    # =============================================================
    # BASE MCX UNIVERSE
    # =============================================================
    df = build_commodities_universe()

    # =============================================================
    # MCX FILTERS
    # =============================================================
    st.markdown("### MCX Filters")

    f1, f2, f3 = st.columns(3)

    with f1:
        selected_commodities = st.multiselect(
            "Commodities",
            available_commodities(df),
            default=[],
            key="ifit_mcx_commodities",
        )

    with f2:
        selected_signals = st.multiselect(
            "Signal",
            available_commodity_signals(),
            default=[],
            key="ifit_mcx_signals",
        )

    with f3:
        min_score = st.slider(
            "Minimum Commodity Score",
            0.0,
            100.0,
            0.0,
            1.0,
            key="ifit_mcx_min_score",
        )

    f4, f5, f6 = st.columns(3)

    with f4:
        min_momentum = st.slider(
            "Minimum Momentum Score",
            0.0,
            100.0,
            0.0,
            1.0,
            key="ifit_mcx_min_momentum",
        )

    with f5:
        min_volume_ratio = st.slider(
            "Minimum Volume Ratio",
            0.0,
            3.0,
            0.0,
            0.05,
            key="ifit_mcx_min_volume_ratio",
        )

    with f6:
        max_volatility = st.slider(
            "Max Volatility Percentile",
            0.0,
            100.0,
            100.0,
            1.0,
            key="ifit_mcx_max_volatility",
        )

    f7, f8, f9 = st.columns(3)

    with f7:
        min_oi_change = st.slider(
            "Minimum OI Change %",
            -100.0,
            100.0,
            -100.0,
            1.0,
            key="ifit_mcx_min_oi_change",
        )

    with f8:
        max_oi_change = st.slider(
            "Maximum OI Change %",
            -100.0,
            100.0,
            100.0,
            1.0,
            key="ifit_mcx_max_oi_change",
        )

    with f9:
        selected_term_structure = st.multiselect(
            "Term Structure",
            available_term_structures(),
            default=[],
            key="ifit_mcx_term_structure",
        )

    selected_roll = st.multiselect(
        "Roll Behaviour",
        available_roll_behaviours(),
        default=[],
        key="ifit_mcx_roll_behaviour",
    )

    # =============================================================
    # APPLY BASE MCX FILTERS
    # =============================================================
    filtered = apply_commodity_filters(
        df,
        commodities=selected_commodities,
        signals=selected_signals,
        min_score=min_score,
        min_momentum=min_momentum,
        min_volume_ratio=min_volume_ratio,
        min_oi_change=min_oi_change,
        max_oi_change=max_oi_change,
        max_volatility_percentile=max_volatility,
        term_structure=selected_term_structure,
        roll_behaviour=selected_roll,
    )

    ranked = rank_commodities(
        filtered,
        sort_by="Commodity Score",
        ascending=False,
    )

    summary = commodity_summary(ranked)

    # =============================================================
    # MCX SUBVIEW: COMMODITIES
    # =============================================================
    if subview == "Commodities":
        st.markdown("### Commodity Universe")

        st.dataframe(
            ranked[
                [
                    "Commodity",
                    "Unit",
                    "Price",
                    "Price Change %",
                    "Volume",
                    "Volume Ratio",
                    "Open Interest",
                    "OI Change %",
                    "Commodity Score",
                    "Signal",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
        return

    # =============================================================
    # MCX SUBVIEW: MOMENTUM
    # =============================================================
    if subview == "Momentum":
        st.markdown("### MCX Momentum Intelligence")

        momentum = ranked.sort_values(
            "Momentum Score",
            ascending=False,
        )

        if "Relative Performance %" in momentum.columns:
            momentum_columns = [
                "Commodity",
                "Price Change %",
                "Momentum 1M %",
                "Momentum Score",
                "Trend Strength",
                "Relative Performance %",
            ]
        else:
            momentum_columns = [
                "Commodity",
                "Price Change %",
                "Momentum 1M %",
                "Momentum Score",
                "Trend Strength",
                "Commodity Score",
            ]

        st.dataframe(
            momentum[momentum_columns],
            width="stretch",
            hide_index=True,
        )
        return

    # =============================================================
    # MCX SUBVIEW: POSITIONING
    # =============================================================
    if subview == "Positioning":
        st.markdown("### MCX Positioning Intelligence")

        positioning = ranked.sort_values(
            "Positioning Score",
            ascending=False,
        )

        st.dataframe(
            positioning[
                [
                    "Commodity",
                    "Price Change %",
                    "Open Interest",
                    "OI Change %",
                    "Volume",
                    "Volume Ratio",
                    "Positioning Score",
                    "Signal",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
        return

    # =============================================================
    # MCX SUBVIEW: VOLATILITY
    # =============================================================
    if subview == "Volatility":
        st.markdown("### MCX Volatility Intelligence")

        volatility = ranked.sort_values(
            "Volatility Percentile",
            ascending=False,
        )

        st.dataframe(
            volatility[
                [
                    "Commodity",
                    "Realized Volatility %",
                    "Volatility Percentile",
                    "Front IV %",
                    "Back IV %",
                    "Term Structure",
                    "Liquidity Score",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
        return

    # =============================================================
    # MCX SUBVIEW: TERM STRUCTURE
    # =============================================================
    if subview == "Term Structure":
        st.markdown("### MCX Term Structure Intelligence")

        term = ranked.sort_values(
            "Front IV %",
            ascending=False,
        )

        st.dataframe(
            term[
                [
                    "Commodity",
                    "Front IV %",
                    "Back IV %",
                    "Term Structure",
                    "Realized Volatility %",
                    "Volatility Percentile",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
        return

    # =============================================================
    # MCX SUBVIEW: BASIS & ROLL
    # =============================================================
    if subview == "Basis & Roll":
        st.markdown("### MCX Basis & Roll Intelligence")

        basis_roll = ranked.sort_values(
            "Basis %",
            ascending=False,
        )

        st.dataframe(
            basis_roll[
                [
                    "Commodity",
                    "Price",
                    "Basis %",
                    "Roll Behaviour",
                    "Front IV %",
                    "Back IV %",
                    "Open Interest",
                    "OI Change %",
                ]
            ],
            width="stretch",
            hide_index=True,
        )
        return

    # =============================================================
    # MCX SUBVIEW: INTELLIGENCE V0.2
    # =============================================================
    if subview == "Intelligence":
        st.markdown("### MCX Intelligence V0.2")
        st.caption(
            "Cross-commodity intelligence combining momentum, "
            "price/OI positioning, IV vs realised volatility, "
            "term structure, basis, roll behaviour, liquidity "
            "and cross-asset context."
        )

        intelligence = build_mcx_intelligence()

        # Respect the commodity selection from the existing MCX filters.
        if selected_commodities:
            intelligence = apply_mcx_intelligence_filters(
                intelligence,
                commodities=selected_commodities,
            )

        intelligence = rank_mcx_intelligence(
            intelligence,
            ascending=False,
        )

        intel_summary = mcx_intelligence_summary(
            intelligence
        )

        # ---------------------------------------------------------
        # SUMMARY
        # ---------------------------------------------------------
        st.markdown("### Intelligence Summary")

        i1, i2, i3, i4, i5 = st.columns(5)

        with i1:
            st.metric(
                "Avg Intelligence",
                f'{intel_summary["Average Intelligence Score"]:.2f}',
            )

        with i2:
            st.metric(
                "Bullish",
                intel_summary["Bullish"]
                + intel_summary["Strong Bullish"],
            )

        with i3:
            st.metric(
                "Bearish",
                intel_summary["Bearish"]
                + intel_summary["Strong Bearish"],
            )

        with i4:
            st.metric(
                "IV-RV Spread",
                f'{intel_summary["Average IV-RV Spread"]:.2f}%',
            )

        with i5:
            st.metric(
                "MCX Signal",
                intel_summary["Signal"],
            )

        st.caption(
            f'Avg IV: {intel_summary["Average IV"]:.2f}% • '
            f'Avg RV: {intel_summary["Average RV"]:.2f}% • '
            f'Avg Momentum: {intel_summary["Average Momentum"]:.2f}% • '
            f'Avg OI Change: {intel_summary["Average OI Change"]:.2f}% • '
            f'Avg Liquidity: {intel_summary["Average Liquidity"]:.2f}'
        )

        # ---------------------------------------------------------
        # INTELLIGENCE MATRIX
        # ---------------------------------------------------------
        st.markdown("### Intelligence Matrix")

        if not intelligence.empty:

            intelligence_columns = [
                "Rank",
                "Commodity",
                "MCX Intelligence Score",
                "Signal",
                "Positioning",
                "Positioning Score",
                "Momentum 1M %",
                "Momentum Score",
                "IV %",
                "RV %",
                "IV-RV Spread %",
                "Volatility Regime",
                "Term Structure",
                "Term Structure Signal",
                "Basis %",
                "Basis Signal",
                "Roll Behaviour",
                "Roll Signal",
                "Liquidity Score",
                "Liquidity Regime",
                "Cross-Asset Score",
            ]

            intelligence_columns = [
                col
                for col in intelligence_columns
                if col in intelligence.columns
            ]

            st.dataframe(
                intelligence[intelligence_columns],
                width="stretch",
                hide_index=True,
            )

            # -----------------------------------------------------
            # POSITIONING + VOLATILITY
            # -----------------------------------------------------
            st.markdown("### Positioning & Volatility")

            p1, p2 = st.columns(2)

            with p1:
                st.markdown("**Positioning Intelligence**")

                positioning_view = intelligence[
                    [
                        "Commodity",
                        "Price Change %",
                        "OI Change %",
                        "Positioning",
                        "Positioning Score",
                        "MCX Intelligence Score",
                    ]
                ].sort_values(
                    "Positioning Score",
                    ascending=False,
                )

                st.dataframe(
                    positioning_view,
                    width="stretch",
                    hide_index=True,
                )

            with p2:
                st.markdown("**Volatility Intelligence**")

                volatility_view = intelligence[
                    [
                        "Commodity",
                        "IV %",
                        "RV %",
                        "IV-RV Spread %",
                        "Volatility Percentile",
                        "Volatility Regime",
                    ]
                ].sort_values(
                    "Volatility Percentile",
                    ascending=False,
                )

                st.dataframe(
                    volatility_view,
                    width="stretch",
                    hide_index=True,
                )

            # -----------------------------------------------------
            # STRUCTURE
            # -----------------------------------------------------
            st.markdown("### Term Structure, Basis & Roll")

            structure_view = intelligence[
                [
                    "Commodity",
                    "Term Structure",
                    "Term Structure Signal",
                    "Basis %",
                    "Basis Signal",
                    "Roll Behaviour",
                    "Roll Signal",
                ]
            ]

            st.dataframe(
                structure_view,
                width="stretch",
                hide_index=True,
            )

            # -----------------------------------------------------
            # TOP INTELLIGENCE THESIS
            # -----------------------------------------------------
            st.markdown("### Top MCX Intelligence")

            for _, row in intelligence.head(5).iterrows():
                st.markdown(
                    f"**{row['Commodity']} — "
                    f"{row['MCX Intelligence Score']:.2f} — "
                    f"{row['Signal']}**"
                )

                st.caption(
                    row["Thesis"]
                )

        else:
            st.warning(
                "No commodities match the MCX Intelligence universe."
            )

        return

    # =============================================================
    # DEFAULT MCX OVERVIEW
    # =============================================================
    st.markdown("### MCX Intelligence Summary")

    s1, s2, s3, s4, s5 = st.columns(5)

    s1.metric(
        "Commodities",
        summary["Commodities"],
    )

    s2.metric(
        "Bullish Signals",
        summary["Bullish Signals"],
    )

    s3.metric(
        "Bearish Signals",
        summary["Bearish Signals"],
    )

    s4.metric(
        "Avg Momentum",
        f'{summary["Average Momentum"]:.2f}%',
    )

    s5.metric(
        "Avg Commodity Score",
        f'{summary["Average Commodity Score"]:.2f}',
    )

    st.caption(
        f'Current MCX Signal: {summary["Signal"]} • '
        f'Avg Price Change: {summary["Average Price Change"]:.2f}% • '
        f'Avg Volatility: {summary["Average Volatility"]:.2f}% • '
        f'Avg OI Change: {summary["Average OI Change"]:.2f}%'
    )

    # =============================================================
    # RANKED TABLE
    # =============================================================
    st.markdown("### Ranked MCX Commodities")

    display_columns = [
        "Commodity",
        "Unit",
        "Price",
        "Price Change %",
        "Volume",
        "Volume Ratio",
        "Open Interest",
        "OI Change %",
        "Momentum 1M %",
        "Momentum Score",
        "Realized Volatility %",
        "Volatility Percentile",
        "Front IV %",
        "Back IV %",
        "Term Structure",
        "Basis %",
        "Roll Behaviour",
        "Trend Strength",
        "Positioning Score",
        "Liquidity Score",
        "Commodity Score",
        "Signal",
    ]

    display_columns = [
        col
        for col in display_columns
        if col in ranked.columns
    ]

    if not ranked.empty:
        st.dataframe(
            ranked[display_columns],
            width="stretch",
            hide_index=True,
        )
    else:
        st.warning(
            "No commodities match the current filters."
        )

    # =============================================================
    # INTELLIGENCE PANELS
    # =============================================================
    st.markdown("### Commodity Intelligence")

    p1, p2, p3 = st.columns(3)

    with p1:
        st.markdown("**Momentum Leaders**")

        if not ranked.empty:
            momentum = (
                ranked.sort_values(
                    "Momentum Score",
                    ascending=False,
                )[
                    [
                        "Commodity",
                        "Momentum Score",
                        "Momentum 1M %",
                    ]
                ]
                .head(5)
            )

            st.dataframe(
                momentum,
                width="stretch",
                hide_index=True,
            )

    with p2:
        st.markdown("**Positioning Leaders**")

        if not ranked.empty:
            positioning = (
                ranked.sort_values(
                    "Positioning Score",
                    ascending=False,
                )[
                    [
                        "Commodity",
                        "Positioning Score",
                        "OI Change %",
                    ]
                ]
                .head(5)
            )

            st.dataframe(
                positioning,
                width="stretch",
                hide_index=True,
            )

    with p3:
        st.markdown("**Volatility Watch**")

        if not ranked.empty:
            volatility = (
                ranked.sort_values(
                    "Volatility Percentile",
                    ascending=False,
                )[
                    [
                        "Commodity",
                        "Realized Volatility %",
                        "Volatility Percentile",
                        "Term Structure",
                    ]
                ]
                .head(5)
            )

            st.dataframe(
                volatility,
                width="stretch",
                hide_index=True,
            )

    # =============================================================
    # TERM STRUCTURE / ROLL
    # =============================================================
    st.markdown("### Term Structure & Roll")

    if not ranked.empty:
        term_roll = ranked[
            [
                "Commodity",
                "Front IV %",
                "Back IV %",
                "Term Structure",
                "Basis %",
                "Roll Behaviour",
            ]
        ]

        st.dataframe(
            term_roll,
            width="stretch",
            hide_index=True,
        )


def render_commodities(ctx=None):
    _ifit_v085_mcx_page()
