
from pathlib import Path
import re

p = Path("app.py")
s = p.read_text(encoding="utf-8")

backup = p.with_name("app.py.BEFORE_ROBUST_CHT_NAV_FIX")
if not backup.exists():
    backup.write_text(s, encoding="utf-8")

sidebar_pattern = re.compile(
    r"with st\.sidebar:\n.*?(?=    subviews = subviews_for\(module\))",
    re.S
)

new_sidebar = """with st.sidebar:
    st.markdown("## ⚡ IFIT TERMINAL")
    st.caption("V0.8.2 • Navigation & Workspace Engine")
    if "ifit_v082_module_select" not in st.session_state:
        st.session_state["ifit_v082_module_select"] = st.session_state["ifit_v082_module"]

    def _ifit_v082_sidebar_module_changed():
        selected_module = st.session_state["ifit_v082_module_select"]
        st.session_state["ifit_v082_module"] = selected_module
        st.session_state["ifit_v082_subview"] = subviews_for(selected_module)[0]

    module = st.selectbox(
        "Workspace",
        workspace_names(),
        key="ifit_v082_module_select",
        on_change=_ifit_v082_sidebar_module_changed,
    )

"""

s2, n1 = sidebar_pattern.subn(new_sidebar, s, count=1)
if n1 != 1:
    raise SystemExit("SIDEBAR BLOCK NOT FOUND — NO CHANGES MADE.")

handler_pattern = re.compile(
    r'(if nav_cols\[i\]\.button\(.*?\n'
    r'\s*st\.session_state\["ifit_v082_module"\] = name\n'
    r'\s*st\.session_state\["ifit_v082_subview"\] = subviews_for\(name\)\[0\]\n'
    r'\s*)st\.rerun\(\)',
    re.S
)

replacement = r'\1st.session_state["ifit_v082_module_select"] = name\n        st.rerun()'
s3, n2 = handler_pattern.subn(replacement, s2, count=1)

if n2 != 1:
    raise SystemExit("TOP NAV HANDLER NOT FOUND — NO CHANGES MADE.")

p.write_text(s3, encoding="utf-8")
print("ROBUST CHT NAVIGATION FIX APPLIED")
print("Backup:", backup.name)
