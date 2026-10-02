import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { generateFloorplans, createProject } from '../services/api';
import { useProject } from '../context/ProjectContext';

export default function GeneratingPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { project } = useProject();

  const [progress, setProgress] = useState(18);
  const [statusText, setStatusText] = useState('Creating your 2D floor plan & 3D model...');
  const hasRun = useRef(false);

  useEffect(() => {
    if (hasRun.current) return;
    hasRun.current = true;

    const wizardPayload = location.state?.wizardPayload || project || {
      property: { builtUpArea: 2400, floors: 2, siteWidth: 30, siteLength: 40 },
      family:   { rooms: { bedrooms: 3, bathrooms: 3 } },
      location: { orientation: 'East', city: 'Chennai', country: 'India' },
      style:    { architecturalStyle: 'Modern' },
    };

    runGeneration(wizardPayload);
  }, []);

  async function runGeneration(wizardPayload) {
    try {
      setProgress(35);
      const projRes = await createProject({
        name: project?.name || 'Custom Home',
        projectType: project?.projectType || 'Villa',
        ...wizardPayload,
      });
      const projectId = projRes.data?.id || id || 'proj-001';

      setProgress(70);
      setStatusText('Preparing 2D layout & 3D view...');
      const genRes = await generateFloorplans(projectId, wizardPayload);
      const candidates = genRes.data?.candidates || genRes.data || [];

      setProgress(100);
      await new Promise((r) => setTimeout(r, 250));

      navigate(`/projects/${projectId}/floorplans`, {
        state: {
          candidates,
          generationMeta: genRes.data,
          isFallback: genRes.isDemoData,
        },
      });
    } catch (err) {
      console.error('Generation error:', err);
      navigate(`/projects/${id || 'demo'}/floorplans`);
    }
  }

  return (
    <div
      style={{
        minHeight: 'calc(100vh - 64px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f8fafc',
        padding: '24px',
      }}
    >
      <div
        style={{
          background: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: '16px',
          padding: '40px 36px',
          maxWidth: '420px',
          width: '100%',
          textAlign: 'center',
          boxShadow: '0 10px 30px rgba(15, 23, 42, 0.06)',
        }}
      >
        {/* Minimal Spinner */}
        <div
          style={{
            width: '48px',
            height: '48px',
            margin: '0 auto 20px',
            borderRadius: '50%',
            border: '3.5px solid #e2e8f0',
            borderTopColor: '#2563eb',
            animation: 'spin 0.8s linear infinite',
          }}
        />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

        <h2
          style={{
            fontSize: '18px',
            fontWeight: 600,
            color: '#0f172a',
            margin: '0 0 8px',
          }}
        >
          Generating Floor Plan
        </h2>
        <p
          style={{
            fontSize: '13.5px',
            color: '#64748b',
            margin: '0 0 24px',
          }}
        >
          {statusText}
        </p>

        {/* Clean Progress Bar */}
        <div
          style={{
            height: '6px',
            background: '#f1f5f9',
            borderRadius: '999px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${progress}%`,
              background: '#2563eb',
              borderRadius: '999px',
              transition: 'width 0.35s ease',
            }}
          />
        </div>
        <div
          style={{
            marginTop: '10px',
            fontSize: '12px',
            fontWeight: 600,
            color: '#64748b',
          }}
        >
          {progress}%
        </div>
      </div>
    </div>
  );
}
