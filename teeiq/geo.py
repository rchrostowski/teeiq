import requests
from functools import lru_cache

# Known-course hardcoded fallbacks (feel free to add more)
KNOWN_COURSE_COORDS = {
    # "exact address string lowercased": (lat, lon)
    "110 championship way, ponte vedra beach, fl 32082":
        (30.19924, -81.39402),  # TPC Sawgrass (Stadium Course clubhouse area)
}

OPEN_METEO_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"

@lru_cache(maxsize=512)
def geocode_address(address: str):
    """
    Input: full street address (e.g., '110 Championship Way, Ponte Vedra Beach, FL 32082')
    Returns: (lat, lon) or None
    Order:
      1) KNOWN_COURSE_COORDS exact match (lowercased)
      2) Open-Meteo Geocoding (no key, free)
    """
    if not address or not address.strip():
        return None
    key = address.strip().lower()

    # 1) Hardcoded fallback for popular courses / demo reliability
    if key in KNOWN_COURSE_COORDS:
        return KNOWN_COURSE_COORDS[key]

    # 2) Open-Meteo Geocoding
    try:
        r = requests.get(OPEN_METEO_GEOCODE, params={"name": address, "count": 1}, timeout=15)
        r.raise_for_status()
        js = r.json()
        results = js.get("results") or []
        if results:
            return float(results[0]["latitude"]), float(results[0]["longitude"])
    except Exception:
        pass

    return None


