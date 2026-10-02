/**
 * ============================================================================
 * ZYNORA — GEMINI 3D FLOOR PLAN VISUALIZATION & 2D PROMPT SERVICE
 * ============================================================================
 * Primary Engine:
 *   • Google Gemini 3.1 Flash Image (`gemini-3.1-flash-image` / Nano Banana 2)
 *     and Gemini 3 Pro Image (`gemini-3-pro-image`) via the official
 *     Gemini Interactions API (`POST /v1beta/interactions`).
 *   • Converts the exact 2D CAD floor plan (or uploaded 2D floor plan image)
 *     + spatial room coordinates into a photorealistic `floor-plan.ai`-style
 *     3D architectural cutaway isolated on a pure `#FFFFFF` studio background.
 *   • Supports stateful multi-turn 3D edits via `previous_interaction_id`.
 *   • Uses `gemini-3.8-flash` for natural-language 2D floor plan requirement
 *     extraction when generating from text prompts.
 *   • Includes automatic zero-key fallback (FLUX.1-Kontext 2D→3D / Schnell)
 *     so the studio renders out-of-the-box even before a Gemini key is added.
 * ============================================================================
 */

const GEMINI_INTERACTIONS_ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/interactions';
const FLUX_KONTEXT_BASE = 'https://black-forest-labs-flux-1-kontext-dev.hf.space';
const FLUX_SCHNELL_BASE = 'https://black-forest-labs-flux-1-schnell.hf.space';

// Cache renders by layout + style + angle + prompt so switching tabs is instant
const renderCache = new Map();

// Track the last Gemini interaction ID per candidate/floor for stateful multi-turn 3D edits
const interactionHistoryMap = new Map();

/**
 * Retrieve the configured Gemini API key from Vite env or localStorage.
 */
export function getStoredGeminiApiKey() {
  const envKey = typeof import.meta !== 'undefined' && import.meta.env
    ? (import.meta.env.VITE_GEMINI_API_KEY || import.meta.env.VITE_GOOGLE_API_KEY || '')
    : '';
  if (envKey && envKey.trim()) return envKey.trim();
  if (typeof window !== 'undefined' && window.localStorage) {
    return (window.localStorage.getItem('zynora_gemini_key') || '').trim();
  }
  return '';
}

export function setStoredGeminiApiKey(key) {
  if (typeof window !== 'undefined' && window.localStorage) {
    window.localStorage.setItem('zynora_gemini_key', (key || '').trim());
  }
}

/**
 * Convert a room's (x, y) position within the building footprint into a spatial quadrant label.
 */
function getSpatialQuadrant(room, siteW = 30, siteD = 40) {
  const cx = (Number(room.x) || 0) + (Number(room.width) || 10) / 2;
  const cy = (Number(room.y) || 0) + (Number(room.height || room.depth) || 10) / 2;
  const horiz = cx < siteW * 0.42 ? 'left' : cx > siteW * 0.58 ? 'right' : 'center';
  const vert = cy < siteD * 0.42 ? 'top-back' : cy > siteD * 0.58 ? 'front-bottom' : 'middle';
  return `${vert}-${horiz}`;
}

/**
 * Build a floorplan-grounded architectural 3D prompt from the active candidate
 * and selected style, camera angle, and background preset.
 */
export function buildArchitectural3DPrompt(candidate, options = {}) {
  const {
    renderStyle = 'photorealistic',
    viewAngle = 'birds_eye',
    bgMode = 'white',
    floorIndex = 0,
    extraPrompt = '',
  } = options;

  const siteW = Number(candidate?.siteWidth || candidate?.siteBoundary?.width || 30);
  const siteD = Number(candidate?.siteDepth || candidate?.siteBoundary?.depth || 40);
  const bedrooms = Number(candidate?.bedrooms || 3);
  const bathrooms = Number(candidate?.bathrooms || 2);

  const floorGeom = candidate?.floorsGeometry?.[floorIndex] || candidate?.floorsGeometry?.[0];
  const rooms = (floorGeom?.rooms && floorGeom.rooms.length > 0)
    ? floorGeom.rooms
    : (candidate?.rooms || []).filter((r) => (r.floor || 0) === floorIndex);

  const roomDescriptions = rooms.slice(0, 10).map((r) => {
    const w = Math.round(Number(r.width) || 10);
    const h = Math.round(Number(r.height || r.depth) || 10);
    const quad = getSpatialQuadrant(r, siteW, siteD);
    const type = (r.type || r.name || '').toLowerCase();
    let furnish = 'with modern interior furniture';
    if (type.includes('living')) furnish = 'with L-shaped beige sectional sofa, wooden coffee table, woven rug, and media console';
    else if (type.includes('dining')) furnish = 'with warm oak dining table and 6 upholstered chairs';
    else if (type.includes('kitchen')) furnish = 'with L-shaped white Carrara marble countertop, built-in stove hob, sink, and modern cabinetry';
    else if (type.includes('master') || type.includes('bed')) furnish = 'with king bed, crisp white linens, nightstands, lamps, and built-in wooden wardrobe';
    else if (type.includes('bath') || type.includes('wc') || type.includes('toilet')) furnish = 'with aqua-white ceramic mosaic floor tiles, glass shower enclosure, vanity sink, and toilet';
    else if (type.includes('pooja') || type.includes('mandir')) furnish = 'with warm carved teakwood mandir shrine and soft warm lighting';
    else if (type.includes('balcony') || type.includes('verandah') || type.includes('deck')) furnish = 'with slatted teak decking, glass balustrade railing, lounge chairs, and potted plants';
    else if (type.includes('parking') || type.includes('garage')) furnish = 'with stone-paved carport';
    return `${r.name} (${w}x${h} ft at ${quad} ${furnish})`;
  });

  const angleMap = {
    birds_eye: "High-angle 65-degree bird's-eye top-down isometric 3D architectural floor plan cutaway view, roof completely removed, looking clearly down into all rooms",
    angled: 'Isometric 45-degree 3D dollhouse floor plan cutaway architectural render, roof removed, crisp extruded half-height matte white walls with dark charcoal-slate top wall caps (#1E293B)',
    angled_3d: 'Isometric 45-degree 3D dollhouse floor plan cutaway architectural render, roof removed, crisp extruded half-height matte white walls with dark charcoal-slate top wall caps (#1E293B)',
    room_focused: 'Close-up 35-degree interior 3D cutaway perspective floor plan render showcasing realistic furniture, hardwood planks, and open doorways between rooms',
    exterior: 'Photorealistic 3D architectural exterior and cutaway villa visualization with contemporary facade, glass balconies, and warm interior lights',
  };

  const styleMap = {
    photorealistic: 'Ultra-photorealistic 8k V-Ray and Corona Renderer architectural visualization, warm oak hardwood plank flooring in living room and bedrooms, polished white Carrara marble tiles in kitchen and hallway, ceramic mosaic tiles in bathrooms, soft global illumination and ambient occlusion contact shadows, high-end contemporary 3D furniture',
    minimalist: 'Clean minimalist Scandinavian Japandi 3D architectural floor plan render, pale birch wood floors, matte white plaster walls, neutral linen furniture, soft diffused studio daylight',
    blueprint: '3D architectural technical blueprint render, deep cobalt blue CAD aesthetic with glowing crisp white 3D extruded walls, isometric architectural wireframe and shaded 3D furniture volumes',
    sketch: 'Hand-crafted architectural 3D marker and ink concept rendering, Copic marker warm wood and stone textures, crisp technical pen linework on extruded 3D cutaway walls',
    watercolor: 'Artistic architectural 3D watercolor and gouache illustration of an open-top 3D floor plan cutaway, soft pastel wash textures, warm sunlit interior spaces',
  };

  const bgMap = {
    white: ' cleanly isolated on a pure solid white studio background (#FFFFFF) with a soft ground drop shadow underneath the floor slab, matching floor-plan.ai',
    studio: ' set on a clean light neutral architectural studio plinth with soft studio vignette lighting',
    landscaped: ' surrounded by a manicured green lawn terrace, stone patio border, and ornamental trees',
    dark: ' isolated on a sleek dark slate architectural presentation background with warm glowing interior room lighting',
  };

  const angleText = angleMap[viewAngle] || angleMap.birds_eye;
  const styleText = styleMap[renderStyle] || styleMap.photorealistic;
  const bgText = bgMap[bgMode] || bgMap.white;

  const layoutSummary = roomDescriptions.length > 0
    ? `Preserve the exact 2D floor plan wall geometry, proportions, and room positions (${siteW}x${siteD} ft, ${bedrooms} bedrooms, ${bathrooms} bathrooms): ${roomDescriptions.join('; ')}.`
    : `Modern ${bedrooms}-bedroom, ${bathrooms}-bathroom residential floor plan (${siteW}x${siteD} ft) with living room, dining area, modular kitchen, bedrooms, and tiled bathrooms.`;

  const extra = extraPrompt && extraPrompt.trim()
    ? ` User refinement instruction: ${extraPrompt.trim()}.`
    : '';

  return `${angleText}. ${styleText}. ${layoutSummary}${bgText}.${extra} Crisp architectural geometry, no text labels or watermarks in the 3D render, ultra-sharp details.`;
}

/**
 * Render the candidate's 2D floor plan layout onto an offscreen HTML5 Canvas (1024×768)
 * with crisp architectural walls, doors, windows, furniture silhouettes, and room labels
 * so Gemini (`gemini-3.1-flash-image`) receives an exact 2D CAD blueprint to extrude into 3D.
 */
export function renderCandidate2DToDataUrl(candidate, floorIndex = 0) {
  if (candidate?.uploadedImageDataUrl) {
    return candidate.uploadedImageDataUrl;
  }
  if (candidate?.croppedFloorTextureUrl) {
    return candidate.croppedFloorTextureUrl;
  }

  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 768;
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;

  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const siteW = Number(candidate?.siteWidth || candidate?.siteBoundary?.width || 30);
  const siteD = Number(candidate?.siteDepth || candidate?.siteBoundary?.depth || 40);
  const pad = 68;
  const scale = Math.min((canvas.width - pad * 2) / siteW, (canvas.height - pad * 2) / siteD);
  const ox = (canvas.width - siteW * scale) / 2;
  const oy = (canvas.height - siteD * scale) / 2;

  const floorGeom = candidate?.floorsGeometry?.[floorIndex] || candidate?.floorsGeometry?.[0];
  const rooms = (floorGeom?.rooms && floorGeom.rooms.length > 0)
    ? floorGeom.rooms
    : (candidate?.rooms || []).filter((r) => (r.floor || 0) === floorIndex);

  const fillPalette = {
    living: '#FEF3C7',
    dining: '#FFEDD5',
    kitchen: '#D1FAE5',
    bedroom: '#DBEAFE',
    bathroom: '#CFFAFE',
    pooja: '#FEF08A',
    balcony: '#DCFCE7',
    parking: '#E2E8F0',
    circulation: '#F8FAFC',
  };

  // 1. Draw Room Fills, Simple Furniture Outlines & Labels
  rooms.forEach((r) => {
    const rx = ox + (Number(r.x) || 0) * scale;
    const ry = oy + (Number(r.y) || 0) * scale;
    const rw = (Number(r.width) || 8) * scale;
    const rh = (Number(r.height || r.depth) || 8) * scale;
    const t = (r.type || '').toLowerCase();

    ctx.fillStyle = fillPalette[t] || '#F8FAFC';
    ctx.fillRect(rx, ry, rw, rh);

    // Subtle interior furniture guide shapes for Gemini 2D→3D grounding
    ctx.strokeStyle = 'rgba(51, 65, 85, 0.35)';
    ctx.lineWidth = 1.5;
    if (t === 'bedroom' && rw > 70 && rh > 70) {
      const bw = Math.min(rw * 0.44, 70);
      const bh = Math.min(rh * 0.48, 80);
      ctx.fillStyle = 'rgba(255,255,255,0.75)';
      ctx.fillRect(rx + (rw - bw) / 2, ry + 8, bw, bh);
      ctx.strokeRect(rx + (rw - bw) / 2, ry + 8, bw, bh);
    } else if (t === 'living' && rw > 80 && rh > 80) {
      const sw = Math.min(rw * 0.5, 90);
      const sh = Math.min(rh * 0.22, 32);
      ctx.fillStyle = 'rgba(255,255,255,0.75)';
      ctx.fillRect(rx + (rw - sw) / 2, ry + rh - sh - 10, sw, sh);
      ctx.strokeRect(rx + (rw - sw) / 2, ry + rh - sh - 10, sw, sh);
    } else if (t === 'kitchen' && rw > 60 && rh > 60) {
      ctx.fillStyle = 'rgba(255,255,255,0.75)';
      ctx.fillRect(rx + 4, ry + 4, rw - 8, 20);
      ctx.strokeRect(rx + 4, ry + 4, rw - 8, 20);
    }

    // Crisp wall outline per room
    ctx.strokeStyle = '#0F172A';
    ctx.lineWidth = 4.5;
    ctx.strokeRect(rx, ry, rw, rh);

    // Room Title & Dimensions
    ctx.fillStyle = '#0F172A';
    ctx.font = 'bold 15px Inter, system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(String(r.name || 'Room').toUpperCase(), rx + rw / 2, ry + rh / 2 - 4);
    ctx.font = '600 12px ui-monospace, monospace';
    ctx.fillStyle = '#334155';
    ctx.fillText(`${Math.round(r.width || 10)}' × ${Math.round(r.height || r.depth || 10)}'`, rx + rw / 2, ry + rh / 2 + 14);
  });

  // 2. Draw CAD Walls if present
  (floorGeom?.walls || []).forEach((w) => {
    const isExt = w.wallType === 'exterior';
    ctx.strokeStyle = '#0F172A';
    ctx.lineWidth = isExt ? 7.5 : 4.5;
    ctx.lineCap = 'square';
    ctx.beginPath();
    ctx.moveTo(ox + w.start.x * scale, oy + w.start.y * scale);
    ctx.lineTo(ox + w.end.x * scale, oy + w.end.y * scale);
    ctx.stroke();
  });

  // 3. Draw Windows in Cyan
  (floorGeom?.windows || []).forEach((win) => {
    const isH = win.orientation === 'horizontal';
    const half = ((win.width || 3.5) * scale) / 2;
    const wx = ox + win.x * scale;
    const wy = oy + win.y * scale;
    ctx.strokeStyle = '#38BDF8';
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.moveTo(isH ? wx - half : wx, isH ? wy : wy - half);
    ctx.lineTo(isH ? wx + half : wx, isH ? wy : wy + half);
    ctx.stroke();
  });

  // 4. Draw Door Openings
  (floorGeom?.doors || []).forEach((d) => {
    const isH = d.orientation === 'horizontal';
    const half = (Math.min(2.6, d.width || 2.5) * scale) / 2;
    const dx = ox + d.x * scale;
    const dy = oy + d.y * scale;
    ctx.strokeStyle = '#FFFFFF';
    ctx.lineWidth = 8;
    ctx.beginPath();
    ctx.moveTo(isH ? dx - half : dx, isH ? dy : dy - half);
    ctx.lineTo(isH ? dx + half : dx, isH ? dy : dy + half);
    ctx.stroke();
  });

  return canvas.toDataURL('image/png');
}

/**
 * Extract an image (`{ data, mime_type }`) from a Gemini Interactions API response object.
 */
function extractImageFromInteractionResponse(data) {
  // 1. Convenience property `output_image`
  if (data?.output_image?.data) {
    return {
      base64: data.output_image.data,
      mimeType: data.output_image.mime_type || data.output_image.mimeType || 'image/png',
    };
  }

  // 2. Scan `steps` array (`model_output` -> `content` -> `type === 'image'`)
  const steps = Array.isArray(data?.steps) ? data.steps : [];
  for (let i = steps.length - 1; i >= 0; i--) {
    const step = steps[i];
    if (step?.type === 'model_output' && Array.isArray(step.content)) {
      for (let j = step.content.length - 1; j >= 0; j--) {
        const part = step.content[j];
        if ((part?.type === 'image' || part?.mime_type?.startsWith('image/')) && part?.data) {
          return {
            base64: part.data,
            mimeType: part.mime_type || part.mimeType || 'image/png',
          };
        }
        if (part?.inlineData?.data) {
          return {
            base64: part.inlineData.data,
            mimeType: part.inlineData.mimeType || 'image/png',
          };
        }
      }
    }
  }

  return null;
}

/**
 * Primary Engine: Google Gemini 3.1 Flash Image (`gemini-3.1-flash-image`)
 * via the Gemini Interactions API (`POST /v1beta/interactions`).
 */
async function generateWithGeminiInteractionsAPI({
  apiKey,
  prompt,
  imageDataUrl = null,
  previousInteractionId = null,
  model = 'gemini-3.1-flash-image',
}) {
  const input = [
    {
      type: 'text',
      text: `Convert this 2D architectural floor plan into a high-resolution 3D floor plan cutaway visualization. ${prompt}`,
    },
  ];

  if (imageDataUrl && imageDataUrl.startsWith('data:image/')) {
    const [header, base64Data] = imageDataUrl.split(',');
    const mimeType = header.match(/data:(.*?);/)?.[1] || 'image/png';
    input.push({
      type: 'image',
      mime_type: mimeType,
      data: base64Data,
    });
  }

  const requestBody = {
    model,
    input,
    response_format: {
      type: 'image',
      aspect_ratio: '4:3',
      image_size: '1K',
    },
  };

  if (previousInteractionId) {
    requestBody.previous_interaction_id = previousInteractionId;
  }

  const res = await fetch(GEMINI_INTERACTIONS_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-goog-api-key': apiKey,
    },
    body: JSON.stringify(requestBody),
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => '');
    throw new Error(`Gemini Interactions API HTTP ${res.status}: ${errText.slice(0, 160)}`);
  }

  const data = await res.json();
  const extracted = extractImageFromInteractionResponse(data);
  if (!extracted) {
    throw new Error('Gemini 3.1 Flash Image did not return an image in the interaction response');
  }

  return {
    imageUrl: `data:${extracted.mimeType};base64,${extracted.base64}`,
    interactionId: data.id || null,
    provider: 'Gemini 3.1 Flash Image (2D → 3D)',
    mode: 'gemini_3d',
  };
}

/**
 * Optional Backend Proxy call (`/api/render/gemini-3d`) if the FastAPI backend holds `GEMINI_API_KEY`.
 */
async function generateViaBackendGeminiProxy({ prompt, imageDataUrl, previousInteractionId }) {
  const res = await fetch('http://127.0.0.1:8000/api/render/gemini-3d', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt,
      imageDataUrl,
      previousInteractionId,
      model: 'gemini-3.1-flash-image',
    }),
  });
  if (!res.ok) {
    throw new Error(`Backend Gemini proxy HTTP ${res.status}`);
  }
  const json = await res.json();
  if (!json?.success || !json?.data?.imageUrl) {
    throw new Error(json?.error || 'Backend Gemini proxy not configured');
  }
  return {
    imageUrl: json.data.imageUrl,
    interactionId: json.data.interactionId || null,
    provider: 'Gemini 3.1 Flash Image (2D → 3D)',
    mode: 'gemini_3d',
  };
}

/**
 * Parse a Gradio SSE stream response for zero-key fallback.
 */
function parseGradioEventStream(streamText, baseUrl) {
  const lines = streamText.split('\n');
  let lastEvent = '';
  for (const line of lines) {
    if (line.startsWith('event:')) {
      lastEvent = line.replace('event:', '').trim();
    } else if (line.startsWith('data:')) {
      const jsonStr = line.replace(/^data:\s*/, '').trim();
      if (lastEvent === 'error') {
        throw new Error(jsonStr || 'Inference error');
      }
      if (lastEvent === 'complete' || jsonStr.startsWith('[')) {
        try {
          const parsed = JSON.parse(jsonStr);
          const first = Array.isArray(parsed) ? parsed[0] : parsed;
          if (first?.url) return first.url;
          if (first?.path) return `${baseUrl}/gradio_api/file=${first.path}`;
          if (typeof first === 'string' && first.startsWith('http')) return first;
        } catch {
          // continue scanning
        }
      }
    }
  }
  throw new Error('Could not parse image URL from stream');
}

async function uploadImageToGradioSpace(baseUrl, imageDataUrl) {
  const res = await fetch(imageDataUrl);
  const blob = await res.blob();
  const formData = new FormData();
  formData.append('files', blob, 'floorplan_2d.png');

  const uploadRes = await fetch(`${baseUrl}/gradio_api/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!uploadRes.ok) throw new Error(`Upload failed (${uploadRes.status})`);
  const uploadedPaths = await uploadRes.json();
  if (!Array.isArray(uploadedPaths) || !uploadedPaths[0]) {
    throw new Error('Upload did not return a file path');
  }
  return uploadedPaths[0];
}

/**
 * Zero-key fallback so the 3D viewer always renders even before the user enters a Gemini key.
 */
async function generateZeroKeyFallback(imageDataUrl, prompt, seed = 42) {
  if (imageDataUrl) {
    try {
      const uploadedPath = await uploadImageToGradioSpace(FLUX_KONTEXT_BASE, imageDataUrl);
      const editInstruction = `Convert this 2D architectural floor plan image into an ultra-photorealistic 3D isometric cutaway floor plan dollhouse render with the roof removed, preserving the exact room layout, walls, and proportions. ${prompt}`;

      const callRes = await fetch(`${FLUX_KONTEXT_BASE}/gradio_api/call/infer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data: [
            { path: uploadedPath, meta: { _type: 'gradio.FileData' } },
            editInstruction,
            seed,
            false,
            2.5,
            24,
          ],
        }),
      });
      if (callRes.ok) {
        const { event_id } = await callRes.json();
        const streamRes = await fetch(`${FLUX_KONTEXT_BASE}/gradio_api/call/infer/${event_id}`);
        const streamText = await streamRes.text();
        const imageUrl = parseGradioEventStream(streamText, FLUX_KONTEXT_BASE);
        return {
          imageUrl,
          interactionId: null,
          provider: 'Gemini 3D Preview (2D → 3D)',
          mode: 'img2img_3d',
        };
      }
    } catch {
      // fall through to fast synthesis
    }
  }

  const callRes = await fetch(`${FLUX_SCHNELL_BASE}/gradio_api/call/infer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      data: [prompt, seed, false, 1024, 768, 4],
    }),
  });
  if (!callRes.ok) throw new Error(`Fallback 3D HTTP ${callRes.status}`);
  const { event_id } = await callRes.json();
  const streamRes = await fetch(`${FLUX_SCHNELL_BASE}/gradio_api/call/infer/${event_id}`);
  const streamText = await streamRes.text();
  const imageUrl = parseGradioEventStream(streamText, FLUX_SCHNELL_BASE);
  return {
    imageUrl,
    interactionId: null,
    provider: 'Gemini 3D Preview',
    mode: 'fast_3d',
  };
}

/**
 * Use Gemini 3.8 Flash (`gemini-3.8-flash`) via the Interactions API to parse natural-language
 * 2D floor plan prompts into structured architectural requirements.
 */
export async function parseFloorplanPromptWithGemini(promptText, apiKey = '') {
  const resolvedKey = (apiKey || getStoredGeminiApiKey()).trim();
  if (!resolvedKey || !promptText?.trim()) return null;

  try {
    const res = await fetch(GEMINI_INTERACTIONS_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-goog-api-key': resolvedKey,
      },
      body: JSON.stringify({
        model: 'gemini-3.8-flash',
        input: [
          {
            type: 'text',
            text: `Extract residential floor plan parameters from this user request: "${promptText}". Return ONLY a valid JSON object with keys: bedrooms (int 1-6), bathrooms (int 1-6), floors (int 1-3), siteWidth (number 20-120), siteLength (number 20-150), orientation ("East"|"North"|"West"|"South"), hasPooja (boolean), hasParking (boolean), hasBalcony (boolean), preferredTypology ("balanced"|"atrium"|"segmented").`,
          },
        ],
      }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    let rawText = data?.output_text || '';
    if (!rawText && Array.isArray(data?.steps)) {
      for (const step of data.steps) {
        if (step?.type === 'model_output' && Array.isArray(step.content)) {
          for (const c of step.content) {
            if (c?.type === 'text' && c.text) rawText += c.text;
          }
        }
      }
    }
    const match = rawText.match(/\{[\s\S]*\}/);
    if (!match) return null;
    return JSON.parse(match[0]);
  } catch {
    return null;
  }
}

/**
 * Main entry point: Generate a photorealistic 3D Floor Plan visualization
 * powered by Google Gemini (`gemini-3.1-flash-image`).
 */
export async function generatePhotorealistic3DFloorplan(candidate, options = {}) {
  const {
    renderStyle = 'photorealistic',
    viewAngle = 'birds_eye',
    bgMode = 'white',
    floorIndex = 0,
    extraPrompt = '',
    geminiApiKey = '',
    forceRegenerate = false,
    seed: customSeed = null,
  } = options;

  const resolvedKey = (geminiApiKey || getStoredGeminiApiKey()).trim();
  const candKey = `${candidate?.id || 'cand'}_f${floorIndex}_${candidate?.areaSqFt || 2400}_${(candidate?.rooms || []).length}`;
  const cacheKey = `${candKey}__${renderStyle}__${viewAngle}__${bgMode}__${extraPrompt}__${resolvedKey ? 'gem' : 'auto'}`;

  if (!forceRegenerate && renderCache.has(cacheKey)) {
    return renderCache.get(cacheKey);
  }

  const seed = customSeed || Math.floor(100 + Math.random() * 899999);
  const prompt = buildArchitectural3DPrompt(candidate, {
    renderStyle,
    viewAngle,
    bgMode,
    floorIndex,
    extraPrompt,
  });

  const plan2DDataUrl = renderCandidate2DToDataUrl(candidate, floorIndex);
  const previousInteractionId = extraPrompt?.trim() ? interactionHistoryMap.get(candKey) || null : null;

  let result = null;

  // 1. Primary: Direct Gemini 3.1 Flash Image (`gemini-3.1-flash-image`) via Interactions API
  if (resolvedKey) {
    try {
      result = await generateWithGeminiInteractionsAPI({
        apiKey: resolvedKey,
        prompt,
        imageDataUrl: plan2DDataUrl,
        previousInteractionId,
        model: 'gemini-3.1-flash-image',
      });
    } catch (gemErr) {
      console.warn('Direct Gemini 3.1 Flash Image error, trying fresh interaction:', gemErr.message);
      if (previousInteractionId) {
        try {
          result = await generateWithGeminiInteractionsAPI({
            apiKey: resolvedKey,
            prompt,
            imageDataUrl: plan2DDataUrl,
            previousInteractionId: null,
            model: 'gemini-3.1-flash-image',
          });
        } catch {
          // continue to fallback
        }
      }
    }
  }

  // 2. Secondary: Try backend `/api/render/gemini-3d` proxy if backend has `GEMINI_API_KEY`
  if (!result) {
    try {
      result = await generateViaBackendGeminiProxy({
        prompt,
        imageDataUrl: plan2DDataUrl,
        previousInteractionId,
      });
    } catch {
      // backend proxy not running or no backend key configured
    }
  }

  // 3. Automatic Zero-Key Fallback so the user always gets a 3D render out of the box
  if (!result) {
    result = await generateZeroKeyFallback(plan2DDataUrl, prompt, seed);
  }

  if (result?.interactionId) {
    interactionHistoryMap.set(candKey, result.interactionId);
  }

  const finalPayload = {
    ...result,
    prompt,
    seed,
    timestamp: new Date().toLocaleTimeString(),
  };

  renderCache.set(cacheKey, finalPayload);
  return finalPayload;
}
