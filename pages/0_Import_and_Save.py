import streamlit as st
from teeiq.import_ui import import_flow
from teeiq.persistence import save_teetimes

st.header("Import & Save (Bulletproof Loader)")

course_id = st.text_input("Course ID (e.g., palm-woods-fl)")
if not course_id:
    st.info("Enter a Course ID to save data.")

tee_df = import_flow()

if not tee_df.empty:
    st.success(f"Imported {len(tee_df):,} rows.")
    if course_id and st.button("Save to database"):
        save_teetimes(tee_df, course_id)
        st.success("Saved to DB.")
