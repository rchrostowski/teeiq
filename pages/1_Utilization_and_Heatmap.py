import streamlit as st
import matplotlib.pyplot as plt

from teeiq.data_utils import clean_teetimes
from teeiq.analytics import utilization_matrix, daily_utilization

st.header("Utilization & Heatmap")

if "tee_df" not in st.session_state or st.session_state["tee_df"].empty:
    st.info("Load tee times on the main page first.")
    st.stop()

df = clean_teetimes(st.session_state["tee_df"])

mat = utilization_matrix(df)
fig, ax = plt.subplots(figsize=(12,4))
im = ax.imshow(mat.to_numpy(), aspect="auto")
ax.set_yticks(range(len(mat.index))); ax.set_yticklabels(mat.index)
ax.set_xticks(range(len(mat.columns))); ax.set_xticklabels(mat.columns)
ax.set_xlabel("Hour of Day"); ax.set_title("Utilization Heatmap")
st.pyplot(fig, use_container_width=True)

st.subheader("Daily Utilization Trend")
st.line_chart(daily_utilization(df).set_index("date"))
