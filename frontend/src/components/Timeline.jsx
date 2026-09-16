const statusLabel = {
  driving: 'Driving',
  on_duty_not_driving: 'On duty',
  off_duty: 'Off duty',
  sleeper_berth: 'Sleeper berth',
}

export default function Timeline({ events }) {
  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Generated HOS plan</span>
          <h2>Trip timeline</h2>
        </div>
      </div>
      <div className="timeline">
        {events.map((event, index) => (
          <div className={`timeline-row status-${event.status}`} key={`${event.start}-${index}`}>
            <div className="timeline-dot" />
            <div className="timeline-time">
              {event.start_local} {event.timezone_abbr}<br />
              <span>{event.duration_hours.toFixed(2)} h</span>
            </div>
            <div className="timeline-content">
              <strong>{event.label}</strong>
              <span>{statusLabel[event.status]}</span>
              {event.location_text && <small>{event.location_text}</small>}
              {event.kind === 'driving' && <small>Route mile {event.start_mile} → {event.end_mile}</small>}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
