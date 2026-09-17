import DailyLogSheet from './DailyLogSheet'

export default function DailyLogs({ logs }) {
  return (
    <section className="panel daily-logs-panel">
      <div className="section-heading">
        <div>
          <span className="eyebrow">ELD output</span>
          <h2>Daily log sheets</h2>
        </div>
        <button className="secondary-button" onClick={() => window.print()}>Print logs</button>
      </div>
      <div className="daily-logs">
        {logs.map((log) => <DailyLogSheet key={log.date} log={log} />)}
      </div>
    </section>
  )
}
