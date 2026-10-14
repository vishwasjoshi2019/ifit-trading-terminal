
from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

old_sidebar = r'''_ifit_v082_sync_state()

# Primary terminal navigation lives in the sidebar; the compact top rail mirrors the active workspace.
with st.sidebar:
    st.markdown("## ⚡ IFIT TERMINAL")
    st.caption("V0.8.2 • Navigation & Workspace Engine")
    module = st.selectbox(
        "Workspace",
        workspace_names(),
        index=workspace_names().index(st.session_state["ifit_v082_module"]),
        )
    if module != st.session_state["ifit_v082_module"]:
        st.session_state["ifit_v082_module"] = module
        st.session_state["ifit_v082_subview"] = subviews_for(module)[0]
        st.rerun()
'''

new_sidebar = r'''_ifit_v082_sync_state()

# Primary terminal navigation lives in the sidebar.
# The widget is synchronized with canonical session state so top-nav clicks
# survive Streamlit reruns instead of being overwritten by the old selectbox.
if "ifit_v082_module_select" not in st.session_state:
    st.session_state["ifit_v082_module_select"] = st.session_state["ifit_v082_module"]

def _ifit_v082_sidebar_module_changed():
    selected_module = st.session_state["ifit_v082_module_select"]
    st.session_state["ifit_v082_module"] = selected_module
    st.session_state["ifit_v082_subview"] = subviews_for(selected_module)[0]

with st.sidebar:
    st.markdown("## ⚡ IFIT TERMINAL")
    st.caption("V0.8.2 • Navigation & Workspace Engine")
    module = st.selectbox(
        "Workspace",
        workspace_names(),
        key="ifit_v082_module_select",
        on_change=_ifit_v082_sidebar_module_changed,
    )
'''

old_topnav = r'''# Compact top navigation mirrors the sidebar and gives the terminal a one-click workspace rail.
st.markdown("### Terminal Workspaces")
nav_cols = st.columns(len(workspace_names()))
for i, name in enumerate(workspace_names()):
    label = f"{workspace_code(name)}  {name}"
    if nav_cols[i].button(label, use_container_width=True, type="primary" if name == ctx.module else "secondary", key=f"ifit_v082_topnav_{i}"):
        st.session_state["ifit_v082_module"] = name
        st.session_state["ifit_v082_subview"] = subviews_for(name)[0]
        st.rerun()
'''

new_topnav = r'''# Compact top navigation mirrors the sidebar and gives the terminal a one-click workspace rail.
st.markdown("### Terminal Workspaces")
nav_cols = st.columns(len(workspace_names()))
for i, name in enumerate(workspace_names()):
    label = f"{workspace_code(name)}  {name}"
    if nav_cols[i].button(
        label,
        use_container_width=True,
        type="primary" if name == ctx.module else "secondary",
        key=f"ifit_v082_topnav_{i}",
    ):
        st.session_state["ifit_v082_module"] = name
        st.session_state["ifit_v082_subview"] = subviews_for(name)[0]
        st.session_state["ifit_v082_module_select"] = name
        st.rerun()
'''

if old_sidebar not in s:
    raise SystemExit("SIDEBAR BLOCK NOT FOUND — no changes made.")
if old_topnav not in s:
    raise SystemExit("TOP NAV BLOCK NOT FOUND — no changes made.")

backup = p.with_name("app.py.BEFORE_CHT_NAV_FIX")
if not backup.exists():
    backup.write_text(s, encoding="utf-8")

s = s.replace(old_sidebar, new_sidebar, 1)
s = s.replace(old_topnav, new_topnav, 1)
p.write_text(s, encoding="utf-8")

print("CHT NAVIGATION FIX APPLIED")
print("Backup:", backup.name)
