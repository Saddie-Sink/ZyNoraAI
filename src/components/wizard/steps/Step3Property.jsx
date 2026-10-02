import React from 'react';
import { useProject } from '../../../context/ProjectContext';
import Card from '../../common/Card';

const PLOT_SHAPES = ['Rectangle', 'L-shape', 'Other'];

export default function Step3Property() {
  const { project, updateNested } = useProject();
  const prop = project.property || {};

  const width = Number(prop.siteWidth) || 40;
  const length = Number(prop.siteLength) || 60;
  const totalSiteArea = width * length;

  return (
    <div className="wizard__body">
      <div className="form-grid-3">
        <div className="form-group">
          <label className="form-label" htmlFor="prop-width">Site Width (ft)</label>
          <input
            id="prop-width"
            type="number"
            className="form-input"
            value={prop.siteWidth || 40}
            onChange={(e) => updateNested('property', 'siteWidth', Math.max(15, Number(e.target.value)))}
          />
          <span className="form-hint">Standard Chennai plot width: 40ft</span>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="prop-length">Site Length (ft)</label>
          <input
            id="prop-length"
            type="number"
            className="form-input"
            value={prop.siteLength || 60}
            onChange={(e) => updateNested('property', 'siteLength', Math.max(20, Number(e.target.value)))}
          />
          <span className="form-hint">Standard Chennai plot depth: 60ft</span>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="prop-floors">Number of Floors</label>
          <select
            id="prop-floors"
            className="form-select"
            value={prop.floors || 2}
            onChange={(e) => updateNested('property', 'floors', Number(e.target.value))}
          >
            <option value={1}>1 Floor (Single Level)</option>
            <option value={2}>2 Floors (Duplex / Ground + 1)</option>
            <option value={3}>3 Floors (G + 2 Villa)</option>
            <option value={4}>4 Floors (Multi-level Villa)</option>
          </select>
        </div>
      </div>

      <div className="form-grid-2">
        <div className="form-group">
          <label className="form-label" htmlFor="prop-builtup">Target Built-Up Area (sq ft)</label>
          <input
            id="prop-builtup"
            type="number"
            className="form-input"
            value={prop.builtUpArea || 2400}
            onChange={(e) => updateNested('property', 'builtUpArea', Number(e.target.value))}
          />
          <span className="form-hint">Total built-up area (Standard Chennai 1 Ground parcel = 2,400 sq ft).</span>
        </div>

        <div className="form-group">
          <label className="form-label">Plot Shape</label>
          <div className="option-grid option-grid-3">
            {PLOT_SHAPES.map((shape) => (
              <div
                key={shape}
                className={`option-card ${prop.plotShape === shape ? 'selected' : ''}`}
                onClick={() => updateNested('property', 'plotShape', shape)}
              >
                <div className="option-card__indicator" />
                <div className="option-card__content">
                  <div className="option-card__title">{shape}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Visual Plot Representation */}
      <Card
        label="Parametric Plot Geometry"
        title="Interactive Site Boundary Representation"
        subtitle={`Computed parcel area: ${totalSiteArea.toLocaleString()} sq ft · Aspect ratio: ${(length / width).toFixed(2)}:1`}
      >
        <div className="flex justify-center items-center" style={{ background: 'var(--surface-warm)', padding: '2rem', borderRadius: 'var(--r-lg)' }}>
          <svg viewBox="0 0 320 220" width="100%" height="220" style={{ maxWidth: '380px' }}>
            <rect width="100%" height="100%" fill="none" />
            {/* Outer Site Box */}
            {prop.plotShape === 'L-shape' ? (
              <polygon
                points="40,30 280,30 280,120 180,120 180,190 40,190"
                fill="rgba(200,169,110,0.08)"
                stroke="var(--accent)"
                strokeWidth="2"
                strokeDasharray="4 4"
              />
            ) : (
              <rect
                x="40"
                y="30"
                width="240"
                height="150"
                fill="rgba(200,169,110,0.08)"
                stroke="var(--accent)"
                strokeWidth="2"
                strokeDasharray="4 4"
              />
            )}

            {/* Setback / Building Envelope Mock */}
            <rect
              x="65"
              y="55"
              width="190"
              height="100"
              fill="rgba(15,17,23,0.06)"
              stroke="var(--ink)"
              strokeWidth="1.5"
            />
            <text x="160" y="105" fill="var(--ink)" fontSize="11" fontWeight="600" textAnchor="middle">
              ESTIMATED BUILDING ENVELOPE
            </text>
            <text x="160" y="122" fill="var(--text-muted)" fontSize="9" textAnchor="middle">
              {prop.builtUpArea || 3800} sq ft · {prop.floors || 2} Floors
            </text>

            {/* Dimension Markers */}
            <text x="160" y="22" fill="var(--accent-dark)" fontSize="10" fontWeight="bold" textAnchor="middle">
              WIDTH: {width} ft
            </text>
            <text x="295" y="110" fill="var(--accent-dark)" fontSize="10" fontWeight="bold" textAnchor="middle" transform="rotate(90 295 110)">
              LENGTH: {length} ft
            </text>

            {/* Compass */}
            <circle cx="280" cy="50" r="12" fill="var(--surface)" stroke="var(--border)" strokeWidth="1" />
            <text x="280" y="53" fill="var(--accent)" fontSize="9" fontWeight="bold" textAnchor="middle">N</text>
          </svg>
        </div>
      </Card>
    </div>
  );
}
