import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useProject } from '../../../context/ProjectContext';
import Button from '../../common/Button';
import Badge from '../../common/Badge';

export default function Step8Review({ onEditStep }) {
  const navigate = useNavigate();
  const { project, saveProjectToDashboard } = useProject();

  const handleLaunchGeneration = () => {
    saveProjectToDashboard();
    navigate(`/projects/${project.id || 'demo'}/generating`, {
      state: { wizardPayload: project }
    });
  };

  const loc = project.location || {};
  const prop = project.property || {};
  const fam = project.family || {};
  const bgt = project.budget || {};
  const sty = project.style || {};

  return (
    <div className="wizard__body">
      {/* 1. Project & Purpose */}
      <div className="review-block">
        <div className="review-block__header">
          <span className="text-xs uppercase tracking-widest font-semibold text-muted">01. Project Identification</span>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => onEditStep(1)}>Edit</button>
        </div>
        <div className="review-block__content">
          <div><div className="review-item__k">Name</div><div className="review-item__v">{project.name || 'Custom Home'}</div></div>
          <div><div className="review-item__k">Type</div><div className="review-item__v">{project.projectType || 'Villa'}</div></div>
          <div><div className="review-item__k">Purpose</div><div className="review-item__v">{project.purpose || 'New Construction'}</div></div>
        </div>
      </div>

      {/* 2. Location */}
      <div className="review-block">
        <div className="review-block__header">
          <span className="text-xs uppercase tracking-widest font-semibold text-muted">02. Site & Orientation</span>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => onEditStep(2)}>Edit</button>
        </div>
        <div className="review-block__content">
          <div><div className="review-item__k">Location</div><div className="review-item__v">{loc.city || 'Chennai'}, {loc.state || 'Tamil Nadu'}, {loc.country || 'India'}</div></div>
          <div><div className="review-item__k">Orientation</div><div className="review-item__v">{loc.orientation || 'East'}-Facing</div></div>
        </div>
      </div>

      {/* 3. Property */}
      <div className="review-block">
        <div className="review-block__header">
          <span className="text-xs uppercase tracking-widest font-semibold text-muted">03. Property Dimensions & Envelope</span>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => onEditStep(3)}>Edit</button>
        </div>
        <div className="review-block__content">
          <div><div className="review-item__k">Parcel Dimensions</div><div className="review-item__v">{prop.siteWidth || 40}ft × {prop.siteLength || 60}ft</div></div>
          <div><div className="review-item__k">Floors</div><div className="review-item__v">{prop.floors || 2} Storeys</div></div>
          <div><div className="review-item__k">Built-Up Area</div><div className="review-item__v">{prop.builtUpArea || 2400} sq ft</div></div>
          <div><div className="review-item__k">Shape</div><div className="review-item__v">{prop.plotShape || 'Rectangle'}</div></div>
        </div>
      </div>

      {/* 4. Family & Rooms */}
      <div className="review-block">
        <div className="review-block__header">
          <span className="text-xs uppercase tracking-widest font-semibold text-muted">04. Family & Room Program</span>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => onEditStep(4)}>Edit</button>
        </div>
        <div className="review-block__content">
          <div><div className="review-item__k">Household Profile</div><div className="review-item__v">{fam.adults || 2} Adults · {fam.children || 1} Children · {fam.elderly || 1} Elderly</div></div>
          <div><div className="review-item__k">Bedrooms / Baths</div><div className="review-item__v">{fam.rooms?.bedrooms || 3} Beds · {fam.rooms?.bathrooms || 3} Baths</div></div>
          <div><div className="review-item__k">Service Areas</div><div className="review-item__v">{fam.rooms?.kitchen || 1} Modular Kitchen · {fam.rooms?.pooja || 1} Pooja Room · {fam.rooms?.parking || 1} Car Park</div></div>
          <div><div className="review-item__k">Priorities</div><div className="review-item__v">{(fam.requirements || ['Vastu Compliance', 'Cross Ventilation', 'Natural Lighting']).join(', ')}</div></div>
        </div>
      </div>

      {/* 5. Budget */}
      <div className="review-block">
        <div className="review-block__header">
          <span className="text-xs uppercase tracking-widest font-semibold text-muted">05. Financial Allocation</span>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => onEditStep(5)}>Edit</button>
        </div>
        <div className="review-block__content">
          <div>
            <div className="review-item__k">Target Budget</div>
            <div className="review-item__v">
              {bgt.currency === 'USD' ? `$${Number(bgt.budgetRange || 200000).toLocaleString()}` : `₹${((Number(bgt.budgetRange) || 16500000) / 10000000).toFixed(2)} Crores`}
            </div>
          </div>
          <div><div className="review-item__k">Spec Grade</div><div className="review-item__v">{bgt.priority || 'Premium'}</div></div>
          <div>
            <div className="review-item__k">Rough Estimate</div>
            <div className="review-item__v">
              ~₹{Math.round((Number(bgt.budgetRange) || 16500000) / (Number(prop.builtUpArea) || 2400)).toLocaleString()}/sq ft
            </div>
          </div>
        </div>
      </div>

      {/* 6. Style & Materials */}
      <div className="review-block">
        <div className="review-block__header">
          <span className="text-xs uppercase tracking-widest font-semibold text-muted">06. Architectural Expression</span>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => onEditStep(6)}>Edit</button>
        </div>
        <div className="review-block__content">
          <div><div className="review-item__k">Style</div><div className="review-item__v">{sty.architecturalStyle || 'Modern'}</div></div>
          <div><div className="review-item__k">Materials</div><div className="review-item__v">{(sty.materialPreferences || ['Wood', 'Concrete', 'Glass']).join(', ')}</div></div>
          <div><div className="review-item__k">Custom Directives</div><div className="review-item__v">{sty.customRequirements || 'None specified'}</div></div>
        </div>
      </div>

      {/* 7. Floor Plan Mode */}
      <div className="review-block">
        <div className="review-block__header">
          <span className="text-xs uppercase tracking-widest font-semibold text-muted">07. Floorplan Engine Mode</span>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => onEditStep(7)}>Edit</button>
        </div>
        <div className="review-block__content">
          <div><div className="review-item__k">Generation Mode</div><div className="review-item__v">{project.floorplanMode === 'upload' ? 'Uploaded Existing CAD / Blueprint' : 'Parametric Spatial Topology Synthesizer'}</div></div>
        </div>
      </div>

      <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
        <Button variant="primary" size="xl" onClick={handleLaunchGeneration}>
          Generate Floor Plans →
        </Button>
      </div>
    </div>
  );
}
