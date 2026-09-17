import { useState } from 'react'
import DailyLogSheet from './DailyLogSheet'

export default function DailyLogs({ logs }) {
  const [selectedDate, setSelectedDate] = useState(logs[0]?.date || '')
  const selectedLog = logs.find((log) => log.date === selectedDate) || logs[0]

  if (!logs.length) return null

  return (
    <section className="panel daily-logs-panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">ELD output</span>
          <h2>Daily log sheets</h2>
        </div>
        <div className="daily-log-actions">
          <label className="date-picker">
            <span>Select log date</span>
            <input
              type="date"
              value={selectedLog.date}
              min={logs[0].date}
              max={logs[logs.length - 1].date}
              onChange={(event) => setSelectedDate(event.target.value)}
            />
          </label>
          <button className="secondary-button" onClick={() => window.print()}>Print this log</button>
        </div>
      </div>
      <div className="daily-logs">
        <DailyLogSheet log={selectedLog} />
      </div>
      <p className="daily-log-caption">Showing 1 of {logs.length} generated log sheets. Choose another date to view that day.</p>
    </section>
  )
}
