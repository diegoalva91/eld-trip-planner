# ELD Trip Planner — Django + React + OpenStreetMap/Nominatim

This project implements the full-stack driver-assessment application with **Django REST Framework** and **React/Vite**.

## Map stack (no paid API key)

The map implementation is explicit and visible in the source:

- **OpenStreetMap Standard tiles** — rendered in the browser by React Leaflet from `https://tile.openstreetmap.org/{z}/{x}/{y}.png`.
- **OpenStreetMap Nominatim** — Django performs forward and reverse geocoding with `https://nominatim.openstreetmap.org/search` and `/reverse`.
- **OSRM** — calculates the driving route and turn-by-turn steps from the coordinates returned by Nominatim.
- The OpenStreetMap base map renders **before** the user clicks Plan Trip, so you can immediately verify that map tiles are connected.

No OpenStreetMap or Nominatim API key is required for this assessment/demo. The public Nominatim service must be used responsibly: the backend sends a custom User-Agent, caches results, never implements autocomplete, and enforces at least one second between Nominatim calls.

## Requirements

- Python 3.11 or 3.12 recommended
- Node.js 20+
- npm
- Git (optional)

## 1. Start the Django backend (Windows PowerShell)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver 8000
```

Backend should be available at:

```text
http://127.0.0.1:8000/api/health/
```

### Nominatim configuration

Open `backend/.env` and keep/set:

```env
NOMINATIM_BASE_URL=https://nominatim.openstreetmap.org
NOMINATIM_USER_AGENT=ELDTripPlanner/2.0
NOMINATIM_CONTACT_EMAIL=your-real-email@example.com
NOMINATIM_MIN_INTERVAL_SECONDS=1.1
```

A contact email is recommended for a deployed assessment. After changing `.env`, restart Django.

## 2. Start React

Open another terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173/
```

The base OpenStreetMap should appear immediately. A status pill says **OpenStreetMap tiles connected** once visible tiles load.

## 3. Test a trip

Example:

- Current location: `Chicago, IL`
- Pickup: `Indianapolis, IN`
- Drop-off: `Columbus, OH`
- Current cycle used: `10`

Click **Plan trip**. The backend will:

1. geocode all three typed locations using OpenStreetMap Nominatim;
2. request a driving route from OSRM;
3. calculate HOS driving/break/rest/fuel events;
4. reverse-geocode planned stop coordinates using Nominatim where practical;
5. return the GeoJSON route to React;
6. draw the route, markers, stop information, instructions, and ELD daily logs.

## Where the OpenStreetMap code is

### Browser map tiles

`frontend/src/components/RouteMap.jsx`

```jsx
<TileLayer
  url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
  attribution='&copy; OpenStreetMap contributors'
/>
```

### Nominatim geocoding

`backend/trips/services/geocoding.py`

Forward geocoding calls:

```text
https://nominatim.openstreetmap.org/search
```

Reverse geocoding calls:

```text
https://nominatim.openstreetmap.org/reverse
```

## If Nominatim returns 403

1. Make sure you are using this regenerated project, not an older folder.
2. Check `backend/.env` and use a custom value such as `NOMINATIM_USER_AGENT=ELDTripPlanner/2.0`.
3. Add your real email to `NOMINATIM_CONTACT_EMAIL` for a deployed submission.
4. Stop and restart Django after changing `.env`.
5. Do not repeatedly click Plan Trip many times per second; the public service is rate-limited.

You can also enter a location as `latitude,longitude` (for example `41.8781,-87.6298`). In that case forward geocoding is not needed, but the map and routing still work.

## Assessment assumptions implemented

- Property-carrying driver
- 70 hours / 8 days
- 11-hour driving limit
- 14-hour driving window
- 30-minute break after 8 cumulative driving hours
- 10-hour daily rest
- 34-hour cycle restart when necessary
- 1 hour at pickup
- 1 hour at drop-off
- fuel at least every 1,000 miles
- no adverse driving conditions
- daily ELD-style log sheets with 24-hour / 15-minute grid and four duty-status lines

## Run tests

```powershell
cd backend
.venv\Scripts\Activate.ps1
pytest
```

## Deploy to Vercel + Render

### 1) Deploy the backend to Render

- Create a new Web Service on Render
- Connect this repository
- Set the root directory to `backend`
- Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
- Add environment variables from `backend/.env.example`
- Set `DJANGO_ALLOWED_HOSTS` to your Render domain
- Set `CORS_ALLOWED_ORIGINS` to your Vercel frontend URL

### 2) Deploy the frontend to Vercel

- Import the repository into Vercel
- Set the project root to the repository root
- Set environment variable:
  - `VITE_API_BASE_URL=https://your-render-service.onrender.com/api`
- Deploy

### 3) Verify the live app

1. Open the Vercel frontend URL
2. Confirm the OpenStreetMap map loads immediately
3. Submit a trip such as Chicago → Indianapolis → Columbus
4. Confirm the route and daily logs render correctly


## Important note about public services

OpenStreetMap's public tile and Nominatim servers are community-funded, best-effort services. This implementation is appropriate for a small assessment/demo. For a production fleet or high-volume application, use a hosted provider or self-host the relevant services.
