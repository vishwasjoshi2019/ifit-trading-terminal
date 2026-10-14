from __future__ import annotations
import streamlit as st
from engines.mutual_funds_intelligence_engine import (
    build_mf_universe,mf_intelligence_summary,mf_decision_snapshot,apply_mf_filters,
    rank_mf,available_mf_categories,available_mf_asset_classes,available_mf_amcs,available_mf_signals)

def render_mutual_funds_intelligence(ctx=None):
    st.markdown("## MUTUAL FUNDS INTELLIGENCE")
    st.caption("Fund intelligence, screening, performance, risk, flows and decision context. Prototype data is simulated/proxy unless an authorized live source is connected.")
    df=build_mf_universe(); s=mf_intelligence_summary(df)
    c=st.columns(6)
    c[0].metric("FUNDS",s["Funds"]); c[1].metric("MF SCORE",f"{s['Average Intelligence Score']:.2f}")
    flow_value = next(v for k, v in s.items() if "Average Flow" in k)
    c[3].metric("AVG FLOW", f"₹{flow_value:,.1f} Cr")
    c[4].metric("BULLISH",s["Bullish"]); c[5].metric("SIGNAL",s["Signal"])
    selected = str(getattr(ctx, "subview", "Overview")).strip() if ctx is not None else "Overview"
    if selected == "Overview":
        st.markdown("### Mutual Fund Universe")
        aum_col = next(c for c in df.columns if c.startswith("AUM"))
        out = df[["Fund","Category","Asset Class","AMC","MF Intelligence Score","Signal","1Y Return %","3Y Return %","Volatility %",aum_col]].sort_values("MF Intelligence Score", ascending=False)
        st.dataframe(out, use_container_width=True, hide_index=True)
        st.info("Simulation/proxy disclosure: returns, AUM, flows and scores are generated prototype values until authorized live mutual-fund data is connected.")
    elif selected == "Intelligence":
        st.markdown("### Fund Intelligence")
        st.dataframe(rank_mf(df)[["Fund","Category","MF Intelligence Score","Consistency Score","Alpha %","Sharpe","Expense Ratio %","Max Drawdown %","Signal"]],use_container_width=True,hide_index=True)
    elif selected == "Screener":
        st.markdown("### Mutual Fund Screener")
        a,b,d=st.columns(3)
        cats=a.multiselect("Category",available_mf_categories(),key="ifit_mf_categories")
        assets=b.multiselect("Asset Class",available_mf_asset_classes(),key="ifit_mf_asset_classes")
        amcs=d.multiselect("AMC",available_mf_amcs(),key="ifit_mf_amcs")
        e,f,g=st.columns(3)
        sig=e.multiselect("Signal",available_mf_signals(),key="ifit_mf_signals")
        score=f.slider("Min Intelligence Score",0.0,95.0,0.0,1.0,key="ifit_mf_min_score")
        expense=g.slider("Max Expense Ratio %",0.0,3.0,3.0,0.05,key="ifit_mf_max_expense")
        out=apply_mf_filters(df,cats,assets,amcs,sig,score,-999,expense)
        st.caption(f"{len(out)} funds match the current filters.")
        st.dataframe(out.sort_values("MF Intelligence Score",ascending=False),use_container_width=True,hide_index=True)
    elif selected == "Performance & Risk":
        st.markdown("### Performance & Risk")
        st.dataframe(df[["Fund","1Y Return %","3Y Return %","5Y Return %","Volatility %","Max Drawdown %","Sharpe","Expense Ratio %"]].sort_values("3Y Return %",ascending=False),use_container_width=True,hide_index=True)
    elif selected == "Flows":
        st.markdown("### Fund Flows")

        aum_col = next(c for c in df.columns if c.startswith("AUM"))
        flow_col = next(c for c in df.columns if c.startswith("Net Flow"))

        out = df[["Fund", "Category", aum_col, flow_col, "Signal"]].copy()
        out["Flow State"] = out[flow_col].apply(
            lambda x: "INFLOW" if x > 0 else "OUTFLOW"
        )

        st.dataframe(
            out.sort_values(flow_col, ascending=False),
            use_container_width=True,
            hide_index=True,
        )

        st.caption("Flow values are simulated/proxy in V0.1.")

    elif selected == "Decision Intelligence":
        st.markdown("### Mutual Fund Decision Intelligence")
        d=mf_decision_snapshot(df); a,b,c=st.columns(3)
        a.metric("MARKET STATE",d["Market State"]); b.metric("SIGNAL",d["Signal"]); c.metric("CONFIDENCE",d["Confidence"])
        st.info(f"**Thesis:** {d['Thesis']}\n\n**Confirmation:** {d['Confirmation']}\n\n**Risk / Invalidation:** {d['Risk / Invalidation']}")



