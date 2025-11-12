import requests

def geocode_address(address: str):
    """Free geocoding using OpenStreetMap Nominatim (no key). Respect rate limits."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": "TeeIQ/1.0 (education; contact: example@example.com)"}
    r = requests.get(url, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    js = r.json()
    if not js:
        return None
    lat = float(js[0]["lat"]); lon = float(js[0]["lon"])
    return lat, lon
