import streamlit as st
from teeiq.analytics import kpis
from teeiq.data_utils import clean_teetimes
from teeiq.model import train_model, expected_utilization, dynamic_price_suggestion
from teeiq.reports import make_weekly_pdf
from pathlib import Path
from datetime import datetime

st.header("Reports (Detailed PDF)")

reports_dir = Path("reports"); reports_dir.mkdir(exist_ok=True)

if "tee_df" not in st.session_state or st.session_state["tee_df"].empty:
    st.info("Load tee times on the main page first.")
    st.stop()

df = clean_teetimes(st.session_state["tee_df"])
T,B,U,R,P = kpis(df)
kpi_dict = {
    "Utilization": f"{U*100:.0f}%",
    "Booked": f"{B:,}",
    "Revenue (booked)": f"${R:,.0f}",
    "Potential (open)": f"${P:,.0f}",
}

# Build top action items via model (no weather to keep it free/offline)
try:
    clf = train_model(df, None)
    util_df = expected_utilization(clf, df, None)
    recs = dynamic_price_suggestion(util_df)
    recs_sorted = recs.sort_values("expected_util").head(10)
    top_rows = []
    for _, r in recs_sorted.iterrows():
        hour = int(r["hour"])
        hh = hour % 12 or 12
        ampm = "AM" if hour < 12 else "PM"
        top_rows.append([r["weekday"], f"{hh}{ampm}", f"{r['expected_util']*100:.0f}%", f"{r['avg_price']:.2f}", f"{r['new_price']:.2f}", f"{(r['avg_price']-r['new_price'])*100:.0f}"])
except Exception:
    top_rows = []

# Highlights sample
highlights = [
    f"Week utilization at {U*100:.0f}%.",
    "Focus discounts on the lowest expected-utilization block above.",
    "Promote 9-hole twilight tee times to lift late-day utilization.",
]

if st.button("Generate detailed weekly PDF"):
    fname = reports_dir / f"report_{datetime.now().date()}.pdf"
    pdf_bytes = make_weekly_pdf(kpi_dict, str(fname), highlights=highlights, top_blocks=top_rows)
    st.success(f"Saved {fname.name}")
    st.download_button("Download report", data=pdf_bytes, file_name=fname.name, mime="application/pdf")

st.subheader("Existing reports")
for p in sorted(reports_dir.glob("*.pdf")):
    st.write("•", p.name)

