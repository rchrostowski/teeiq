import pandas as pd
from .data_utils import clean_teetimes

# Example CSV header mappings. Adjust as needed to match real exports.
def from_lightspeed(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "Start Time": "tee_time",
        "Green Fee": "price",
        "Booked": "booked",
    }
    tmp = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
    return clean_teetimes(tmp)

def from_chronogolf(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "time": "tee_time",
        "rate": "price",
        "is_booked": "booked",
    }
    tmp = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
    return clean_teetimes(tmp)

def from_golfnow(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "teeTime": "tee_time",
        "price": "price",
        "status": "booked",  # 'sold'/'open'
    }
    tmp = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
    if "booked" in tmp.columns:
        tmp["booked"] = tmp["booked"].astype(str).str.lower().isin(["sold","1","true","yes"])
    return clean_teetimes(tmp)
