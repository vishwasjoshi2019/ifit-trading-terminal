import streamlit as st
import pandas as pd
from engines.gsec_intelligence_engine import (
    build_gsec_intelligence, apply_gsec_intelligence_filters,
    rank_gsec_intelligence, gsec_intelligence_summary, available_gsec_signals
)
from engines.bond_screener_engine import (
    build_bond_screener, apply_bond_screener_filters, rank_bond_screener,
    bond_screener_summary, available_bond_screener_asset_types,
    available_bond_screener_signals, available_bond_screener_ratings
)
from engines.tbill_intelligence_engine import (
    build_tbill_intelligence, apply_tbill_intelligence_filters,
    rank_tbill_intelligence, tbill_intelligence_summary,
    available_tbill_tenors, available_tbill_signals
)
from engines.corporate_bond_intelligence_engine import (
    build_corporate_bond_intelligence, apply_corporate_bond_intelligence_filters,
    rank_corporate_bond_intelligence, corporate_bond_intelligence_summary,
    available_corporate_bond_ratings, available_corporate_issuer_types,
    available_corporate_bond_signals
)
from engines.sdl_intelligence_engine import (
    build_sdl_intelligence, apply_sdl_intelligence_filters,
    rank_sdl_intelligence, sdl_intelligence_summary,
    available_sdl_states, available_sdl_signals
)
from engines.yield_curve_engine import (
    build_yield_curve, yield_curve_summary
)
from engines.bond_intelligence_engine import (
    build_bond_intelligence, apply_bond_intelligence_filters,
    rank_bond_intelligence, bond_intelligence_summary,
    available_bond_asset_types, available_bond_ratings, available_bond_signals
)

def _ifit_v086_gsec_page():
    st.markdown("## G-SEC INTELLIGENCE V0.1")
    st.caption("Indian government securities intelligence — simulation data")

    universe = build_gsec_intelligence()

    st.markdown("### G-Sec Filters")
    f1, f2, f3 = st.columns(3)
    with f1:
        signals = st.multiselect("Signal", available_gsec_signals(), key="ifit_gsec_signals")
    with f2:
        min_ytm = st.number_input("Min YTM %", value=0.0, step=0.25, key="ifit_gsec_min_ytm")
    with f3:
        max_ytm = st.number_input("Max YTM %", value=15.0, step=0.25, key="ifit_gsec_max_ytm")

    f4, f5, f6 = st.columns(3)
    with f4:
        min_duration = st.number_input("Min Duration", value=0.0, step=0.5, key="ifit_gsec_min_duration")
    with f5:
        max_duration = st.number_input("Max Duration", value=100.0, step=0.5, key="ifit_gsec_max_duration")
    with f6:
        min_score = st.number_input("Min Intelligence Score", value=0.0, min_value=0.0, max_value=100.0, step=5.0, key="ifit_gsec_min_score")

    filtered = apply_gsec_intelligence_filters(universe, signals=signals or None, min_ytm=min_ytm, max_ytm=max_ytm, min_duration=min_duration, max_duration=max_duration, min_score=min_score)
    ranked = rank_gsec_intelligence(filtered)
    summary = gsec_intelligence_summary(ranked)

    st.markdown("### G-Sec Intelligence Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("G-Secs", summary["G-Secs"])
    c2.metric("Buy", summary["Buy"])
    c3.metric("Sell", summary["Sell"])
    c4.metric("Average YTM", f'{summary["Average YTM"]:.3f}%')
    c5.metric("Intelligence Score", f'{summary["Average Intelligence Score"]:.2f}')
    st.caption(f'Average Duration: {summary["Average Duration"]:.2f}Y | Average Liquidity: {summary["Average Liquidity"]:.1f} | Signal: {summary["Signal"]}')

    st.markdown("### G-Sec Intelligence Matrix")
    if ranked.empty:
        st.warning("No G-Secs match the selected filters.")
        return

    display_cols = ["Bond", "Maturity Year", "Maturity Years", "Coupon %", "YTM %", "Duration", "Liquidity Score", "Yield Score", "Duration Score", "Relative Value Score", "Curve Position Score", "G-Sec Intelligence Score", "Signal"]
    st.dataframe(ranked[display_cols], width="stretch", hide_index=True)

    st.markdown("### G-Sec Thesis")
    for _, row in ranked.head(5).iterrows():
        st.markdown(f'**{row["Bond"]} — {row["G-Sec Intelligence Score"]:.2f} — {row["Signal"]}**')
        st.caption(row["Thesis"])

    st.info("Simulation data only. Connect an authorized G-Sec market/API data source before using this module for live market decisions.")

def _ifit_v086_bond_screener_page():
    st.markdown("## BOND SCREENER V0.1")
    st.caption("Unified fixed-income discovery across G-Secs, SDLs, Corporate Bonds and T-Bills — simulation data")
    universe = build_bond_screener()

    st.markdown("### Screener Filters")
    f1, f2, f3 = st.columns(3)
    with f1:
        asset_types = st.multiselect("Asset Type", available_bond_screener_asset_types(), key="ifit_bond_screen_asset_types")
    with f2:
        ratings = st.multiselect("Rating", available_bond_screener_ratings(), key="ifit_bond_screen_ratings")
    with f3:
        signals = st.multiselect("Signal", available_bond_screener_signals(), key="ifit_bond_screen_signals")

    f4, f5, f6 = st.columns(3)
    with f4:
        min_maturity = st.number_input("Min Maturity (Years)", value=0.0, min_value=0.0, step=0.5, key="ifit_bond_screen_min_maturity")
    with f5:
        max_maturity = st.number_input("Max Maturity (Years)", value=100.0, min_value=0.0, step=0.5, key="ifit_bond_screen_max_maturity")
    with f6:
        min_score = st.number_input("Min Intelligence Score", value=0.0, min_value=0.0, max_value=100.0, step=5.0, key="ifit_bond_screen_min_score")

    f7, f8, f9 = st.columns(3)
    with f7:
        min_ytm = st.number_input("Min YTM %", value=0.0, step=0.25, key="ifit_bond_screen_min_ytm")
    with f8:
        max_ytm = st.number_input("Max YTM %", value=20.0, step=0.25, key="ifit_bond_screen_max_ytm")
    with f9:
        max_duration = st.number_input("Max Duration", value=100.0, min_value=0.0, step=0.5, key="ifit_bond_screen_max_duration")

    filtered = apply_bond_screener_filters(universe, asset_types=asset_types or None, ratings=ratings or None, signals=signals or None, min_maturity=min_maturity, max_maturity=max_maturity, min_ytm=min_ytm, max_ytm=max_ytm, max_duration=max_duration, min_score=min_score)
    ranked = rank_bond_screener(filtered)
    summary = bond_screener_summary(ranked)

    st.markdown("### Bond Screener Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Instruments", summary["Instruments"])
    c2.metric("Asset Types", summary["Asset Types"])
    c3.metric("Buy", summary["Buy"])
    c4.metric("Average YTM", f'{summary["Average YTM"]:.3f}%')
    c5.metric("Average Score", f'{summary["Average Score"]:.2f}')
    st.caption(f'Average Duration: {summary["Average Duration"]:.2f}Y | Sell: {summary["Sell"]}')

    st.markdown("### Unified Bond Intelligence Matrix")
    if ranked.empty:
        st.warning("No instruments match the selected screener filters.")
        return
    display_cols = ["Instrument", "Asset Type", "Rating", "Issuer / State", "Maturity Year", "Maturity Years", "YTM %", "Duration", "Spread bp", "Liquidity Score", "Intelligence Score", "Signal"]
    st.dataframe(ranked[display_cols], width="stretch", hide_index=True)

    st.markdown("### Top Bond Opportunities")
    for _, row in ranked.head(5).iterrows():
        st.markdown(f'**{row["Instrument"]} — {row["Intelligence Score"]:.2f} — {row["Signal"]}**')
        st.caption(str(row["Thesis"]))

    st.info("Simulation data only. Connect authorized fixed-income market/API data sources before using this screener for live market decisions.")

def _ifit_v086_tbill_page():
    st.markdown("## T-BILL INTELLIGENCE V0.1")
    st.caption("Indian Treasury Bill intelligence — simulation data")
    universe = build_tbill_intelligence()

    st.markdown("### T-Bill Filters")
    f1, f2, f3 = st.columns(3)
    with f1:
        tenors = st.multiselect("Tenor (Days)", available_tbill_tenors(), key="ifit_tbill_tenors")
    with f2:
        signals = st.multiselect("Signal", available_tbill_signals(), key="ifit_tbill_signals")
    with f3:
        min_score = st.number_input("Min Intelligence Score", value=0.0, min_value=0.0, max_value=100.0, step=5.0, key="ifit_tbill_min_score")

    f4, f5 = st.columns(2)
    with f4:
        min_ytm = st.number_input("Min YTM %", value=0.0, step=0.25, key="ifit_tbill_min_ytm")
    with f5:
        max_ytm = st.number_input("Max YTM %", value=15.0, step=0.25, key="ifit_tbill_max_ytm")

    filtered = apply_tbill_intelligence_filters(universe, tenors=tenors or None, signals=signals or None, min_ytm=min_ytm, max_ytm=max_ytm, min_score=min_score)
    ranked = rank_tbill_intelligence(filtered)
    summary = tbill_intelligence_summary(ranked)

    st.markdown("### T-Bill Intelligence Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("T-Bills", summary["T-Bills"])
    c2.metric("Buy", summary["Buy"])
    c3.metric("Sell", summary["Sell"])
    c4.metric("Average YTM", f'{summary["Average YTM"]:.3f}%')
    c5.metric("Intelligence Score", f'{summary["Average Intelligence Score"]:.2f}')
    st.caption(f'Average Duration: {summary["Average Duration"]:.2f}Y | Average Liquidity: {summary["Average Liquidity"]:.1f} | Signal: {summary["Signal"]}')

    st.markdown("### T-Bill Intelligence Matrix")
    if ranked.empty:
        st.warning("No T-Bills match the selected filters.")
        return
    display_cols = ["T-Bill", "Tenor Days", "Maturity Years", "Coupon Equivalent %", "YTM %", "Duration", "Implied Discount Price", "Liquidity Score", "Yield Score", "Maturity Score", "Relative Value Score", "Safety Score", "T-Bill Intelligence Score", "Signal"]
    st.dataframe(ranked[display_cols], width="stretch", hide_index=True)

    st.markdown("### T-Bill Thesis")
    for _, row in ranked.head(5).iterrows():
        st.markdown(f'**{row["T-Bill"]} — {row["T-Bill Intelligence Score"]:.2f} — {row["Signal"]}**')
        st.caption(row["Thesis"])
    st.info("Simulation data only. Connect an authorized T-Bill market/API data source before using this module for live market decisions.")

def _ifit_v086_corporate_bond_page():
    st.markdown("## CORPORATE BOND INTELLIGENCE V0.1")
    st.caption("Indian corporate fixed-income intelligence — simulation data")
    universe = build_corporate_bond_intelligence()

    st.markdown("### Corporate Bond Filters")
    f1, f2, f3 = st.columns(3)
    with f1:
        ratings = st.multiselect("Rating", available_corporate_bond_ratings(), key="ifit_corp_ratings")
    with f2:
        issuer_types = st.multiselect("Issuer Type", available_corporate_issuer_types(), key="ifit_corp_issuer_types")
    with f3:
        signals = st.multiselect("Signal", available_corporate_bond_signals(), key="ifit_corp_signals")

    f4, f5, f6 = st.columns(3)
    with f4:
        min_ytm = st.number_input("Min YTM %", value=0.0, step=0.25, key="ifit_corp_min_ytm")
    with f5:
        max_ytm = st.number_input("Max YTM %", value=20.0, step=0.25, key="ifit_corp_max_ytm")
    with f6:
        min_score = st.number_input("Min Intelligence Score", value=0.0, min_value=0.0, max_value=100.0, step=5.0, key="ifit_corp_min_score")

    f7, f8 = st.columns(2)
    with f7:
        min_spread = st.number_input("Min Credit Spread bp", value=-100.0, step=25.0, key="ifit_corp_min_spread")
    with f8:
        max_spread = st.number_input("Max Credit Spread bp", value=2000.0, step=25.0, key="ifit_corp_max_spread")

    filtered = apply_corporate_bond_intelligence_filters(universe, ratings=ratings or None, issuer_types=issuer_types or None, signals=signals or None, min_ytm=min_ytm, max_ytm=max_ytm, min_spread=min_spread, max_spread=max_spread, min_score=min_score)
    ranked = rank_corporate_bond_intelligence(filtered)
    summary = corporate_bond_intelligence_summary(ranked)

    st.markdown("### Corporate Bond Intelligence Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Corporate Bonds", summary["Corporate Bonds"])
    c2.metric("Ratings", summary["Ratings"])
    c3.metric("Buy", summary["Buy"])
    c4.metric("Average YTM", f'{summary["Average YTM"]:.3f}%')
    c5.metric("Intelligence Score", f'{summary["Average Intelligence Score"]:.2f}')
    st.caption(f'Average Duration: {summary["Average Duration"]:.2f}Y | Average Spread: {summary["Average Spread"]:.1f} bp | Signal: {summary["Signal"]}')

    st.markdown("### Corporate Bond Intelligence Matrix")
    if ranked.empty:
        st.warning("No corporate bonds match the selected filters.")
        return
    display_cols = ["Bond", "Rating", "Issuer Type", "Maturity Year", "Coupon %", "YTM %", "Duration", "Credit Spread bp", "Liquidity Score", "Yield Score", "Credit Score", "Duration Score", "Spread Score", "Relative Value Score", "Corporate Bond Intelligence Score", "Signal"]
    st.dataframe(ranked[display_cols], width="stretch", hide_index=True)

    st.markdown("### Corporate Bond Thesis")
    for _, row in ranked.head(5).iterrows():
        st.markdown(f'**{row["Bond"]} — {row["Corporate Bond Intelligence Score"]:.2f} — {row["Signal"]}**')
        st.caption(row["Thesis"])
    st.info("Simulation data only. Connect an authorized corporate-bond market/API data source before using this module for live market decisions.")

def _ifit_v086_sdl_page():
    st.markdown("## SDL INTELLIGENCE V0.1")
    st.caption("State Development Loan intelligence — simulation data")
    universe = build_sdl_intelligence()

    st.markdown("### SDL Filters")
    f1, f2, f3 = st.columns(3)
    with f1:
        states = st.multiselect("State", available_sdl_states(), key="ifit_sdl_states")
    with f2:
        signals = st.multiselect("Signal", available_sdl_signals(), key="ifit_sdl_signals")
    with f3:
        min_score = st.number_input("Min Intelligence Score", value=0.0, min_value=0.0, max_value=100.0, step=5.0, key="ifit_sdl_min_score")

    f4, f5, f6 = st.columns(3)
    with f4:
        min_ytm = st.number_input("Min YTM %", value=0.0, step=0.25, key="ifit_sdl_min_ytm")
    with f5:
        max_ytm = st.number_input("Max YTM %", value=15.0, step=0.25, key="ifit_sdl_max_ytm")
    with f6:
        max_duration = st.number_input("Max Duration", value=100.0, min_value=0.0, step=0.5, key="ifit_sdl_max_duration")

    filtered = apply_sdl_intelligence_filters(universe, states=states or None, signals=signals or None, min_ytm=min_ytm, max_ytm=max_ytm, max_duration=max_duration, min_score=min_score)
    ranked = rank_sdl_intelligence(filtered)
    summary = sdl_intelligence_summary(ranked)

    st.markdown("### SDL Intelligence Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("SDLs", summary["SDLs"])
    c2.metric("States", summary["States"])
    c3.metric("Buy", summary["Buy"])
    c4.metric("Average YTM", f'{summary["Average YTM"]:.3f}%')
    c5.metric("Intelligence Score", f'{summary["Average Intelligence Score"]:.2f}')
    st.caption(f'Average Duration: {summary["Average Duration"]:.2f}Y | Average Spread: {summary["Average Spread"]:.1f} bp | Signal: {summary["Signal"]}')

    st.markdown("### SDL Intelligence Matrix")
    if ranked.empty:
        st.warning("No SDLs match the selected filters.")
        return
    display_cols = ["Bond", "State", "Maturity Year", "Coupon %", "YTM %", "Duration", "Spread to G-Sec bp", "Liquidity Score", "Yield Score", "Duration Score", "Spread Score", "Relative Value Score", "SDL Intelligence Score", "Signal"]
    st.dataframe(ranked[display_cols], width="stretch", hide_index=True)

    st.markdown("### SDL Thesis")
    for _, row in ranked.head(5).iterrows():
        st.markdown(f'**{row["Bond"]} — {row["SDL Intelligence Score"]:.2f} — {row["Signal"]}**')
        st.caption(row["Thesis"])
    st.info("Simulation data only. Connect an authorized SDL market/API data source before using this module for live market decisions.")

def _ifit_v086_yield_curve_page():
    st.markdown("## YIELD CURVE INTELLIGENCE V0.1")
    st.caption("Simulation-first sovereign term-structure intelligence")
    df = build_yield_curve()
    summary = yield_curve_summary(df)

    st.markdown("### Curve Snapshot")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("2Y–10Y Spread", f"{summary['2Y-10Y Spread bp']:.1f} bp")
    c2.metric("3M–10Y Spread", f"{summary['3M-10Y Spread bp']:.1f} bp")
    c3.metric("Curve Shape", summary["Curve Shape"])
    c4.metric("Curve Regime", summary["Curve Regime"])

    st.markdown("### Yield Curve")
    chart_df = df[["Maturity Years", "YTM %"]].set_index("Maturity Years")
    st.line_chart(chart_df, height=320)

    st.markdown("### Curve Intelligence")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Average YTM", f"{summary['Average YTM']:.3f}%")
    c2.metric("5Y–10Y Spread", f"{summary['5Y-10Y Spread bp']:.1f} bp")
    c3.metric("Curve Score", f"{summary['Curve Score']:.1f}")
    c4.metric("Signal", summary["Signal"])

    st.markdown("### Maturity Filter")
    min_m, max_m = st.slider("Maturity (Years)", 0.0, 30.0, (0.0, 30.0), 0.25, key="ifit_yield_curve_maturity")
    filtered = apply_yield_curve_filters(df, min_m, max_m)

    st.markdown("### Yield Curve Matrix")
    display_cols = ["Tenor", "Maturity Years", "YTM %", "Yield Change bp", "Duration", "Slope from 3M bp", "Curve Curvature bp"]
    st.dataframe(filtered[display_cols], width="stretch", hide_index=True)

    st.markdown("### Curve Interpretation")
    st.write(f"**Shape:** {summary['Curve Shape']}")
    st.write(f"**Regime:** {summary['Curve Regime']}")
    st.write(f"**Signal:** {summary['Signal']}")
    st.info("Simulation data only. Connect an authorized bond-market/API data source before using this module for live market decisions.")


def _ifit_v086_bond_overview_page():
    st.markdown("## BOND OVERVIEW V0.1")
    st.caption("Unified Indian fixed-income dashboard — simulation data")

    bonds = build_bond_intelligence()
    gsecs = build_gsec_intelligence()
    sdls = build_sdl_intelligence()
    corporates = build_corporate_bond_intelligence()
    tbills = build_tbill_intelligence()
    screener = build_bond_screener()
    curve = build_yield_curve()
    curve_summary = yield_curve_summary(curve)

    st.markdown("### Fixed-Income Universe")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Instruments", len(screener))
    c2.metric("G-Secs", len(gsecs))
    c3.metric("SDLs", len(sdls))
    c4.metric("Corporate Bonds", len(corporates))
    c5.metric("T-Bills", len(tbills))

    st.markdown("### Market Snapshot")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Average YTM", f'{screener["YTM %"].mean():.3f}%')
    c2.metric("Average Duration", f'{screener["Duration"].mean():.2f}Y')
    c3.metric("2Y–10Y Spread", f'{curve_summary["2Y-10Y Spread bp"]:.1f} bp')
    c4.metric("Curve Shape", curve_summary["Curve Shape"])
    c5.metric("Curve Regime", curve_summary["Curve Regime"])

    st.markdown("### Yield Curve")
    chart_df = curve[["Maturity Years", "YTM %"]].set_index("Maturity Years")
    st.line_chart(chart_df, height=280)

    st.markdown("### Segment Intelligence")
    segments = pd.DataFrame([
        {"Segment": "G-Secs", "Instruments": len(gsecs), "Average YTM %": gsecs["YTM %"].mean(), "Average Score": gsecs["G-Sec Intelligence Score"].mean()},
        {"Segment": "SDLs", "Instruments": len(sdls), "Average YTM %": sdls["YTM %"].mean(), "Average Score": sdls["SDL Intelligence Score"].mean()},
        {"Segment": "Corporate Bonds", "Instruments": len(corporates), "Average YTM %": corporates["YTM %"].mean(), "Average Score": corporates["Corporate Bond Intelligence Score"].mean()},
        {"Segment": "T-Bills", "Instruments": len(tbills), "Average YTM %": tbills["YTM %"].mean(), "Average Score": tbills["T-Bill Intelligence Score"].mean()},
    ])
    segments["Average YTM %"] = segments["Average YTM %"].round(3)
    segments["Average Score"] = segments["Average Score"].round(2)
    st.dataframe(segments, width="stretch", hide_index=True)

    st.markdown("### Top Fixed-Income Intelligence")
    top = rank_bond_screener(screener).head(10)
    st.dataframe(top[["Instrument", "Asset Type", "Rating", "YTM %", "Duration", "Spread bp", "Liquidity Score", "Intelligence Score", "Signal"]], width="stretch", hide_index=True)

    st.markdown("### Bond Intelligence Distribution")
    dist = screener["Signal"].value_counts().reindex(available_bond_screener_signals(), fill_value=0)
    st.bar_chart(dist, height=220)

    st.markdown("### Bond Workspace Status")
    status = pd.DataFrame([
        {"Module": "Bond Intelligence", "Status": "ACTIVE"},
        {"Module": "Yield Curve", "Status": "ACTIVE"},
        {"Module": "G-Secs", "Status": "ACTIVE"},
        {"Module": "SDLs", "Status": "ACTIVE"},
        {"Module": "Corporate Bonds", "Status": "ACTIVE"},
        {"Module": "T-Bills", "Status": "ACTIVE"},
        {"Module": "Bond Screener", "Status": "ACTIVE"},
    ])
    st.dataframe(status, width="stretch", hide_index=True)
    st.info("Simulation data only. Connect authorized fixed-income market/API sources before using this workspace for live market decisions.")

def _ifit_v086_bond_page():
    subview = st.session_state.get("ifit_v082_subview", "Overview")
    st.markdown("## BONDS / FIXED INCOME")
    st.caption("Indian fixed-income intelligence — simulation data until an authorized live bond feed is connected.")

    if subview == "Overview":
        _ifit_v086_bond_overview_page()
        return

    if subview == "G-Secs":
        _ifit_v086_gsec_page()
        return

    if subview == "SDLs":
        _ifit_v086_sdl_page()
        return

    if subview == "Corporate Bonds":
        _ifit_v086_corporate_bond_page()
        return

    if subview == "T-Bills":
        _ifit_v086_tbill_page()
        return

    if subview == "Bond Screener":
        _ifit_v086_bond_screener_page()
        return

    if subview == "Yield Curve":
        _ifit_v086_yield_curve_page()
        return

    if subview != "Intelligence":
        st.info(f"Bond workspace: {subview}. Bond Intelligence V0.1 is currently available under the Intelligence subview.")
        return

    st.markdown("### Bond Intelligence V0.1")
    st.caption("Yield, duration, credit, liquidity and relative-value intelligence across Indian fixed income.")
    universe = build_bond_intelligence()

    st.markdown("### Intelligence Filters")
    f1, f2, f3 = st.columns(3)
    with f1:
        asset_types = st.multiselect("Asset Type", available_bond_asset_types(), key="ifit_bond_asset_types")
    with f2:
        ratings = st.multiselect("Rating", available_bond_ratings(), key="ifit_bond_ratings")
    with f3:
        signals = st.multiselect("Signal", available_bond_signals(), key="ifit_bond_signals")

    f4, f5, f6 = st.columns(3)
    with f4:
        min_ytm = st.number_input("Min YTM %", value=0.0, step=0.25, key="ifit_bond_min_ytm")
    with f5:
        max_ytm = st.number_input("Max YTM %", value=15.0, step=0.25, key="ifit_bond_max_ytm")
    with f6:
        min_score = st.number_input("Min Intelligence Score", value=0.0, min_value=0.0, max_value=100.0, step=5.0, key="ifit_bond_min_score")

    filtered = apply_bond_intelligence_filters(universe, asset_types=asset_types or None, ratings=ratings or None, signals=signals or None, min_ytm=min_ytm, max_ytm=max_ytm, min_score=min_score)
    ranked = rank_bond_intelligence(filtered, ascending=False)
    summary = bond_intelligence_summary(ranked)

    st.markdown("### Intelligence Summary")
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Bonds", summary["Bonds"])
    s2.metric("Buy", summary["Buy"])
    s3.metric("Sell", summary["Sell"])
    s4.metric("Average YTM", f'{summary["Average YTM"]:.3f}%')
    s5.metric("Intelligence Score", f'{summary["Average Intelligence Score"]:.2f}')
    st.caption(f'Average Duration: {summary["Average Duration"]:.2f}Y | Average Spread: {summary["Average Spread"]:.3f}% | Signal: {summary["Signal"]}')

    st.markdown("### Bond Intelligence Matrix")
    if ranked.empty:
        st.warning("No bonds match the selected intelligence filters.")
        return
    display_cols = ["Bond", "Asset Type", "Rating", "YTM %", "Yield Change bp", "Duration", "Credit Spread %", "Liquidity Score", "Relative Value Score", "Bond Intelligence Score", "Signal"]
    st.dataframe(ranked[display_cols], width="stretch", hide_index=True)

    st.markdown("### Bond Thesis")
    for _, row in ranked.head(5).iterrows():
        st.markdown(f'**{row["Bond"]} — {row["Bond Intelligence Score"]:.2f} — {row["Signal"]}**')
        st.caption(row["Thesis"])
    st.info("Simulation data only. Connect an authorized bond-market/API data source before using this module for live market decisions.")




def render_bonds(ctx=None):
    _ifit_v086_bond_page()
