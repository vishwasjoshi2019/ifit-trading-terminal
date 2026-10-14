p = "app.py"

with open(p, encoding="utf-8") as f:
    s = f.read()

start = s.find("def _ifit_v081_options_page():")
end = s.find("\ndef ", start + 10)

assert start >= 0, "Options function not found"
assert end > start, "End of Options function not found"

old = s[start:end]

with open("app.py.bak_before_options_subview_fix", "w", encoding="utf-8") as f:
    f.write(s)

new = '''def _ifit_v081_options_page():
    _ifit_v081_header("Options")
    subview = st.session_state.get("ifit_v082_subview", "Option Chain")

    chain = build_option_chain(spot, days, atm_iv)
    om = calculate_metrics(chain, spot, days, atm_iv)

    if subview == "Greeks":
        _ifit_v062_render(chain, spot, days, atm_iv)
        return

    if subview == "Volatility":
        _ifit_v063_render(chain, spot)
        _ifit_v066_render(chain, spot, atm_iv, hv30, days)
        return

    if subview == "OI & Gamma":
        _ifit_v062_render(chain, spot, days, atm_iv)
        st.markdown("### Open Interest & Gamma")
        gdf = gamma_exposure(chain)
        st.bar_chart(gdf.set_index("Strike"), height=420)
        return

    if subview == "Heston":
        _ifit_v064_render(chain, spot, days)
        _ifit_v065_render(chain, spot, days)
        return

    if subview == "Execution":
        _ifit_v076_render()
        return

    st.markdown("## Options")
    st.caption(
        "Options workspace built around the existing live Greeks, volatility, "
        "model and execution engines."
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("SPOT", f"{spot:,.2f}")
    c2.metric("ATM", f'{om["atm"]:,.0f}')
    c3.metric("PCR", f'{om["pcr"]:.2f}')
    c4.metric("ATM IV", f'{atm_iv:.2f}%')
    c5.metric("IV / HV", f'{atm_iv/max(hv30,0.01):.2f}x')
    c6.metric("MAX PAIN", f'{om["max_pain"]:,.0f}')

    st.info(f'1σ expected range: {spot-om["move"]:,.0f} → {spot+om["move"]:,.0f}')

    near = chain.iloc[(chain["Strike"] - spot).abs().argsort()[:15]].sort_values("Strike")
    display = near[
        [
            "CE OI", "CE ΔOI", "CE LTP", "CE IV", "CE Δ", "CE Γ",
            "Moneyness", "Strike", "PE IV", "PE Δ", "PE Γ",
            "PE LTP", "PE ΔOI", "PE OI"
        ]
    ]

    st.markdown("### Professional Option Chain")
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        height=430
    )

    a, b, c = st.columns(3)

    with a:
        st.markdown("### IV Smile")
        st.line_chart(
            chain[["Strike", "CE IV", "PE IV"]].set_index("Strike"),
            height=260
        )

    with b:
        st.markdown("### Gamma")
        gdf = gamma_exposure(chain)
        st.bar_chart(gdf.set_index("Strike"), height=260)

    with c:
        st.markdown("### Expected Move")
        st.dataframe(
            expected_move_table(spot, atm_iv, days),
            use_container_width=True,
            hide_index=True
        )

    with st.expander("Open full Options Intelligence stack"):
        _ifit_v062_render(chain, spot, days, atm_iv)
        _ifit_v063_render(chain, spot)
        _ifit_v064_render(chain, spot, days)
        _ifit_v065_render(chain, spot, days)
        _ifit_v066_render(chain, spot, atm_iv, hv30, days)
'''

with open(p, "w", encoding="utf-8") as f:
    f.write(s[:start] + new + s[end:])

print("Options subview routing patch applied.")
print("Backup created: app.py.bak_before_options_subview_fix")