"""IFIT Terminal Sticky Command Bar & Breadcrumb Header."""
import streamlit as st
from engines.workspace_engine import workspace_code, workspace_description


def render_terminal_header(ctx):
    """Render the sticky Bloomberg-style command bar with live heartbeat."""
    is_live = "LIVE" in str(ctx.data_mode).upper()
    dot_class = "ifit-live-dot" if is_live else "ifit-sim-dot"
    status_label = "LIVE" if is_live else "SIM"

    st.markdown(
        f'<div class="ifit-terminal-bar">'
        f'  <div style="display:flex; align-items:center; gap:0.5rem;">'
        f'    <span class="ifit-logo">🇮🇳 <span class="ifit-logo-badge">IFIT</span></span>'
        f'    <span class="ifit-terminal-name">QUANT TERMINAL</span>'
        f'  </div>'
        f'  <div style="display:flex; align-items:center; gap:0.75rem;">'
        f'    <a href="https://ifit-trading-terminal.vercel.app" target="_blank" style="text-decoration:none; display:inline-flex; align-items:center; gap:0.35rem; background:rgba(34,197,94,0.12); border:1px solid rgba(34,197,94,0.35); padding:0.25rem 0.65rem; border-radius:9999px; font-size:0.72rem; font-weight:700; color:#22c55e;">⚡ Live TradingView Terminal ↗</a>'
        f'    <div class="ifit-active-pill"><span class="{dot_class}"></span>[{status_label}] {workspace_code(ctx.module)} • {ctx.module.upper()} • {ctx.subview.upper()}</div>'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="ifit-nav-note"><b>{ctx.instrument}</b> • {ctx.timeframe} • '
        f'Feed: <b>{ctx.data_mode}</b> • {workspace_description(ctx.module)}</div>',
        unsafe_allow_html=True,
    )
