"""Driving routing through the free public OSRM demo service."""

import requests
from django.conf import settings

METERS_PER_MILE = 1609.344


class RoutingError(Exception):
    pass


def _instruction_text(step: dict) -> str:
    maneuver = step.get("maneuver", {})
    mtype = (maneuver.get("type") or "continue").replace("_", " ")
    modifier = maneuver.get("modifier")
    road = step.get("name") or "the road"
    if modifier:
        return f"{mtype.title()} {modifier} onto {road}"
    return f"{mtype.title()} onto {road}"


def get_route(points: list[dict]) -> dict:
    if len(points) < 2:
        raise RoutingError("At least two route points are required.")

    coords = ";".join(f"{p['lon']},{p['lat']}" for p in points)
    url = f"{settings.OSRM_BASE_URL}/{coords}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "true",
        "alternatives": "false",
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers={"User-Agent": "ELDTripPlanner/2.0"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise RoutingError(f"Cannot connect to the OSRM routing service: {exc}") from exc
    except ValueError as exc:
        raise RoutingError("OSRM returned invalid JSON.") from exc

    if data.get("code") != "Ok" or not data.get("routes"):
        raise RoutingError(data.get("message") or "No driving route was found.")

    route = data["routes"][0]
    legs = []
    instructions = []

    for leg_index, leg in enumerate(route.get("legs", [])):
        legs.append({
            "distance_miles": leg.get("distance", 0) / METERS_PER_MILE,
            "duration_hours": leg.get("duration", 0) / 3600.0,
        })
        for step in leg.get("steps", []):
            instructions.append({
                "leg_index": leg_index,
                "instruction": _instruction_text(step),
                "distance_miles": round(step.get("distance", 0) / METERS_PER_MILE, 2),
                "duration_minutes": round(step.get("duration", 0) / 60.0, 1),
            })

    return {
        "distance_miles": route["distance"] / METERS_PER_MILE,
        "duration_hours": route["duration"] / 3600.0,
        "geometry": route["geometry"],
        "legs": legs,
        "instructions": instructions,
        "source": "OSRM / OpenStreetMap road data",
    }
