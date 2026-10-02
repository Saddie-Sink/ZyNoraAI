import React from 'react';

export default function ProgressBar({
  progress = 0,
  showLabel = false,
  className = ''
}) {
  const clamped = Math.min(100, Math.max(0, progress));

  return (
    <div className={`w-full ${className}`}>
      {showLabel && (
        <div className="flex justify-between items-center mb-2 text-xs text-muted">
          <span className="uppercase tracking-widest font-medium">Step Progress</span>
          <span className="font-semibold text-accent">{Math.round(clamped)}%</span>
        </div>
      )}
      <div className="progress-bar">
        <div
          className="progress-bar__fill"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
