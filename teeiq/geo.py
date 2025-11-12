import requests
from functools import lru_cache

OPEN_METEO_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
NOMINATIM = "https://nominatim.openstreetmap.org/search"

@lru_cache(maxsize=256)
def geocode_address(address: str):
    """
    Free, reliable geocoding with safe fallbacks:
    1) Open-Meteo Geocoding API (no key)
    2) OSM Nominatim (as a backup)
    Returns (lat, lon) or None.
    """
    if not address or not address.strip():
        return None

    # 1) Try Open-Meteo Geocoding first
    try:
        r = requests.get(OPEN_METEO_GEOCODE, params={"name": address, "count": 1}, timeout=15)
        r.raise_for_status()
        js = r.json()
        results = js.get("results") or []
        if results:
            lat = float(results[0]["latitude"])
            lon = float(results[0]["longitude"])
            return lat, lon
    except Exception:
        pass

    # 2) Fallback to Nominatim (rate-limited, so keep as backup)
    try:
        headers = {"User-Agent": "TeeIQ/1.0 (contact: hello@example.com)"}  # please change to your contact email
        r = requests.get(NOMINATIM, params={"q": address, "format": "json", "limit": 1}, headers=headers, timeout=15)
        r.raise_for_status()
        js = r.json()
        if js:
            lat = float(js[0]["lat"])
            lon = float(js[0]["lon"])
            return lat, lon
    except Exception:
        pass

    return None
