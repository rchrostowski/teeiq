import streamlit as st
import pandas as pd
from teeiq.reviews import summarize_reviews

st.header("Reviews & Themes (optional)")

rev_file = st.file_uploader("Upload reviews CSV (review_date, rating, text)", type=["csv"])
if rev_file is None:
    st.info("Upload a reviews CSV to see themes and average rating.")
    st.stop()

rev_df = pd.read_csv(rev_file)

if "rating" in rev_df.columns:
    avg = pd.to_numeric(rev_df["rating"], errors="coerce").mean()
    if pd.notna(avg):
        st.metric("Avg Rating", f"{avg:.2f}")
        st.progress(max(0.0, min(1.0, (avg - 1) / 4)))

summary = summarize_reviews(rev_df)
if summary.empty:
    st.caption("No text column found or no matches for themes.")
else:
    st.subheader("Review Themes (keyword counts)")
    st.dataframe(summary, use_container_width=True)

