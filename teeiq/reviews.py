import pandas as pd

KEYWORDS = {
    "pace": ["slow","pace","waiting","backed up"],
    "greens": ["greens","condition","speed"],
    "price": ["expensive","price","value"],
    "staff": ["staff","friendly","rude"],
    "booking": ["tee time","booking","availability"],
}

def summarize_reviews(df_reviews: pd.DataFrame) -> pd.DataFrame:
    df = df_reviews.copy()
    text_col = next((c for c in df.columns if df[c].dtype == object), None)
    if text_col is None:
        return pd.DataFrame(columns=["theme","mentions"])
    texts = df[text_col].dropna().astype(str).str.lower()
    out = []
    for theme, words in KEYWORDS.items():
        count = int(texts.str.contains("|".join([pd.regex.escape(w) for w in words])).sum())
        out.append({"theme": theme, "mentions": count})
    return pd.DataFrame(out).sort_values("mentions", ascending=False)
