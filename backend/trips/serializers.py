from rest_framework import serializers


US_TIMEZONES = (
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "America/Phoenix",
    "America/Anchorage",
    "Pacific/Honolulu",
)


class TripPlanRequestSerializer(serializers.Serializer):
    current_location = serializers.CharField(max_length=255)
    pickup_location = serializers.CharField(max_length=255)
    dropoff_location = serializers.CharField(max_length=255)
    current_cycle_used = serializers.FloatField(min_value=0, max_value=70)
    start_datetime = serializers.DateTimeField(required=False)
    home_terminal_timezone = serializers.ChoiceField(choices=US_TIMEZONES, default="America/Chicago")

    # Optional logbook details. These are not required by the assessment's four core inputs,
    # but allow the generated sheet to match a real driver log much more closely.
    driver_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    driver_number = serializers.CharField(max_length=80, required=False, allow_blank=True)
    driver_initials = serializers.CharField(max_length=20, required=False, allow_blank=True)
    co_driver = serializers.CharField(max_length=120, required=False, allow_blank=True)
    carrier_name = serializers.CharField(max_length=160, required=False, allow_blank=True)
    main_office_address = serializers.CharField(max_length=220, required=False, allow_blank=True)
    home_terminal = serializers.CharField(max_length=160, required=False, allow_blank=True)
    tractor_number = serializers.CharField(max_length=80, required=False, allow_blank=True)
    trailer_number = serializers.CharField(max_length=80, required=False, allow_blank=True)
    shipper = serializers.CharField(max_length=160, required=False, allow_blank=True)
    commodity = serializers.CharField(max_length=160, required=False, allow_blank=True)
    load_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
