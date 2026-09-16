import { useState } from 'react'

const initial = {
  current_location: 'Chicago, IL',
  pickup_location: 'Denver, CO',
  dropoff_location: 'Los Angeles, CA',
  current_cycle_used: 20,
  home_terminal_timezone: 'America/Chicago',
  driver_name: 'John Doe',
  driver_number: 'D-1001',
  driver_initials: 'JD',
  co_driver: '',
  carrier_name: 'Demo Motor Carrier',
  main_office_address: 'Chicago, IL',
  home_terminal: 'Chicago, IL',
  tractor_number: 'TR-101',
  trailer_number: 'TL-501',
  shipper: 'Demo Shipper',
  commodity: 'General Freight',
  load_id: 'LOAD-001',
}

export default function TripForm({ onSubmit, loading }) {
  const [form, setForm] = useState(initial)

  function update(event) {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  function submit(event) {
    event.preventDefault()
    onSubmit({
      ...form,
      current_cycle_used: Number(form.current_cycle_used),
    })
  }

  return (
    <form onSubmit={submit} className="trip-form">
      <div>
        <span className="eyebrow">Trip inputs</span>
        <h2>Build your route</h2>
      </div>

      <label>
        Current location
        <input name="current_location" value={form.current_location} onChange={update} required />
      </label>

      <label>
        Pickup location
        <input name="pickup_location" value={form.pickup_location} onChange={update} required />
      </label>

      <label>
        Drop-off location
        <input name="dropoff_location" value={form.dropoff_location} onChange={update} required />
      </label>

      <label>
        Current cycle used (hours)
        <div className="range-row">
          <input
            name="current_cycle_used"
            type="range"
            min="0"
            max="70"
            step="0.5"
            value={form.current_cycle_used}
            onChange={update}
          />
          <output>{form.current_cycle_used} h</output>
        </div>
      </label>

      <label>
        Home-terminal time zone
        <select name="home_terminal_timezone" value={form.home_terminal_timezone} onChange={update}>
          <option value="America/New_York">Eastern — America/New_York</option>
          <option value="America/Chicago">Central — America/Chicago</option>
          <option value="America/Denver">Mountain — America/Denver</option>
          <option value="America/Los_Angeles">Pacific — America/Los_Angeles</option>
          <option value="America/Phoenix">Arizona — America/Phoenix</option>
          <option value="America/Anchorage">Alaska — America/Anchorage</option>
          <option value="Pacific/Honolulu">Hawaii — Pacific/Honolulu</option>
        </select>
      </label>

      <details className="logbook-details">
        <summary>Logbook details <span>optional</span></summary>
        <div className="details-grid">
          <label>Driver name<input name="driver_name" value={form.driver_name} onChange={update} /></label>
          <label>Driver number<input name="driver_number" value={form.driver_number} onChange={update} /></label>
          <label>Driver initials<input name="driver_initials" value={form.driver_initials} onChange={update} /></label>
          <label>Co-driver<input name="co_driver" value={form.co_driver} onChange={update} placeholder="N/A" /></label>
          <label>Carrier<input name="carrier_name" value={form.carrier_name} onChange={update} /></label>
          <label>Main office<input name="main_office_address" value={form.main_office_address} onChange={update} /></label>
          <label>Home terminal<input name="home_terminal" value={form.home_terminal} onChange={update} /></label>
          <label>Tractor number<input name="tractor_number" value={form.tractor_number} onChange={update} /></label>
          <label>Trailer number<input name="trailer_number" value={form.trailer_number} onChange={update} /></label>
          <label>Shipper<input name="shipper" value={form.shipper} onChange={update} /></label>
          <label>Commodity<input name="commodity" value={form.commodity} onChange={update} /></label>
          <label>Load / shipping ID<input name="load_id" value={form.load_id} onChange={update} /></label>
        </div>
      </details>

      <button type="submit" disabled={loading}>
        {loading ? 'Planning trip…' : 'Plan trip'}
      </button>
      <p className="help-text">Tip: locations may also be entered as <code>lat,lon</code>.</p>
    </form>
  )
}
