import React from 'react';
import { useParams } from 'react-router-dom';
import { useProject } from '../context/ProjectContext';
import ExteriorGallery from '../components/gallery/ExteriorGallery';
import Badge from '../components/common/Badge';

export default function GalleryPage() {
  const { id } = useParams();
  const { project, selectedCandidate } = useProject();

  return (
    <div className="page-pad container">
      <div className="flex justify-between items-center mb-6 flex-wrap gap-4">
        <div>
          <span className="section-label">Parametric CAD Projections</span>
          <h1 className="section-title">Architectural CAD Elevations</h1>
          <p className="text-secondary" style={{ marginTop: '4px' }}>
            5 coordinated orthographic & oblique CAD projections generated directly from {selectedCandidate?.code || 'Candidate B'} ({selectedCandidate?.bedrooms || 3} BHK Villa).
          </p>
        </div>

        <div className="flex gap-2">
          <Badge variant="success">Parametric CAD Engine Active</Badge>
        </div>
      </div>

      <div className="demo-banner mb-8">
        <span><strong>GEOMETRIC ACCURACY:</strong> All CAD elevations are derived from the floorplan room boundaries and 3D extrusion coordinates with exact dimension datums and direct AutoCAD .DXF export.</span>
      </div>

      <ExteriorGallery project={project} candidate={selectedCandidate} />
    </div>
  );
}
