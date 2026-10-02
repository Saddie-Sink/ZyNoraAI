import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { useProject } from '../context/ProjectContext';

export default function ProjectPage() {
  const { id } = useParams();
  const { project } = useProject();

  return (
    <div className="page-pad container">
      <div className="flex justify-between items-center mb-8 flex-wrap gap-4">
        <div>
          <span className="section-label">Project Overview</span>
          <h1 className="section-title">{project.name || 'My Home Floor Plan'}</h1>
          <p className="text-secondary" style={{ marginTop: '4px' }}>
            {project.projectType || 'Independent House'} · {project.purpose || 'New Construction'} · {project.location?.city || 'Local Site'}
          </p>
        </div>

        <div className="flex gap-3">
          <Link to={`/projects/${id}/floorplans`} className="btn btn-primary">
            Open Floor Plan & 3D →
          </Link>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <Link to="/projects/new" className="card card-hover">
          <div className="card__label">Step 01</div>
          <div className="card__title">Project Setup & Rooms</div>
          <p className="text-xs text-muted">Edit plot size, room requirements, and facing direction</p>
        </Link>

        <Link to={`/projects/${id}/floorplans`} className="card card-hover">
          <div className="card__label">Step 02</div>
          <div className="card__title">2D Floor Plan & 3D Studio</div>
          <p className="text-xs text-muted">Customize 2D floor plans, convert to 3D, and export .DXF</p>
        </Link>
      </div>
    </div>
  );
}
