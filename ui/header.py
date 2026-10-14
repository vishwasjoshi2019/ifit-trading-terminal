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
        f'<div><span class="ifit-logo">🇮🇳 <span class="ifit-logo-badge">IFIT</span></span><span class="ifit-terminal-name">TERMINAL</span></div>'
        f'<div class="ifit-active-pill"><span class="{dot_class}"></span>[{status_label}] {workspace_code(ctx.module)} • {ctx.module.upper()} • {ctx.subview.upper()}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="ifit-nav-note"><b>{ctx.instrument}</b> • {ctx.timeframe} • '
        f'Feed: <b>{ctx.data_mode}</b> • {workspace_description(ctx.module)}</div>',
        unsafe_allow_html=True,
    )
