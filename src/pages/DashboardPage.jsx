import React from 'react';
import { Link } from 'react-router-dom';
import { useProject } from '../context/ProjectContext';
import Badge from '../components/common/Badge';

export default function DashboardPage() {
  const { projectsList, deleteProject } = useProject();

  return (
    <div className="page-pad container">
      <div className="flex justify-between items-center mb-8 flex-wrap gap-4">
        <div>
          <span className="section-label">Your Workspace</span>
          <h1 className="section-title">Saved Floor Plan Projects</h1>
          <p className="text-secondary" style={{ marginTop: '4px' }}>
            Access your generated 2D floor plans and interactive 3D models.
          </p>
        </div>

        <div className="flex gap-3">
          <Link to="/projects/new" className="btn btn-primary">
            + New Project
          </Link>
        </div>
      </div>

      {projectsList.length === 0 ? (
        <div
          style={{
            background: 'var(--surface-alt)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--r-xl)',
            padding: '3.5rem 2rem',
            textAlign: 'center',
            maxWidth: '540px',
            margin: '2rem auto',
          }}
        >
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>
            No saved projects yet
          </h2>
          <p className="text-secondary" style={{ fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Start a new project to generate custom 2D floor plans and 3D home visualizations.
          </p>
          <Link to="/projects/new" className="btn btn-primary">
            Create Your First Floor Plan →
          </Link>
        </div>
      ) : (
        <div className="projects-grid">
          {projectsList.map((proj) => (
            <div key={proj.id} className="project-card-ui">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-xs uppercase tracking-widest text-accent font-semibold">
                    {proj.type} · {proj.style}
                  </span>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginTop: '2px' }}>{proj.name}</h3>
                  <span className="text-xs text-muted">{proj.city} · {proj.area}</span>
                </div>
                <Badge variant="ready">{proj.status || 'Ready'}</Badge>
              </div>

              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  background: 'var(--surface-alt)',
                  padding: '12px',
                  borderRadius: 'var(--r-lg)',
                  border: '1px solid var(--border)',
                }}
              >
                <div className="flex justify-between items-center text-xs">
                  <span className="text-muted">Plot Size:</span>
                  <span className="font-semibold">{proj.stats?.site || '30′ × 40′ Plot'}</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-muted">Configuration:</span>
                  <span className="font-semibold">{proj.stats?.rooms || '3 BHK'}</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-muted">Floors:</span>
                  <span className="font-semibold">{proj.stats?.floorsLabel || `${proj.floors || 2} Floors`}</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-muted">Orientation:</span>
                  <span className="font-semibold">{proj.stats?.orientation || 'East Facing'}</span>
                </div>
              </div>

              <div className="flex justify-between items-center mt-2">
                <button
                  type="button"
                  onClick={() => deleteProject?.(proj.id)}
                  className="text-xs text-muted"
                  style={{ background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
                >
                  Delete
                </button>
                <div className="flex gap-2">
                  <Link to={`/projects/${proj.id}/floorplans`} className="btn btn-primary btn-sm">
                    Open Floor Plan & 3D →
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
