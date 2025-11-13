import streamlit as st
from datetime import date, timedelta
import pandas as pd
import matplotlib.pyplot as plt

from teeiq.data_utils import clean_teetimes
from teeiq.recs import low_fill_opportunities
from teeiq.model import train_model, expected_utilization, dynamic_price_suggestion
from teeiq.weather import fetch_daily_weather
from teeiq.geo import geocode_address

def hour_label(h: int) -> str:
    h = int(h)
    ampm = "AM" if h < 12 else "PM"
    hh = h % 12 or 12
    return f"{hh}{ampm}"

st.header("Pricing & AI (Combined)")

# Data gate
if "tee_df" not in st.session_state or st.session_state["tee_df"].empty:
    st.info("Load tee times on the main page first.")
    st.stop()

df = clean_teetimes(st.session_state["tee_df"])

# -------- Address → Weather ----------
with st.expander("Location & Weather (type the street address)"):
    addr = st.text_input(
        "Full course address",
        help="Example: 110 Championship Way, Ponte Vedra Beach, FL 32082"
    )
    c1, c2 = st.columns(2)
    with c1:
        start = st.date_input("Forecast start", value=date.today())
    with c2:
        end = st.date_input("Forecast end", value=date.today() + timedelta(days=6))

    lat = lon = None
    weather_df = None

    if st.button("Use this address for weather"):
        coords = geocode_address(addr)
        if not coords:
            st.error("Could not geocode that address. You can enter coordinates below as a fallback.")
        else:
            lat, lon = coords
            st.success(f"Geocoded: {lat:.5f}, {lon:.5f}")
            st.session_state["geo_latlon"] = (lat, lon)

    # Remember last successful geocode
    if "geo_latlon" in st.session_state and (lat is None or lon is None):
        lat, lon = st.session_state["geo_latlon"]

    # Manual fallback always available
    st.markdown("**Manual fallback (optional):**")
    m1, m2 = st.columns(2)
    with m1:
        lat = st.number_input("Latitude", value=lat if lat is not None else 30.19924, format="%.5f")
    with m2:
        lon = st.number_input("Longitude", value=lon if lon is not None else -81.39402, format="%.5f")
    st.caption("Tip: For TPC Sawgrass, the clubhouse area is roughly 30.19924, -81.39402.")

    # Weather fetch is optional; model will still run without it
    if st.button("Fetch weather (optional)"):
        try:
            weather_df = fetch_daily_weather(lat, lon, start.isoformat(), end.isoformat())
            if weather_df is not None and not weather_df.empty:
                st.caption("Weather preview")
                st.dataframe(weather_df.head(), use_container_width=True)
            else:
                st.info("No weather rows for that range. Continuing without weather.")
        except Exception as e:
            st.warning(f"Weather fetch failed: {e}. Continuing without weather.")

# -------- Combined AI Rec + Predictive Pricing -----------
util_th = st.slider("Flag times below this utilization threshold", 0.3, 0.9, 0.6, 0.05)
min_slots = st.number_input("Min slots per (weekday, hour) to consider", min_value=4, max_value=100, value=8, step=1)

if st.button("Generate ONE pricing suggestion"):
    # Rule-based low-fill blocks
    opp = low_fill_opportunities(df, util_threshold=util_th, min_slots=min_slots)

    # Predictive overlay (uses weather if fetched)
    try:
        clf = train_model(df, weather_df)
        util_pred = expected_utilization(clf, df, weather_df)
        enhanced = opp.merge(util_pred, on=["weekday","hour"], how="left", suffixes=("", "_pred"))
        enhanced["expected_util"] = enhanced["expected_util"].fillna(enhanced["util"])
    except Exception:
        enhanced = opp.copy()
        enhanced["expected_util"] = enhanced["util"]  # fallback without model

    # Final dynamic price suggestion
    base = enhanced.rename(columns={"avg_price": "avg_price"})
    final = dynamic_price_suggestion(base[["weekday","hour","expected_util","avg_price"]])
    final = final.sort_values(["expected_util","weekday","hour"]).reset_index(drop=True)

    if final.empty:
        st.success("No low-fill blocks detected under current thresholds.")
    else:
        # ---- Pretty table formatting ----
        pretty = final.copy()
        pretty["Hour"] = pretty["hour"].apply(hour_label)
        pretty["Expected Utilization"] = (pretty["expected_util"]*100).map(lambda x: f"{x:.2f}%")
        pretty["Average Price"] = pretty["avg_price"].map(lambda x: f"${x:.2f}")
        pretty["Suggested Discount"] = (pretty["suggested_discount"]*100).map(lambda x: f"{x:.2f}%")
        pretty["New Price"] = pretty["new_price"].map(lambda x: f"${x:.2f}")
        pretty = pretty.rename(columns={"weekday":"Weekday"})
        # Reorder and drop raw cols
        pretty = pretty[["Weekday","Hour","Expected Utilization","Average Price","Suggested Discount","New Price"]]

        # Top single rec
        top = final.iloc[0]
        hour = int(top["hour"])
        hh = hour % 12 or 12
        ampm = "AM" if hour < 12 else "PM"
        st.subheader("Top Single Recommendation")
        st.markdown(
            f"**Block:** {top['weekday']} @ {hh}{ampm}  \n"
            f"**Expected Utilization:** {top['expected_util']*100:.2f}%  \n"
            f"**Average Price:** ${top['avg_price']:.2f}  \n"
            f"**Suggested Discount:** {(top['suggested_discount']*100):.2f}%  \n"
            f"**New Price:** ${top['new_price']:.2f}"
        )
        st.caption("One focused action to take right now. Full table below.")
        st.dataframe(pretty, use_container_width=True)

        st.download_button(
            "Download all suggestions (CSV)",
            data=pretty.to_csv(index=False).encode(),
            file_name="teeiq_dynamic_pricing_pretty.csv",
            mime="text/csv",
        )

        # ---- Labeled bar chart of expected utilization by hour (12h labels) ----
        st.subheader("Expected Utilization by Hour")
        chart_df = final.groupby("hour", as_index=False)["expected_util"].mean()
        chart_df["Hour"] = chart_df["hour"].apply(hour_label)
        fig, ax = plt.subplots(figsize=(10,3))
        ax.bar(chart_df["Hour"], chart_df["expected_util"]*100)
        ax.set_ylabel("Expected Utilization (%)")
        ax.set_xlabel("Hour of Day")
        for i, v in enumerate(chart_df["expected_util"]*100):
            ax.text(i, v + 1, f"{v:.0f}%", ha="center", va="bottom", fontsize=8)
        st.pyplot(fig, use_container_width=True)
