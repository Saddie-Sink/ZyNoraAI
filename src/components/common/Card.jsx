import React from 'react';

export default function Card({
  children,
  label,
  title,
  subtitle,
  variant = 'default',
  className = '',
  onClick,
  headerAction = null
}) {
  const isDark = variant === 'dark' ? 'card-dark' : '';
  const isAccent = variant === 'accent' ? 'card-accent' : '';
  const isHover = onClick ? 'card-hover' : '';

  return (
    <div
      onClick={onClick}
      className={`card ${isDark} ${isAccent} ${isHover} ${className}`.trim()}
    >
      {(label || title || headerAction) && (
        <div style={{ marginBottom: '1rem' }}>
          {label && <div className="card__label">{label}</div>}
          <div className="flex items-center justify-between">
            {title && <h3 className="card__title" style={{ margin: 0 }}>{title}</h3>}
            {headerAction && <div>{headerAction}</div>}
          </div>
          {subtitle && <p className="text-xs text-muted" style={{ marginTop: '0.25rem' }}>{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  );
}
