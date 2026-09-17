import { useState } from 'react'
import { planTrip } from './api'
import TripForm from './components/TripForm'
import RouteMap from './components/RouteMap'
import SummaryCards from './components/SummaryCards'
import Timeline from './components/Timeline'
import RouteInstructions from './components/RouteInstructions'
import DailyLogs from './components/DailyLogs'
import AccordionSection from './components/AccordionSection'

export default function App() {
  const [view, setView] = useState('home')
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

  if (view === 'home') {
    return (
      <div className="home-shell">
        <header className="site-nav">
          <button className="brand" type="button" onClick={() => setView('home')}>
            <span className="brand-mark">ELD</span>
            <span>Trip Planner</span>
          </button>
          <div className="nav-meta"><span className="status-dot status-dot--live" /> Open route intelligence</div>
          <button className="nav-link" type="button" onClick={() => setView('planner')}>Open planner <span aria-hidden="true">→</span></button>
        </header>

        <main className="home-main">
          <section className="home-hero">
            <div className="home-copy">
              <div className="eyebrow eyebrow--light">Built for the next mile</div>
              <h1>Know the road<br /><em>before you roll.</em></h1>
              <p className="home-lede">A calmer way to plan compliant freight trips. Map the route, place every required stop, and leave the yard with a clear daily log.</p>
              <div className="home-actions">
                <button className="primary-cta" type="button" onClick={() => setView('planner')}>Plan a trip <span aria-hidden="true">→</span></button>
                <span className="action-note">No account. No API key.</span>
              </div>
              <div className="home-trust"><span>FMCSA HOS logic</span><span>OpenStreetMap data</span><span>Driver-first output</span></div>
            </div>

            <div className="route-art" aria-label="Illustration of a planned route from Chicago to Los Angeles">
              <div className="route-art__top"><span>LIVE ROUTE PREVIEW</span><strong>2,015 mi</strong></div>
              <div className="route-art__map">
                <span className="route-grid route-grid--one" /><span className="route-grid route-grid--two" />
                <span className="route-line" /><span className="route-point route-point--start">C</span><span className="route-point route-point--end">D</span>
                <span className="route-stop route-stop--one">R</span><span className="route-stop route-stop--two">B</span><span className="route-stop route-stop--three">F</span>
              </div>
              <div className="route-art__footer"><span>Chicago, IL</span><span className="route-arrow">→</span><span>Los Angeles, CA</span></div>
            </div>
          </section>

          <section className="home-proof">
            <div><strong>01</strong><h2>Start with the real route</h2><p>Enter current, pickup, and drop-off locations. The map handles the geography.</p></div>
            <div><strong>02</strong><h2>Build a legal day</h2><p>See breaks, fuel, rest, and cycle limits placed along the journey.</p></div>
            <div><strong>03</strong><h2>Leave with the log</h2><p>Generate a practical ELD-style record for every day on the road.</p></div>
          </section>
        </main>

        <footer className="home-footer"><span>ELD Trip Planner</span><span>Route planning with clarity.</span><span>OSM · Nominatim · OSRM</span></footer>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <header className="planner-nav">
        <button className="brand" type="button" onClick={() => setView('home')}><span className="brand-mark">ELD</span><span>Trip Planner</span></button>
        <div className="planner-nav__right"><span className="nav-meta"><span className="status-dot status-dot--live" /> Planning desk</span><button className="nav-link nav-link--quiet" type="button" onClick={() => setView('home')}>Back home</button></div>
      </header>
      <header className="hero">
        <div className="hero__badge">FMCSA HOS · OpenStreetMap</div>
        <h1>Build a route<br /><span>that works.</span></h1>
        <p>Plan a property-carrying trip with mapped HOS stops, practical timing, and a daily driver log ready to use.</p>
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
          <RouteMap result={result} />
        </section>
      </main>

      {result && (
        <div className="results-stack">
          <SummaryCards summary={result.summary} />
          <Timeline events={result.events} />
          <RouteInstructions instructions={result.route.instructions} />
          <DailyLogs logs={result.daily_logs} />
          <AccordionSection eyebrow="Planning rules" title="Assumptions used" summary={`${result.assumptions.length} rules`}>
            <ul>
              {result.assumptions.map((item) => <li key={item}>{item}</li>)}
            </ul>
          </AccordionSection>
        </div>
      )}
    </div>
  )
}
