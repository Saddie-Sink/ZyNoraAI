import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProject } from '../../context/ProjectContext';
import { parseRequirementsNL } from '../../services/api';

const EXAMPLE_PROMPTS = [
  {
    label: '30×40 Two-Storey 3BHK + Parking + Terrace',
    prompt:
      'I need a modern two-storey house on a 30 × 40 ft site. I need 3 bedrooms, 2 bathrooms, a living room, dining room, kitchen, one-car parking, a balcony and a terrace.',
  },
  {
    label: '40×60 Duplex 4BHK + Pooja + Study + 2-Car Park',
    prompt:
      'I want a two-storey East-facing house on a 40 × 60 ft plot with 4 bedrooms, 3 bathrooms, living room, dining room, modular kitchen, pooja room, study room, utility room, 2-car parking, balcony and terrace.',
  },
  {
    label: 'Conflict Test: 5BHK on Tiny 20×25 Single Floor',
    prompt:
      'I want a single-storey house on a 20 × 25 ft site with 5 bedrooms, 4 bathrooms, living room, dining room, kitchen, study room and two-car parking.',
  },
];

export default function NLRequirementBar({ onGenerateWithPrompt = null, compact = false }) {
  const navigate = useNavigate();
  const { project, updateProject, saveProjectToDashboard } = useProject();

  const [promptText, setPromptText] = useState(
    project.nlPrompt ||
      'I need a modern two-storey house on a 30 × 40 ft site. I need 3 bedrooms, 2 bathrooms, a living room, dining room, kitchen, one-car parking, a balcony and a terrace.'
  );
  const [parsedResult, setParsedResult] = useState(null);
  const [isParsing, setIsParsing] = useState(false);

  const handleAnalyzePrompt = async (customText) => {
    const textToParse = typeof customText === 'string' ? customText : promptText;
    if (!textToParse.trim()) return;
    setIsParsing(true);
    try {
      const res = await parseRequirementsNL(textToParse, project);
      const data = res.data || res;
      setParsedResult(data);

      // Sync extracted parameters into ProjectContext
      if (data?.wizardSync) {
        const sync = data.wizardSync;
        updateProject({
          nlPrompt: textToParse,
          property: { ...(project.property || {}), ...(sync.property || {}) },
          location: { ...(project.location || {}), ...(sync.location || {}) },
          family: {
            ...(project.family || {}),
            ...(sync.family || {}),
            rooms: { ...(project.family?.rooms || {}), ...(sync.family?.rooms || {}) },
          },
          style: { ...(project.style || {}), ...(sync.style || {}) },
        });
      }
    } finally {
      setIsParsing(false);
    }
  };

  const handleGenerateNow = async () => {
    const res = await parseRequirementsNL(promptText, project);
    const data = res.data || res;
    setParsedResult(data);

    const sync = data?.wizardSync || {};
    const mergedProject = {
      ...project,
      nlPrompt: promptText,
      property: { ...(project.property || {}), ...(sync.property || {}) },
      location: { ...(project.location || {}), ...(sync.location || {}) },
      family: {
        ...(project.family || {}),
        ...(sync.family || {}),
        rooms: { ...(project.family?.rooms || {}), ...(sync.family?.rooms || {}) },
      },
      style: { ...(project.style || {}), ...(sync.style || {}) },
    };
    updateProject(mergedProject);

    if (onGenerateWithPrompt) {
      onGenerateWithPrompt(mergedProject, data);
    } else {
      saveProjectToDashboard();
      navigate(`/projects/${project.id || 'proj-001'}/generating`, {
        state: { wizardPayload: mergedProject },
      });
    }
  };

  const structured = parsedResult?.structuredRequirements;
  const validation = parsedResult?.requirementValidation;

  return (
    <div
      style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--r-xl)',
        padding: compact ? '1rem 1.25rem' : '1.25rem 1.5rem',
        marginBottom: '1.5rem',
        boxShadow: '0 4px 18px rgba(0,0,0,0.04)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              background: 'rgba(200, 169, 110, 0.16)',
              color: 'var(--accent-dark)',
              fontSize: '10px',
              fontWeight: 700,
              padding: '3px 8px',
              borderRadius: '4px',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
            }}
          >
            Stages 1–3 · AI Natural Language Requirement Extractor
          </span>
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Describe your site, floors & required rooms in plain English or use the form controls below
          </span>
        </div>

        {/* Example Prompt Pills */}
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {EXAMPLE_PROMPTS.map((ex, i) => (
            <button
              key={i}
              type="button"
              onClick={() => {
                setPromptText(ex.prompt);
                handleAnalyzePrompt(ex.prompt);
              }}
              style={{
                fontSize: '10.5px',
                padding: '3px 8px',
                borderRadius: '6px',
                border: '1px solid var(--border)',
                background: 'var(--surface-alt)',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
              }}
            >
              {ex.label}
            </button>
          ))}
        </div>
      </div>

      {/* Textarea + Action Buttons */}
      <div style={{ display: 'flex', gap: '10px', alignItems: 'stretch', flexWrap: 'wrap' }}>
        <textarea
          aria-label="Natural language architectural requirements"
          rows={compact ? 2 : 3}
          className="form-input"
          style={{ flex: '1 1 420px', fontSize: '13px', lineHeight: 1.45, resize: 'vertical' }}
          placeholder="Example: I need a modern two-storey house on a 30 × 40 ft site. I need 3 bedrooms, 2 bathrooms, a living room, dining room, kitchen, one-car parking, a balcony and a terrace."
          value={promptText}
          onChange={(e) => setPromptText(e.target.value)}
        />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', justifyContent: 'center' }}>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => handleAnalyzePrompt(promptText)}
            disabled={isParsing}
          >
            {isParsing ? 'Extracting...' : '1. Extract & Validate Constraints'}
          </button>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={handleGenerateNow}
          >
            2. Generate 2D Floor Plan →
          </button>
        </div>
      </div>

      {/* Extracted Constraints & Stage 3 Validation Report */}
      {structured && validation && (
        <div
          style={{
            marginTop: '14px',
            paddingTop: '12px',
            borderTop: '1px solid var(--border-soft)',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
          }}
        >
          {/* Stage 3 Validation Status Banner */}
          <div
            style={{
              padding: '10px 14px',
              borderRadius: '8px',
              background:
                validation.status === 'CONFLICT'
                  ? 'rgba(239, 68, 68, 0.10)'
                  : validation.status === 'WARNING'
                  ? 'rgba(245, 158, 11, 0.10)'
                  : 'rgba(16, 185, 129, 0.10)',
              border: `1px solid ${
                validation.status === 'CONFLICT'
                  ? 'rgba(239, 68, 68, 0.4)'
                  : validation.status === 'WARNING'
                  ? 'rgba(245, 158, 11, 0.4)'
                  : 'rgba(16, 185, 129, 0.35)'
              }`,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              flexWrap: 'wrap',
              gap: '10px',
            }}
          >
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)' }}>
                {validation.status === 'CONFLICT'
                  ? '⚠️ Stage 3 Validation: Site & Program Conflict Detected'
                  : validation.status === 'WARNING'
                  ? '⚡ Stage 3 Validation: Feasible with Compact Space Optimization'
                  : '✓ Stage 3 Validation: All Architectural Constraints Feasible'}
              </div>
              {validation.conflicts?.map((c, idx) => (
                <div key={idx} style={{ fontSize: '12px', color: '#dc2626', marginTop: '4px', fontWeight: 500 }}>
                  • {c.message}
                </div>
              ))}
              {validation.warnings?.map((w, idx) => (
                <div key={idx} style={{ fontSize: '12px', color: '#d97706', marginTop: '4px' }}>
                  • {w.message}
                </div>
              ))}
              {validation.recommendations?.map((r, idx) => (
                <div key={idx} style={{ fontSize: '11.5px', color: 'var(--text-secondary)', marginTop: '3px' }}>
                  💡 {r}
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', gap: '12px', fontSize: '11px', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>
              <div>
                <div style={{ color: 'var(--text-muted)' }}>Site Area</div>
                <strong>{validation.siteAreaSqFt} sq ft</strong>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)' }}>Buildable / Flr</div>
                <strong>{validation.buildableFootprintSqFt} sq ft</strong>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)' }}>Total Envelope</div>
                <strong>{validation.totalBuildableAreaSqFt} sq ft</strong>
              </div>
              <div>
                <div style={{ color: 'var(--text-muted)' }}>Min Req Area</div>
                <strong>{validation.minRequiredAreaSqFt} sq ft</strong>
              </div>
            </div>
          </div>

          {/* Stage 2 Mandatory vs Optional Requirements */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
            <div style={{ background: 'var(--surface-alt)', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '10.5px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#059669', marginBottom: '6px' }}>
                ✓ Mandatory Requirements ({structured.mandatoryRequirements?.length || 0})
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                {(structured.mandatoryRequirements || []).map((item, i) => (
                  <span
                    key={i}
                    style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: 'rgba(16, 185, 129, 0.12)',
                      color: 'var(--text-primary)',
                      border: '1px solid rgba(16, 185, 129, 0.28)',
                      fontWeight: 500,
                    }}
                  >
                    {item.label}
                  </span>
                ))}
              </div>
            </div>

            <div style={{ background: 'var(--surface-alt)', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '10.5px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--accent-dark)', marginBottom: '6px' }}>
                ✦ Optional / Preference Constraints ({structured.optionalRequirements?.length || 0})
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                {(structured.optionalRequirements || []).map((item, i) => (
                  <span
                    key={i}
                    style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: 'rgba(200, 169, 110, 0.14)',
                      color: 'var(--text-secondary)',
                      border: '1px solid rgba(200, 169, 110, 0.30)',
                    }}
                  >
                    {item.label}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
