from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from django.core.cache import cache

from trips.services.geocoding import GeocodingError, geocode_location, reverse_geocode_city_state


@override_settings(
    NOMINATIM_BASE_URL="https://nominatim.example",
    NOMINATIM_USER_AGENT="ELDTripPlannerTests/1.0",
    NOMINATIM_CONTACT_EMAIL="",
    NOMINATIM_MIN_INTERVAL_SECONDS=1.0,
    NOMINATIM_CACHE_SECONDS=3600,
)
class NominatimGeocodingTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def _response(self, payload, status=200):
        response = Mock()
        response.status_code = status
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        return response

    @patch("trips.services.geocoding._SESSION.get")
    @patch("trips.services.geocoding.time.sleep")
    def test_forward_geocode_uses_nominatim(self, _sleep, get):
        get.return_value = self._response([
            {
                "display_name": "Chicago, Cook County, Illinois, United States",
                "lat": "41.8755616",
                "lon": "-87.6244212",
                "osm_type": "relation",
                "osm_id": 122604,
            }
        ])
        result = geocode_location("Chicago, IL")
        self.assertAlmostEqual(result["lat"], 41.8755616)
        self.assertEqual(result["source"], "OpenStreetMap Nominatim")
        args, kwargs = get.call_args
        self.assertTrue(args[0].endswith("/search"))
        self.assertEqual(kwargs["headers"]["User-Agent"], "ELDTripPlannerTests/1.0")

    @patch("trips.services.geocoding._SESSION.get")
    @patch("trips.services.geocoding.time.sleep")
    def test_reverse_geocode_city_state(self, _sleep, get):
        get.return_value = self._response({
            "display_name": "Denver, Colorado, United States",
            "address": {"city": "Denver", "state": "Colorado", "country_code": "us"},
        })
        self.assertEqual(reverse_geocode_city_state(39.7392, -104.9903), "Denver, Colorado")

    def test_raw_coordinates_do_not_call_network(self):
        result = geocode_location("41.88,-87.63")
        self.assertEqual(result["source"], "coordinates")

    @patch("trips.services.geocoding._SESSION.get")
    @patch("trips.services.geocoding.time.sleep")
    def test_403_has_helpful_message(self, _sleep, get):
        response = self._response({}, status=403)
        get.return_value = response
        with self.assertRaises(GeocodingError) as context:
            geocode_location("Somewhere unique test 403")
        self.assertIn("NOMINATIM_USER_AGENT", str(context.exception))
