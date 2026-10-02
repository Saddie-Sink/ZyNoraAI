import React from 'react';
import { useProject } from '../../../context/ProjectContext';

const PROJECT_TYPES = ['Independent House', 'Villa', 'Apartment', 'Other'];
const PURPOSES = ['New Construction', 'Renovation', 'Extension'];

export default function Step1Project() {
  const { project, updateProject } = useProject();

  return (
    <div className="wizard__body">
      <div className="form-group">
        <label className="form-label" htmlFor="proj-name">Project Name</label>
        <input
          id="proj-name"
          type="text"
          className="form-input"
          placeholder="e.g., Ananya Luxury Villa · ECR, Chennai"
          value={project.name || ''}
          onChange={(e) => updateProject('name', e.target.value)}
        />
        <span className="form-hint">Assign a descriptive identification label for this architectural project.</span>
      </div>

      <div className="form-group">
        <label className="form-label">Project Type</label>
        <div className="option-grid option-grid-2">
          {PROJECT_TYPES.map((type) => (
            <div
              key={type}
              className={`option-card ${project.projectType === type ? 'selected' : ''}`}
              onClick={() => updateProject('projectType', type)}
            >
              <div className="option-card__indicator" />
              <div className="option-card__content">
                <div className="option-card__title">{type}</div>
                <div className="option-card__sub">
                  {type === 'Villa' && 'Detached luxury residential estate with dedicated landscape'}
                  {type === 'Independent House' && 'Stand-alone family residence on private parcel'}
                  {type === 'Apartment' && 'High-density multi-unit residential floorplan'}
                  {type === 'Other' && 'Custom typology, duplex or townhouse unit'}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Construction Purpose</label>
        <div className="option-grid option-grid-3">
          {PURPOSES.map((purpose) => (
            <div
              key={purpose}
              className={`option-card ${project.purpose === purpose ? 'selected' : ''}`}
              onClick={() => updateProject('purpose', purpose)}
            >
              <div className="option-card__indicator" />
              <div className="option-card__content">
                <div className="option-card__title">{purpose}</div>
                <div className="option-card__sub">
                  {purpose === 'New Construction' && 'Greenfield development from foundation up'}
                  {purpose === 'Renovation' && 'Interior structural repartitioning and retrofitting'}
                  {purpose === 'Extension' && 'Horizontal or vertical wing expansion'}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
