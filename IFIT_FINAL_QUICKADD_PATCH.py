from pathlib import Path
import shutil

p = Path("app.py")
if not p.exists():
    raise SystemExit("ERROR: app.py not found. Run this script from the IFIT project folder.")

s = p.read_text(encoding="utf-8")

start_marker = 'st.markdown("### Indicator Stack")'
end_marker = 'p1, p2, p3, p4, p5 = st.columns(5)'

start = s.find(start_marker)
end = s.find(end_marker, start)

if start < 0 or end < 0:
    raise SystemExit("ERROR: Clean Indicator Stack block not found. No changes were made.")

backup = p.with_name("app.py.BEFORE_QUICKADD_FINAL")
if not backup.exists():
    shutil.copy2(p, backup)

new_block = '''st.markdown("### Indicator Stack")

# Quick Add: updates the existing indicator selection without replacing
# indicators that are already selected.
if "ifit_v084_indicators" not in st.session_state:
    st.session_state["ifit_v084_indicators"] = ["EMA", "VWAP", "Volume"]

st.markdown("#### ⚡ Quick Add")

qa1, qa2, qa3, qa4, qa5, qa6 = st.columns(6)

quick_adds = [
    ("EMA 20", "EMA"),
    ("VWAP", "VWAP"),
    ("RSI 14", "RSI"),
    ("Bollinger Bands", "Bollinger Bands"),
    ("MACD", "MACD"),
    ("Supertrend", "Supertrend"),
]

for col, (label, indicator) in zip([qa1, qa2, qa3, qa4, qa5, qa6], quick_adds):
    if col.button(label, key=f"ifit_v084_quickadd_{indicator.replace(' ', '_').lower()}"):
        current = list(st.session_state["ifit_v084_indicators"])
        if indicator not in current:
            current.append(indicator)
            st.session_state["ifit_v084_indicators"] = current
        st.rerun()

indicator_options = [
    "EMA", "SMA", "VWAP", "Bollinger Bands", "Supertrend",
    "RSI", "MACD", "ATR", "Volume", "CVD", "Delta"
]

selected = st.multiselect(
    "Indicators",
    indicator_options,
    default=st.session_state["ifit_v084_indicators"],
    key="ifit_v084_indicators",
)

'''

s = s[:start] + new_block + s[end:]
p.write_text(s, encoding="utf-8")

print("QUICK ADD FINAL PATCH APPLIED")
print("Backup:", backup.name)
