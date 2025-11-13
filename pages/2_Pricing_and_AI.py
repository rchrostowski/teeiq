import streamlit as st
from datetime import date, timedelta
import matplotlib.pyplot as plt
import pandas as pd

from teeiq.data_utils import clean_teetimes, add_time_bins, fmt_time_ampm
from teeiq.model import train_model, expected_utilization
from teeiq.weather import fetch_daily_weather
from teeiq.geo import geocode_address


st.header("Pricing & AI (Combined)")


# ---------- Data gate ----------
if "tee_df" not in st.session_state or st.session_state["tee_df"].empty:
    st.info("Load tee times on the main page first.")
    st.stop()

df = clean_teetimes(st.session_state["tee_df"])


# ---------- Location & Weather ----------
with st.expander("Location & Weather (type the street address)"):
    addr = st.text_input(
        "Full course address",
        help="Example: 110 Championship Way, Ponte Vedra Beach, FL 32082",
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

    # Use last known coords if we have them
    if "geo_latlon" in st.session_state and (lat is None or lon is None):
        lat, lon = st.session_state["geo_latlon"]

    # Manual fallback always available
    m1, m2 = st.columns(2)
    with m1:
        lat = st.number_input(
            "Latitude",
            value=lat if lat is not None else 30.19924,
            format="%.5f",
        )
    with m2:
        lon = st.number_input(
            "Longitude",
            value=lon if lon is not None else -81.39402,
            format="%.5f",
        )
    st.caption("Tip: For TPC Sawgrass, the clubhouse area is roughly 30.19924, -81.39402.")

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
    else:
        weather_df = None


# ---------- Tee-time interval + settings ----------
slot_minutes = st.selectbox(
    "Tee-time interval",
    options=[5, 7, 8, 9, 10, 12, 15],
    index=[5, 7, 8, 9, 10, 12, 15].index(10),
    help="Choose the spacing between tee times. Pricing & AI will use this granularity.",
)

top_n = st.slider(
    "How many low-fill blocks to show",
    min_value=5,
    max_value=30,
    value=10,
    step=1,
    help="We always surface at least this many lowest-utilization blocks.",
)

target_util = st.slider(
    "Target utilization for pricing model",
    min_value=0.5,
    max_value=0.95,
    value=0.75,
    step=0.01,
)


# ---------- Helper: compute low-fill blocks (always returns something if data exists) ----------
def compute_low_fill_blocks(df_base: pd.DataFrame,
                            weather_df: pd.DataFrame | None,
                            slot_minutes: int,
                            target: float,
                            top_n: int) -> pd.DataFrame:
    # Slot the tee times
    tmp = add_time_bins(df_base, slot_minutes=slot_minutes)

    # Aggregate by slot
    grp = tmp.groupby(["weekday", "slot_index", "slot_label", "slot_hour", "slot_minute"]).agg(
        slots=("booked", "size"),
        booked=("booked", "sum"),
        avg_price=("price", "mean"),
    ).reset_index()

    # Drop empty-slot rows
    grp = grp[grp["slots"] > 0].copy()
    if grp.empty:
        return grp  # no data

    grp["util"] = grp["booked"] / grp["slots"]

    # Predict expected utilization with model if possible
    try:
        clf = train_model(df_base, weather_df, slot_minutes=slot_minutes)
        util_pred = expected_utilization(clf, df_base, weather_df, slot_minutes=slot_minutes)
        grp = grp.merge(
            util_pred[
                ["weekday", "slot_index", "slot_label", "slot_hour", "slot_minute", "expected_util"]
            ],
            on=["weekday", "slot_index", "slot_label", "slot_hour", "slot_minute"],
            how="left",
        )
        grp["expected_util"] = grp["expected_util"].fillna(grp["util"])
    except Exception:
        grp["expected_util"] = grp["util"]

    # Sort by expected utilization (lowest first)
    grp = grp.sort_values(["expected_util", "weekday", "slot_index"]).reset_index(drop=True)

    # Take the bottom N blocks
    grp = grp.head(top_n).copy()

    # Pricing logic: more aggressive discount for softer slots
    gap = (target - grp["expected_util"]).clip(lower=0)
    grp["suggested_discount"] = (0.10 + 0.20 * (gap / target)).clip(upper=0.35)
    grp["new_price"] = grp["avg_price"] * (1 - grp["suggested_discount"])

    return grp


# ---------- Button: generate suggestions ----------
if st.button("Generate pricing suggestions"):
    low_df = compute_low_fill_blocks(df, weather_df, slot_minutes, target_util, top_n)

    if low_df.empty:
        st.info("No tee-time data found to analyze.")
    else:
        # Pretty formatting
        pretty = low_df.copy()
        pretty = pretty.rename(columns={"weekday": "Weekday"})
        pretty["Time"] = pretty.apply(
            lambda r: fmt_time_ampm(int(r["slot_hour"]), int(r["slot_minute"])),
            axis=1,
        )
        pretty["Expected Utilization"] = (
            pretty["expected_util"] * 100
        ).map(lambda x: f"{x:.2f}%")
        pretty["Average Price"] = pretty["avg_price"].map(lambda x: f"${x:.2f}")
        pretty["Suggested Discount"] = (pretty["suggested_discount"] * 100).map(
            lambda x: f"{x:.2f}%"
        )
        pretty["New Price"] = pretty["new_price"].map(lambda x: f"${x:.2f}")

        pretty = pretty[
            [
                "Weekday",
                "Time",
                "Expected Utilization",
                "Average Price",
                "Suggested Discount",
                "New Price",
            ]
        ]

        # Top single recommendation
        top = low_df.iloc[0]
        st.subheader("Top Single Recommendation")
        st.markdown(
            f"**Block:** {top['weekday']} @ {fmt_time_ampm(int(top['slot_hour']), int(top['slot_minute']))}  \n"
            f"**Expected Utilization:** {top['expected_util']*100:.2f}%  \n"
            f"**Average Price:** ${top['avg_price']:.2f}  \n"
            f"**Suggested Discount:** {(top['suggested_discount']*100):.2f}%  \n"
            f"**New Price:** ${top['new_price']:.2f}"
        )

        st.caption("Lowest-utilization blocks to target with pricing and promotions.")
        st.dataframe(pretty, use_container_width=True)

        # CSV download
        st.download_button(
            "Download all suggestions (CSV)",
            data=pretty.to_csv(index=False).encode(),
            file_name=f"teeiq_dynamic_pricing_{slot_minutes}min.csv",
            mime="text/csv",
        )

        # Simple bar chart of expected utilization
        chart_df = low_df.copy()
        chart_df["Time"] = chart_df.apply(
            lambda r: fmt_time_ampm(int(r["slot_hour"]), int(r["slot_minute"])),
            axis=1,
        )
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.bar(chart_df["Time"], chart_df["expected_util"] * 100)
        ax.set_ylabel("Expected Utilization (%)")
        ax.set_xlabel("Time of Day (softest blocks left)")
        ax.tick_params(axis="x", labelrotation=90)
        for i, v in enumerate(chart_df["expected_util"] * 100):
            ax.text(i, v + 1, f"{v:.0f}%", ha="center", va="bottom", fontsize=8)
        st.pyplot(fig, use_container_width=True)


