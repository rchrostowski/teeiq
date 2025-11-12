import streamlit as st
from datetime import date, timedelta

from teeiq.data_utils import clean_teetimes
from teeiq.recs import low_fill_opportunities
from teeiq.model import train_model, expected_utilization, dynamic_price_suggestion
from teeiq.weather import fetch_daily_weather
from teeiq.geo import geocode_candidates

st.header("Pricing & AI (Combined)")

# Data gate
if "tee_df" not in st.session_state or st.session_state["tee_df"].empty:
    st.info("Load tee times on the main page first.")
    st.stop()

df = clean_teetimes(st.session_state["tee_df"])

# -------- Location & Weather (Address → Candidates → Weather) ----------
with st.expander("Location & Weather (recommended)"):
    addr = st.text_input("Course address, name, URL, or 'lat,lon' (e.g., 'TPC Sawgrass, Ponte Vedra Beach, FL' or '30.199,-81.394')")
    colA, colB = st.columns(2)
    with colA:
        start = st.date_input("Forecast start", value=date.today())
    with colB:
        end = st.date_input("Forecast end", value=date.today() + timedelta(days=6))

    weather_df = None
    lat = lon = None

    if st.button("Find course location"):
        cands = geocode_candidates(addr.strip())
        if not cands:
            st.error("No geocoding results. Try adding the city/state, or paste a Google Maps link.")
        else:
            st.success(f"Found {len(cands)} location option(s). Choose one below.")
            st.session_state["geo_candidates"] = cands

    # If candidates exist, let user choose
    if "geo_candidates" in st.session_state:
        labels = [f"{name}  ({src})  [{lat:.5f}, {lon:.5f}]" for (name, lat, lon, src) in st.session_state["geo_candidates"]]
        idx = st.selectbox("Select location", range(len(labels)), format_func=lambda i: labels[i]) if labels else None
        if idx is not None and labels:
            name, lat, lon, src = st.session_state["geo_candidates"][idx]
            st.caption(f"Using: {name}  →  {lat:.5f}, {lon:.5f}")
            st.session_state["geo_latlon"] = (lat, lon)

    # Use last good lat/lon if set
    if "geo_latlon" in st.session_state:
        lat, lon = st.session_state["geo_latlon"]

    # Weather fetch (optional)
    if (lat is not None) and (lon is not None):
        try:
            weather_df = fetch_daily_weather(lat, lon, start.isoformat(), end.isoformat())
            if weather_df is not None and not weather_df.empty:
                st.caption("Weather preview")
                st.dataframe(weather_df.head(), use_container_width=True)
            else:
                st.info("No weather rows returned for that range. Continuing without weather.")
        except Exception as e:
            st.warning(f"Weather fetch failed: {e}. Continuing without weather.")

# -------- Combined AI Rec + Predictive Pricing -----------
util_th = st.slider("Flag times below this utilization threshold", 0.3, 0.9, 0.6, 0.05)
min_slots = st.number_input("Min slots per (weekday, hour) to consider", min_value=4, max_value=100, value=8, step=1)

if st.button("Generate ONE pricing suggestion"):
    # Rule-based low-fill blocks
    opp = low_fill_opportunities(df, util_threshold=util_th, min_slots=min_slots)

    # Predictive overlay (if weather available)
    try:
        clf = train_model(df, weather_df)
        util_pred = expected_utilization(clf, df, weather_df)
        enhanced = opp.merge(util_pred, on=["weekday","hour"], how="left", suffixes=("", "_pred"))
        enhanced["expected_util"] = enhanced["expected_util"].fillna(enhanced["util"])
    except Exception:
        enhanced = opp.copy()
        enhanced["expected_util"] = enhanced["util"]  # fallback without model

    # Final dynamic price suggestion (single top action)
    base = enhanced.rename(columns={"avg_price": "avg_price"})
    final = dynamic_price_suggestion(base[["weekday","hour","expected_util","avg_price"]])
    final = final.sort_values(["expected_util","weekday","hour"]).reset_index(drop=True)

    if final.empty:
        st.success("No low-fill blocks detected under current thresholds.")
    else:
        top = final.iloc[0]
        hour = int(top["hour"])
        hh = hour % 12 or 12
        ampm = "AM" if hour < 12 else "PM"
        st.subheader("Top Single Recommendation")
        st.markdown(
            f"**Block:** {top['weekday']} @ {hh}{ampm}  \n"
            f"**Expected Utilization:** {top['expected_util']*100:.0f}%  \n"
            f"**Current Avg Price:** ${top['avg_price']:.2f}  \n"
            f"**Suggested Discount:** {(top['suggested_discount']*100):.0f}%  \n"
            f"**Suggested New Price:** ${top['new_price']:.2f}"
        )
        st.caption("One focused action to take right now. Full table below.")
        st.dataframe(final, use_container_width=True)
        st.download_button(
            "Download all suggestions (CSV)",
            data=final.to_csv(index=False).encode(),
            file_name="teeiq_dynamic_pricing.csv",
            mime="text/csv",
        )
