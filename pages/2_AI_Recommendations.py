import streamlit as st
from teeiq.data_utils import clean_teetimes
from teeiq.recs import low_fill_opportunities

st.header("AI Pricing & Promotion Suggestions (Rule-based MVP)")

if "tee_df" not in st.session_state or st.session_state["tee_df"].empty:
    st.info("Load tee times on the main page first.")
    st.stop()

df = clean_teetimes(st.session_state["tee_df"])

util_th = st.slider("Flag times below this utilization threshold", 0.3, 0.9, 0.6, 0.05)
min_slots = st.number_input("Min slots per (weekday, hour) to consider", min_value=4, max_value=100, value=8, step=1)

opp = low_fill_opportunities(df, util_threshold=util_th, min_slots=min_slots)

if opp.empty:
    st.success("No low-fill opportunities under current thresholds.")
else:
    show_cols = ["weekday","hour","slots","booked","util","avg_price","suggested_discount","new_price","expected_additional_bookings","est_monthly_lift"]
    pretty = opp[show_cols].copy()
    pretty["util"] = (pretty["util"]*100).round(1).astype(str) + "%"
    pretty["suggested_discount"] = (pretty["suggested_discount"]*100).round(0).astype(int).astype(str) + "%"
    pretty["new_price"] = pretty["new_price"].round(2)
    st.dataframe(pretty, use_container_width=True)

    csv_bytes = opp.to_csv(index=False).encode()
    st.download_button("Download recommendations CSV", data=csv_bytes, file_name="teeiq_recommendations.csv", mime="text/csv")

    st.info(f"Estimated monthly revenue lift (conservative): **${float(opp['est_monthly_lift'].sum()):,.0f}**")
