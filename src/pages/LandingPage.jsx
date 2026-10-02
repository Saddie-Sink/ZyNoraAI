import React from 'react';
import HeroSection from '../components/landing/HeroSection';
import PipelineSection from '../components/landing/PipelineSection';
import Card from '../components/common/Card';
import { Link } from 'react-router-dom';

export default function LandingPage() {
  return (
    <div>
      <HeroSection />
      <PipelineSection />

      <section style={{ padding: '5rem 0', background: 'var(--surface-alt)' }}>
        <div className="container">
          <div style={{ textAlign: 'center', maxWidth: '640px', margin: '0 auto 3.5rem' }}>
            <span className="section-label">Key Capabilities</span>
            <h2 className="section-title">Built for Homeowners & Architects</h2>
            <p className="section-subtitle" style={{ margin: '0.75rem auto 0' }}>
              Generate clear 2D floor plans, convert any floor plan to 3D, and export directly to CAD.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
            <Card
              label="2D Floor Plan"
              title="AI Floor Plan Generator"
              subtitle="Generate high-contrast 2D architectural layouts customized to your plot dimensions, room counts, and facing direction."
            />

            <Card
              label="2D to 3D"
              title="Floor Plan to 3D Converter"
              subtitle="Convert your selected floor plan or upload an existing 2D plan to view it in Photorealistic, Minimalist, Blueprint, or Sketch 3D."
            />

            <Card
              label="CAD & Print"
              title="AutoCAD .DXF & PDF Export"
              subtitle="Download vector .DXF files for AutoCAD, print scaled floor plans, or export high-resolution 3D PNG views."
            />
          </div>

          <div style={{ textAlign: 'center', marginTop: '4rem' }}>
            <Link to="/projects/new" className="btn btn-primary btn-xl">
              Start Your Floor Plan Now →
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
