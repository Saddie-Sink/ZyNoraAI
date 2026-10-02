import React from 'react';
import { useProject } from '../../../context/ProjectContext';
import Card from '../../common/Card';

const CURRENCIES = [
  { code: 'INR', symbol: '₹' },
  { code: 'USD', symbol: '$' },
  { code: 'EUR', symbol: '€' },
  { code: 'GBP', symbol: '£' },
  { code: 'AED', symbol: 'AED ' },
  { code: 'SGD', symbol: 'S$' }
];

const PRIORITIES = [
  { id: 'Economy', desc: 'Standard materials, standardized spans, cost efficiency focus' },
  { id: 'Balanced', desc: 'Optimal blend of premium materials and structural economy' },
  { id: 'Premium', desc: 'Custom architectural glazing, luxury teak timber, cantilevered spans' }
];

export default function Step5Budget() {
  const { project, updateNested } = useProject();
  const bgt = project.budget || {};
  const currencySymbol = CURRENCIES.find(c => c.code === (bgt.currency || 'INR'))?.symbol || '₹';
  const budgetVal = Number(bgt.budgetRange) || 16500000;
  const builtUpArea = Number(project.property?.builtUpArea) || 2400;
  const estimatedPerSqFt = Math.round(budgetVal / (builtUpArea || 1));

  // Format INR in Lakhs / Crores
  const formatIndianCurrency = (val) => {
    if (val >= 10000000) return `${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `${(val / 100000).toFixed(1)} Lakhs`;
    return val.toLocaleString();
  };

  return (
    <div className="wizard__body">
      <div className="form-grid-2">
        <div className="form-group">
          <label className="form-label" htmlFor="bgt-currency">Currency</label>
          <select
            id="bgt-currency"
            className="form-select"
            value={bgt.currency || 'INR'}
            onChange={(e) => updateNested('budget', 'currency', e.target.value)}
          >
            {CURRENCIES.map(c => (
              <option key={c.code} value={c.code}>{c.code} ({c.symbol})</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="bgt-range">
            Total Target Budget ({currencySymbol}{formatIndianCurrency(budgetVal)})
          </label>
          <input
            id="bgt-range"
            type="range"
            min={2500000}
            max={50000000}
            step={500000}
            value={budgetVal}
            onChange={(e) => updateNested('budget', 'budgetRange', Number(e.target.value))}
            style={{ marginTop: '10px' }}
          />
          <div className="flex justify-between text-xs text-muted mt-2">
            <span>₹25 Lakhs</span>
            <span>₹1.5 Crores</span>
            <span>₹5.0 Crores</span>
          </div>
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Construction Specification Priority</label>
        <div className="option-grid option-grid-3">
          {PRIORITIES.map((p) => (
            <div
              key={p.id}
              className={`option-card ${bgt.priority === p.id ? 'selected' : ''}`}
              onClick={() => updateNested('budget', 'priority', p.id)}
            >
              <div className="option-card__indicator" />
              <div className="option-card__content">
                <div className="option-card__title">{p.id} Priority</div>
                <div className="option-card__sub">{p.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Estimated Budget Summary Card */}
      <Card
        label="Financial Planning Envelope"
        title="Estimated Construction Allocation Summary"
        subtitle="Frontend analytical estimate based on chosen built-up area and specification grade."
      >
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', background: 'var(--surface-warm)', padding: '1.5rem', borderRadius: 'var(--r-lg)' }}>
          <div>
            <div className="text-xs text-muted uppercase tracking-widest">Total Envelope</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 600, color: 'var(--accent-dark)', marginTop: '4px' }}>
              {currencySymbol}{budgetVal.toLocaleString()}
            </div>
            <div className="text-xs text-muted">Fixed Target</div>
          </div>

          <div>
            <div className="text-xs text-muted uppercase tracking-widest">Est. Cost / Area</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px' }}>
              {currencySymbol}{estimatedPerSqFt}
            </div>
            <div className="text-xs text-muted">per sq ft habitable</div>
          </div>

          <div>
            <div className="text-xs text-muted uppercase tracking-widest">Spec Grade</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px' }}>
              {bgt.priority || 'Balanced'}
            </div>
            <div className="text-xs text-muted">Finishes & Systems</div>
          </div>
        </div>
        <div className="text-xs text-muted mt-3" style={{ fontStyle: 'italic' }}>
          * Notice: Budget figures are UI projections for parametric matching. Formal quantity takeoff requires contractor tender.
        </div>
      </Card>
    </div>
  );
}
