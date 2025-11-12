import requests
import pandas as pd

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"

def fetch_daily_weather(lat: float, lon: float, start: str, end: str) -> pd.DataFrame:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": ["temperature_2m_max","temperature_2m_min","precipitation_sum","windspeed_10m_max"],
        "timezone": "auto",
    }
    r = requests.get(OPEN_METEO, params=params, timeout=20)
    r.raise_for_status()
    js = r.json()
    daily = js.get("daily", {})
    df = pd.DataFrame(daily)
    if not df.empty:
        df.rename(columns={"time": "date"}, inplace=True)
        df["date"] = pd.to_datetime(df["date"]).dt.date
    return df
