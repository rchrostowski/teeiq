import numpy as np
import pandas as pd
from .data_utils import WEEK_ORDER

def kpis(df: pd.DataFrame):
    total = len(df)
    booked = int(df["booked"].sum())
    util = booked / total if total else 0.0
    revenue = float(df.loc[df["booked"], "price"].sum())
    potential = float(df.loc[~df["booked"], "price"].sum())
    return total, booked, util, revenue, potential

def utilization_matrix(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["weekday"] = pd.Categorical(df["weekday"], categories=WEEK_ORDER, ordered=True)
    grp = df.groupby(["weekday","hour"]).agg(slots=("booked","size"), booked=("booked","sum"))
    grp["util"] = np.where(grp["slots"]>0, grp["booked"]/grp["slots"], np.nan)
    return grp["util"].unstack("hour").sort_index()

def daily_utilization(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("date").agg(util=("booked","mean")).reset_index()
