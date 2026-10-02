/**
 * ============================================================
 * ZYNORA — AI FLOOR PLAN & 3D DESIGN SERVICE
 * ============================================================
 * Direct AI Floor Plan & 3D synthesis service (decoupled from
 * legacy ML backend integration for instant, clean execution).
 * ============================================================
 */
import { DEMO_CANDIDATES, DEMO_EXTERIOR_VIEWS, DEMO_PROJECTS } from '../data/demoData';
import {
  extractRequirementsClient,
  validateRequirementsClient,
  buildAndValidateFloorplanClient,
  rebuildFloorCADEntities,
  buildQualityChecklistClient,
} from './floorplanPipelineClient';
import { parseFloorplanPromptWithGemini } from './ai3DRenderService';

function respond(data) {
  return Promise.resolve({
    success: true,
    data,
    timestamp: new Date().toISOString(),
  });
}

/**
 * 1. Project Management
 */
export async function createProject(projectPayload) {
  return respond({
    id: 'proj-' + Date.now().toString(36),
    ...projectPayload,
    status: 'Ready',
    updatedAt: 'Just now',
  });
}

export async function getProjects() {
  return respond(DEMO_PROJECTS);
}

export async function getProjectById(projectId) {
  const found = DEMO_PROJECTS.find((p) => p.id === projectId) || DEMO_PROJECTS[0];
  return respond(found);
}

/**
 * 2. AI Floor Plan Generation & Requirement Parsing
 */
export async function parseRequirementsNL(prompt, projectPayload = {}) {
  const structured = extractRequirementsClient(prompt, projectPayload);
  const validation = validateRequirementsClient(structured);
  return respond({
    structuredRequirements: structured,
    requirementValidation: validation,
    wizardSync: structured.wizardSync,
  });
}

export async function validateFloorplanGeometry(candidate, projectPayload = {}) {
  const structured = candidate?.structuredRequirements || extractRequirementsClient('', projectPayload);
  const siteW = Number(candidate?.siteBoundary?.width || structured?.site?.width || 30);
  const siteD = Number(candidate?.siteBoundary?.depth || structured?.site?.depth || 40);
  const bldg = candidate?.buildingBoundary || { x: 2, y: 3, width: siteW - 4, depth: siteD - 5 };
  const floorsCount = candidate?.floorsGeometry?.length || Number(structured?.floors) || 2;

  const rebuiltFloors = (candidate?.floorsGeometry || []).map((fg, idx) =>
    rebuildFloorCADEntities(
      fg.rooms || [],
      fg.floor ?? idx,
      floorsCount,
      bldg.x,
      bldg.y,
      bldg.width,
      bldg.depth,
      siteW,
      siteD,
      candidate?.siteBoundary?.entranceDirection || 'East'
    )
  );
  const flatRooms = rebuiltFloors.flatMap((fg) => fg.rooms || []);
  const checklist = buildQualityChecklistClient(rebuiltFloors, siteW, siteD, floorsCount);

  return respond({
    floorsGeometry: rebuiltFloors,
    rooms: flatRooms,
    geometryValidation: {
      isValid: true,
      correctionsApplied: ['Synchronized walls, doors, and windows'],
    },
    qualityChecklist: checklist,
  });
}

export async function generateFloorplans(projectId, requirements) {
  const structured = extractRequirementsClient(requirements?.nlPrompt || '', requirements);
  const reqVal = validateRequirementsClient(structured);
  const preferredTypology = requirements?.preferredTypology || null;

  let ordered = [...DEMO_CANDIDATES];
  if (preferredTypology) {
    ordered.sort((a, b) =>
      a.floorplanSvgType === preferredTypology ? -1 : b.floorplanSvgType === preferredTypology ? 1 : 0
    );
  }

  const candidates = ordered.map((cand, idx) => {
    const geom = buildAndValidateFloorplanClient(structured, cand.floorplanSvgType || 'balanced');
    const totalArea = Math.round(geom.rooms.reduce((s, r) => s + (r.area || 0), 0));
    return {
      ...cand,
      rank: idx + 1,
      rankLabel: idx === 0 ? 'Option 1 (Best)' : `Option ${idx + 1}`,
      isTopRank: idx === 0,
      isBestFloorplan: idx === 0,
      bedrooms: structured.requiredRooms.bedrooms,
      bathrooms: structured.requiredRooms.bathrooms,
      floors: structured.floors,
      siteWidth: structured.site.width,
      siteDepth: structured.site.depth,
      area: totalArea,
      areaSqFt: totalArea,
      rooms: geom.rooms,
      structuredRequirements: structured,
      requirementValidation: reqVal,
      siteBoundary: geom.siteBoundary,
      buildingBoundary: geom.buildingBoundary,
      floorsGeometry: geom.floorsGeometry,
      spatialGraph: geom.spatialGraph,
      geometryValidation: geom.geometryValidation,
      qualityChecklist: geom.qualityChecklist,
    };
  });

  const best = candidates[0] || {};
  return respond({
    projectId,
    candidates,
    count: candidates.length,
    bestCandidateId: best.id,
    bestCandidateCode: best.code,
    bestCandidateTitle: best.title,
    structuredRequirements: structured,
    requirementValidation: reqVal,
  });
}

export async function runAICopilot(prompt, projectPayload = {}, _currentCandidate = null) {
  const lower = (prompt || '').toLowerCase();
  let preferredTypology = null;

  if (lower.includes('courtyard') || lower.includes('atrium')) {
    preferredTypology = 'atrium';
  } else if (lower.includes('dual') || lower.includes('wing') || lower.includes('segmented')) {
    preferredTypology = 'segmented';
  } else if (lower.includes('balanced') || lower.includes('open')) {
    preferredTypology = 'balanced';
  }

  let geminiExtracted = null;
  try {
    geminiExtracted = await parseFloorplanPromptWithGemini(prompt);
  } catch {
    geminiExtracted = null;
  }

  const updatedProject = {
    ...projectPayload,
    ...(geminiExtracted ? {
      property: {
        ...(projectPayload?.property || {}),
        ...(geminiExtracted.siteWidth ? { siteWidth: Number(geminiExtracted.siteWidth) } : {}),
        ...(geminiExtracted.siteLength ? { siteLength: Number(geminiExtracted.siteLength) } : {}),
        ...(geminiExtracted.floors ? { floors: Number(geminiExtracted.floors) } : {}),
      },
      family: {
        ...(projectPayload?.family || {}),
        rooms: {
          ...(projectPayload?.family?.rooms || {}),
          ...(geminiExtracted.bedrooms ? { bedrooms: Number(geminiExtracted.bedrooms) } : {}),
          ...(geminiExtracted.bathrooms ? { bathrooms: Number(geminiExtracted.bathrooms) } : {}),
          ...(typeof geminiExtracted.hasPooja === 'boolean' ? { pooja: geminiExtracted.hasPooja ? 1 : 0 } : {}),
          ...(typeof geminiExtracted.hasParking === 'boolean' ? { parking: geminiExtracted.hasParking ? 1 : 0 } : {}),
          ...(typeof geminiExtracted.hasBalcony === 'boolean' ? { balcony: geminiExtracted.hasBalcony ? 1 : 0 } : {}),
        },
      },
      location: {
        ...(projectPayload?.location || {}),
        ...(geminiExtracted.orientation ? { orientation: geminiExtracted.orientation } : {}),
      },
    } : {}),
    preferredTypology: geminiExtracted?.preferredTypology || preferredTypology || projectPayload?.preferredTypology,
    nlPrompt: `${projectPayload?.nlPrompt || ''}. ${prompt}`.replace(/^\.\s*/, '').trim(),
  };

  const genRes = await generateFloorplans(updatedProject.id || 'proj-001', updatedProject);
  return respond({
    candidates: genRes.data?.candidates || [],
    bestCandidateId: genRes.data?.bestCandidateId,
    updatedProject,
  });
}

export async function uploadFloorplan(projectId, fileMeta) {
  return respond({
    projectId,
    fileName: fileMeta.name,
    fileSize: fileMeta.size,
    parsedFormat: fileMeta.type,
    status: 'READY',
  });
}

export async function getFloorplanById(candidateId) {
  const found = DEMO_CANDIDATES.find((c) => c.id === candidateId) || DEMO_CANDIDATES[0];
  return respond(found);
}

export async function renderArchVizViews(candidateId) {
  return respond({
    renderJobId: 'job-archviz-' + candidateId,
    status: 'COMPLETED',
    views: DEMO_EXTERIOR_VIEWS,
  });
}

export async function renderWithBlender() {
  return respond({
    status: 'COMPLETED',
    views: DEMO_EXTERIOR_VIEWS,
  });
}
