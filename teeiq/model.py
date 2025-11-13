import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from .data_utils import add_time_bins

def featurize(tee_df: pd.DataFrame, weather_df: pd.DataFrame|None=None, slot_minutes: int = 10):
    df = add_time_bins(tee_df, slot_minutes=slot_minutes).copy()
    df["is_weekend"] = df["tee_time"].dt.weekday >= 5

    if weather_df is not None and not weather_df.empty:
        w = weather_df[["date","temperature_2m_max","precipitation_sum"]].rename(
            columns={"temperature_2m_max":"temp_max","precipitation_sum":"precip"}
        )
        df = df.merge(w, on="date", how="left")
    else:
        df["temp_max"] = np.nan
        df["precip"] = np.nan

    minute_of_day = df["hour"]*60 + df["tee_time"].dt.minute
    X = pd.DataFrame({
        "slot_index": df["slot_index"],
        "minute_of_day": minute_of_day,
        "is_weekend": df["is_weekend"].astype(int),
        "price": df["price"],
        "temp_max": df["temp_max"],
        "precip": df["precip"],
    }).fillna(method="ffill").fillna(method="bfill")
    y = df["booked"].astype(int)
    meta = df[["date","weekday","hour","slot_index","slot_label"]]
    return X, y, meta

def train_model(tee_df: pd.DataFrame, weather_df: pd.DataFrame|None=None, slot_minutes: int = 10) -> RandomForestClassifier:
    X, y, _ = featurize(tee_df, weather_df, slot_minutes=slot_minutes)
    clf = RandomForestClassifier(n_estimators=200, random_state=7)
    clf.fit(X, y)
    return clf

def expected_utilization(clf: RandomForestClassifier, tee_df: pd.DataFrame, weather_df: pd.DataFrame|None=None, slot_minutes: int = 10, by="slot"):
    """by='slot' → (weekday, slot_index, slot_label); by='hour' → (weekday, hour)"""
    X, _, meta = featurize(tee_df, weather_df, slot_minutes=slot_minutes)
    proba = clf.predict_proba(X)[:,1]
    out = meta.copy()
    out["p_book"] = proba

    if by == "hour":
        agg = out.groupby(["weekday","hour"]).agg(expected_util=("p_book","mean")).reset_index()
    else:
        agg = out.groupby(["weekday","slot_index","slot_label"]).agg(
            expected_util=("p_book","mean"),
            hour=("hour","first")
        ).reset_index()
    return agg

def dynamic_price_suggestion(util_df: pd.DataFrame, target=0.75, price_col="avg_price"):
    df = util_df.copy()
    gap = (target - df["expected_util"]).clip(lower=0)
    df["suggested_discount"] = (0.10 + 0.20 * (gap/target)).clip(upper=0.35)
    if price_col not in df.columns:
        # If caller didn’t merge prices, default to 0 for safety
        df[price_col] = 0.0
    df["new_price"] = df[price_col] * (1 - df["suggested_discount"])
    return df
