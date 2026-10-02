import React from 'react';
import { useProject } from '../../../context/ProjectContext';
import Card from '../../common/Card';

const ROOM_FIELDS = [
  { key: 'bedrooms', label: 'Bedrooms', defaultVal: 3 },
  { key: 'bathrooms', label: 'Bathrooms', defaultVal: 2 },
  { key: 'livingRoom', label: 'Drawing / Living Hall', defaultVal: 1 },
  { key: 'dining', label: 'Formal Dining', defaultVal: 1 },
  { key: 'kitchen', label: 'Modular Kitchen', defaultVal: 1 },
  { key: 'parking', label: 'Car Parking Bay', defaultVal: 1 },
  { key: 'balcony', label: 'Balcony / Sit-Out', defaultVal: 1 },
  { key: 'terrace', label: 'Open Terrace Deck', defaultVal: 1 },
  { key: 'pooja', label: 'Pooja Room (Vastu Eeshanya)', defaultVal: 1 },
  { key: 'utility', label: 'Utility / Wash Area', defaultVal: 1 },
  { key: 'study', label: 'Study / Home Office', defaultVal: 0 },
  { key: 'guestRoom', label: 'Guest Bedroom', defaultVal: 0 },
  { key: 'storeRoom', label: 'Store / Pantry', defaultVal: 0 },
  { key: 'garden', label: 'Lawn / Garden', defaultVal: 0 }
];

const OPTIONAL_REQUIREMENTS = [
  'Vastu Shastra Compliance',
  'Cross Ventilation (Coastal Breeze)',
  'Dedicated North-East Pooja Room',
  'Elder-friendly ground floor access',
  'Natural Daylighting',
  'Rainwater Harvesting (Chennai mandate)'
];

export default function Step4Family() {
  const { project, updateNested, updateRoomCount, toggleRequirement } = useProject();
  const fam = project.family || {};
  const rooms = fam.rooms || {};
  const reqs = fam.requirements || [];

  return (
    <div className="wizard__body">
      {/* Household Profile */}
      <div className="form-grid-3">
        <div className="form-group">
          <label className="form-label" htmlFor="fam-adults">Adults</label>
          <div className="stepper">
            <button
              type="button"
              className="stepper__btn"
              onClick={() => updateNested('family', 'adults', Math.max(1, (fam.adults || 2) - 1))}
            >
              -
            </button>
            <div className="stepper__val">{fam.adults || 2}</div>
            <button
              type="button"
              className="stepper__btn"
              onClick={() => updateNested('family', 'adults', (fam.adults || 2) + 1)}
            >
              +
            </button>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="fam-children">Children</label>
          <div className="stepper">
            <button
              type="button"
              className="stepper__btn"
              onClick={() => updateNested('family', 'children', Math.max(0, (fam.children || 0) - 1))}
            >
              -
            </button>
            <div className="stepper__val">{fam.children || 0}</div>
            <button
              type="button"
              className="stepper__btn"
              onClick={() => updateNested('family', 'children', (fam.children || 0) + 1)}
            >
              +
            </button>
          </div>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="fam-elderly">Elderly Members</label>
          <div className="stepper">
            <button
              type="button"
              className="stepper__btn"
              onClick={() => updateNested('family', 'elderly', Math.max(0, (fam.elderly || 0) - 1))}
            >
              -
            </button>
            <div className="stepper__val">{fam.elderly || 0}</div>
            <button
              type="button"
              className="stepper__btn"
              onClick={() => updateNested('family', 'elderly', (fam.elderly || 0) + 1)}
            >
              +
            </button>
          </div>
        </div>
      </div>

      {/* Required Rooms Grid */}
      <Card
        label="Room Count Program"
        title="Required Spatial Allocations"
        subtitle="Specify required habitable rooms and mechanical service zones."
      >
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '1rem' }}>
          {ROOM_FIELDS.map(({ key, label, defaultVal }) => {
            const val = rooms[key] ?? defaultVal;
            return (
              <div key={key} style={{ background: 'var(--surface-alt)', padding: '12px', borderRadius: 'var(--r-lg)', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px', fontWeight: 600 }}>
                  {label}
                </div>
                <div className="stepper" style={{ maxWidth: '100%' }}>
                  <button
                    type="button"
                    className="stepper__btn"
                    onClick={() => updateRoomCount(key, val - 1)}
                  >
                    -
                  </button>
                  <div className="stepper__val">{val}</div>
                  <button
                    type="button"
                    className="stepper__btn"
                    onClick={() => updateRoomCount(key, val + 1)}
                  >
                    +
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Optional Spatial Priorities */}
      <div className="form-group">
        <label className="form-label">Special Architectural & Accessibility Priorities</label>
        <div className="option-grid option-grid-3">
          {OPTIONAL_REQUIREMENTS.map((req) => {
            const isSelected = reqs.includes(req);
            return (
              <div
                key={req}
                className={`option-card checkbox-card ${isSelected ? 'selected' : ''}`}
                onClick={() => toggleRequirement(req)}
              >
                <div className="option-card__indicator" />
                <div className="option-card__content">
                  <div className="option-card__title">{req}</div>
                  <div className="option-card__sub">
                    {req === 'Accessibility' && 'Zero-threshold doors, wide halls'}
                    {req === 'Elder-friendly design' && 'Ground floor suite & grab rails'}
                    {req === 'Natural lighting' && 'Clerestory & skylight prioritisation'}
                    {req === 'Ventilation' && 'Cross-ventilation airway corridors'}
                    {req === 'Privacy' && 'Buffer wings between social & beds'}
                    {req === 'Sustainability' && 'Passive thermal massing & solar gain'}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
