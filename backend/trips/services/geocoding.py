"""OpenStreetMap Nominatim geocoding service.

This module intentionally uses Nominatim directly (no Photon fallback). It
implements the public-service requirements that matter for this assessment:

* a custom application User-Agent;
* no autocomplete calls (only explicit Plan Trip requests);
* a process-wide rate limiter of at most one request per second;
* Django caching so repeated addresses do not hit Nominatim again;
* optional contact e-mail passed as both `email` query parameter and `From`.
"""

import re
import threading
import time
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache

COORD_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$")

_SESSION = requests.Session()
_LOCK = threading.Lock()
_LAST_REQUEST_AT = 0.0


class GeocodingError(Exception):
    pass


def _headers() -> dict[str, str]:
    user_agent = (getattr(settings, "NOMINATIM_USER_AGENT", "") or "").strip()
    if not user_agent:
        user_agent = "ELDTripPlanner/2.0"

    headers = {
        "User-Agent": user_agent,
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }
    contact = (getattr(settings, "NOMINATIM_CONTACT_EMAIL", "") or "").strip()
    if contact:
        headers["From"] = contact
    return headers


def _nominatim_get(path: str, params: dict[str, Any]) -> Any:
    """GET JSON from Nominatim while enforcing the public rate limit."""
    global _LAST_REQUEST_AT

    base = settings.NOMINATIM_BASE_URL.rstrip("/")
    url = f"{base}/{path.lstrip('/')}"
    request_params = dict(params)

    contact = (getattr(settings, "NOMINATIM_CONTACT_EMAIL", "") or "").strip()
    if contact:
        request_params["email"] = contact

    min_interval = max(float(settings.NOMINATIM_MIN_INTERVAL_SECONDS), 1.0)

    with _LOCK:
        wait_for = min_interval - (time.monotonic() - _LAST_REQUEST_AT)
        if wait_for > 0:
            time.sleep(wait_for)

        try:
            response = _SESSION.get(
                url,
                params=request_params,
                headers=_headers(),
                timeout=20,
            )
        except requests.RequestException as exc:
            raise GeocodingError(
                f"Cannot connect to OpenStreetMap Nominatim: {exc}"
            ) from exc
        finally:
            _LAST_REQUEST_AT = time.monotonic()

    if response.status_code == 403:
        raise GeocodingError(
            "OpenStreetMap Nominatim returned 403 Forbidden. "
            "Make sure NOMINATIM_USER_AGENT identifies this app, optionally set "
            "NOMINATIM_CONTACT_EMAIL in backend/.env, then restart Django."
        )
    if response.status_code == 429:
        raise GeocodingError(
            "OpenStreetMap Nominatim rate limit was reached. Wait a few seconds and try again."
        )

    try:
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise GeocodingError(
            f"OpenStreetMap Nominatim request failed ({response.status_code})."
        ) from exc
    except ValueError as exc:
        raise GeocodingError("OpenStreetMap Nominatim returned invalid JSON.") from exc


def geocode_location(query: str) -> dict[str, Any]:
    query = (query or "").strip()
    if not query:
        raise GeocodingError("Location cannot be empty.")

    coordinate_match = COORD_RE.match(query)
    if coordinate_match:
        lat = float(coordinate_match.group(1))
        lon = float(coordinate_match.group(2))
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise GeocodingError(f"Coordinates are out of range: {query}")
        return {"name": query, "lat": lat, "lon": lon, "source": "coordinates"}

    cache_key = f"nominatim:forward:v3:{query.lower()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    data = _nominatim_get(
        "search",
        {
            "q": query,
            "format": "jsonv2",
            "limit": 1,
            "addressdetails": 1,
        },
    )

    if not isinstance(data, list) or not data:
        raise GeocodingError(f"OpenStreetMap could not find '{query}'.")

    item = data[0]
    result = {
        "name": item.get("display_name") or query,
        "lat": float(item["lat"]),
        "lon": float(item["lon"]),
        "source": "OpenStreetMap Nominatim",
        "osm_type": item.get("osm_type"),
        "osm_id": item.get("osm_id"),
    }
    cache.set(cache_key, result, settings.NOMINATIM_CACHE_SECONDS)
    return result


def _city_state_from_address(address: dict[str, Any]) -> str:
    city = (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("municipality")
        or address.get("county")
        or address.get("hamlet")
    )
    state = address.get("state") or address.get("state_district")
    country_code = (address.get("country_code") or "").upper()

    parts = [p for p in (city, state) if p]
    if country_code and country_code != "US":
        parts.append(country_code)
    return ", ".join(dict.fromkeys(parts))


def reverse_geocode_city_state(lat: float, lon: float) -> str:
    rounded_lat = round(float(lat), 4)
    rounded_lon = round(float(lon), 4)
    fallback = f"{rounded_lat:.4f}, {rounded_lon:.4f}"
    cache_key = f"nominatim:reverse:v3:{rounded_lat}:{rounded_lon}"

    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        data = _nominatim_get(
            "reverse",
            {
                "lat": rounded_lat,
                "lon": rounded_lon,
                "format": "jsonv2",
                "zoom": 10,
                "addressdetails": 1,
            },
        )
        address = data.get("address") or {}
        label = _city_state_from_address(address) or data.get("display_name") or fallback
    except GeocodingError:
        # Reverse geocoding is supplemental to the HOS calculation. If a stop
        # label cannot be resolved, keep the trip usable with coordinates.
        label = fallback

    cache.set(cache_key, label, settings.NOMINATIM_CACHE_SECONDS)
    return label
