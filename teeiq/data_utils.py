import numpy as np
import pandas as pd

WEEK_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

def coerce_bool(x):
    if isinstance(x, (bool, np.bool_)): return bool(x)
    if isinstance(x, (int, float)): return x == 1
    if isinstance(x, str): return x.strip().lower() in {"1","true","yes","y","sold","booked"}
    return False

def ensure_datetime_col(df: pd.DataFrame) -> pd.DataFrame:
    for c in ["tee_time","datetime","start_time","time","date_time"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
            if df[c].notna().any():
                df["tee_time"] = df[c]
                return df
    # try compose from date+time columns
    date_cols = [c for c in df.columns if "date" in c.lower()]
    time_cols = [c for c in df.columns if "time" in c.lower()]
    if date_cols and time_cols:
        df["tee_time"] = pd.to_datetime(
            df[date_cols[0]].astype(str) + " " + df[time_cols[0]].astype(str),
            errors="coerce"
        )
        if df["tee_time"].notna().any():
            return df
    raise ValueError("No datetime column found. Include 'tee_time' or (date + time).")

def clean_teetimes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = ensure_datetime_col(df)

    # price
    df["price"] = pd.to_numeric(df.get("price", np.nan), errors="coerce")

    # booked
    book_col = next((c for c in df.columns if c.lower() in {"booked","is_booked","reserved","filled","status"}), None)
    df["booked"] = df[book_col].apply(coerce_bool) if book_col else False

    # derived
    df["weekday"] = pd.Categorical(df["tee_time"].dt.day_name(), categories=WEEK_ORDER, ordered=True)
    df["hour"] = df["tee_time"].dt.hour
    df["date"] = df["tee_time"].dt.date

    # fill missing price w/group median then global median
    if df["price"].isna().any():
        grp_med = df.groupby(["weekday","hour"])["price"].transform("median")
        df["price"] = df["price"].fillna(grp_med).fillna(df["price"].median())

    return df.sort_values("tee_time").reset_index(drop=True)

