import os, requests, pandas as pd, streamlit as st
from teeiq.reviews import summarize_reviews

st.header("Reviews & Sentiment")

st.caption("To auto-pull Google reviews, add a free SERPAPI key to your environment: SERPAPI_KEY='your_key_here' (serpapi.com).")

course = st.text_input("Course name")
town = st.text_input("Town/City + State (e.g., 'Ponte Vedra Beach, FL')")
serp_key = os.getenv("SERPAPI_KEY", "")

def fetch_google_reviews_with_serpapi(query: str, api_key: str) -> pd.DataFrame:
    # Find place
    s = requests.get(
        "https://serpapi.com/search.json",
        params={"engine": "google_maps", "q": query, "api_key": api_key},
        timeout=30,
    )
    s.raise_for_status()
    results = s.json().get("local_results", [])
    if not results:
        return pd.DataFrame()
    place_id = results[0].get("place_id")
    if not place_id:
        return pd.DataFrame()

    # Pull reviews
    r = requests.get(
        "https://serpapi.com/search.json",
        params={"engine": "google_maps_reviews", "place_id": place_id, "api_key": api_key},
        timeout=30,
    )
    r.raise_for_status()
    items = r.json().get("reviews", [])
    rows = [{"review_date": i.get("date"), "rating": i.get("rating"), "text": i.get("snippet")} for i in items]
    return pd.DataFrame(rows)

reviews_df = pd.DataFrame()

col1, col2 = st.columns(2)
with col1:
    if st.button("Fetch Google reviews (auto)"):
        if not course or not town:
            st.warning("Enter both course and town.")
        elif not serp_key:
            st.error("No SERPAPI_KEY set. Get a free key at serpapi.com and set it in your environment.")
        else:
            try:
                q = f"{course} {town}"
                reviews_df = fetch_google_reviews_with_serpapi(q, serp_key)
                if reviews_df.empty:
                    st.info("No reviews returned for that query.")
            except Exception as e:
                st.error(f"SERPAPI error: {e}")

with col2:
    file = st.file_uploader("Or upload reviews CSV (review_date, rating, text)", type=["csv"])
    if file:
        reviews_df = pd.read_csv(file)

if reviews_df.empty:
    st.stop()

# Display summary
if "rating" in reviews_df.columns:
    avg = pd.to_numeric(reviews_df["rating"], errors="coerce").mean()
    if pd.notna(avg):
        st.metric("Avg Rating", f"{avg:.2f}")
        st.progress(max(0.0, min(1.0, (avg - 1) / 4)))

summary = summarize_reviews(reviews_df)
st.subheader("Review Themes (keyword counts)")
st.dataframe(summary, use_container_width=True)

