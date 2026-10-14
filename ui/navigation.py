"""IFIT Terminal Multi-Row Navigation Rail."""
import streamlit as st
from engines.workspace_engine import workspace_names, workspace_code, subviews_for


def render_workspace_rail(active_module: str) -> None:
    """Render the high-density 2-row workspace switcher."""
    st.markdown("##### ⚡ Terminal Workspaces")
    all_workspaces = workspace_names()
    
    # Split into 2 rows of 8 columns for optimal horizontal spacing
    row1 = all_workspaces[:8]
    row2 = all_workspaces[8:]
    
    for r_idx, ws_row in enumerate([row1, row2]):
        cols = st.columns(len(ws_row))
        for j, name in enumerate(ws_row):
            label = f"[{workspace_code(name)}] {name}"
            is_active = (name == active_module)
            if cols[j].button(
                label,
                use_container_width=True,
                type="primary" if is_active else "secondary",
                key=f"ifit_nav_rail_{r_idx}_{j}"
            ):
                st.session_state["ifit_v082_module"] = name
                st.session_state["ifit_v082_subview"] = subviews_for(name)[0]
                st.rerun()
