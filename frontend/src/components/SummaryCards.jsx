function hours(value) {
  return `${Number(value).toFixed(1)} h`
}

export default function SummaryCards({ summary }) {
  const cards = [
    ['Route distance', `${summary.route_distance_miles.toLocaleString()} mi`],
    ['Driving time', hours(summary.route_driving_hours)],
    ['Planned elapsed', hours(summary.planned_elapsed_hours)],
    ['10h rests', summary.daily_rests],
    ['30m breaks', summary.hos_breaks],
    ['Fuel stops', summary.fuel_stops],
    ['34h restarts', summary.cycle_restarts],
  ]

  return (
    <section className="summary-grid">
      {cards.map(([label, value]) => (
        <div className="summary-card" key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </section>
  )
}
