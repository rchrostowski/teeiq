import streamlit as st
import pandas as pd
from . import adapters
from .data_utils import clean_teetimes

VENDORS = {
    "Generic/Manual": None,
    "Lightspeed": adapters.from_lightspeed,
    "Chronogolf": adapters.from_chronogolf,
    "GolfNow": adapters.from_golfnow,
}

def mapping_widget(df: pd.DataFrame) -> pd.DataFrame:
    st.write("### Map Your Columns")
    cols = list(df.columns)
    tee_col = st.selectbox("Which column = tee_time?", cols, key="map_tee")
    price_col = st.selectbox("Which column = price?", cols, key="map_price")
    booked_col = st.selectbox("Which column = booked?", cols, key="map_booked")
    tmp = df.rename(columns={tee_col: "tee_time", price_col: "price", booked_col: "booked"})
    return clean_teetimes(tmp)

def import_flow() -> pd.DataFrame:
    st.subheader("Import Tee Sheet")
    vendor = st.selectbox("Source vendor", list(VENDORS.keys()))
    file = st.file_uploader("Upload CSV", type=["csv"])
    if not file:
        st.info("Upload a CSV to continue.")
        return pd.DataFrame()
    raw = pd.read_csv(file)

    if VENDORS[vendor] is not None:
        try:
            df = VENDORS[vendor](raw)
            st.success(f"Imported using {vendor} adapter.")
            return df
        except Exception as e:
            st.warning(f"Adapter failed: {e}. Falling back to manual mapping.")

    # Manual mapping fallback
    return mapping_widget(raw)
