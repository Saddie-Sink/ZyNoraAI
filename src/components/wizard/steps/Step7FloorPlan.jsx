import React, { useState } from 'react';
import { useProject } from '../../../context/ProjectContext';
import Card from '../../common/Card';

export default function Step7FloorPlan() {
  const { project, updateProject } = useProject();
  const [dragOver, setDragOver] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);

  const mode = project.floorplanMode || 'generate';

  const handleFileDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setUploadedFile({
        name: file.name,
        size: (file.size / 1024).toFixed(1) + ' KB',
        type: file.type || 'Architectural Document'
      });
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setUploadedFile({
        name: file.name,
        size: (file.size / 1024).toFixed(1) + ' KB',
        type: file.type || 'Architectural Document'
      });
    }
  };

  return (
    <div className="wizard__body">
      <div className="form-group">
        <label className="form-label">Floor Plan Pipeline Strategy</label>
        <div className="option-grid option-grid-2">
          <div
            className={`option-card ${mode === 'generate' ? 'selected' : ''}`}
            onClick={() => updateProject('floorplanMode', 'generate')}
          >
            <div className="option-card__indicator" />
            <div className="option-card__content">
              <div className="option-card__title">Option A: Synthesize via Spatial ML (Recommended)</div>
              <div className="option-card__sub">
                Automatically generate multiple candidate layouts based on your site dimensions, room program, orientation, and family requirements.
              </div>
            </div>
          </div>

          <div
            className={`option-card ${mode === 'upload' ? 'selected' : ''}`}
            onClick={() => updateProject('floorplanMode', 'upload')}
          >
            <div className="option-card__indicator" />
            <div className="option-card__content">
              <div className="option-card__title">Option B: Upload Existing Floor Plan Document</div>
              <div className="option-card__sub">
                Ingest an existing draft, architectural blueprint, or hand-drawn plan to extract spatial topology and convert into 3D massing.
              </div>
            </div>
          </div>
        </div>
      </div>

      {mode === 'upload' ? (
        <Card
          label="Blueprint Ingestion Pipeline"
          title="Upload Architectural Floorplan"
          subtitle="Accepted formats: SVG, PNG, JPG, PDF (Vector CAD or high-res scan)"
        >
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleFileDrop}
            style={{
              border: dragOver ? '2px dashed var(--accent)' : '2px dashed var(--border)',
              background: dragOver ? 'rgba(200,169,110,0.06)' : 'var(--surface-warm)',
              padding: '3rem 2rem',
              borderRadius: 'var(--r-lg)',
              textAlign: 'center',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onClick={() => document.getElementById('file-upload-input')?.click()}
          >
            <input
              id="file-upload-input"
              type="file"
              accept=".svg,.png,.jpg,.jpeg,.pdf"
              style={{ display: 'none' }}
              onChange={handleFileInput}
            />
            <div style={{ fontSize: '36px', opacity: 0.5, marginBottom: '0.75rem' }}>📄</div>
            <div style={{ fontWeight: 600, fontSize: '15px' }}>
              {uploadedFile ? uploadedFile.name : 'Click to select or drag and drop floorplan file'}
            </div>
            <div className="text-xs text-muted" style={{ marginTop: '4px' }}>
              {uploadedFile ? `${uploadedFile.size} · Ready for future vector parsing` : 'Supports architectural SVG, PNG, JPG, PDF'}
            </div>
            <div className="badge badge-demo" style={{ marginTop: '1rem' }}>
              Frontend Mock Upload Flow · Real OCR/Vector Parsing Offline
            </div>
          </div>
        </Card>
      ) : (
        <Card
          label="Automated Spatial Graph Engine"
          title="Parametric Layout Generation Ready"
          subtitle="The system will generate 5 diverse topological arrangements meeting your specified 3,800 sq ft footprint."
        >
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', background: 'var(--surface-warm)', padding: '1.25rem', borderRadius: 'var(--r-lg)' }}>
            <div>
              <div className="text-xs text-muted uppercase tracking-wider">Permutations</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
                5 Ranked Candidates
              </div>
            </div>
            <div>
              <div className="text-xs text-muted uppercase tracking-wider">Spatial Target</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--accent-dark)', marginTop: '2px' }}>
                {project.family?.rooms?.bedrooms || 4} Bed / {project.family?.rooms?.bathrooms || 4} Bath
              </div>
            </div>
            <div>
              <div className="text-xs text-muted uppercase tracking-wider">Orientation</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '2px' }}>
                {project.location?.orientation || 'North'}-Facing Solar Axis
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
