const rows = [
  ['off_duty', 'Off Duty'],
  ['sleeper_berth', 'Sleeper Berth'],
  ['driving', 'Driving'],
  ['on_duty_not_driving', 'On Duty (Not Driving)'],
]

function x(hour) {
  return 138 + (hour / 24) * 702
}

function y(status) {
  const idx = rows.findIndex(([key]) => key === status)
  return 78 + idx * 48 + 24
}

function buildPath(segments) {
  if (!segments.length) return ''
  let d = `M ${x(segments[0].start)} ${y(segments[0].status)}`
  segments.forEach((seg, index) => {
    d += ` H ${x(seg.end)}`
    const next = segments[index + 1]
    if (next) d += ` V ${y(next.status)}`
  })
  return d
}

function fmt(value) {
  const n = Number(value || 0)
  return n % 1 === 0 ? String(n) : n.toFixed(2).replace(/0$/, '')
}

function shortDate(value) {
  const [year, month, day] = value.split('-')
  return `${month}/${day}/${year}`
}

export default function DailyLogSheet({ log }) {
  const path = buildPath(log.segments)
  const meta = log.metadata || {}
  const brackets = log.segments.filter((seg) => seg.status !== 'driving' && seg.label !== 'Off duty')

  return (
    <article className="log-sheet">
      <div className="log-header">
        <div>
          <span className="log-kicker">U.S. Department of Transportation</span>
          <h3>Driver&apos;s Daily Log</h3>
          <span>(One calendar day — 24 hours)</span>
        </div>
        <div className="log-meta">
          <label>Date <strong>{shortDate(log.date)}</strong></label>
          <label>Total miles driving today <strong>{log.miles_driven}</strong></label>
          <label>Time base <strong>{meta.timezone_abbr || meta.home_terminal_timezone}</strong></label>
          <label>On-duty total <strong>{fmt(log.on_duty_total)} h</strong></label>
        </div>
      </div>

      <div className="log-fields log-fields--dense">
        <div><span>Driver name / signature</span><strong>{meta.driver_name}</strong></div>
        <div><span>Driver number / initials</span><strong>{meta.driver_number} / {meta.driver_initials}</strong></div>
        <div><span>Name of carrier</span><strong>{meta.carrier_name}</strong></div>
        <div><span>Main office address</span><strong>{meta.main_office_address}</strong></div>
        <div><span>Home terminal</span><strong>{meta.home_terminal}</strong></div>
        <div><span>Co-driver</span><strong>{meta.co_driver}</strong></div>
        <div><span>Tractor number</span><strong>{meta.tractor_number}</strong></div>
        <div><span>Trailer number</span><strong>{meta.trailer_number}</strong></div>
        <div><span>Shipper</span><strong>{meta.shipper}</strong></div>
        <div><span>Commodity</span><strong>{meta.commodity}</strong></div>
        <div><span>Load / shipping no.</span><strong>{meta.load_id}</strong></div>
        <div><span>Certification</span><strong>I certify these entries are true and correct</strong></div>
      </div>

      <div className="svg-scroll">
        <svg viewBox="0 0 960 360" role="img" aria-label={`ELD graph for ${log.date}`}>
          <rect x="138" y="78" width="702" height="192" fill="white" stroke="currentColor" />
          {rows.map(([key, label], idx) => (
            <g key={key}>
              <text x="128" y={78 + idx * 48 + 29} textAnchor="end" className="row-label">{label}</text>
              {idx > 0 && <line x1="138" y1={78 + idx * 48} x2="840" y2={78 + idx * 48} className="grid-line" />}
              <text x="858" y={78 + idx * 48 + 29} className="total-label">{fmt(log.totals[key])}</text>
            </g>
          ))}

          {Array.from({ length: 25 }, (_, hour) => (
            <g key={hour}>
              <line x1={x(hour)} y1="78" x2={x(hour)} y2="270" className="hour-line" />
              {hour < 24 && <text x={x(hour)} y="65" textAnchor="middle" className="hour-label">{hour}</text>}
            </g>
          ))}

          {Array.from({ length: 96 }, (_, q) => {
            const hour = q / 4
            if (q % 4 === 0) return null
            return rows.map((_, rowIndex) => {
              const rowTop = 78 + rowIndex * 48
              return (
                <line
                  key={`${q}-${rowIndex}`}
                  x1={x(hour)}
                  y1={rowTop}
                  x2={x(hour)}
                  y2={rowTop + 10}
                  className="minor-tick"
                />
              )
            })
          })}

          <path d={path} className="duty-path" fill="none" />

          {log.remarks.map((remark, index) => (
            <circle
              key={`dot-${remark.time}-${index}`}
              cx={x(remark.hour)}
              cy={y(remark.status)}
              r="3.4"
              className="status-dot"
            />
          ))}

          <text x="870" y="68" className="total-title">TOTAL</text>
          <text x="870" y="78" className="total-title">HOURS</text>
          <text x="36" y="305" className="remarks-title">REMARKS / STATUS FLAGS</text>
          <line x1="138" y1="292" x2="840" y2="292" className="remarks-rail" />

          {brackets.map((seg, index) => {
            const yTop = 282 + (index % 2) * 15
            return (
              <g key={`bracket-${seg.start}-${index}`}>
                <path
                  d={`M ${x(seg.start)} ${yTop} V ${yTop + 8} H ${x(seg.end)} V ${yTop}`}
                  className="bracket-line"
                  fill="none"
                />
              </g>
            )
          })}
        </svg>
      </div>

      <div className="remarks">
        <strong>Remarks — location and activity at duty-status changes</strong>
        {log.remarks.length ? (
          log.remarks.map((remark, i) => (
            <span key={`${remark.time}-${i}`}>
              <b>{remark.time}</b> {remark.location} — {remark.activity}
            </span>
          ))
        ) : <span>No trip events.</span>}
      </div>
      <div className="log-total">Duty-status total: {fmt(log.total_hours)} hours</div>
    </article>
  )
}
