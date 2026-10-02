import React from 'react';
import Badge from '../common/Badge';

export default function ViewSlot({
  view,
  isActive,
  onSelect
}) {
  const { slot, name, subTitle, angle, lens } = view;

  return (
    <div
      className={`gallery-slot-card ${isActive ? 'active' : ''}`}
      onClick={() => onSelect && onSelect(view)}
      role="button"
      tabIndex={0}
      aria-label={`View perspective ${slot}: ${name}`}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onSelect && onSelect(view); }}
    >
      <div className="gallery-slot-card__thumb" style={{ position: 'relative', overflow: 'hidden' }}>
        {view.imageUrl ? (
          <img
            src={view.imageUrl}
            alt={name}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : (
          /* Schematic Architectural Camera Angle Viewport */
          <svg viewBox="0 0 160 100" width="100%" height="100%">
            <rect width="100%" height="100%" fill="#1a1d28" />

            {/* Grid lines */}
            <line x1="0" y1="80" x2="160" y2="80" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
            <line x1="0" y1="50" x2="160" y2="50" stroke="rgba(255,255,255,0.04)" strokeWidth="1" />

            {/* Massing Silhouette specific to slot */}
            {slot === '01' ? (
              <polygon points="35,80 35,45 85,30 135,45 135,80 85,75" fill="rgba(200,169,110,0.15)" stroke="#c8a96e" strokeWidth="1.5" />
            ) : slot === '02' ? (
              <polygon points="25,80 25,50 70,35 120,40 120,80 70,75" fill="rgba(255,255,255,0.06)" stroke="#8a8f9e" strokeWidth="1.5" />
            ) : slot === '03' ? (
              <polygon points="35,80 35,40 125,40 125,80" fill="rgba(255,255,255,0.06)" stroke="#8a8f9e" strokeWidth="1.5" />
            ) : slot === '04' ? (
              <polygon points="30,80 30,55 75,55 75,35 130,35 130,80" fill="rgba(255,255,255,0.06)" stroke="#8a8f9e" strokeWidth="1.5" />
            ) : (
              <polygon points="30,80 30,35 85,35 85,55 130,55 130,80" fill="rgba(255,255,255,0.06)" stroke="#8a8f9e" strokeWidth="1.5" />
            )}

            {/* Viewport Reticle */}
            <circle cx="80" cy="50" r="14" fill="none" stroke="rgba(200,169,110,0.3)" strokeWidth="0.8" strokeDasharray="2 2" />
          </svg>
        )}

        <span style={{ position: 'absolute', top: '6px', left: '6px', background: 'rgba(0,0,0,0.7)', padding: '1px 5px', borderRadius: '3px', color: 'var(--accent)', fontSize: '10px', fontWeight: 'bold' }}>
          {slot}
        </span>
      </div>

      <div className="gallery-slot-card__info">
        <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>{name}</div>
        <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>{angle} · {lens}</div>
      </div>
    </div>
  );
}
