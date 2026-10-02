import React from 'react';
import { Link } from 'react-router-dom';

const PIPELINE_STEPS = [
  {
    num: '01',
    title: 'Configure Requirements',
    desc: 'Set your plot dimensions, bedrooms, bathrooms, floors, and entrance orientation.',
  },
  {
    num: '02',
    title: 'Generate 2D Floor Plan',
    desc: 'Instantly generate clean, high-contrast 2D architectural floor plans with room dimensions and furniture.',
  },
  {
    num: '03',
    title: 'Convert to 3D View',
    desc: 'Convert your selected or uploaded 2D floor plan into an interactive 3D visualization with multiple styles and angles.',
  },
  {
    num: '04',
    title: 'Export CAD & PDF',
    desc: 'Download your 2D floor plan as an AutoCAD (.DXF) file, print to PDF, or save high-resolution 3D renders.',
  }
];

export default function PipelineSection() {
  return (
    <section id="pipeline-section" className="pipeline-section">
      <div className="container">
        <div style={{ textAlign: 'center', maxWidth: '700px', margin: '0 auto' }}>
          <span className="section-label">How It Works</span>
          <h2 className="section-title">From Requirements to 2D Floor Plan & 3D View</h2>
          <p className="section-subtitle" style={{ margin: '0.75rem auto 0' }}>
            Design your custom home layout in four simple steps.
          </p>
        </div>

        <div className="pipeline-grid">
          {PIPELINE_STEPS.map((step) => (
            <div key={step.num} className="pipeline-card">
              <div className="flex items-center justify-between">
                <span className="pipeline-card__num">{step.num}</span>
              </div>
              <h3 className="pipeline-card__title">{step.title}</h3>
              <p className="pipeline-card__desc">{step.desc}</p>
            </div>
          ))}
        </div>

        <div style={{ textAlign: 'center', marginTop: '3rem' }}>
          <Link to="/projects/new" className="btn btn-primary btn-lg">
            Create Floor Plan
          </Link>
        </div>
      </div>
    </section>
  );
}
