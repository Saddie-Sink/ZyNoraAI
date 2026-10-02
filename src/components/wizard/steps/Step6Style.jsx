import React from 'react';
import { useProject } from '../../../context/ProjectContext';

const ARCHITECTURAL_STYLES = [
  { name: 'Modern Contemporary Indian', desc: 'Clean geometric massing, travertine sandstone, teak screening, cantilevered portico' },
  { name: 'Chettinad Contemporary', desc: 'Courtyard-centric layout, carved teak wood louvers, Athangudi-inspired tiles, wide verandahs' },
  { name: 'Tropical Vernacular', desc: 'Deep eaves for monsoon shade, terracotta chajjas, breathable lattice jalis, open courtyards' },
  { name: 'Minimalist Luxury', desc: 'Monolithic granite and limestone surfaces, floor-to-ceiling glass, floating concrete slabs' },
  { name: 'Traditional Kerala / Tamil Style', desc: 'Pitched mangalore tiled roofs, timber rafters, central Nadumuttam (atrium), wooden pillars' },
  { name: 'Eco-Biophilic Villa', desc: 'Internal landscape gardens, rainwater harvesting integration, natural lime plaster finishes' }
];

const MATERIALS = [
  'Nilambur Teak Wood',
  'Travertine Sandstone',
  'Black Granite & Limestone',
  'Terracotta Jali & Tiles',
  'Low-E Structural Glazing',
  'Fair-face Concrete Plinth'
];

export default function Step6Style() {
  const { project, updateNested, toggleMaterial } = useProject();
  const sty = project.style || {};
  const currentStyle = sty.architecturalStyle || 'Modern';
  const selectedMaterials = sty.materialPreferences || [];

  return (
    <div className="wizard__body">
      <div className="form-group">
        <label className="form-label">Architectural Aesthetic Expression</label>
        <div className="option-grid option-grid-3">
          {ARCHITECTURAL_STYLES.map((style) => (
            <div
              key={style.name}
              className={`option-card ${currentStyle === style.name ? 'selected' : ''}`}
              onClick={() => updateNested('style', 'architecturalStyle', style.name)}
            >
              <div className="option-card__indicator" />
              <div className="option-card__content">
                <div className="option-card__title">{style.name}</div>
                <div className="option-card__sub">{style.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label className="form-label">Primary Material Palette Preferences</label>
        <div className="option-grid option-grid-3">
          {MATERIALS.map((mat) => {
            const isSelected = selectedMaterials.includes(mat);
            return (
              <div
                key={mat}
                className={`option-card checkbox-card ${isSelected ? 'selected' : ''}`}
                onClick={() => toggleMaterial(mat)}
              >
                <div className="option-card__indicator" />
                <div className="option-card__content">
                  <div className="option-card__title">{mat}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="custom-req">Custom Architectural Notes & Feature Directives</label>
        <textarea
          id="custom-req"
          className="form-textarea"
          placeholder="e.g. Large cantilevered balcony overlooking backyard, double-height entryway, covered entrance with limestone accents."
          value={sty.customRequirements || ''}
          onChange={(e) => updateNested('style', 'customRequirements', e.target.value)}
        />
        <span className="form-hint">These specific qualitative requirements will guide prompt conditioning in future ML generation phases.</span>
      </div>
    </div>
  );
}
