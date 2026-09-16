export default function RouteInstructions({ instructions }) {
  const shown = instructions.filter((x) => x.distance_miles > 0.03).slice(0, 40)
  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">OSRM route</span>
          <h2>Route instructions</h2>
        </div>
        <span className="muted">Showing first {shown.length} meaningful steps</span>
      </div>
      <div className="instruction-list">
        {shown.map((step, i) => (
          <div className="instruction" key={`${step.leg_index}-${i}`}>
            <div className="instruction-number">{i + 1}</div>
            <div>
              <strong>{step.instruction}</strong>
              <span>{step.distance_miles} mi · {step.duration_minutes} min</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
