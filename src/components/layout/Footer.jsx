import React from 'react';
import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="footer" role="contentinfo">
      <div className="footer__inner">
        <div className="footer__top">
          <div>
            <div className="footer__brand">ZYNORA AI</div>
            <div style={{ color: 'rgba(255,255,255,0.45)', marginTop: '4px' }}>
              AI Floor Plan Generator & 3D Visualization Studio
            </div>
          </div>
          <div className="flex gap-6">
            <Link to="/" style={{ color: 'rgba(255,255,255,0.75)' }}>Overview</Link>
            <Link to="/projects/new" style={{ color: 'var(--accent)' }}>Create Floor Plan</Link>
            <Link to="/projects">Dashboard</Link>
          </div>
        </div>

        <div className="footer__bottom">
          <span>© 2026 ZYNORA AI. Built for homeowners, architects, and builders.</span>
        </div>
      </div>
    </footer>
  );
}
