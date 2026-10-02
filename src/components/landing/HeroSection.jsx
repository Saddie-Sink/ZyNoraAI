import React from 'react';
import { Link } from 'react-router-dom';

export default function HeroSection() {
  return (
    <section className="hero">
      <div className="hero__inner">
        <div>
          <div className="hero__kicker">
            <span className="hero__kicker-line"></span>
            <span>AI Architectural Floor Plan & 3D Studio</span>
          </div>

          <h1 className="hero__title">
            <strong>AI-Powered Personalized</strong> Home Planning
          </h1>

          <p className="hero__subtitle">
            Transform your requirements into clear 2D floor plans, interactive 3D visualizations,
            and exportable AutoCAD (.DXF) blueprints.
          </p>

          <div className="hero__actions">
            <Link to="/projects/new" className="btn btn-primary btn-lg">
              Create Floor Plan
            </Link>
            <a href="#pipeline-section" className="btn btn-secondary btn-lg">
              How It Works
            </a>
          </div>

          <div className="flex items-center gap-4 mt-8" style={{ color: 'rgba(255,255,255,0.45)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            <span>• 2D Floor Plan Generator</span>
            <span>• Floor Plan to 3D Converter</span>
            <span>• AutoCAD .DXF Export</span>
          </div>
        </div>

        {/* Architectural Concept Blueprint Preview */}
        <div className="blueprint-card">
          <div className="blueprint-card__header">
            <span className="blueprint-card__tag">2D & 3D Floor Plan Preview</span>
          </div>

          {/* SVG Architectural Concept Diagram */}
          <svg viewBox="0 0 440 320" width="100%" height="auto" style={{ borderRadius: '4px', background: '#141722' }}>
            <defs>
              <pattern id="smallGrid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="0.5"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#smallGrid)" />

            <rect x="30" y="30" width="380" height="260" fill="none" stroke="rgba(200,169,110,0.3)" strokeWidth="1" strokeDasharray="4 4" />
            <text x="36" y="46" fill="rgba(200,169,110,0.6)" fontSize="9" letterSpacing="1" fontFamily="sans-serif">PLOT: 30ft × 40ft · 3 BHK RESIDENCE</text>

            <rect x="60" y="70" width="180" height="130" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.2)" strokeWidth="1.5" />
            <text x="75" y="95" fill="#f5f4f0" fontSize="11" fontWeight="600" fontFamily="sans-serif">LIVING & DINING</text>
            <text x="75" y="112" fill="rgba(255,255,255,0.5)" fontSize="9" fontFamily="sans-serif">Spacious Open Layout</text>

            <rect x="250" y="70" width="130" height="90" fill="rgba(200,169,110,0.08)" stroke="rgba(200,169,110,0.4)" strokeWidth="1.5" />
            <text x="265" y="95" fill="#c8a96e" fontSize="11" fontWeight="600" fontFamily="sans-serif">MASTER BEDROOM</text>
            <text x="265" y="112" fill="rgba(200,169,110,0.6)" fontSize="9" fontFamily="sans-serif">Attached Bath & Dress</text>

            <rect x="250" y="170" width="130" height="90" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.15)" strokeWidth="1.5" />
            <text x="265" y="195" fill="#f5f4f0" fontSize="11" fontWeight="600" fontFamily="sans-serif">KITCHEN & POOJA</text>
            <text x="265" y="212" fill="rgba(255,255,255,0.5)" fontSize="9" fontFamily="sans-serif">Vastu Aligned</text>

            <rect x="60" y="210" width="180" height="50" fill="rgba(255,255,255,0.02)" stroke="rgba(255,255,255,0.1)" strokeWidth="1" />
            <text x="75" y="238" fill="rgba(255,255,255,0.7)" fontSize="10" fontFamily="sans-serif">VERANDAH & CAR PARKING</text>

            <line x1="60" y1="275" x2="380" y2="275" stroke="rgba(200,169,110,0.5)" strokeWidth="1" />
            <circle cx="60" cy="275" r="2" fill="#c8a96e" />
            <circle cx="380" cy="275" r="2" fill="#c8a96e" />
            <text x="200" y="288" fill="rgba(200,169,110,0.8)" fontSize="9" textAnchor="middle" fontFamily="sans-serif">FRONTAGE: 30ft · EAST FACING</text>

            <circle cx="380" cy="55" r="14" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="1" />
            <path d="M 380 43 L 383 55 L 380 52 L 377 55 Z" fill="#c8a96e" />
            <text x="380" y="38" fill="#c8a96e" fontSize="8" fontWeight="bold" textAnchor="middle" fontFamily="sans-serif">N</text>
          </svg>
        </div>
      </div>
    </section>
  );
}
