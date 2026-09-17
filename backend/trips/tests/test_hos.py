from datetime import datetime, timezone

from trips.services.hos import HOSPlanner, build_daily_logs


def start():
    return datetime(2026, 9, 16, 8, 0, tzinfo=timezone.utc)


def kinds(events):
    return [e.kind for e in events]


def test_inserts_30_minute_break_after_eight_hours():
    planner = HOSPlanner(start(), current_cycle_used=0)
    events = planner.plan([
        {"distance_miles": 500, "duration_hours": 8.5},
        {"distance_miles": 50, "duration_hours": 1.0},
    ])
    assert "hos_break" in kinds(events)
    brk = next(e for e in events if e.kind == "hos_break")
    assert round(brk.duration_hours, 2) == 0.5


def test_inserts_ten_hour_rest_after_eleven_driving_hours():
    planner = HOSPlanner(start(), current_cycle_used=0)
    events = planner.plan([
        {"distance_miles": 700, "duration_hours": 12.0},
        {"distance_miles": 1, "duration_hours": 0.02},
    ])
    assert "daily_rest" in kinds(events)
    assert sum(e.duration_hours for e in events if e.kind == "driving") > 12


def test_cycle_restart_when_70_hour_limit_is_reached():
    planner = HOSPlanner(start(), current_cycle_used=69)
    events = planner.plan([
        {"distance_miles": 100, "duration_hours": 2.0},
        {"distance_miles": 1, "duration_hours": 0.02},
    ])
    assert "cycle_restart" in kinds(events)
    restart = next(e for e in events if e.kind == "cycle_restart")
    assert round(restart.duration_hours, 1) == 34.0


def test_fuel_stop_at_1000_miles_or_less():
    planner = HOSPlanner(start(), current_cycle_used=0)
    events = planner.plan([
        {"distance_miles": 1100, "duration_hours": 20.0},
        {"distance_miles": 5, "duration_hours": 0.1},
    ])
    fuels = [e for e in events if e.kind == "fuel"]
    assert fuels
    assert fuels[0].end_mile <= 1000.01


def test_daily_logs_total_24_hours():
    planner = HOSPlanner(start(), current_cycle_used=0)
    events = planner.plan([
        {"distance_miles": 100, "duration_hours": 2.0},
        {"distance_miles": 200, "duration_hours": 4.0},
    ])
    logs = build_daily_logs(events)
    assert logs
    for log in logs:
        assert abs(log["total_hours"] - 24.0) < 0.01


def test_daily_logs_include_logbook_metadata_and_status_remarks():
    planner = HOSPlanner(start(), current_cycle_used=0)
    events = planner.plan([
        {"distance_miles": 100, "duration_hours": 2.0},
        {"distance_miles": 200, "duration_hours": 4.0},
    ])
    events[0].location_text = "Chicago, IL"
    for event in events:
        if event.kind == "pickup":
            event.location_text = "Denver, CO"
        elif event.kind == "dropoff":
            event.location_text = "Los Angeles, CA"
        elif not event.location_text:
            event.location_text = "Route location"

    logs = build_daily_logs(events, {"driver_name": "John Doe", "timezone_abbr": "CDT"})
    assert logs[0]["metadata"]["driver_name"] == "John Doe"
    assert logs[0]["remarks"]
    assert all("location" in remark and "activity" in remark for log in logs for remark in log["remarks"])


def test_event_serialization_preserves_terminal_clock_display():
    planner = HOSPlanner(start(), current_cycle_used=0)
    event = planner.plan([
        {"distance_miles": 10, "duration_hours": 0.2},
        {"distance_miles": 10, "duration_hours": 0.2},
    ])[0]
    serialized = event.to_dict()
    assert serialized["start_local"].startswith("2026-09-16 08:00")
    assert "timezone_abbr" in serialized
