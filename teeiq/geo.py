import re
import requests
from functools import lru_cache

OPEN_METEO_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
NOMINATIM = "https://nominatim.openstreetmap.org/search"

_COORD_RE = re.compile(
    r"(-?\d{1,3}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)"
)

def _parse_coords_any(s: str):
    """Extract lat,lon from raw text or a Maps URL (e.g., '@30.19,-81.39', 'q=30.19,-81.39', or '30.19,-81.39')."""
    if not s:
        return None
    # @lat,lon patterns from Google/Apple/Bing
    m = re.search(r"@(-?\d{1,3}\.\d+),(-?\d{1,3}\.\d+)", s)
    if m:
        return float(m.group(1)), float(m.group(2))
    # q=lat,lon in querystring
    m = re.search(r"[?&]q=(-?\d{1,3}\.\d+),(-?\d{1,3}\.\d+)", s)
    if m:
        return float(m.group(1)), float(m.group(2))
    # plain "lat, lon"
    m = _COORD_RE.search(s)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None

@lru_cache(maxsize=256)
def geocode_candidates(query: str):
    """
    Return a list of (name, lat, lon, source) candidates using:
      1) Open-Meteo Geocoding (no key)
      2) OSM Nominatim (backup)
    Tries multiple query variants for courses.
    """
    out = []

    if not query or not query.strip():
        return out

    # 0) If user pasted a URL or "lat,lon", short-circuit
    coord = _parse_coords_any(query)
    if coord:
        lat, lon = coord
        return [("Manual Coordinates", lat, lon, "manual")]

    variants = [
        query,
        f"{query} golf course",
        f"{query} golf",
        query.replace("TPC", "TPC Golf").strip(),  # e.g., "TPC Sawgrass" → "TPC Golf Sawgrass"
    ]

    # 1) Open-Meteo (fast, generous)
    tried = set()
    for v in variants:
        if v in tried: 
            continue
        tried.add(v)
        try:
            r = requests.get(OPEN_METEO_GEOCODE, params={"name": v, "count": 5}, timeout=15)
            r.raise_for_status()
            js = r.json()
            for it in (js.get("results") or []):
                name = ", ".join([p for p in [it.get("name"), it.get("admin1"), it.get("country")] if p])
                out.append((name or v, float(it["latitude"]), float(it["longitude"]), "open-meteo"))
        except Exception:
            pass

    if out:
        # de-dup by (lat,lon)
        seen = set()
        uniq = []
        for name, lat, lon, src in out:
            key = (round(lat, 5), round(lon, 5))
            if key not in seen:
                seen.add(key)
                uniq.append((name, lat, lon, src))
        return uniq

    # 2) Nominatim backup (respect rate limits)
    headers = {"User-Agent": "TeeIQ/1.0 (contact: replace-with-your-email@example.com)"}
    for v in variants:
        try:
            r = requests.get(NOMINATIM, params={"q": v, "format": "jsonv2", "limit": 5}, headers=headers, timeout=15)
            r.raise_for_status()
            js = r.json()
            for it in js or []:
                disp = it.get("display_name") or v
                out.append((disp, float(it["lat"]), float(it["lon"]), "nominatim"))
        except Exception:
            pass

    # Final de-dup
    seen = set()
    uniq = []
    for name, lat, lon, src in out:
        key = (round(lat, 5), round(lon, 5))
        if key not in seen:
            seen.add(key)
            uniq.append((name, lat, lon, src))
    return uniq

