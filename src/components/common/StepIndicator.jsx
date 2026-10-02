import React from 'react';

const STEPS = [
  { id: 1, label: 'Project' },
  { id: 2, label: 'Location' },
  { id: 3, label: 'Property' },
  { id: 4, label: 'Family' },
  { id: 5, label: 'Budget' },
  { id: 6, label: 'Style' },
  { id: 7, label: 'Floor Plan' },
  { id: 8, label: 'Review' }
];

export default function StepIndicator({ activeStep = 1, onSelectStep }) {
  return (
    <div className="step-indicator" role="navigation" aria-label="Wizard Steps">
      {STEPS.map((step) => {
        const isDone = step.id < activeStep;
        const isActive = step.id === activeStep;
        const stateClass = isDone ? 'done' : isActive ? 'active' : '';

        return (
          <button
            key={step.id}
            type="button"
            className={`step-indicator__item ${stateClass}`}
            onClick={() => onSelectStep && onSelectStep(step.id)}
            aria-current={isActive ? 'step' : undefined}
          >
            <span className="step-indicator__num">
              {isDone ? '✓' : step.id}
            </span>
            <span className="step-indicator__label">
              {step.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}
