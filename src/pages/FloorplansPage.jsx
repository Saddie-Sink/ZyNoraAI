import React, { useState, useEffect, useRef } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { useProject } from '../context/ProjectContext';
import { generateFloorplans, runAICopilot } from '../services/api';
import { downloadFloorplanDXF } from '../services/dxfExport';
import { analyzeUploadedFloorplanImage } from '../services/floorplanImageAnalyzer';
import {
  getStoredGeminiApiKey,
  setStoredGeminiApiKey,
} from '../services/ai3DRenderService';
import EditableFloorplanCanvas, { True2DCandidatePreview } from '../components/floorplan/EditableFloorplanCanvas';
import { RENDER_STYLES, VIEW_ANGLES } from '../components/floorplan/Interactive3DViewer';

export default function FloorplansPage({ defaultStudioTab = 'cad' }) {
  const { id } = useParams();
  const location = useLocation();
  const {
    project,
    selectedCandidateId,
    selectCandidate,
    selectedCandidate,
    setCandidates: setContextCandidates,
  } = useProject();
  const fileInputRef = useRef(null);

  const [candidates, setCandidates] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [toastMsg, setToastMsg] = useState(null);

  // Workbench tool mode: 'generator' (2D Plan) | 'to3d' (Floor Plan to 3D)
  const [workbenchTool, setWorkbenchTool] = useState(defaultStudioTab === '3d' ? 'to3d' : 'generator');
  const [studioTab, setStudioTab] = useState(defaultStudioTab === '3d' ? 'split' : 'cad');

  // 2D Generator state
  const [inputMode, setInputMode] = useState('house'); // 'house' | 'prompt'
  const [bedrooms, setBedrooms] = useState(project?.family?.rooms?.bedrooms || 3);
  const [bathrooms, setBathrooms] = useState(project?.family?.rooms?.bathrooms || 3);
  const [floors, setFloors] = useState(project?.property?.floors || 2);
  const [siteWidth, setSiteWidth] = useState(project?.property?.siteWidth || 30);
  const [siteLength, setSiteLength] = useState(project?.property?.siteLength || 40);
  const [orientation, setOrientation] = useState(project?.location?.orientation || 'East');
  const [hasPooja, setHasPooja] = useState((project?.family?.rooms?.pooja ?? 1) > 0);
  const [hasParking, setHasParking] = useState((project?.family?.rooms?.parking ?? 1) > 0);
  const [hasBalcony, setHasBalcony] = useState((project?.family?.rooms?.balcony ?? 1) > 0);
  const [promptText, setPromptText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  // Minimal Floor Plan to 3D state (Gemini 3.1 Flash Image)
  const [planSourceMode, setPlanSourceMode] = useState('selected'); // 'selected' | 'upload'
  const [uploadedCandidate, setUploadedCandidate] = useState(null);
  const [isAnalyzingUpload, setIsAnalyzingUpload] = useState(false);
  const [renderStyle3D, setRenderStyle3D] = useState('photorealistic');
  const [viewAngle3D, setViewAngle3D] = useState('birds_eye');
  const [bgMode3D, setBgMode3D] = useState('white');
  const [extraReqPrompt, setExtraReqPrompt] = useState('');
  const [trigger3DCount, setTrigger3DCount] = useState(0);

  // Minimal Gemini API Key state
  const [geminiKey, setGeminiKey] = useState(() => getStoredGeminiApiKey());
  const [showKeyPopover, setShowKeyPopover] = useState(false);

  useEffect(() => {
    if (defaultStudioTab === '3d') {
      setWorkbenchTool('to3d');
      setStudioTab('split');
    } else {
      setWorkbenchTool('generator');
      setStudioTab('cad');
    }
  }, [defaultStudioTab]);

  useEffect(() => {
    async function loadCandidates() {
      setIsLoading(true);

      const passedCandidates = location.state?.candidates;
      if (passedCandidates && passedCandidates.length > 0) {
        const topThree = passedCandidates.slice(0, 3);
        setCandidates(topThree);
        setContextCandidates?.(topThree);
        const best = topThree.find((c) => c.isTopRank) || topThree[0];
        if (best) {
          selectCandidate?.(best.id);
          if (best.bedrooms) setBedrooms(best.bedrooms);
          if (best.bathrooms) setBathrooms(best.bathrooms);
          if (best.floors) setFloors(best.floors);
          if (best.siteWidth) setSiteWidth(best.siteWidth);
          if (best.siteDepth) setSiteLength(best.siteDepth);
        }
        setIsLoading(false);
        return;
      }

      try {
        const payload = {
          id: id || project?.id || 'proj-001',
          property: project?.property || {
            builtUpArea: 2400,
            floors: 2,
            siteWidth: 30,
            siteLength: 40,
            plotShape: 'Rectangle',
          },
          family: project?.family || { rooms: { bedrooms: 3, bathrooms: 3 } },
          location: project?.location || { orientation: 'East' },
          budget: project?.budget || { priority: 'Balanced', budgetRange: 16500000 },
          style: project?.style || { architecturalStyle: 'Modern Contemporary Indian' },
          topK: 3,
        };
        const res = await generateFloorplans(payload.id, payload);
        const cands = (res.data?.candidates || []).slice(0, 3);
        setCandidates(cands);
        setContextCandidates?.(cands);
        const best = cands.find((c) => c.isTopRank) || cands[0];
        if (best) selectCandidate?.(best.id);
      } catch (err) {
        console.error('Failed to load candidates:', err);
      } finally {
        setIsLoading(false);
      }
    }

    loadCandidates();
  }, [id]);

  const bestCandidate = candidates.find((c) => c.isTopRank) || candidates[0];
  const selectedGenCandidate =
    candidates.find((c) => c.id === selectedCandidateId) || bestCandidate || selectedCandidate;

  const activeCandidate =
    workbenchTool === 'to3d' && planSourceMode === 'upload' && uploadedCandidate
      ? uploadedCandidate
      : selectedGenCandidate;

  const showNotification = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3200);
  };

  const handleConvertSelectedTo3D = () => {
    setPlanSourceMode('selected');
    setWorkbenchTool('to3d');
    setStudioTab('split');
    setTrigger3DCount((c) => c + 1);
  };

  const handleUploadFloorplanFile = async (file) => {
    if (!file) return;
    setIsAnalyzingUpload(true);
    try {
      const analyzedCandidate = await analyzeUploadedFloorplanImage(file, {
        fileName: file.name,
        siteLength: Number(siteLength) || 42,
      });
      setUploadedCandidate(analyzedCandidate);
      setPlanSourceMode('upload');
      setWorkbenchTool('to3d');
      setStudioTab('split');
      setTrigger3DCount((c) => c + 1);
      showNotification(`Loaded "${file.name}" into 3D Converter`);
    } catch (err) {
      console.error('Failed to analyze uploaded floor plan:', err);
      showNotification('Could not read image. Please use PNG, JPG, or WEBP.');
    } finally {
      setIsAnalyzingUpload(false);
    }
  };

  const handleGenerateFromControls = async () => {
    setIsGenerating(true);
    try {
      const w = Math.max(20, Math.min(120, Number(siteWidth) || 30));
      const d = Math.max(20, Math.min(150, Number(siteLength) || 40));
      const payload = {
        id: id || project?.id || 'proj-001',
        property: {
          ...(project?.property || {}),
          siteWidth: w,
          siteLength: d,
          floors: Number(floors) || 2,
          plotShape: 'Rectangle',
          builtUpArea: Math.round(w * d * 0.74 * (Number(floors) || 2)),
        },
        family: {
          ...(project?.family || {}),
          rooms: {
            ...(project?.family?.rooms || {}),
            bedrooms: Number(bedrooms) || 3,
            bathrooms: Number(bathrooms) || 2,
            livingRoom: 1,
            dining: 1,
            kitchen: 1,
            pooja: hasPooja ? 1 : 0,
            parking: hasParking ? 1 : 0,
            balcony: hasBalcony ? 1 : 0,
            terrace: Number(floors) > 1 ? 1 : 0,
          },
        },
        location: { ...(project?.location || {}), orientation },
        budget: project?.budget || { priority: 'Balanced', budgetRange: 16500000 },
        style: project?.style || { architecturalStyle: 'Modern Contemporary Indian' },
        topK: 3,
      };
      const res = await generateFloorplans(payload.id, payload);
      const cands = (res.data?.candidates || []).slice(0, 3);
      setCandidates(cands);
      setContextCandidates?.(cands);
      const best = cands.find((c) => c.isTopRank) || cands[0];
      if (best) selectCandidate?.(best.id);
      showNotification(`2D Plan updated (${bedrooms} BHK · ${w}×${d} ft)`);
    } catch (err) {
      console.error('Generation failed:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleGenerateFromPrompt = async (customCmd) => {
    const cmd = (customCmd ?? promptText).trim();
    if (!cmd) return;
    setIsGenerating(true);
    try {
      const payload = {
        id: id || project?.id || 'proj-001',
        property: {
          siteWidth: Number(siteWidth) || 30,
          siteLength: Number(siteLength) || 40,
          floors: Number(floors) || 2,
        },
        family: { rooms: { bedrooms: Number(bedrooms) || 3, bathrooms: Number(bathrooms) || 3 } },
        location: { orientation },
        style: { architecturalStyle: 'Modern Contemporary Indian' },
      };
      const res = await runAICopilot(cmd, payload, activeCandidate);
      const data = res.data || res;
      if (data?.candidates?.length) {
        const topThree = data.candidates.slice(0, 3);
        setCandidates(topThree);
        setContextCandidates?.(topThree);
        const best = topThree.find((c) => c.isTopRank) || topThree[0];
        if (best) {
          selectCandidate?.(best.id);
          if (best.bedrooms) setBedrooms(best.bedrooms);
          if (best.bathrooms) setBathrooms(best.bathrooms);
          if (best.floors) setFloors(best.floors);
          if (best.siteWidth) setSiteWidth(best.siteWidth);
          if (best.siteDepth) setSiteLength(best.siteDepth);
        }
      }
      showNotification('Floor plan generated with Gemini');
    } catch (err) {
      console.error('Prompt generation error:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApply3DSettings = () => {
    if (extraReqPrompt.trim()) {
      const lower = extraReqPrompt.toLowerCase();
      if (lower.includes('blueprint')) setRenderStyle3D('blueprint');
      else if (lower.includes('sketch')) setRenderStyle3D('sketch');
      else if (lower.includes('minimal')) setRenderStyle3D('minimalist');
      if (lower.includes('dark') || lower.includes('night')) setBgMode3D('dark');
      else if (lower.includes('white')) setBgMode3D('white');
      else if (lower.includes('garden') || lower.includes('lawn')) setBgMode3D('landscaped');
    }
    if (studioTab === 'cad') setStudioTab('split');
    setTrigger3DCount((c) => c + 1);
  };

  const handleExportDXF = () => {
    if (!activeCandidate) return;
    const res = downloadFloorplanDXF(activeCandidate, project);
    if (res.success) {
      showNotification(`Exported ${activeCandidate.code}.dxf`);
    } else {
      showNotification(`Export error: ${res.error}`);
    }
  };

  const handleUpdateCandidate = (updatedCandidate) => {
    if (updatedCandidate.isUploadedPlan) {
      setUploadedCandidate(updatedCandidate);
    } else {
      setCandidates((prev) => {
        const next = prev.map((c) => (c.id === updatedCandidate.id ? updatedCandidate : c));
        setContextCandidates?.(next);
        return next;
      });
    }
  };

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: 'calc(100vh - 64px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#F8FAFC',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              width: '34px',
              height: '34px',
              margin: '0 auto 10px',
              borderRadius: '50%',
              border: '3px solid #E2E8F0',
              borderTopColor: '#2563EB',
              animation: 'fpSpin 0.8s linear infinite',
            }}
          />
          <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#0F172A' }}>
            Loading Studio...
          </div>
          <style>{`@keyframes fpSpin { to { transform: rotate(360deg); } }`}</style>
        </div>
      </div>
    );
  }

  return (
    <div style={{ background: '#F8FAFC', minHeight: 'calc(100vh - 64px)', padding: '18px 20px 36px' }}>
      {toastMsg && (
        <div
          style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            background: '#0F172A',
            color: '#FFFFFF',
            padding: '9px 16px',
            borderRadius: '10px',
            fontWeight: 600,
            fontSize: '12.5px',
            boxShadow: '0 8px 20px rgba(15,23,42,0.18)',
            zIndex: 9999,
          }}
        >
          {toastMsg}
        </div>
      )}

      {/* Minimal 2-Column Studio Grid (floor-plan.ai layout) */}
      <div
        className="fp-studio-grid"
        style={{
          maxWidth: '1480px',
          margin: '0 auto',
          display: 'grid',
          gridTemplateColumns: '290px minmax(0, 1fr)',
          gap: '18px',
          alignItems: 'start',
        }}
      >
        {/* ════════════════════════════════════════════════════════════════
            LEFT SIDEBAR: Compact, Uncongested Controls
            ════════════════════════════════════════════════════════════════ */}
        <aside
          style={{
            background: '#FFFFFF',
            border: '1px solid #E2E8F0',
            borderRadius: '14px',
            padding: '16px',
            boxShadow: '0 2px 10px rgba(15, 23, 42, 0.04)',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
          }}
        >
          {/* Top Mode Pill: 2D Plan | Floor Plan to 3D */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              background: '#F1F5F9',
              padding: '3px',
              borderRadius: '10px',
            }}
          >
            <button
              type="button"
              onClick={() => {
                setWorkbenchTool('generator');
                setStudioTab('cad');
              }}
              style={{
                padding: '6px 8px',
                borderRadius: '7px',
                fontSize: '12px',
                fontWeight: 700,
                border: 'none',
                cursor: 'pointer',
                background: workbenchTool === 'generator' ? '#FFFFFF' : 'transparent',
                color: workbenchTool === 'generator' ? '#0F172A' : '#64748B',
                boxShadow: workbenchTool === 'generator' ? '0 1px 2px rgba(15,23,42,0.08)' : 'none',
              }}
            >
              2D Generator
            </button>
            <button
              type="button"
              onClick={() => {
                setWorkbenchTool('to3d');
                if (studioTab === 'cad') setStudioTab('split');
              }}
              style={{
                padding: '6px 8px',
                borderRadius: '7px',
                fontSize: '12px',
                fontWeight: 700,
                border: 'none',
                cursor: 'pointer',
                background: workbenchTool === 'to3d' ? '#FFFFFF' : 'transparent',
                color: workbenchTool === 'to3d' ? '#2563EB' : '#64748B',
                boxShadow: workbenchTool === 'to3d' ? '0 1px 2px rgba(15,23,42,0.08)' : 'none',
              }}
            >
              Floor Plan to 3D
            </button>
          </div>

          {workbenchTool === 'to3d' ? (
            <>
              {/* ── MINIMAL FLOOR PLAN TO 3D SIDEBAR ── */}
              <div>
                <h2 style={{ fontSize: '15.5px', fontWeight: 800, color: '#0F172A', margin: 0 }}>
                  Floor Plan to 3D
                </h2>
                <p style={{ fontSize: '11.5px', color: '#64748B', margin: '2px 0 0' }}>
                  Powered by Gemini 3D Visualization
                </p>
              </div>

              {/* 1. Source Pill: Current Plan | Upload 2D */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  background: '#F1F5F9',
                  padding: '3px',
                  borderRadius: '9px',
                }}
              >
                <button
                  type="button"
                  onClick={() => setPlanSourceMode('selected')}
                  style={{
                    padding: '5px 8px',
                    borderRadius: '6px',
                    fontSize: '11.5px',
                    fontWeight: 600,
                    border: 'none',
                    cursor: 'pointer',
                    background: planSourceMode === 'selected' ? '#FFFFFF' : 'transparent',
                    color: planSourceMode === 'selected' ? '#0F172A' : '#64748B',
                    boxShadow: planSourceMode === 'selected' ? '0 1px 2px rgba(15,23,42,0.06)' : 'none',
                  }}
                >
                  Current Plan
                </button>
                <button
                  type="button"
                  onClick={() => setPlanSourceMode('upload')}
                  style={{
                    padding: '5px 8px',
                    borderRadius: '6px',
                    fontSize: '11.5px',
                    fontWeight: 600,
                    border: 'none',
                    cursor: 'pointer',
                    background: planSourceMode === 'upload' ? '#FFFFFF' : 'transparent',
                    color: planSourceMode === 'upload' ? '#0F172A' : '#64748B',
                    boxShadow: planSourceMode === 'upload' ? '0 1px 2px rgba(15,23,42,0.06)' : 'none',
                  }}
                >
                  Upload 2D
                </button>
              </div>

              {/* Compact 2D Thumbnail Preview or Upload Dropzone */}
              {planSourceMode === 'selected' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div
                    style={{
                      height: '104px',
                      borderRadius: '10px',
                      border: '1px solid #E2E8F0',
                      background: '#F8FAFC',
                      overflow: 'hidden',
                      padding: '4px',
                    }}
                  >
                    {selectedGenCandidate && <True2DCandidatePreview candidate={selectedGenCandidate} />}
                  </div>
                  {candidates.length > 1 && (
                    <div style={{ display: 'grid', gridTemplateColumns: `repeat(${candidates.length}, 1fr)`, gap: '5px' }}>
                      {candidates.map((cand, idx) => {
                        const isSel = selectedGenCandidate?.id === cand.id;
                        return (
                          <button
                            key={cand.id}
                            type="button"
                            onClick={() => selectCandidate?.(cand.id)}
                            style={{
                              padding: '5px 6px',
                              borderRadius: '7px',
                              fontSize: '11px',
                              fontWeight: 600,
                              cursor: 'pointer',
                              border: isSel ? '1.5px solid #2563EB' : '1px solid #E2E8F0',
                              background: isSel ? '#EFF6FF' : '#FFFFFF',
                              color: isSel ? '#1D4ED8' : '#475569',
                            }}
                          >
                            Option {idx + 1}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*,.png,.jpg,.jpeg,.webp,.svg"
                    style={{ display: 'none' }}
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) handleUploadFloorplanFile(f);
                    }}
                  />
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      const f = e.dataTransfer?.files?.[0];
                      if (f) handleUploadFloorplanFile(f);
                    }}
                    style={{
                      border: '1.5px dashed #93C5FD',
                      background: '#F8FBFF',
                      borderRadius: '10px',
                      padding: '12px',
                      textAlign: 'center',
                      cursor: 'pointer',
                    }}
                  >
                    {uploadedCandidate?.uploadedImageDataUrl ? (
                      <div>
                        <img
                          src={uploadedCandidate.uploadedImageDataUrl}
                          alt="Uploaded Floor Plan"
                          style={{
                            maxHeight: '76px',
                            maxWidth: '100%',
                            objectFit: 'contain',
                            margin: '0 auto 6px',
                            borderRadius: '6px',
                          }}
                        />
                        <div style={{ fontSize: '11px', fontWeight: 700, color: '#2563EB' }}>
                          ✓ Uploaded — Click to change
                        </div>
                      </div>
                    ) : (
                      <>
                        <div style={{ fontSize: '12px', fontWeight: 700, color: '#2563EB', marginBottom: '2px' }}>
                          {isAnalyzingUpload ? 'Reading 2D Plan...' : 'Upload 2D Floor Plan'}
                        </div>
                        <div style={{ fontSize: '10.5px', color: '#64748B' }}>
                          JPG, PNG, WEBP, SVG
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}

              {/* 2. Compact Style Pills (2x2 Grid) */}
              <div>
                <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                  Style
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                  {Object.entries(RENDER_STYLES).map(([key, item]) => {
                    const active = renderStyle3D === key;
                    return (
                      <button
                        key={key}
                        type="button"
                        onClick={() => setRenderStyle3D(key)}
                        style={{
                          padding: '7px 10px',
                          borderRadius: '999px',
                          fontSize: '11.5px',
                          fontWeight: 600,
                          border: active ? '1.5px solid #2563EB' : '1px solid #E2E8F0',
                          background: active ? '#2563EB' : '#F8FAFC',
                          color: active ? '#FFFFFF' : '#334155',
                          cursor: 'pointer',
                          textAlign: 'center',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        {item.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 3. Compact View Angle Pills (2x2 Grid) */}
              <div>
                <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                  View
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                  {Object.entries(VIEW_ANGLES).map(([key, item]) => {
                    const active = viewAngle3D === key;
                    return (
                      <button
                        key={key}
                        type="button"
                        onClick={() => setViewAngle3D(key)}
                        style={{
                          padding: '7px 10px',
                          borderRadius: '999px',
                          fontSize: '11.5px',
                          fontWeight: 600,
                          border: active ? '1.5px solid #2563EB' : '1px solid #E2E8F0',
                          background: active ? '#EFF6FF' : '#F8FAFC',
                          color: active ? '#1D4ED8' : '#334155',
                          cursor: 'pointer',
                          textAlign: 'center',
                        }}
                      >
                        {item.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 4. Studio Background (3 Pills) */}
              <div>
                <label style={{ display: 'block', fontSize: '11.5px', fontWeight: 700, color: '#334155', marginBottom: '6px' }}>
                  Studio Background
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '5px' }}>
                  {[
                    { id: 'white', label: 'White' },
                    { id: 'studio', label: 'Studio' },
                    { id: 'dark', label: 'Dark' },
                  ].map((bg) => {
                    const active = bgMode3D === bg.id;
                    return (
                      <button
                        key={bg.id}
                        type="button"
                        onClick={() => setBgMode3D(bg.id)}
                        style={{
                          padding: '6px 4px',
                          borderRadius: '8px',
                          fontSize: '11px',
                          fontWeight: 600,
                          cursor: 'pointer',
                          border: active ? '1.5px solid #2563EB' : '1px solid #E2E8F0',
                          background: active ? '#EFF6FF' : '#F8FAFC',
                          color: active ? '#1D4ED8' : '#475569',
                          textAlign: 'center',
                        }}
                      >
                        {bg.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* 5. 3D Interaction Tip */}
              <div
                style={{
                  background: '#F8FAFC',
                  border: '1px solid #E2E8F0',
                  borderRadius: '9px',
                  padding: '9px 11px',
                  fontSize: '11px',
                  color: '#64748B',
                  lineHeight: '1.45',
                }}
              >
                <strong style={{ color: '#0F172A', display: 'block', marginBottom: '2px' }}>
                  🎮 3D Viewport Controls
                </strong>
                • Drag to rotate 360°<br />
                • Right-drag to pan<br />
                • Scroll to zoom in/out
              </div>

              {/* 6. Export CAD Action */}
              <button
                type="button"
                onClick={handleExportDXF}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: '9px',
                  border: '1px solid #CBD5E1',
                  background: '#FFFFFF',
                  color: '#0F172A',
                  fontSize: '12px',
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                Download CAD (.DXF)
              </button>
            </>
          ) : (
            <>
              {/* ── MINIMAL 2D GENERATOR SIDEBAR ── */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  background: '#F1F5F9',
                  padding: '3px',
                  borderRadius: '9px',
                }}
              >
                <button
                  type="button"
                  onClick={() => setInputMode('house')}
                  style={{
                    padding: '5px 8px',
                    borderRadius: '6px',
                    fontSize: '11.5px',
                    fontWeight: 600,
                    border: 'none',
                    cursor: 'pointer',
                    background: inputMode === 'house' ? '#FFFFFF' : 'transparent',
                    color: inputMode === 'house' ? '#0F172A' : '#64748B',
                  }}
                >
                  Controls
                </button>
                <button
                  type="button"
                  onClick={() => setInputMode('prompt')}
                  style={{
                    padding: '5px 8px',
                    borderRadius: '6px',
                    fontSize: '11.5px',
                    fontWeight: 600,
                    border: 'none',
                    cursor: 'pointer',
                    background: inputMode === 'prompt' ? '#FFFFFF' : 'transparent',
                    color: inputMode === 'prompt' ? '#0F172A' : '#64748B',
                  }}
                >
                  Gemini Prompt
                </button>
              </div>

              {inputMode === 'house' ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '9px' }}>
                  {[
                    { label: 'Bedrooms', value: bedrooms, setValue: setBedrooms, min: 1, max: 6 },
                    { label: 'Bathrooms', value: bathrooms, setValue: setBathrooms, min: 1, max: 6 },
                    { label: 'Floors', value: floors, setValue: setFloors, min: 1, max: 3 },
                  ].map((item) => (
                    <div
                      key={item.label}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '6px 10px',
                        background: '#F8FAFC',
                        borderRadius: '8px',
                        border: '1px solid #E2E8F0',
                      }}
                    >
                      <span style={{ fontSize: '12px', fontWeight: 600, color: '#1E293B' }}>{item.label}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <button
                          type="button"
                          onClick={() => item.setValue(Math.max(item.min, item.value - 1))}
                          style={{
                            width: '24px',
                            height: '24px',
                            borderRadius: '6px',
                            border: '1px solid #CBD5E1',
                            background: '#FFFFFF',
                            cursor: 'pointer',
                            fontWeight: 700,
                          }}
                        >
                          −
                        </button>
                        <span style={{ fontSize: '12.5px', fontWeight: 700, minWidth: '16px', textAlign: 'center' }}>
                          {item.value}
                        </span>
                        <button
                          type="button"
                          onClick={() => item.setValue(Math.min(item.max, item.value + 1))}
                          style={{
                            width: '24px',
                            height: '24px',
                            borderRadius: '6px',
                            border: '1px solid #CBD5E1',
                            background: '#FFFFFF',
                            cursor: 'pointer',
                            fontWeight: 700,
                          }}
                        >
                          +
                        </button>
                      </div>
                    </div>
                  ))}

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '10.5px', fontWeight: 600, color: '#64748B', marginBottom: '3px' }}>
                        Width (ft)
                      </label>
                      <input
                        type="number"
                        min={20}
                        max={120}
                        value={siteWidth}
                        onChange={(e) => setSiteWidth(e.target.value)}
                        style={{
                          width: '100%',
                          padding: '6px 8px',
                          borderRadius: '7px',
                          border: '1px solid #CBD5E1',
                          fontSize: '12px',
                          fontWeight: 600,
                          boxSizing: 'border-box',
                        }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '10.5px', fontWeight: 600, color: '#64748B', marginBottom: '3px' }}>
                        Depth (ft)
                      </label>
                      <input
                        type="number"
                        min={20}
                        max={150}
                        value={siteLength}
                        onChange={(e) => setSiteLength(e.target.value)}
                        style={{
                          width: '100%',
                          padding: '6px 8px',
                          borderRadius: '7px',
                          border: '1px solid #CBD5E1',
                          fontSize: '12px',
                          fontWeight: 600,
                          boxSizing: 'border-box',
                        }}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '4px' }}>
                    {['East', 'North', 'West', 'South'].map((dir) => (
                      <button
                        key={dir}
                        type="button"
                        onClick={() => setOrientation(dir)}
                        style={{
                          padding: '5px 4px',
                          borderRadius: '6px',
                          fontSize: '11px',
                          fontWeight: 600,
                          cursor: 'pointer',
                          border: orientation === dir ? '1.5px solid #2563EB' : '1px solid #E2E8F0',
                          background: orientation === dir ? '#EFF6FF' : '#F8FAFC',
                          color: orientation === dir ? '#1D4ED8' : '#475569',
                        }}
                      >
                        {dir}
                      </button>
                    ))}
                  </div>

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                    {[
                      { label: 'Pooja', active: hasPooja, toggle: () => setHasPooja(!hasPooja) },
                      { label: 'Parking', active: hasParking, toggle: () => setHasParking(!hasParking) },
                      { label: 'Balcony', active: hasBalcony, toggle: () => setHasBalcony(!hasBalcony) },
                    ].map((chip) => (
                      <button
                        key={chip.label}
                        type="button"
                        onClick={chip.toggle}
                        style={{
                          padding: '4px 9px',
                          borderRadius: '999px',
                          fontSize: '11px',
                          fontWeight: 600,
                          cursor: 'pointer',
                          border: chip.active ? '1px solid #93C5FD' : '1px solid #E2E8F0',
                          background: chip.active ? '#EFF6FF' : '#F8FAFC',
                          color: chip.active ? '#1D4ED8' : '#64748B',
                        }}
                      >
                        {chip.active ? '✓ ' : '+ '}{chip.label}
                      </button>
                    ))}
                  </div>

                  <button
                    type="button"
                    onClick={handleGenerateFromControls}
                    disabled={isGenerating}
                    style={{
                      width: '100%',
                      padding: '9px 12px',
                      borderRadius: '9px',
                      border: 'none',
                      background: '#2563EB',
                      color: '#FFFFFF',
                      fontSize: '12.5px',
                      fontWeight: 700,
                      cursor: isGenerating ? 'wait' : 'pointer',
                    }}
                  >
                    {isGenerating ? 'Updating...' : 'Update 2D Plan'}
                  </button>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <textarea
                    rows={3}
                    value={promptText}
                    onChange={(e) => setPromptText(e.target.value)}
                    placeholder="e.g. 3 BHK on 30x40 ft East facing plot with pooja room..."
                    style={{
                      width: '100%',
                      padding: '8px 10px',
                      borderRadius: '8px',
                      border: '1px solid #CBD5E1',
                      fontSize: '12px',
                      background: '#F8FAFC',
                      fontFamily: 'inherit',
                      boxSizing: 'border-box',
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => handleGenerateFromPrompt()}
                    disabled={isGenerating || !promptText.trim()}
                    style={{
                      width: '100%',
                      padding: '9px 12px',
                      borderRadius: '9px',
                      border: 'none',
                      background: '#2563EB',
                      color: '#FFFFFF',
                      fontSize: '12.5px',
                      fontWeight: 700,
                      cursor: isGenerating ? 'wait' : 'pointer',
                      opacity: isGenerating || !promptText.trim() ? 0.65 : 1,
                    }}
                  >
                    {isGenerating ? 'Generating...' : 'Generate with Gemini'}
                  </button>
                </div>
              )}

              {/* Compact Option Selector Pills */}
              {candidates.length > 1 && (
                <div>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748B', marginBottom: '5px' }}>
                    Layout Option
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: `repeat(${candidates.length}, 1fr)`, gap: '5px' }}>
                    {candidates.map((cand, idx) => {
                      const isSel = selectedGenCandidate?.id === cand.id;
                      return (
                        <button
                          key={cand.id}
                          type="button"
                          onClick={() => selectCandidate?.(cand.id)}
                          style={{
                            padding: '6px 6px',
                            borderRadius: '7px',
                            fontSize: '11.5px',
                            fontWeight: 600,
                            cursor: 'pointer',
                            border: isSel ? '1.5px solid #2563EB' : '1px solid #E2E8F0',
                            background: isSel ? '#EFF6FF' : '#F8FAFC',
                            color: isSel ? '#1D4ED8' : '#475569',
                          }}
                        >
                          Opt {idx + 1}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              <button
                type="button"
                onClick={handleConvertSelectedTo3D}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: '9px',
                  border: '1.5px solid #2563EB',
                  background: '#EFF6FF',
                  color: '#1D4ED8',
                  fontSize: '12.5px',
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                ✨ Convert to 3D →
              </button>

              <button
                type="button"
                onClick={handleExportDXF}
                style={{
                  width: '100%',
                  padding: '7px 10px',
                  borderRadius: '8px',
                  border: '1px solid #E2E8F0',
                  background: '#FFFFFF',
                  color: '#475569',
                  fontSize: '11.5px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Download CAD (.DXF)
              </button>
            </>
          )}
        </aside>

        {/* ════════════════════════════════════════════════════════════════
            RIGHT MAIN STAGE: Minimal 2D / 3D / Split Studio Card
            ════════════════════════════════════════════════════════════════ */}
        <main style={{ minWidth: 0 }}>
          {activeCandidate && (
            <EditableFloorplanCanvas
              candidate={activeCandidate}
              project={project}
              onUpdateCandidate={handleUpdateCandidate}
              initialStudioTab={studioTab}
              copilotTimeOfDay="day"
              externalRenderStyle={renderStyle3D}
              externalViewAngle={viewAngle3D}
              externalBgMode={bgMode3D}
              externalExtraPrompt={extraReqPrompt}
              externalTriggerCount={trigger3DCount}
              onSwitchStudioTab={(tab) => {
                setStudioTab(tab);
                if (tab === '3d' || tab === 'split') {
                  setWorkbenchTool('to3d');
                }
              }}
            />
          )}
        </main>
      </div>

      <style>{`
        @media (max-width: 960px) {
          .fp-studio-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}
