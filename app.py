import streamlit as st
import pandas as pd
from teeiq.data_utils import clean_teetimes
from teeiq.analytics import kpis
from teeiq.demo import make_demo_teetimes

st.set_page_config(page_title="TeeIQ – Run your course like a hedge fund", page_icon="⛳", layout="wide")

# --- Classy minimal styling (free) ---
CSS = """
<style>
/* Elegant font stack */
html, body, [class*="css"]  { font-family: ui-sans-serif, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial; }
h1, h2, h3, .metric-label { letter-spacing: .2px; }
.small-muted { color:#9fb5a7; font-size:0.9rem; }
.kpi-card { background: #0f201a; border:1px solid #1c3b2f; border-radius:16px; padding:18px; }
hr { border-color:#183428; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

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
    with c1: st.container(border=False).markdown(f'<div class="kpi-card"><div class="metric-label">Total Slots</div><h3>{total:,}</h3></div>', unsafe_allow_html=True)
    with c2: st.container(border=False).markdown(f'<div class="kpi-card"><div class="metric-label">Booked</div><h3>{booked:,} · {util*100:.0f}%</h3></div>', unsafe_allow_html=True)
    with c3: st.container(border=False).markdown(f'<div class="kpi-card"><div class="metric-label">Revenue (booked)</div><h3>${revenue:,.0f}</h3></div>', unsafe_allow_html=True)
    with c4: st.container(border=False).markdown(f'<div class="kpi-card"><div class="metric-label">Potential (open)</div><h3>${potential:,.0f}</h3></div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("Use the **pages** (left sidebar) for: Import/Save, Heatmap, Pricing & AI (combined), Competitors, Reviews, Reports.")
