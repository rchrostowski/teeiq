# --- Add near the top of the page, before Generate button ---
slot_minutes = st.selectbox(
    "Tee-time interval",
    options=[5, 7, 8, 9, 10, 12, 15],
    index=[5,7,8,9,10,12,15].index(10),
    help="Choose the spacing between tee times. Pricing & AI will use this granularity."
)

# -------- Combined AI Rec + Predictive Pricing -----------
util_th = st.slider("Flag times below this utilization threshold", 0.3, 0.9, 0.6, 0.05)
min_slots = st.number_input("Min slots per (weekday, slot) to consider", min_value=4, max_value=100, value=8, step=1)

if st.button("Generate ONE pricing suggestion"):
    # Slot-level opportunities at chosen interval
    opp = low_fill_opportunities(df, util_threshold=util_th, min_slots=min_slots, slot_minutes=slot_minutes)

    # Predictive overlay (uses weather if fetched earlier)
    try:
        clf = train_model(df, weather_df, slot_minutes=slot_minutes)
        util_pred = expected_utilization(clf, df, weather_df, slot_minutes=slot_minutes, by="slot")
        # Merge predicted util with observed + price
        enhanced = opp.merge(
            util_pred[["weekday","slot_index","slot_label","expected_util"]],
            on=["weekday","slot_index"], how="left", suffixes=("", "_pred")
        )
        enhanced["expected_util"] = enhanced["expected_util"].fillna(enhanced["util"])
    except Exception:
        enhanced = opp.copy()
        enhanced["expected_util"] = enhanced["util"]  # fallback without model

    # Compute final price suggestions (we already have avg_price in enhanced)
    final = dynamic_price_suggestion(
        enhanced.rename(columns={"avg_price":"avg_price"})[
            ["weekday","slot_index","slot_label","hour","expected_util","avg_price","suggested_discount","new_price"]
        ],
        target=0.75,
        price_col="avg_price"
    ).copy()

    final = final.sort_values(["expected_util","weekday","slot_index"]).reset_index(drop=True)

    if final.empty:
        st.success("No low-fill blocks detected under current thresholds.")
    else:
        # Pretty table
        from teeiq.data_utils import fmt_time_ampm
        final["Time"] = final.apply(lambda r: fmt_time_ampm(int(r["hour"]), int(r["slot_label"].split(':')[1])), axis=1)
        pretty = final.copy()
        pretty = pretty.rename(columns={"weekday":"Weekday"})
        pretty["Expected Utilization"] = (pretty["expected_util"]*100).map(lambda x: f"{x:.2f}%")
        pretty["Average Price"] = pretty["avg_price"].map(lambda x: f"${x:.2f}")
        pretty["Suggested Discount"] = (pretty["suggested_discount"]*100).map(lambda x: f"{x:.2f}%")
        pretty["New Price"] = pretty["new_price"].map(lambda x: f"${x:.2f}")
        pretty = pretty[["Weekday","Time","Expected Utilization","Average Price","Suggested Discount","New Price"]]

        # Top single rec
        top = final.iloc[0]
        st.subheader("Top Single Recommendation")
        st.markdown(
            f"**Block:** {top['weekday']} @ {fmt_time_ampm(int(top['hour']), int(top['slot_label'].split(':')[1]))}  \n"
            f"**Expected Utilization:** {top['expected_util']*100:.2f}%  \n"
            f"**Average Price:** ${top['avg_price']:.2f}  \n"
            f"**Suggested Discount:** {(top['suggested_discount']*100):.2f}%  \n"
            f"**New Price:** ${top['new_price']:.2f}"
        )

        st.dataframe(pretty, use_container_width=True)
        st.download_button(
            "Download all suggestions (CSV)",
            data=pretty.to_csv(index=False).encode(),
            file_name=f"teeiq_dynamic_pricing_{slot_minutes}min.csv",
            mime="text/csv",
        )
