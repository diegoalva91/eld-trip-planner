from datetime import datetime
from zoneinfo import ZoneInfo

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .serializers import TripPlanRequestSerializer
from .services.geocoding import GeocodingError, geocode_location, reverse_geocode_city_state
from .services.routing import RoutingError, get_route
from .services.hos import HOSPlanner, attach_stop_coordinates, build_daily_logs, summarize


@api_view(["GET"])
def health(request):
    return Response({
        "status": "ok",
        "map_tiles": "OpenStreetMap Standard",
        "geocoding": "OpenStreetMap Nominatim",
        "routing": "OSRM",
    })


def _clean(value, fallback=""):
    value = (value or "").strip()
    return value or fallback


@api_view(["POST"])
def plan_trip(request):
    serializer = TripPlanRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    try:
        current = geocode_location(data["current_location"])
        pickup = geocode_location(data["pickup_location"])
        dropoff = geocode_location(data["dropoff_location"])
        route = get_route([current, pickup, dropoff])
    except (GeocodingError, RoutingError) as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    timezone_name = data["home_terminal_timezone"]
    terminal_tz = ZoneInfo(timezone_name)
    supplied_start = data.get("start_datetime")
    if supplied_start:
        start = supplied_start.astimezone(terminal_tz)
    else:
        start = datetime.now(terminal_tz)

    planner = HOSPlanner(start=start, current_cycle_used=data["current_cycle_used"])
    events = planner.plan(route["legs"])

    stops = attach_stop_coordinates(events, route["geometry"])
    stop_by_event = {}
    for stop in stops:
        event_index = stop["event_index"]
        if stop["type"] == "pickup":
            stop.update({"lat": pickup["lat"], "lon": pickup["lon"], "location": data["pickup_location"]})
        elif stop["type"] == "dropoff":
            stop.update({"lat": dropoff["lat"], "lon": dropoff["lon"], "location": data["dropoff_location"]})
        else:
            stop["location"] = reverse_geocode_city_state(stop["lat"], stop["lon"])
        stop_by_event[event_index] = stop["location"]

    # Put a city/state (or coordinate fallback) on each status transition so the
    # logbook remarks can identify where each change occurred.
    last_location = data["current_location"]
    for index, event in enumerate(events):
        if event.kind == "pickup":
            event.location_text = data["pickup_location"]
        elif event.kind == "dropoff":
            event.location_text = data["dropoff_location"]
        elif index in stop_by_event:
            event.location_text = stop_by_event[index]
        else:
            event.location_text = last_location
        if event.location_text:
            last_location = event.location_text

    metadata = {
        "driver_name": _clean(data.get("driver_name"), "Driver Name"),
        "driver_number": _clean(data.get("driver_number"), "N/A"),
        "driver_initials": _clean(data.get("driver_initials"), "N/A"),
        "co_driver": _clean(data.get("co_driver"), "N/A"),
        "carrier_name": _clean(data.get("carrier_name"), "ELD Trip Planner Demo"),
        "main_office_address": _clean(data.get("main_office_address"), "N/A"),
        "home_terminal": _clean(data.get("home_terminal"), data["current_location"]),
        "tractor_number": _clean(data.get("tractor_number"), "N/A"),
        "trailer_number": _clean(data.get("trailer_number"), "N/A"),
        "shipper": _clean(data.get("shipper"), "N/A"),
        "commodity": _clean(data.get("commodity"), "N/A"),
        "load_id": _clean(data.get("load_id"), "N/A"),
        "home_terminal_timezone": timezone_name,
        "timezone_abbr": start.tzname() or timezone_name,
        "dropoff_location": data["dropoff_location"],
    }

    response = {
        "map_providers": {
            "tiles": "OpenStreetMap Standard",
            "geocoding": "OpenStreetMap Nominatim",
            "routing": "OSRM",
        },
        "locations": {
            "current": current,
            "pickup": pickup,
            "dropoff": dropoff,
        },
        "route": {
            "geometry": route["geometry"],
            "source": route.get("source", "OSRM / OpenStreetMap road data"),
            "distance_miles": round(route["distance_miles"], 1),
            "duration_hours": round(route["duration_hours"], 2),
            "instructions": route["instructions"],
        },
        "summary": summarize(events, route["distance_miles"], route["duration_hours"]),
        "events": [e.to_dict() for e in events],
        "stops": stops,
        "daily_logs": build_daily_logs(events, metadata),
        "logbook": metadata,
        "assumptions": [
            "Property-carrying CMV, 70-hour/8-day cycle",
            "Fresh 11-hour/14-hour daily clock at trip start because only current cycle hours are provided",
            "No adverse driving conditions",
            "30-minute non-driving break after 8 cumulative driving hours",
            "Fuel at least every 1,000 miles; each planned fuel stop is 30 minutes on duty",
            "Pickup and drop-off are 1 hour each on duty/not driving",
            "34-hour restart is used when the 70-hour cycle is exhausted",
            f"Log times are shown in the home-terminal timezone: {timezone_name}",
            "No split-sleeper calculation",
        ],
    }
    return Response(response)
