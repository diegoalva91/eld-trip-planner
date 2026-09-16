from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, time
from math import asin, cos, radians, sin, sqrt
from typing import Iterable

MAX_DRIVE_HOURS = 11.0
MAX_WINDOW_HOURS = 14.0
BREAK_AFTER_DRIVE_HOURS = 8.0
BREAK_HOURS = 0.5
DAILY_RESET_HOURS = 10.0
CYCLE_LIMIT_HOURS = 70.0
CYCLE_RESTART_HOURS = 34.0
FUEL_INTERVAL_MILES = 1000.0
FUEL_STOP_HOURS = 0.5
PICKUP_HOURS = 1.0
DROPOFF_HOURS = 1.0
EPS = 1e-7

STATUS_OFF = "off_duty"
STATUS_SB = "sleeper_berth"
STATUS_DRIVE = "driving"
STATUS_ON = "on_duty_not_driving"


@dataclass
class Event:
    kind: str
    label: str
    start: datetime
    end: datetime
    status: str
    start_mile: float
    end_mile: float
    location_type: str | None = None
    location_text: str | None = None

    @property
    def duration_hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600.0

    def to_dict(self) -> dict:
        result = asdict(self)
        result["start"] = self.start.isoformat()
        result["end"] = self.end.isoformat()
        result["start_local"] = self.start.strftime("%Y-%m-%d %H:%M")
        result["end_local"] = self.end.strftime("%Y-%m-%d %H:%M")
        result["timezone_abbr"] = self.start.tzname() or ""
        result["duration_hours"] = round(self.duration_hours, 3)
        result["start_mile"] = round(self.start_mile, 2)
        result["end_mile"] = round(self.end_mile, 2)
        return result


class HOSPlanner:
    """Deterministic HOS scheduler for the assessment's simplified assumptions.

    Daily clocks are assumed fresh at trip start because the assessment only provides
    current cycle hours, not the driver's current daily clock or prior eight days.
    """

    def __init__(self, start: datetime, current_cycle_used: float):
        self.now = start
        self.cycle_used = float(current_cycle_used)
        self.drive_today = 0.0
        self.drive_since_break = 0.0
        self.window_start: datetime | None = None
        self.miles_since_fuel = 0.0
        self.route_mile = 0.0
        self.events: list[Event] = []

    def _append(self, *, kind: str, label: str, hours: float, status: str,
                end_mile: float | None = None, location_type: str | None = None) -> Event:
        start_mile = self.route_mile
        if end_mile is None:
            end_mile = start_mile
        start = self.now
        end = start + timedelta(hours=hours)
        event = Event(
            kind=kind,
            label=label,
            start=start,
            end=end,
            status=status,
            start_mile=start_mile,
            end_mile=end_mile,
            location_type=location_type,
        )
        self.events.append(event)
        self.now = end
        self.route_mile = end_mile
        return event

    def _start_window_if_needed(self):
        if self.window_start is None:
            self.window_start = self.now

    def _window_remaining(self) -> float:
        if self.window_start is None:
            return MAX_WINDOW_HOURS
        elapsed = (self.now - self.window_start).total_seconds() / 3600.0
        return MAX_WINDOW_HOURS - elapsed

    def _daily_reset(self, hours: float = DAILY_RESET_HOURS, label: str = "10-hour sleeper berth rest"):
        self._append(
            kind="daily_rest",
            label=label,
            hours=hours,
            status=STATUS_SB,
            location_type="rest",
        )
        self.drive_today = 0.0
        self.drive_since_break = 0.0
        self.window_start = None

    def _cycle_restart(self):
        self._append(
            kind="cycle_restart",
            label="34-hour restart (70-hour/8-day cycle)",
            hours=CYCLE_RESTART_HOURS,
            status=STATUS_SB,
            location_type="restart",
        )
        self.cycle_used = 0.0
        self.drive_today = 0.0
        self.drive_since_break = 0.0
        self.window_start = None

    def _break(self):
        self._append(
            kind="hos_break",
            label="30-minute HOS break",
            hours=BREAK_HOURS,
            status=STATUS_OFF,
            location_type="break",
        )
        self.drive_since_break = 0.0

    def _fuel(self):
        self._start_window_if_needed()
        self._append(
            kind="fuel",
            label="Fuel stop (30 minutes)",
            hours=FUEL_STOP_HOURS,
            status=STATUS_ON,
            location_type="fuel",
        )
        self.cycle_used += FUEL_STOP_HOURS
        # A consecutive 30-minute on-duty/not-driving period satisfies the break.
        self.drive_since_break = 0.0
        self.miles_since_fuel = 0.0

    def _on_duty(self, hours: float, label: str, kind: str, location_type: str):
        self._start_window_if_needed()
        self._append(
            kind=kind,
            label=label,
            hours=hours,
            status=STATUS_ON,
            location_type=location_type,
        )
        self.cycle_used += hours
        if hours >= BREAK_HOURS - EPS:
            self.drive_since_break = 0.0

    def _ensure_can_drive(self):
        if self.cycle_used >= CYCLE_LIMIT_HOURS - EPS:
            self._cycle_restart()
            return False
        if self.drive_today >= MAX_DRIVE_HOURS - EPS:
            self._daily_reset()
            return False
        if self._window_remaining() <= EPS:
            self._daily_reset()
            return False
        if self.drive_since_break >= BREAK_AFTER_DRIVE_HOURS - EPS:
            self._break()
            return False
        return True

    def drive_leg(self, distance_miles: float, duration_hours: float, label: str):
        if distance_miles <= EPS or duration_hours <= EPS:
            self.route_mile += max(0.0, distance_miles)
            return

        miles_remaining = float(distance_miles)
        hours_remaining = float(duration_hours)

        while hours_remaining > EPS and miles_remaining > EPS:
            if not self._ensure_can_drive():
                continue

            self._start_window_if_needed()
            speed = miles_remaining / hours_remaining
            if speed <= EPS:
                raise ValueError("Route leg has invalid average speed")

            limits = [
                hours_remaining,
                MAX_DRIVE_HOURS - self.drive_today,
                BREAK_AFTER_DRIVE_HOURS - self.drive_since_break,
                self._window_remaining(),
                CYCLE_LIMIT_HOURS - self.cycle_used,
            ]

            miles_to_fuel = FUEL_INTERVAL_MILES - self.miles_since_fuel
            if miles_to_fuel <= EPS:
                self._fuel()
                continue
            limits.append(miles_to_fuel / speed)

            chunk_h = max(0.0, min(limits))
            if chunk_h <= EPS:
                # The next loop will trigger the appropriate reset/break action.
                if self.cycle_used >= CYCLE_LIMIT_HOURS - EPS:
                    self._cycle_restart()
                elif self.drive_today >= MAX_DRIVE_HOURS - EPS or self._window_remaining() <= EPS:
                    self._daily_reset()
                elif self.drive_since_break >= BREAK_AFTER_DRIVE_HOURS - EPS:
                    self._break()
                elif self.miles_since_fuel >= FUEL_INTERVAL_MILES - EPS:
                    self._fuel()
                else:
                    raise RuntimeError("HOS planner could not make progress")
                continue

            chunk_miles = min(miles_remaining, speed * chunk_h)
            end_mile = self.route_mile + chunk_miles
            self._append(
                kind="driving",
                label=label,
                hours=chunk_h,
                status=STATUS_DRIVE,
                end_mile=end_mile,
            )
            self.drive_today += chunk_h
            self.drive_since_break += chunk_h
            self.cycle_used += chunk_h
            self.miles_since_fuel += chunk_miles
            miles_remaining -= chunk_miles
            hours_remaining -= chunk_h

            # If the chunk ends exactly at the fuel interval, take fuel now. A fuel
            # stop also satisfies the 30-minute break if both become due together.
            if self.miles_since_fuel >= FUEL_INTERVAL_MILES - 1e-5 and hours_remaining > EPS:
                self._fuel()

    def plan(self, legs: list[dict]) -> list[Event]:
        if len(legs) != 2:
            raise ValueError("Assessment route must contain exactly two legs: current->pickup and pickup->dropoff")

        self.drive_leg(legs[0]["distance_miles"], legs[0]["duration_hours"], "Drive to pickup")
        self._on_duty(PICKUP_HOURS, "Pickup (1 hour)", "pickup", "pickup")
        self.drive_leg(legs[1]["distance_miles"], legs[1]["duration_hours"], "Drive to drop-off")
        self._on_duty(DROPOFF_HOURS, "Drop-off (1 hour)", "dropoff", "dropoff")
        return self.events


def haversine_miles(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1 = a
    lon2, lat2 = b
    r = 3958.7613
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    x = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(x))


def point_at_route_mile(coordinates: list[list[float]], target_mile: float) -> dict | None:
    if not coordinates:
        return None
    if target_mile <= 0:
        return {"lon": coordinates[0][0], "lat": coordinates[0][1]}

    cumulative = 0.0
    for i in range(1, len(coordinates)):
        a = tuple(coordinates[i - 1])
        b = tuple(coordinates[i])
        segment = haversine_miles(a, b)
        if cumulative + segment >= target_mile and segment > EPS:
            ratio = (target_mile - cumulative) / segment
            lon = a[0] + (b[0] - a[0]) * ratio
            lat = a[1] + (b[1] - a[1]) * ratio
            return {"lon": lon, "lat": lat}
        cumulative += segment

    return {"lon": coordinates[-1][0], "lat": coordinates[-1][1]}


def attach_stop_coordinates(events: Iterable[Event], geometry: dict) -> list[dict]:
    coords = geometry.get("coordinates", [])
    stops = []
    for event_index, event in enumerate(events):
        if not event.location_type:
            continue
        # A stop/rest happens at the current route mile (end mile for driving, unchanged for stop events).
        point = point_at_route_mile(coords, event.end_mile)
        if point:
            stops.append(
                {
                    "event_index": event_index,
                    "type": event.location_type,
                    "label": event.label,
                    "start": event.start.isoformat(),
                    "end": event.end.isoformat(),
                    "start_local": event.start.strftime("%Y-%m-%d %H:%M"),
                    "end_local": event.end.strftime("%Y-%m-%d %H:%M"),
                    "mile": round(event.end_mile, 1),
                    **point,
                }
            )
    return stops


def _split_event_by_day(event: Event):
    cursor = event.start
    total_seconds = max((event.end - event.start).total_seconds(), 1.0)
    while cursor < event.end:
        next_midnight = datetime.combine(cursor.date() + timedelta(days=1), time.min, tzinfo=cursor.tzinfo)
        chunk_end = min(event.end, next_midnight)
        fraction_start = (cursor - event.start).total_seconds() / total_seconds
        fraction_end = (chunk_end - event.start).total_seconds() / total_seconds
        start_mile = event.start_mile + (event.end_mile - event.start_mile) * fraction_start
        end_mile = event.start_mile + (event.end_mile - event.start_mile) * fraction_end
        yield cursor, chunk_end, start_mile, end_mile
        cursor = chunk_end


def _hour_value(dt: datetime) -> float:
    return dt.hour + dt.minute / 60 + dt.second / 3600


def build_daily_logs(events: list[Event], metadata: dict | None = None) -> list[dict]:
    if not events:
        return []

    metadata = metadata or {}
    first_day = events[0].start.date()
    last_day = events[-1].end.date()
    if events[-1].end.time() == time.min:
        last_day = last_day - timedelta(days=1)

    days = {}
    day = first_day
    while day <= last_day:
        days[day.isoformat()] = {
            "date": day.isoformat(),
            "segments": [],
            "remarks": [],
            "miles_driven": 0.0,
            "metadata": dict(metadata),
        }
        day += timedelta(days=1)

    previous_status = None
    for event in events:
        for start, end, start_mile, end_mile in _split_event_by_day(event):
            key = start.date().isoformat()
            if key not in days:
                continue
            end_hour = 24.0 if end.date() != start.date() else _hour_value(end)
            days[key]["segments"].append(
                {
                    "start": round(_hour_value(start), 4),
                    "end": round(end_hour, 4),
                    "status": event.status,
                    "label": event.label,
                }
            )
            if event.status == STATUS_DRIVE:
                days[key]["miles_driven"] += max(0.0, end_mile - start_mile)

        # Add a log remark at each duty-status change (and for pickup/drop/fuel activities).
        should_remark = event.status != previous_status or event.kind in {"pickup", "dropoff", "fuel"}
        if should_remark:
            key = event.start.date().isoformat()
            if key in days:
                location = event.location_text or "Location unavailable"
                days[key]["remarks"].append(
                    {
                        "time": event.start.strftime("%H:%M"),
                        "hour": round(_hour_value(event.start), 4),
                        "status": event.status,
                        "location": location,
                        "activity": event.label,
                        "text": f"{location} — {event.label}",
                    }
                )
        previous_status = event.status

    # The generated trip ends after drop-off. Record the automatic change to off duty
    # so the final status transition also appears in the remarks section.
    final = events[-1]
    final_key = final.end.date().isoformat()
    if final.end.time() != time.min and final_key in days:
        location = final.location_text or metadata.get("dropoff_location") or "Location unavailable"
        days[final_key]["remarks"].append(
            {
                "time": final.end.strftime("%H:%M"),
                "hour": round(_hour_value(final.end), 4),
                "status": STATUS_OFF,
                "location": location,
                "activity": "Off duty — trip complete",
                "text": f"{location} — Off duty / trip complete",
            }
        )

    result = []
    for key in sorted(days):
        item = days[key]
        raw = sorted(item["segments"], key=lambda seg: seg["start"])
        filled = []
        cursor = 0.0
        for seg in raw:
            if seg["start"] > cursor + 1e-4:
                filled.append({"start": cursor, "end": seg["start"], "status": STATUS_OFF, "label": "Off duty"})
            filled.append(seg)
            cursor = max(cursor, seg["end"])
        if cursor < 24.0 - 1e-4:
            filled.append({"start": cursor, "end": 24.0, "status": STATUS_OFF, "label": "Off duty"})

        merged = []
        for seg in filled:
            if merged and merged[-1]["status"] == seg["status"] and abs(merged[-1]["end"] - seg["start"]) < 1e-4:
                merged[-1]["end"] = seg["end"]
            else:
                merged.append(dict(seg))

        totals = {STATUS_OFF: 0.0, STATUS_SB: 0.0, STATUS_DRIVE: 0.0, STATUS_ON: 0.0}
        for seg in merged:
            totals[seg["status"]] += seg["end"] - seg["start"]

        item["segments"] = merged
        item["miles_driven"] = round(item["miles_driven"], 1)
        item["totals"] = {k: round(v, 2) for k, v in totals.items()}
        item["total_hours"] = round(sum(totals.values()), 2)
        item["on_duty_total"] = round(totals[STATUS_DRIVE] + totals[STATUS_ON], 2)
        result.append(item)
    return result


def summarize(events: list[Event], route_distance_miles: float, route_duration_hours: float) -> dict:
    if not events:
        return {}
    trip_elapsed = (events[-1].end - events[0].start).total_seconds() / 3600.0
    return {
        "route_distance_miles": round(route_distance_miles, 1),
        "route_driving_hours": round(route_duration_hours, 2),
        "planned_elapsed_hours": round(trip_elapsed, 2),
        "driving_hours": round(sum(e.duration_hours for e in events if e.status == STATUS_DRIVE), 2),
        "on_duty_not_driving_hours": round(sum(e.duration_hours for e in events if e.status == STATUS_ON), 2),
        "off_duty_break_hours": round(sum(e.duration_hours for e in events if e.status == STATUS_OFF), 2),
        "sleeper_hours": round(sum(e.duration_hours for e in events if e.status == STATUS_SB), 2),
        "fuel_stops": sum(e.kind == "fuel" for e in events),
        "hos_breaks": sum(e.kind == "hos_break" for e in events),
        "daily_rests": sum(e.kind == "daily_rest" for e in events),
        "cycle_restarts": sum(e.kind == "cycle_restart" for e in events),
        "start": events[0].start.isoformat(),
        "finish": events[-1].end.isoformat(),
    }
