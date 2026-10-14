"""IFIT Payoff Charts V0.1 UI."""
import numpy as np
import pandas as pd
import streamlit as st
from engines.payoff_engine import (
    build_default_payoff_legs, strategy_expiry_payoff, strategy_mtm,
    payoff_summary, scenario_grid, payoff_decision_snapshot,
)

def _payoff_spot_grid(spot, width_pct=12.0, points=241):
    lo=max(1.0,float(spot)*(1-width_pct/100.0))
    hi=float(spot)*(1+width_pct/100.0)
    return np.linspace(lo,hi,int(points))

def render_payoff_charts(spot=24782.35, default_days=14):
    st.markdown("---")
    st.markdown("## PAYOFF CHARTS")
    st.caption("Strategy P&L, expiry payoff, MTM and stress scenarios inside Hedging Intelligence.")
    if "ifit_payoff_legs" not in st.session_state:
        st.session_state["ifit_payoff_legs"]=build_default_payoff_legs(spot)
    legs_df=pd.DataFrame(st.session_state["ifit_payoff_legs"])
    with st.expander("Strategy Legs", expanded=True):
        edited=st.data_editor(
            legs_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "Side":st.column_config.SelectboxColumn("Side",options=["BUY","SELL"]),
                "Option":st.column_config.SelectboxColumn("Option",options=["CE","PE"]),
                "Qty":st.column_config.NumberColumn("Qty",min_value=0.0,step=1.0),
                "Multiplier":st.column_config.NumberColumn("Multiplier",min_value=1.0,step=1.0),
                "Strike":st.column_config.NumberColumn("Strike",min_value=1.0,step=50.0),
                "Premium":st.column_config.NumberColumn("Entry Premium",min_value=0.0,step=0.5),
                "IV":st.column_config.NumberColumn("IV %",min_value=0.1,step=0.1),
                "DTE":st.column_config.NumberColumn("DTE",min_value=0.0,step=1.0),
            },
            key="ifit_payoff_editor",
        )
        if st.button("Apply Strategy Legs",key="ifit_payoff_apply"):
            st.session_state["ifit_payoff_legs"]=edited.to_dict("records")
            st.rerun()
    legs=st.session_state["ifit_payoff_legs"]
    width=st.slider("Payoff Price Range ±%",5.0,30.0,12.0,0.5,key="ifit_payoff_width")
    view=st.radio("Payoff View",["Combined","Individual Legs","Expiry + MTM"],horizontal=True,key="ifit_payoff_view")
    dte=st.number_input("Days Passed",0,365,0,1,key="ifit_payoff_days_passed")
    iv_shift=st.number_input("IV Stress (vol pts)",-20.0,20.0,0.0,0.5,key="ifit_payoff_iv_shift")
    rate=st.number_input("Risk-Free Rate %", -5.0,25.0,6.0,0.25,key="ifit_payoff_rate")
    grid=_payoff_spot_grid(spot,width)
    payoff, norm_legs=strategy_expiry_payoff(legs,grid)
    summary=payoff_summary(payoff,spot)
    mtm_total,mtm_legs=strategy_mtm(legs,spot,dte,rate,iv_shift)
    c1,c2,c3,c4,c5=st.columns(5)
    c1.metric("CURRENT SPOT",f"{spot:,.2f}")
    c2.metric("MTM P&L",f"₹{mtm_total:,.0f}")
    c3.metric("MAX PROFIT (GRID)",f"₹{summary['Max Profit (Grid)']:,.0f}")
    c4.metric("MAX LOSS (GRID)",f"₹{summary['Max Loss (Grid)']:,.0f}")
    c5.metric("BREAKEVENS",str(len(summary["Breakevens"])))
    chart_df=payoff.set_index("Spot")
    if view=="Combined":
        st.line_chart(chart_df[["Combined P&L"]],height=460,use_container_width=True)
    elif view=="Individual Legs":
        cols=[c for c in chart_df.columns if c!="Combined P&L"]
        st.line_chart(chart_df[cols],height=460,use_container_width=True)
    else:
        compare=pd.DataFrame({"Expiry P&L":payoff["Combined P&L"].values})
        # Show MTM at each stressed spot with same DTE/IV assumptions.
        compare["MTM P&L"]=[strategy_mtm(legs,float(s),dte,rate,iv_shift)[0] for s in payoff["Spot"]]
        compare.index=payoff["Spot"]
        st.line_chart(compare,height=460,use_container_width=True)
    if summary["Breakevens"]:
        st.info("Breakeven levels: "+", ".join(f"{x:,.2f}" for x in summary["Breakevens"]))
    else:
        st.info("No breakeven crossing on the selected price grid.")
    st.markdown("### Strategy Legs & MTM")
    st.dataframe(mtm_legs.round(2),use_container_width=True,hide_index=True)
    st.markdown("### Scenario Stress Matrix")
    scen=scenario_grid(legs,spot,iv_moves=(-4,0,4),dte_days=(0,1,3,7))
    pivot=scen.pivot_table(index="Spot Shock %",columns="IV Shock pt",values="Approx P&L",aggfunc="mean")
    st.dataframe(pivot.round(0),use_container_width=True)
    decision=payoff_decision_snapshot(summary,scen)
    st.markdown("### Payoff Decision Context")
    a,b,c=st.columns(3)
    a.metric("PROFILE",summary["Profit/Loss Zone"])
    b.metric("BREAKEVEN COUNT",len(summary["Breakevens"]))
    b2= c
    c.metric("GRID RANGE",f"₹{summary['Max Loss (Grid)']:,.0f} → ₹{summary['Max Profit (Grid)']:,.0f}")
    st.info(f'**Thesis:** {decision["Thesis"]}\n\n**Confirmation:** {decision["Confirmation"]}\n\n**Risk / Invalidation:** {decision["Risk / Invalidation"]}')
    st.caption("Simulation/proxy payoff inputs. No order placement. Expiry payoff uses intrinsic value; MTM uses Black-Scholes model pricing.")
