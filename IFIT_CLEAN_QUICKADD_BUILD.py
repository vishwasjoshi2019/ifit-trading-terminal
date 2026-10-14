from pathlib import Path
import shutil
import ast

PROJECT = Path(__file__).resolve().parent
APP = PROJECT / "app.py"
BACKUP = PROJECT / "app.py.BEFORE_QUICKADD_CLEAN"

# Locate the known clean backup from the parent Downloads folder.
candidates = [
    PROJECT / "app.py.BEFORE_QUICKADD_V0841",
    PROJECT.parent / "IFIT_Prototype_v0.8.4.1_BACKUP" / "app.py.BEFORE_QUICKADD_V0841",
    PROJECT.parent / "IFIT_Prototype_v0.8.4.1_BACKUP" / "app.py.BEFORE_QUICKADD_FINAL",
]

source = next((p for p in candidates if p.exists()), None)
if source is None:
    raise SystemExit("ERROR: Clean BEFORE_QUICKADD_V0841 backup was not found.")

# Always start from the known clean source.
shutil.copy2(source, BACKUP)
shutil.copy2(source, APP)

s = APP.read_text(encoding="utf-8")

# Find the Indicator Stack heading and the existing indicator-options line.
heading = 'st.markdown("### Indicator Stack")'
options = 'indicator_options = ["EMA", "SMA", "VWAP", "Bollinger Bands", "Supertrend", "RSI", "MACD", "ATR", "Volume", "CVD", "Delta"]'

h = s.find(heading)
o = s.find(options, h)

if h < 0 or o < 0:
    raise SystemExit("ERROR: Clean Indicator Stack anchors were not found. No final patch applied.")

# Determine the indentation of the heading so everything stays inside the chart page function.
line_start = s.rfind("\n", 0, h) + 1
indent = s[line_start:h]

# Replace only the section from the heading through the existing multiselect.
multiselect_end_marker = 'key="ifit_v084_indicators")'
m = s.find(multiselect_end_marker, o)
if m < 0:
    raise SystemExit("ERROR: Existing indicator multiselect was not found.")

end = m + len(multiselect_end_marker)

body = [
    'st.markdown("### Indicator Stack")',
    '',
    '# Quick Add modifies the existing indicator selection; it never clears it.',
    'if "ifit_v084_indicators" not in st.session_state:',
    '    st.session_state["ifit_v084_indicators"] = ["EMA", "VWAP", "Volume"]',
    '',
    'st.markdown("#### ⚡ Quick Add")',
    'qa1, qa2, qa3, qa4, qa5, qa6 = st.columns(6)',
    '',
    'quick_adds = [',
    '    ("EMA 20", "EMA"),',
    '    ("VWAP", "VWAP"),',
    '    ("RSI 14", "RSI"),',
    '    ("Bollinger Bands", "Bollinger Bands"),',
    '    ("MACD", "MACD"),',
    '    ("Supertrend", "Supertrend"),',
    ']',
    '',
    'for col, (label, indicator) in zip([qa1, qa2, qa3, qa4, qa5, qa6], quick_adds):',
    '    if col.button(label, key=f"ifit_v084_quickadd_{indicator.replace(\' \', \'_\').lower()}"):',
    '        current = list(st.session_state.get("ifit_v084_indicators", []))',
    '        if indicator not in current:',
    '            current.append(indicator)',
    '            st.session_state["ifit_v084_indicators"] = current',
    '        st.rerun()',
    '',
    'selected = st.multiselect(',
    '    "Indicators",',
    '    indicator_options,',
    '    key="ifit_v084_indicators",',
    ')',
]

# Keep the existing indicator_options declaration immediately before this block.
# It already exists in the clean source, so insert Quick Add after it.
insert_at = o + len(options)
patch = "\n\n" + "\n".join(indent + line if line else "" for line in body if True)

# Remove the old selected multiselect only; preserve indicator_options and following controls.
s = s[:o + len(options)] + patch + s[end:]
APP.write_text(s, encoding="utf-8")

# Verify syntax before reporting success.
try:
    ast.parse(APP.read_text(encoding="utf-8"))
except SyntaxError as e:
    shutil.copy2(BACKUP, APP)
    raise SystemExit(f"ERROR: Generated app.py failed syntax validation at line {e.lineno}. Clean backup restored.")

print("CLEAN QUICK ADD BUILD COMPLETE")
print(f"Source: {source}")
print(f"Backup: {BACKUP.name}")
print("Syntax validation: PASS")
print("Next command: python -m py_compile app.py")
