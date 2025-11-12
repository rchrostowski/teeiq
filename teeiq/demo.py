from datetime import datetime, timedelta
import numpy as np
import pandas as pd

def make_demo_teetimes(days=21, slots_per_hour=4, hours=(6,18), seed=7):
    rng = np.random.default_rng(seed)
    start_date = (datetime.now() - timedelta(days=days//2)).date()
    rows = []
    for d in range(days):
        base = datetime.combine(start_date + timedelta(days=d), datetime.min.time())
        for hour in range(hours[0], hours[1]):
            for k in range(slots_per_hour):
                tee_dt = base + timedelta(hours=hour, minutes=15*k)
                price = 45 + 25*(8 <= hour <= 14) + 15*(hour >= 15)
                if tee_dt.weekday() >= 5:
                    price += 20
                price = max(25, price + rng.normal(0,5))
                demand = 0.55 + 0.25*(hour in {8,9,10}) + 0.15*(hour in {15,16})
                demand += 0.15 if tee_dt.weekday() >= 5 else 0
                booked = rng.random() < max(0.05, min(0.95, demand))
                rows.append({"tee_time": tee_dt, "price": round(price,2), "booked": booked, "holes": 18, "source": "public"})
    return pd.DataFrame(rows)
