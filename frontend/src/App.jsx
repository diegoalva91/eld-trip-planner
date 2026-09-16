import { useState } from 'react'
import { planTrip } from './api'
import TripForm from './components/TripForm'
import RouteMap from './components/RouteMap'
import SummaryCards from './components/SummaryCards'
import Timeline from './components/Timeline'
import RouteInstructions from './components/RouteInstructions'
import DailyLogs from './components/DailyLogs'

export default function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(values) {
    setLoading(true)
    setError('')
    try {
      const data = await planTrip(values)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero__badge">FMCSA HOS · OpenStreetMap</div>
        <h1>ELD Trip Planner</h1>
        <p>
          Plan a property-carrying trip with OpenStreetMap, calculate required HOS
          stops, and generate daily driver log sheets.
        </p>
      </header>

      <main className="main-grid">
        <section className="panel form-panel">
          <TripForm onSubmit={handleSubmit} loading={loading} />
          {error && <div className="error-box">{error}</div>}
          <div className="rules-note">
            <strong>Planner assumptions</strong>
            <span>70 hrs / 8 days · 11-hour drive · 14-hour window · 30-min break after 8 driving hrs</span>
          </div>
        </section>

        <section className="panel map-panel">
          {/* The OpenStreetMap base map is rendered immediately, even before a trip is planned. */}
          <RouteMap result={result} />
        </section>
      </main>

      {result && (
        <div className="results-stack">
          <SummaryCards summary={result.summary} />
          <Timeline events={result.events} />
          <RouteInstructions instructions={result.route.instructions} />
          <DailyLogs logs={result.daily_logs} />
          <section className="panel assumptions-panel">
            <h2>Assumptions used</h2>
            <ul>
              {result.assumptions.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </section>
        </div>
      )}
    </div>
  )
}
