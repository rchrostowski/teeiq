import streamlit as st
from teeiq.analytics import kpis
from teeiq.data_utils import clean_teetimes
from teeiq.reports import make_weekly_pdf
from pathlib import Path
from datetime import datetime

st.header("Reports (PDF)")

reports_dir = Path("reports"); reports_dir.mkdir(exist_ok=True)

if "tee_df" not in st.session_state or st.session_state["tee_df"].empty:
    st.info("Load tee times on the main page first.")
    st.stop()

df = clean_teetimes(st.session_state["tee_df"])
T,B,U,R,P = kpis(df)
metrics = {
    "Utilization": f"{U*100:.1f}%",
    "Booked": f"{B:,}",
    "Revenue (booked)": f"${R:,.0f}",
    "Potential (open)": f"${P:,.0f}",
}

if st.button("Generate weekly PDF"):
    fname = reports_dir / f"report_demo_{datetime.now().date()}.pdf"
    pdf_bytes = make_weekly_pdf(metrics, str(fname))
    st.success(f"Saved {fname.name}")
    st.download_button("Download now", data=pdf_bytes, file_name=fname.name, mime="application/pdf")

st.subheader("Existing reports")
for p in sorted(reports_dir.glob("*.pdf")):
    st.write("•", p.name)
