# ELD Trip Planner — Demo Presentation

## 3-minute talk track

"This project is an ELD trip planner built with Django and React. It takes a trip request with the current location, pickup, drop-off, and current cycle hours, then geocodes the locations using OpenStreetMap Nominatim, requests a route from OSRM, and calculates Hours of Service requirements for the trip. The backend applies FMCSA-style logic for driving limits, required breaks, rest periods, fuel stops, and daily log creation. The frontend renders the route on an OpenStreetMap map and presents trip summaries, route instructions, stop timelines, and ELD log sheets. It uses free public APIs and is designed for a small assessment/demo environment, with assumptions clearly documented for property-carrying operations."

## Demo checklist

1. Open the deployed frontend.
2. Confirm the map tiles load immediately.
3. Enter a sample trip such as Chicago → Indianapolis → Columbus.
4. Click Plan trip.
5. Show:
   - route map
   - summary cards
   - stop timeline
   - route instructions
   - daily logs
6. Explain the HOS assumptions used.
7. Mention the app uses OpenStreetMap Nominatim and OSRM with no paid API key.

## Live app checklist

- Frontend hosted on Vercel
- Backend hosted on Render
- `VITE_API_BASE_URL` points to the Render backend
- OpenStreetMap map loads without errors
- API responds successfully at `/api/health/`

## Delivery notes

- Share the GitHub repository URL.
- Share the live frontend URL.
- Share the Render backend URL if needed for testing.
- Record a short Loom or screen-share walkthrough.
