import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from teeiq.data_utils import clean_teetimes
from teeiq.analytics import kpis, utilization_matrix, daily_utilization
from teeiq.model import train_model, expected_utilization, dynamic_price_suggestion
from teeiq.reports import make_advanced_weekly_pdf

def hour_label(h: int) -> str:
    ampm = "AM" if h < 12 else "PM"
    hh = h % 12 or 12
    return f"{hh}{ampm}"

st.header("Reports (Advanced PDF)")

reports_dir = Path("reports"); reports_dir.mkdir(exist_ok=True)

if "tee_df" not in st.session_state or st.session_state["tee_df"].empty:
    st.info("Load tee times on the main page first.")
    st.stop()

df = clean_teetimes(st.session_state["tee_df"])

# Compute KPIs
T,B,U,R,P = kpis(df)
kpi_dict = {
    "Utilization": f"{U*100:.0f}%",
    "Booked": f"{B:,}",
    "Revenue (booked)": f"${R:,.0f}",
    "Potential (open)": f"${P:,.0f}",
}

# Week-over-week deltas (if enough history)
trend = daily_utilization(df).sort_values("date")
notes = [f"Week utilization: {U*100:.0f}%."]
if len(trend) >= 14:
    this_week = trend.tail(7)["util"].mean()
    prev_week = trend.tail(14).head(7)["util"].mean()
    delta = (this_week - prev_week)*100
    notes.append(f"Week-over-week change: {delta:+.1f} pts.")
else:
    notes.append("Not enough history for WoW comparison.")

# Heatmap data
mat = utilization_matrix(df)
heatmap = mat.to_numpy()
hm_ylabels = list(mat.index)
hm_xlabels = [hour_label(h) for h in list(mat.columns)]

# Top actions from predictive engine (no weather for PDF speed)
try:
    clf = train_model(df, None)
    util_df = expected_utilization(clf, df, None)
    recs = dynamic_price_suggestion(util_df).sort_values("expected_util").head(10)
    top_rows = []
    for _, r in recs.iterrows():
        hour = int(r["hour"])
        hh = hour % 12 or 12
        ampm = "AM" if hour < 12 else "PM"
        top_rows.append([
            r["weekday"],
            f"{hh}{ampm}",
            f"{r['expected_util']*100:.0f}%",
            f"{r['avg_price']:.2f}",
            f"{r['new_price']:.2f}",
            f"{(r['avg_price']-r['new_price'])*100:.0f}"
        ])
except Exception:
    top_rows = []

if st.button("Generate advanced weekly PDF"):
    fname = reports_dir / f"report_{datetime.now().date()}.pdf"
    make_advanced_weekly_pdf(
        filename=str(fname),
        kpis=kpi_dict,
        trend_df=trend,
        heatmap=heatmap,
        heatmap_ylabels=hm_ylabels,
        heatmap_xlabels=hm_xlabels,
        top_actions=top_rows,
        notes=notes,
    )
    with open(fname, "rb") as f:
        pdf_bytes = f.read()
    st.success(f"Saved {fname.name}")
    st.download_button("Download report", data=pdf_bytes, file_name=fname.name, mime="application/pdf")

st.subheader("Existing reports")
for p in sorted(reports_dir.glob("*.pdf")):
    st.write("•", p.name)

