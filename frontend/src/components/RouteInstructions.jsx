import AccordionSection from './AccordionSection'

export default function RouteInstructions({ instructions }) {
  const meaningfulSteps = instructions.filter((step) => step.distance_miles > 0.03).slice(0, 40)
  return (
    <AccordionSection eyebrow="OSRM route" title="Route instructions" summary={`${meaningfulSteps.length} meaningful steps`}>
      <div className="instruction-list">
        {meaningfulSteps.map((step, index) => (
          <div className="instruction" key={`${step.leg_index}-${index}`}>
            <div className="instruction-number">{index + 1}</div>
            <div>
              <strong>{step.instruction}</strong>
              <span>{step.distance_miles} mi · {step.duration_minutes} min</span>
            </div>
          </div>
        ))}
      </div>
    </AccordionSection>
  )
}
