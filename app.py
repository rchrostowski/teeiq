
---

### `app.py`
```python
import streamlit as st
import pandas as pd

from teeiq.data_utils import clean_teetimes
from teeiq.analytics import kpis
from teeiq.demo import make_demo_teetimes

st.set_page_config(page_title="TeeIQ – Run your course like a hedge fund", page_icon="⛳", layout="wide")
st.title("TeeIQ – Revenue Optimization Dashboard")
st.caption("Run your course like a hedge fund.")

with st.sidebar:
    st.markdown("## ⛳ TeeIQ")
    st.caption("Upload a tee times CSV or generate demo data.")
    tee_file = st.file_uploader("tee_times.csv", type=["csv"])
    if st.button("Generate demo data"):
        st.session_state["tee_df"] = make_demo_teetimes()

if tee_file is not None:
    st.session_state["tee_df"] = pd.read_csv(tee_file)

df_raw = st.session_state.get("tee_df", pd.DataFrame())

if df_raw.empty:
    st.warning("Upload a tee times CSV in the sidebar or click 'Generate demo data'.")
else:
    try:
        df = clean_teetimes(df_raw)
    except Exception as e:
        st.error(f"Data error: {e}")
        st.stop()

    total, booked, util, revenue, potential = kpis(df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Slots", f"{total:,}")
    c2.metric("Booked", f"{booked:,}", f"{util*100:.1f}% util")
    c3.metric("Revenue (booked)", f"${revenue:,.0f}")
    c4.metric("Potential (open)", f"${potential:,.0f}")

    st.divider()
    st.markdown("Use the **pages** (left sidebar) for: Import/Save, Heatmap, AI Recs, Competitor Benchmark, Reviews, Predictive Pricing, and Reports.")

