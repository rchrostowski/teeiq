import streamlit as st
from datetime import date, timedelta
from teeiq.data_utils import clean_teetimes
from teeiq.model import train_model, expected_utilization, dynamic_price_suggestion
from teeiq.weather import fetch_daily_weather

st.header("Predictive Pricing (RandomForest + Weather)")

if "tee_df" not in st.session_state or st.session_state["tee_df"].empty:
    st.info("Load tee times on the main page first.")
    st.stop()

df = clean_teetimes(st.session_state["tee_df"])

# Weather inputs
st.subheader("Weather (Open-Meteo)")
lat = st.number_input("Latitude", value=27.9506, format="%.6f")
lon = st.number_input("Longitude", value=-82.4572, format="%.6f")
start = st.date_input("Start date", value=date.today())
end = st.date_input("End date", value=date.today() + timedelta(days=6))

weather_df = None
if st.button("Fetch weather"):
    weather_df = fetch_daily_weather(lat, lon, start.isoformat(), end.isoformat())
    st.write(weather_df.head())

if st.button("Train model & suggest prices"):
    clf = train_model(df, weather_df)
    util_df = expected_utilization(clf, df, weather_df)
    recs = dynamic_price_suggestion(util_df)
    st.subheader("Expected Utilization by (Weekday, Hour)")
    st.dataframe(util_df, use_container_width=True)
    st.subheader("Dynamic Price Suggestions")
    st.dataframe(recs, use_container_width=True)
