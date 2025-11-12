import streamlit as st
from teeiq.data_utils import clean_teetimes
from teeiq.recs import low_fill_opportunities
from teeiq.model import train_model, expected_utilization, dynamic_price_suggestion
from teeiq.weather import fetch_daily_weather
from teeiq.geo import geocode_address
from datetime import date, timedelta

st.header("Pricing & AI (Combined)")

if "tee_df" not in st.session_state or st.session_state["tee_df"].empty:
    st.info("Load tee times on the main page first.")
    st.stop()

df = clean_teetimes(st.session_state["tee_df"])

# --- Address → lat/lon (free via Nominatim) ---
with st.expander("Location & Weather (optional but recommended)"):
    addr = st.text_input("Course address (e.g., 'TPC Sawgrass, Ponte Vedra Beach, FL')")
    colA, colB = st.columns(2)
    with colA:
        start = st.date_input("Start date", value=date.today())
    with colB:
        end = st.date_input("End date", value=date.today() + timedelta(days=6))

    weather_df = None
    if st.button("Lookup weather by address"):
        if not addr.strip():
            st.warning("Enter an address first.")
        else:
            coords = geocode_address(addr)
            if not coords:
                st.error("Could not geocode that address (try a more specific query).")
            else:
                lat, lon = coords
                st.success(f"Geocoded: {lat:.5f}, {lon:.5f}")
                weather_df = fetch_daily_weather(lat, lon, start.isoformat(), end.isoformat())
                if weather_df is not None and not weather_df.empty:
                    st.dataframe(weather_df.head(), use_container_width=True)
                else:
                    st.info("No weather rows returned for that range.")

# --- Train model, produce ONE best suggestion ---
util_th = st.slider("Flag times below this utilization threshold", 0.3, 0.9, 0.6, 0.05)
min_slots = st.number_input("Min slots per (weekday, hour) to consider", min_value=4, max_value=100, value=8, step=1)

if st.button("Generate ONE pricing suggestion"):
    # Rule-based opportunities
    opp = low_fill_opportunities(df, util_threshold=util_th, min_slots=min_slots)

    # Predictive overlay (if we fetched weather)
    try:
        clf = train_model(df, weather_df)
        util_pred = expected_utilization(clf, df, weather_df)
        enhanced = opp.merge(util_pred, on=["weekday","hour"], how="left", suffixes=("", "_pred"))
    except Exception:
        enhanced = opp.copy()
        enhanced["expected_util"] = enhanced["util"]  # fallback

    # Make final dynamic price recs based on predicted expected_util
    final = dynamic_price_suggestion(
        enhanced.rename(columns={"avg_price":"avg_price"}).assign(expected_util=enhanced["expected_util"].fillna(enhanced["util"]))
        [["weekday","hour","expected_util","avg_price"]]
    )
    # Rank by (lowest expected utilization first)
    final = final.sort_values(["expected_util","weekday","hour"]).reset_index(drop=True)

    if final.empty:
        st.success("No low-fill blocks detected under current thresholds.")
    else:
        top = final.iloc[0]
        st.subheader("Top Single Recommendation")
        st.markdown(f"""
**Block:** {top['weekday']} @ {int(top['hour']%12) if int(top['hour']%12)!=0 else 12}{'AM' if top['hour']<12 else 'PM'}  
**Expected Utilization:** {top['expected_util']*100:.0f}%  
**Current Avg Price:** ${top['avg_price']:.2f}  
**Suggested Discount:** {(top['suggested_discount']*100):.0f}%  
**Suggested New Price:** ${top['new_price']:.2f}
""")
        st.caption("This is a single, focused action you can take right now. (More blocks appear in the table below.)")
        st.dataframe(final, use_container_width=True)
        csv_bytes = final.to_csv(index=False).encode()
        st.download_button("Download all suggestions (CSV)", data=csv_bytes, file_name="teeiq_dynamic_pricing.csv", mime="text/csv")


