import streamlit as st, numpy as np, matplotlib.pyplot as plt
from teeiq.data_utils import clean_teetimes
from teeiq.analytics import utilization_matrix, daily_utilization

st.header("Utilization & Heatmap")

if "tee_df" not in st.session_state or st.session_state["tee_df"].empty:
    st.info("Load tee times on the main page first.")
    st.stop()

df = clean_teetimes(st.session_state["tee_df"])

# Heatmap with pretty 12-hour labels and value annotations
mat = utilization_matrix(df)
hours = list(mat.columns)

def hour_label(h):
    # 6–11 AM, 12 PM, 1–11 PM, 12 AM
    ampm = "AM" if h < 12 else "PM"
    hh = h % 12
    if hh == 0: hh = 12
    return f"{hh}{ampm}"

xlabels = [hour_label(h) for h in hours]

fig, ax = plt.subplots(figsize=(14, 4))
im = ax.imshow(mat.to_numpy(), aspect="auto")
ax.set_yticks(range(len(mat.index))); ax.set_yticklabels(mat.index)
ax.set_xticks(range(len(hours))); ax.set_xticklabels(xlabels, rotation=0)
ax.set_xlabel("Hour of Day"); ax.set_title("Utilization Heatmap")

# annotate values (as %)
data = mat.to_numpy()
for i in range(data.shape[0]):
    for j in range(data.shape[1]):
        if not np.isnan(data[i, j]):
            ax.text(j, i, f"{data[i,j]*100:.0f}%", ha="center", va="center", fontsize=8, color="white")

plt.colorbar(im, ax=ax, fraction=0.02, pad=0.02, label="Utilization")
st.pyplot(fig, use_container_width=True)

st.subheader("Daily Utilization Trend")
trend = daily_utilization(df)
trend["util_pct"] = (trend["util"] * 100).round(0)
st.line_chart(trend.set_index("date")["util_pct"])
st.caption("Values shown as whole-percent utilization per day.")
