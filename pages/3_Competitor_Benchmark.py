import streamlit as st
import pandas as pd

st.header("Competitor Benchmark (quick manual entry)")
st.caption("Enter nearby courses and their typical weekday/weekend rates to see positioning.")

default = pd.DataFrame({
    "Course": ["You (weekday)","You (weekend)","Rival A (weekday)","Rival A (weekend)","Rival B (weekday)","Rival B (weekend)"],
    "Rate":   [55, 75, 55, 75, 49, 69],
})
edited = st.data_editor(default, num_rows="dynamic", use_container_width=True)

try:
    you_wd = float(edited.loc[edited["Course"]=="You (weekday)","Rate"].iloc[0])
    you_we = float(edited.loc[edited["Course"]=="You (weekend)","Rate"].iloc[0])
    rivals = edited[~edited["Course"].str.startswith("You")]["Rate"].astype(float)
    wd_rivals = rivals.iloc[::2].mean() if len(rivals)>=1 else float("nan")
    we_rivals = rivals.iloc[1::2].mean() if len(rivals)>=2 else float("nan")
    st.write(f"**Positioning:** Weekday Δ vs rivals: {you_wd - wd_rivals:+.2f}, Weekend Δ: {you_we - we_rivals:+.2f}")
except Exception:
    st.caption("Add at least two rival rates to compute positioning.")
