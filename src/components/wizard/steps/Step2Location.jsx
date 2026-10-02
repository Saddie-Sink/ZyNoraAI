import React from 'react';
import { useProject } from '../../../context/ProjectContext';
import Card from '../../common/Card';

const ORIENTATIONS = ['North', 'South', 'East', 'West'];

export default function Step2Location() {
  const { project, updateNested } = useProject();
  const loc = project.location || {};

  return (
    <div className="wizard__body">
      <div className="form-grid-3">
        <div className="form-group">
          <label className="form-label" htmlFor="loc-country">Country</label>
          <input
            id="loc-country"
            type="text"
            className="form-input"
            value={loc.country || ''}
            onChange={(e) => updateNested('location', 'country', e.target.value)}
            placeholder="e.g. India"
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="loc-state">State / Province</label>
          <input
            id="loc-state"
            type="text"
            className="form-input"
            value={loc.state || ''}
            onChange={(e) => updateNested('location', 'state', e.target.value)}
            placeholder="e.g. Tamil Nadu"
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="loc-city">City / District</label>
          <input
            id="loc-city"
            type="text"
            className="form-input"
            value={loc.city || ''}
            onChange={(e) => updateNested('location', 'city', e.target.value)}
            placeholder="e.g. Chennai (ECR, Anna Nagar, Adyar)"
          />
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Site Primary Orientation (Facing Road)</label>
        <div className="option-grid option-grid-4">
          {ORIENTATIONS.map((dir) => (
            <div
              key={dir}
              className={`option-card ${loc.orientation === dir ? 'selected' : ''}`}
              onClick={() => updateNested('location', 'orientation', dir)}
            >
              <div className="option-card__indicator" />
              <div className="option-card__content">
                <div className="option-card__title">{dir}-Facing</div>
                <div className="option-card__sub">
                  {dir === 'North' && 'Indirect cool diffuse daylight'}
                  {dir === 'South' && 'Maximum solar exposure year-round'}
                  {dir === 'East' && 'Morning dawn sunlight exposure'}
                  {dir === 'West' && 'Afternoon warmth & sunset glare'}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Visual site/location card & future maps placeholder */}
      <Card
        label="Geographic & Site Context"
        title="Site Orientation & Coordinate Reference"
        subtitle="Frontend placeholder for upcoming Google Maps and GIS terrain elevation overlay."
      >
        <div
          style={{
            height: '180px',
            background: 'var(--surface-warm)',
            border: '1px dashed var(--border)',
            borderRadius: 'var(--r-lg)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            position: 'relative'
          }}
        >
          <div style={{ fontSize: '28px', opacity: 0.5 }}>📍</div>
          <div style={{ fontWeight: 600, fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {loc.city ? `${loc.city}, ${loc.state || ''} ${loc.country || ''}` : 'Location Coordinates Active'}
          </div>
          <span className="badge badge-demo">Future Google Maps GIS Integration Placeholder</span>
          <span className="text-xs text-muted" style={{ opacity: 0.8 }}>
            Orientation: Facing {loc.orientation || 'North'} · Microclimate: Mediterranean Moderate
          </span>
        </div>
      </Card>
    </div>
  );
}
