import { useEffect, useMemo, useState } from 'react'
import L from 'leaflet'
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from 'react-leaflet'

const DEFAULT_CENTER = [39.5, -98.35]

const icon = (label, cls) => L.divIcon({
  className: `map-marker ${cls}`,
  html: `<span>${label}</span>`,
  iconSize: [36, 36],
  iconAnchor: [18, 18],
})

const icons = {
  current: icon('C', 'current'),
  pickup: icon('P', 'pickup'),
  dropoff: icon('D', 'dropoff'),
  break: icon('B', 'break'),
  rest: icon('R', 'rest'),
  restart: icon('34', 'restart'),
  fuel: icon('F', 'fuel'),
}

function FitBounds({ positions }) {
  const map = useMap()

  useEffect(() => {
    if (positions.length > 1) {
      map.fitBounds(positions, { padding: [36, 36], maxZoom: 10 })
    } else if (positions.length === 1) {
      map.setView(positions[0], 9)
    }
  }, [map, positions])

  return null
}

export default function RouteMap({ result }) {
  const [tileStatus, setTileStatus] = useState('loading')

  const routeCoords = useMemo(() => {
    const coordinates = result?.route?.geometry?.coordinates || []
    return coordinates.map(([lon, lat]) => [lat, lon])
  }, [result])

  const mapPoints = useMemo(() => {
    if (routeCoords.length) return routeCoords
    if (!result) return []
    const { current, pickup, dropoff } = result.locations
    return [
      [current.lat, current.lon],
      [pickup.lat, pickup.lon],
      [dropoff.lat, dropoff.lon],
    ]
  }, [result, routeCoords])

  const current = result?.locations?.current
  const pickup = result?.locations?.pickup
  const dropoff = result?.locations?.dropoff

  return (
    <div className="map-wrap">
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={4}
        scrollWheelZoom
        className="osm-map"
      >
        <TileLayer
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          maxZoom={19}
          eventHandlers={{
            loading: () => setTileStatus('loading'),
            load: () => setTileStatus('online'),
            tileerror: () => setTileStatus('error'),
          }}
        />

        {mapPoints.length > 0 && <FitBounds positions={mapPoints} />}

        {routeCoords.length > 1 && (
          <Polyline positions={routeCoords} weight={5} opacity={0.9} />
        )}

        {current && (
          <Marker position={[current.lat, current.lon]} icon={icons.current}>
            <Popup><strong>Current location</strong><br />{current.name}</Popup>
          </Marker>
        )}
        {pickup && (
          <Marker position={[pickup.lat, pickup.lon]} icon={icons.pickup}>
            <Popup><strong>Pickup</strong><br />{pickup.name}</Popup>
          </Marker>
        )}
        {dropoff && (
          <Marker position={[dropoff.lat, dropoff.lon]} icon={icons.dropoff}>
            <Popup><strong>Drop-off</strong><br />{dropoff.name}</Popup>
          </Marker>
        )}

        {(result?.stops || [])
          .filter((stop) => !['pickup', 'dropoff'].includes(stop.type))
          .filter((stop) => Number.isFinite(stop.lat) && Number.isFinite(stop.lon))
          .map((stop, index) => (
            <Marker
              key={`${stop.type}-${index}-${stop.start}`}
              position={[stop.lat, stop.lon]}
              icon={icons[stop.type] || icons.break}
            >
              <Popup>
                <strong>{stop.label}</strong><br />
                {stop.location && <>{stop.location}<br /></>}
                Approx. route mile {stop.mile}<br />
                {stop.start_local}
              </Popup>
            </Marker>
          ))}
      </MapContainer>

      <div className={`map-connection map-connection--${tileStatus}`}>
        <span className="map-connection__dot" />
        {tileStatus === 'online' && 'OpenStreetMap tiles connected'}
        {tileStatus === 'loading' && 'Connecting to OpenStreetMap…'}
        {tileStatus === 'error' && 'OpenStreetMap tile connection failed'}
      </div>

      <div className="map-provider-strip">
        <span>Map: OpenStreetMap</span>
        <span>Geocoding: Nominatim</span>
        <span>Routing: OSRM</span>
      </div>

      {result && (
        <div className="map-legend">
          <span><b>C</b> Current</span>
          <span><b>P</b> Pickup</span>
          <span><b>D</b> Drop-off</span>
          <span><b>B</b> Break</span>
          <span><b>R</b> 10h rest</span>
          <span><b>34</b> Restart</span>
          <span><b>F</b> Fuel</span>
        </div>
      )}
    </div>
  )
}
