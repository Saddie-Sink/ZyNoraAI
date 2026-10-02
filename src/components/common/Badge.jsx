import React from 'react';

export default function Badge({
  children,
  variant = 'demo',
  className = ''
}) {
  const variantClass = `badge-${variant}`;

  return (
    <span className={`badge ${variantClass} ${className}`.trim()}>
      {children}
    </span>
  );
}
