import numpy as np
import pandas as pd
from .data_utils import WEEK_ORDER

def low_fill_opportunities(df: pd.DataFrame, util_threshold=0.6, min_slots=8) -> pd.DataFrame:
    df = df.copy()
    df["weekday"] = pd.Categorical(df["weekday"], categories=WEEK_ORDER, ordered=True)
    agg = df.groupby(["weekday","hour"]).agg(
        slots=("booked","size"),
        booked=("booked","sum"),
        avg_price=("price","mean"),
    ).reset_index()
    agg["util"] = np.where(agg["slots"]>0, agg["booked"]/agg["slots"], np.nan)
    opp = agg[(agg["slots"]>=min_slots) & (agg["util"]<util_threshold)].copy()

    target = 0.75
    gap = (target - opp["util"]).clip(lower=0)
    opp["suggested_discount"] = (0.10 + 0.20 * (gap/target)).clip(upper=0.35)
    opp["new_price"] = opp["avg_price"] * (1 - opp["suggested_discount"])
    opp["expected_additional_bookings"] = (opp["slots"] * (target - opp["util"]).clip(lower=0)).round().astype(int)
    opp["est_monthly_lift"] = (opp["expected_additional_bookings"] * opp["new_price"]).round(2)
    return opp.sort_values(["weekday","hour"])
