import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

def featurize(tee_df: pd.DataFrame, weather_df: pd.DataFrame|None=None):
    df = tee_df.copy()
    df["is_weekend"] = df["tee_time"].dt.weekday >= 5
    if weather_df is not None and not weather_df.empty:
        w = weather_df[["date","temperature_2m_max","precipitation_sum"]].rename(
            columns={"temperature_2m_max":"temp_max","precipitation_sum":"precip"}
        )
        df = df.merge(w, on="date", how="left")
    else:
        df["temp_max"] = np.nan
        df["precip"] = np.nan

    X = pd.DataFrame({
        "hour": df["hour"],
        "is_weekend": df["is_weekend"].astype(int),
        "price": df["price"],
        "temp_max": df["temp_max"],
        "precip": df["precip"],
    }).fillna(method="ffill").fillna(method="bfill")
    y = df["booked"].astype(int)
    return X, y

def train_model(tee_df: pd.DataFrame, weather_df: pd.DataFrame|None=None) -> RandomForestClassifier:
    X, y = featurize(tee_df, weather_df)
    clf = RandomForestClassifier(n_estimators=200, random_state=7)
    clf.fit(X, y)
    return clf

def expected_utilization(clf: RandomForestClassifier, tee_df: pd.DataFrame, weather_df: pd.DataFrame|None=None) -> pd.DataFrame:
    X, _ = featurize(tee_df, weather_df)
    proba = clf.predict_proba(X)[:,1]
    out = tee_df[["date","weekday","hour","price"]].copy()
    out["p_book"] = proba
    agg = out.groupby(["weekday","hour"]).agg(expected_util=("p_book","mean"), avg_price=("price","mean")).reset_index()
    return agg

def dynamic_price_suggestion(util_df: pd.DataFrame, target=0.75) -> pd.DataFrame:
    df = util_df.copy()
    gap = (target - df["expected_util"]).clip(lower=0)
    df["suggested_discount"] = (0.10 + 0.20 * (gap/target)).clip(upper=0.35)
    df["new_price"] = df["avg_price"] * (1 - df["suggested_discount"])
    return df
