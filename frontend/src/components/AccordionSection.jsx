export default function AccordionSection({ eyebrow, title, summary, children, defaultOpen = false, className = '' }) {
  return (
    <details className={`panel accordion-section ${className}`} open={defaultOpen}>
      <summary className="accordion-summary">
        <span>
          {eyebrow && <span className="eyebrow">{eyebrow}</span>}
          <strong>{title}</strong>
        </span>
        {summary && <span className="accordion-summary__meta">{summary}</span>}
        <span className="accordion-summary__icon" aria-hidden="true">+</span>
      </summary>
      <div className="accordion-content">{children}</div>
    </details>
  )
}