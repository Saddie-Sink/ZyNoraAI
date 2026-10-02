import React from 'react';

export default function QualityBar({ label, value, max = 100 }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const tierClass = pct >= 90 ? 'high' : pct >= 80 ? 'mid' : 'low';

  return (
    <div style={{ marginBottom: '10px' }}>
      <div className="flex justify-between items-center text-xs mb-1">
        <span className="text-secondary">{label}</span>
        <span className="font-semibold">{value}%</span>
      </div>
      <div style={{ height: '5px', background: 'var(--border)', borderRadius: '3px', overflow: 'hidden' }}>
        <div
          style={{
            width: `${pct}%`,
            height: '100%',
            background: tierClass === 'high' ? 'var(--success)' : tierClass === 'mid' ? 'var(--accent)' : 'var(--warning)',
            borderRadius: '3px',
            transition: 'width 0.6s ease'
          }}
        />
      </div>
    </div>
  );
}
