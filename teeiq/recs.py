import numpy as np
import pandas as pd
from .data_utils import WEEK_ORDER, add_time_bins

def low_fill_opportunities(
    df: pd.DataFrame,
    util_threshold: float = 0.6,
    min_slots: int = 8,
    slot_minutes: int = 10,
) -> pd.DataFrame:
    """
    Find low-fill opportunities at N-minute slot resolution.

    Returns columns:
    - weekday, slot_index, slot_label, hour, minute
    - slots, booked, avg_price, util
    - suggested_discount, new_price, expected_additional_bookings, est_monthly_lift
    """
    tmp = add_time_bins(df, slot_minutes=slot_minutes).copy()
    tmp["weekday"] = pd.Categorical(tmp["weekday"], categories=WEEK_ORDER, ordered=True)

    agg = tmp.groupby(["weekday", "slot_index", "slot_label"]).agg(
        slots=("booked", "size"),
        booked=("booked", "sum"),
        avg_price=("price", "mean"),
        hour=("hour", "first"),
        minute=("tee_time", lambda s: int(s.iloc[0].minute)),
    ).reset_index()

    agg["util"] = np.where(agg["slots"] > 0, agg["booked"] / agg["slots"], np.nan)

    # filter low-fill
    opp = agg[(agg["slots"] >= min_slots) & (agg["util"] < util_threshold)].copy()

    target = 0.75
    gap = (target - opp["util"]).clip(lower=0)
    opp["suggested_discount"] = (0.10 + 0.20 * (gap / target)).clip(upper=0.35)
    opp["new_price"] = opp["avg_price"] * (1 - opp["suggested_discount"])
    opp["expected_additional_bookings"] = (
        opp["slots"] * (target - opp["util"]).clip(lower=0)
    ).round().astype(int)
    opp["est_monthly_lift"] = (
        opp["expected_additional_bookings"] * opp["new_price"]
    ).round(2)

    return opp.sort_values(["weekday", "slot_index"])

