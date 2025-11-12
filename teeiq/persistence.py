import os
from sqlalchemy import create_engine
import pandas as pd

DB_URL = os.getenv("DATABASE_URL", "sqlite:///teeiq.db")
engine = create_engine(DB_URL, future=True)

def save_teetimes(df: pd.DataFrame, course_id: str):
    df = df.copy()
    df["course_id"] = course_id
    df.to_sql("tee_times", engine, if_exists="append", index=False)

def load_teetimes(course_id: str) -> pd.DataFrame:
    try:
        return pd.read_sql("SELECT * FROM tee_times WHERE course_id = :cid", engine, params={"cid": course_id})
    except Exception:
        return pd.DataFrame()
