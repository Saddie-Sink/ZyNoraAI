import React, { useState, useRef, useEffect } from 'react';
import {
  extractRequirementsClient,
  buildAndValidateFloorplanClient,
  rebuildFloorCADEntities,
  fmtFeetInches,
} from '../../services/floorplanPipelineClient';
import Interactive3DViewer from './Interactive3DViewer';

/**
 * High-contrast, bright architectural room palette inspired by floor-plan.ai
 */
const ROOM_PALETTE = {
  living:      { fill: '#FEF3C7', stroke: '#D97706', text: '#0F172A', sub: '#78350F' },
  dining:      { fill: '#FFEDD5', stroke: '#EA580C', text: '#0F172A', sub: '#7C2D12' },
  kitchen:     { fill: '#D1FAE5', stroke: '#059669', text: '#0F172A', sub: '#065F46' },
  pooja:       { fill: '#FEF08A', stroke: '#CA8A04', text: '#0F172A', sub: '#854D0E' },
  bedroom:     { fill: '#DBEAFE', stroke: '#2563EB', text: '#0F172A', sub: '#1E40AF' },
  bathroom:    { fill: '#CFFAFE', stroke: '#0891B2', text: '#0F172A', sub: '#155E75' },
  study:       { fill: '#EDE9FE', stroke: '#7C3AED', text: '#0F172A', sub: '#5B21B6' },
  staircase:   { fill: '#FDE68A', stroke: '#B45309', text: '#0F172A', sub: '#78350F' },
  circulation: { fill: '#F8FAFC', stroke: '#94A3B8', text: '#0F172A', sub: '#475569' },
  parking:     { fill: '#E2E8F0', stroke: '#64748B', text: '#0F172A', sub: '#334155' },
  balcony:     { fill: '#DCFCE7', stroke: '#16A34A', text: '#0F172A', sub: '#166534' },
  terrace:     { fill: '#E0F2FE', stroke: '#0284C7', text: '#0F172A', sub: '#0369A1' },
  utility:     { fill: '#F1F5F9', stroke: '#64748B', text: '#0F172A', sub: '#475569' },
  store:       { fill: '#F1F5F9', stroke: '#64748B', text: '#0F172A', sub: '#475569' },
  default:     { fill: '#F1F5F9', stroke: '#64748B', text: '#0F172A', sub: '#475569' },
};

/**
 * Crisp 2D architectural furniture & fixture symbols inside rooms
 */
function RoomCADFurnitureSVG({ room }) {
  const { x, y, width: w, height: h, type } = room;
  const cx = x + w / 2;
  const cy = y + h / 2;
  const strokeCol = '#334155';
  const accentCol = '#475569';
  const itemFill = 'rgba(255, 255, 255, 0.82)';

  if (type === 'bedroom' && w >= 7 && h >= 7) {
    const bw = Math.min(5.0, w * 0.46);
    const bh = Math.min(5.6, h * 0.50);
    const bx = cx - bw / 2;
    const by = y + 0.6;
    return (
      <g pointerEvents="none" opacity={0.9}>
        {/* Bed Frame */}
        <rect x={bx} y={by} width={bw} height={bh} rx={0.25} fill={itemFill} stroke={strokeCol} strokeWidth={0.14} />
        {/* Headboard */}
        <rect x={bx} y={by} width={bw} height={0.35} fill="#93C5FD" stroke={strokeCol} strokeWidth={0.12} />
        {/* Pillows */}
        <rect x={bx + 0.35} y={by + 0.5} width={bw * 0.36} height={0.85} rx={0.15} fill="#FFFFFF" stroke={strokeCol} strokeWidth={0.11} />
        <rect x={bx + bw - 0.35 - bw * 0.36} y={by + 0.5} width={bw * 0.36} height={0.85} rx={0.15} fill="#FFFFFF" stroke={strokeCol} strokeWidth={0.11} />
        {/* Duvet Fold */}
        <line x1={bx} y1={by + bh * 0.42} x2={bx + bw} y2={by + bh * 0.42} stroke={strokeCol} strokeWidth={0.12} />
        {/* Nightstands */}
        <rect x={bx - 1.05} y={by + 0.15} width={0.85} height={0.85} rx={0.1} fill={itemFill} stroke={accentCol} strokeWidth={0.12} />
        <rect x={bx + bw + 0.2} y={by + 0.15} width={0.85} height={0.85} rx={0.1} fill={itemFill} stroke={accentCol} strokeWidth={0.12} />
        {/* Wardrobe */}
        <rect x={x + 0.5} y={y + h - 1.55} width={Math.min(4.6, w * 0.42)} height={1.05} fill={itemFill} stroke={accentCol} strokeWidth={0.13} />
      </g>
    );
  }

  if (type === 'living' && w >= 8 && h >= 8) {
    const sw = Math.min(6.2, w * 0.52);
    const sh = Math.min(2.1, h * 0.22);
    const sx = cx - sw / 2;
    const sy = y + h - sh - 0.8;
    return (
      <g pointerEvents="none" opacity={0.9}>
        {/* Sofa Base */}
        <rect x={sx} y={sy} width={sw} height={sh} rx={0.25} fill={itemFill} stroke={strokeCol} strokeWidth={0.15} />
        {/* Sofa Backrest */}
        <rect x={sx} y={sy + sh - 0.4} width={sw} height={0.4} rx={0.12} fill="#FDE68A" stroke={strokeCol} strokeWidth={0.12} />
        {/* Coffee Table */}
        <rect x={cx - sw * 0.28} y={sy - 1.95} width={sw * 0.56} height={1.25} rx={0.2} fill="#FFFFFF" stroke={strokeCol} strokeWidth={0.13} />
        {/* TV Console */}
        <rect x={cx - sw * 0.35} y={y + 0.45} width={sw * 0.7} height={0.68} fill="#334155" stroke={strokeCol} strokeWidth={0.12} />
      </g>
    );
  }

  if (type === 'dining' && w >= 6.5 && h >= 6.5) {
    const tw = Math.min(4.4, w * 0.45);
    const th = Math.min(2.6, h * 0.35);
    const tx = cx - tw / 2;
    const ty = cy - th / 2;
    return (
      <g pointerEvents="none" opacity={0.9}>
        <rect x={tx} y={ty} width={tw} height={th} rx={0.3} fill={itemFill} stroke={strokeCol} strokeWidth={0.15} />
        {/* Chairs */}
        <rect x={tx + tw * 0.16} y={ty - 0.6} width={0.85} height={0.45} rx={0.1} fill="#FFFFFF" stroke={strokeCol} strokeWidth={0.11} />
        <rect x={tx + tw * 0.62} y={ty - 0.6} width={0.85} height={0.45} rx={0.1} fill="#FFFFFF" stroke={strokeCol} strokeWidth={0.11} />
        <rect x={tx + tw * 0.16} y={ty + th + 0.15} width={0.85} height={0.45} rx={0.1} fill="#FFFFFF" stroke={strokeCol} strokeWidth={0.11} />
        <rect x={tx + tw * 0.62} y={ty + th + 0.15} width={0.85} height={0.45} rx={0.1} fill="#FFFFFF" stroke={strokeCol} strokeWidth={0.11} />
      </g>
    );
  }

  if (type === 'kitchen' && w >= 5.5 && h >= 5.5) {
    const cDepth = 1.6;
    return (
      <g pointerEvents="none" opacity={0.92}>
        {/* Top Counter */}
        <rect x={x + 0.35} y={y + 0.35} width={w - 0.7} height={cDepth} fill={itemFill} stroke="#059669" strokeWidth={0.14} />
        {/* Side L-Counter */}
        <rect x={x + w - cDepth - 0.35} y={y + 0.35 + cDepth} width={cDepth} height={Math.max(1.5, h * 0.45)} fill={itemFill} stroke="#059669" strokeWidth={0.14} />
        {/* Sink Basin */}
        <rect x={x + 0.9} y={y + 0.55} width={1.55} height={1.1} rx={0.15} fill="#E0F2FE" stroke={strokeCol} strokeWidth={0.12} />
        {/* 4-Burner Stove Hob */}
        <rect x={x + w - 3.5} y={y + 0.55} width={1.55} height={1.1} fill="#1E293B" stroke={strokeCol} strokeWidth={0.12} />
        <circle cx={x + w - 3.05} cy={y + 0.85} r={0.17} fill="none" stroke="#F59E0B" strokeWidth={0.11} />
        <circle cx={x + w - 2.4} cy={y + 0.85} r={0.17} fill="none" stroke="#F59E0B" strokeWidth={0.11} />
        <circle cx={x + w - 3.05} cy={y + 1.35} r={0.17} fill="none" stroke="#F59E0B" strokeWidth={0.11} />
        <circle cx={x + w - 2.4} cy={y + 1.35} r={0.17} fill="none" stroke="#F59E0B" strokeWidth={0.11} />
      </g>
    );
  }

  if (type === 'bathroom' && w >= 4.0 && h >= 4.0) {
    return (
      <g pointerEvents="none" opacity={0.92}>
        {/* WC Toilet */}
        <rect x={x + 0.45} y={y + 0.4} width={1.2} height={0.5} fill="#FFFFFF" stroke={strokeCol} strokeWidth={0.13} />
        <ellipse cx={x + 1.05} cy={y + 1.38} rx={0.5} ry={0.62} fill="#FFFFFF" stroke={strokeCol} strokeWidth={0.13} />
        {/* Vanity Sink */}
        <rect x={x + w - 2.05} y={y + 0.4} width={1.6} height={1.1} rx={0.15} fill="#FFFFFF" stroke={strokeCol} strokeWidth={0.13} />
        <circle cx={x + w - 1.25} cy={y + 0.95} r={0.32} fill="#E0F2FE" stroke={strokeCol} strokeWidth={0.11} />
        {/* Shower Area */}
        <rect x={x + w - 2.5} y={y + h - 2.5} width={2.1} height={2.1} fill="rgba(255,255,255,0.55)" stroke="#0891B2" strokeWidth={0.12} strokeDasharray="0.3 0.2" />
        <circle cx={x + w - 1.45} cy={y + h - 1.45} r={0.18} fill="none" stroke="#0891B2" strokeWidth={0.12} />
      </g>
    );
  }

  if (type === 'pooja') {
    return (
      <g pointerEvents="none" opacity={0.92}>
        <rect x={cx - 1.05} y={y + 0.4} width={2.1} height={1.05} rx={0.2} fill={itemFill} stroke="#CA8A04" strokeWidth={0.15} />
        <circle cx={cx} cy={y + 0.92} r={0.3} fill="#FDE047" stroke="#CA8A04" strokeWidth={0.13} />
      </g>
    );
  }

  if (type === 'parking' && w >= 6 && h >= 8) {
    const cw = Math.min(5.2, w * 0.56);
    const ch = Math.min(11.0, h * 0.70);
    const carX = cx - cw / 2;
    const carY = cy - ch / 2;
    return (
      <g pointerEvents="none" opacity={0.7}>
        <rect x={carX} y={carY} width={cw} height={ch} rx={0.85} fill="#FFFFFF" stroke="#475569" strokeWidth={0.18} />
        <rect x={carX + cw * 0.12} y={carY + ch * 0.22} width={cw * 0.76} height={ch * 0.48} rx={0.4} fill="#E2E8F0" stroke="#475569" strokeWidth={0.13} />
      </g>
    );
  }

  if (type === 'circulation' && (room.name || '').toLowerCase().includes('courtyard')) {
    return (
      <g pointerEvents="none" opacity={0.85}>
        <rect x={x + 0.8} y={y + 0.8} width={Math.max(1, w - 1.6)} height={Math.max(1, h - 1.6)} fill="#ECFDF5" stroke="#10B981" strokeWidth={0.15} strokeDasharray="0.4 0.3" />
        <circle cx={cx} cy={cy} r={0.85} fill="#A7F3D0" stroke="#059669" strokeWidth={0.15} />
      </g>
    );
  }

  return null;
}

function ensureFloorsGeometry(candidate, project) {
  if (candidate?.floorsGeometry && candidate.floorsGeometry.length > 0) {
    return {
      siteBoundary: candidate.siteBoundary || { width: 30, depth: 40, entranceDirection: 'East' },
      buildingBoundary: candidate.buildingBoundary || { x: 2, y: 3, width: 26, depth: 35 },
      floorsGeometry: candidate.floorsGeometry,
      spatialGraph: candidate.spatialGraph || { nodes: [], edges: [] },
      qualityChecklist: candidate.qualityChecklist || [],
      structuredRequirements: candidate.structuredRequirements || null,
    };
  }
  const structured = extractRequirementsClient(project?.nlPrompt || '', project || {});
  return buildAndValidateFloorplanClient(structured, candidate?.floorplanSvgType || 'balanced');
}

/**
 * Compact 2D Floor Plan Preview for Layout Switcher Cards
 */
export function True2DCandidatePreview({ candidate, project }) {
  const geom = ensureFloorsGeometry(candidate, project);
  const floor0 = geom.floorsGeometry[0];
  if (!floor0) return null;

  const siteW = Number(geom.siteBoundary?.width || 30);
  const siteD = Number(geom.siteBoundary?.depth || 40);
  const pad = 2.5;
  const vbW = siteW + pad * 2;
  const vbH = siteD + pad * 2;

  return (
    <svg
      viewBox={`${-pad} ${-pad} ${vbW} ${vbH}`}
      width="100%"
      height="100%"
      xmlns="http://www.w3.org/2000/svg"
      style={{ background: '#F8FAFC' }}
    >
      {/* Site Boundary */}
      <rect
        x={0}
        y={0}
        width={siteW}
        height={siteD}
        fill="#FFFFFF"
        stroke="#CBD5E1"
        strokeWidth={0.25}
      />

      {/* Rooms */}
      {(floor0.rooms || []).map((r) => {
        const pal = ROOM_PALETTE[r.type] || ROOM_PALETTE.default;
        const cx = r.x + r.width / 2;
        const cy = r.y + r.height / 2;
        const shortName = (r.name || 'ROOM').toUpperCase().slice(0, 10);
        return (
          <g key={r.id}>
            <rect
              x={r.x}
              y={r.y}
              width={r.width}
              height={r.height}
              fill={pal.fill}
              stroke={pal.stroke}
              strokeWidth={0.18}
            />
            <text
              x={cx}
              y={cy}
              fill={pal.text}
              fontSize={Math.min(1.15, Math.max(0.75, r.width * 0.11))}
              fontWeight="700"
              textAnchor="middle"
              dominantBaseline="middle"
              fontFamily="system-ui, -apple-system, sans-serif"
            >
              {shortName}
            </text>
          </g>
        );
      })}

      {/* Walls */}
      {(floor0.walls || []).map((w) => (
        <line
          key={w.id}
          x1={w.start.x}
          y1={w.start.y}
          x2={w.end.x}
          y2={w.end.y}
          stroke="#0F172A"
          strokeWidth={w.wallType === 'exterior' ? 0.55 : 0.30}
          strokeLinecap="square"
        />
      ))}
    </svg>
  );
}

/**
 * Single Floor Full Architectural 2D Floor Plan SVG Renderer (Bright floor-plan.ai Style)
 */
function SingleFloorCADSVG({
  floorData,
  siteBoundary,
  buildingBoundary,
  selectedRoomId,
  onSelectRoom,
  isEditMode,
  onDragRoom,
  showLayers,
  svgExportRef,
}) {
  const localSvgRef = useRef(null);
  const svgRef = svgExportRef || localSvgRef;
  const [dragState, setDragState] = useState(null);

  const siteW = Number(siteBoundary?.width || 30);
  const siteD = Number(siteBoundary?.depth || 40);
  const bx = Number(buildingBoundary?.x || 2);
  const by = Number(buildingBoundary?.y || 3);
  const bw = Number(buildingBoundary?.width || siteW - 4);
  const bh = Number(buildingBoundary?.depth || siteD - 5);

  const pad = 5.5;
  const vbX = -pad;
  const vbY = -pad;
  const vbW = siteW + pad * 2;
  const vbH = siteD + pad * 2;

  const clientToSVGCoords = (clientX, clientY) => {
    const svg = svgRef.current;
    if (!svg) return { x: 0, y: 0 };
    const rect = svg.getBoundingClientRect();
    const x = vbX + ((clientX - rect.left) / rect.width) * vbW;
    const y = vbY + ((clientY - rect.top) / rect.height) * vbH;
    return { x, y };
  };

  const handlePointerDownRoom = (e, room, mode = 'move') => {
    e.stopPropagation();
    onSelectRoom?.(room.id);
    if (!isEditMode) return;
    const pt = clientToSVGCoords(e.clientX, e.clientY);
    setDragState({
      roomId: room.id,
      mode,
      startX: pt.x,
      startY: pt.y,
      origX: room.x,
      origY: room.y,
      origW: room.width,
      origH: room.height,
    });
  };

  const handlePointerMove = (e) => {
    if (!dragState || !isEditMode) return;
    const pt = clientToSVGCoords(e.clientX, e.clientY);
    const dx = Math.round((pt.x - dragState.startX) * 2) / 2;
    const dy = Math.round((pt.y - dragState.startY) * 2) / 2;

    if (dragState.mode === 'move') {
      const nx = Math.max(0, Math.min(siteW - dragState.origW, dragState.origX + dx));
      const ny = Math.max(0, Math.min(siteD - dragState.origH, dragState.origY + dy));
      onDragRoom?.(dragState.roomId, { x: nx, y: ny });
    } else if (dragState.mode === 'resize') {
      const nw = Math.max(4.0, Math.min(siteW - dragState.origX, dragState.origW + dx));
      const nh = Math.max(4.0, Math.min(siteD - dragState.origY, dragState.origH + dy));
      onDragRoom?.(dragState.roomId, { width: nw, height: nh });
    }
  };

  const handlePointerUp = () => {
    if (dragState) setDragState(null);
  };

  return (
    <svg
      ref={svgRef}
      viewBox={`${vbX} ${vbY} ${vbW} ${vbH}`}
      width="100%"
      height="100%"
      xmlns="http://www.w3.org/2000/svg"
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
      style={{
        background: '#FFFFFF',
        userSelect: 'none',
        touchAction: 'none',
        cursor: dragState ? 'grabbing' : 'default',
      }}
    >
      <defs>
        <filter id="slabShadow" x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="0" dy="0.3" stdDeviation="0.5" floodColor="#0F172A" floodOpacity="0.08" />
        </filter>
      </defs>

      {/* Clean Building Footprint Slab */}
      <rect
        x={bx}
        y={by}
        width={bw}
        height={bh}
        fill="#FFFFFF"
        filter="url(#slabShadow)"
      />

      {/* 1. COLOR-CODED ROOMS & LABELS */}
      {(floorData.rooms || []).map((r) => {
        const pal = ROOM_PALETTE[r.type] || ROOM_PALETTE.default;
        const isSel = selectedRoomId === r.id;
        const cx = r.x + r.width / 2;
        const cy = r.y + r.height / 2;
        const labelFontSize = Math.min(0.98, Math.max(0.65, Math.min(r.width, r.height) * 0.11));

        return (
          <g
            key={r.id}
            onPointerDown={(e) => handlePointerDownRoom(e, r, 'move')}
            style={{ cursor: isEditMode ? 'move' : 'pointer' }}
          >
            {/* Room Floor Fill */}
            <rect
              x={r.x}
              y={r.y}
              width={r.width}
              height={r.height}
              fill={isSel ? '#DBEAFE' : pal.fill}
              stroke={isSel ? '#2563EB' : pal.stroke}
              strokeWidth={isSel ? 0.28 : 0.12}
            />

            {/* Optional 2D Furniture Blocks (off by default to keep plan uncongested) */}
            {showLayers.furniture && <RoomCADFurnitureSVG room={r} />}

            {/* Clean Centered Room Name & Dimension */}
            {r.type !== 'staircase' && (
              <g pointerEvents="none">
                <text
                  x={cx}
                  y={showLayers.dimensions ? cy - 0.45 : cy}
                  fill={pal.text}
                  fontSize={labelFontSize}
                  fontWeight="700"
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fontFamily="system-ui, -apple-system, sans-serif"
                >
                  {r.name}
                </text>
                {showLayers.dimensions && (
                  <text
                    x={cx}
                    y={cy + 0.55}
                    fill={pal.sub}
                    fontSize={Math.min(0.78, labelFontSize * 0.85)}
                    fontWeight="600"
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fontFamily="ui-monospace, SFMono-Regular, monospace"
                  >
                    {Math.round(r.width)}&apos; × {Math.round(r.height)}&apos;
                  </text>
                )}
              </g>
            )}

            {/* Resize Handle in Edit Mode */}
            {isEditMode && isSel && (
              <rect
                x={r.x + r.width - 1.0}
                y={r.y + r.height - 1.0}
                width={1.0}
                height={1.0}
                fill="#2563EB"
                stroke="#FFFFFF"
                strokeWidth={0.12}
                style={{ cursor: 'nwse-resize' }}
                onPointerDown={(e) => handlePointerDownRoom(e, r, 'resize')}
              />
            )}
          </g>
        );
      })}

      {/* 2. STAIRCASE GEOMETRY */}
      {showLayers.stairs && floorData.staircase && (
        <g pointerEvents="none">
          {floorData.staircase.landing && (
            <rect
              x={floorData.staircase.landing.x}
              y={floorData.staircase.landing.y}
              width={floorData.staircase.landing.width}
              height={floorData.staircase.landing.height}
              fill="#FDE68A"
              stroke="#B45309"
              strokeWidth={0.12}
            />
          )}
          <line
            x1={floorData.staircase.x + floorData.staircase.width / 2}
            y1={floorData.staircase.y}
            x2={floorData.staircase.x + floorData.staircase.width / 2}
            y2={floorData.staircase.y + floorData.staircase.height * 0.76}
            stroke="#B45309"
            strokeWidth={0.14}
          />
          {(floorData.staircase.treads || []).map((t, i) => (
            <line
              key={i}
              x1={t.x1}
              y1={t.y1}
              x2={t.x2}
              y2={t.y2}
              stroke="#92400E"
              strokeWidth={0.12}
            />
          ))}
          <text
            x={floorData.staircase.x + floorData.staircase.width / 2}
            y={floorData.staircase.y + floorData.staircase.height - 0.8}
            fill="#78350F"
            fontSize={0.72}
            fontWeight="700"
            textAnchor="middle"
            fontFamily="system-ui, sans-serif"
          >
            Stairs
          </text>
        </g>
      )}

      {/* 3. CRISP ARCHITECTURAL WALLS */}
      {showLayers.walls &&
        (floorData.walls || []).map((w) => {
          const isExt = w.wallType === 'exterior';
          const thick = isExt ? 0.62 : 0.34;
          return (
            <line
              key={w.id}
              x1={w.start.x}
              y1={w.start.y}
              x2={w.end.x}
              y2={w.end.y}
              stroke={isExt ? '#0F172A' : '#1E293B'}
              strokeWidth={thick}
              strokeLinecap="square"
            />
          );
        })}

      {/* 4. EXTERIOR WINDOWS */}
      {showLayers.windows &&
        (floorData.windows || []).map((win) => {
          const isH = win.orientation === 'horizontal';
          const half = (win.width || 3.5) / 2;
          const x1 = isH ? win.x - half : win.x;
          const y1 = isH ? win.y : win.y - half;
          const x2 = isH ? win.x + half : win.x;
          const y2 = isH ? win.y : win.y + half;
          return (
            <g key={win.id}>
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#FFFFFF" strokeWidth={0.68} />
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#0284C7" strokeWidth={0.36} />
            </g>
          );
        })}

      {/* 5. COMPACT DOORS WITH CLEAN SWING ARCS */}
      {showLayers.doors &&
        (floorData.doors || []).map((d) => {
          const isH = d.orientation === 'horizontal';
          const r = Math.min(2.1, d.width || 2.1);
          const half = r / 2;
          const x1 = isH ? d.x - half : d.x;
          const y1 = isH ? d.y : d.y - half;
          const x2 = isH ? d.x + half : d.x;
          const y2 = isH ? d.y : d.y + half;
          const doorColor = d.doorType === 'main_entrance' ? '#059669' : '#B45309';

          const leafEndX = isH ? x1 : x1 + r;
          const leafEndY = isH ? y1 + r : y1;
          const arcPath = isH
            ? `M ${x2} ${y2} A ${r} ${r} 0 0 1 ${leafEndX} ${leafEndY}`
            : `M ${x2} ${y2} A ${r} ${r} 0 0 0 ${leafEndX} ${leafEndY}`;

          return (
            <g key={d.id}>
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#FFFFFF" strokeWidth={0.72} />
              <line x1={x1} y1={y1} x2={leafEndX} y2={leafEndY} stroke={doorColor} strokeWidth={0.20} />
              <path d={arcPath} fill="none" stroke="#94A3B8" strokeWidth={0.12} strokeDasharray="0.3 0.2" />
            </g>
          );
        })}

      {/* 6. MINIMAL OUTER FOOTPRINT DIMENSIONS */}
      {showLayers.dimensions && (
        <g pointerEvents="none">
          <text
            x={bx + bw / 2}
            y={by - 1.2}
            fill="#475569"
            fontSize={0.88}
            fontWeight="700"
            textAnchor="middle"
            fontFamily="ui-monospace, SFMono-Regular, monospace"
          >
            {Math.round(bw)}&apos;
          </text>
          <text
            x={bx - 1.3}
            y={by + bh / 2}
            fill="#475569"
            fontSize={0.88}
            fontWeight="700"
            textAnchor="middle"
            fontFamily="ui-monospace, SFMono-Regular, monospace"
            transform={`rotate(-90 ${bx - 1.3} ${by + bh / 2})`}
          >
            {Math.round(bh)}&apos;
          </text>
        </g>
      )}
    </svg>
  );
}

/**
 * Clean, minimal floor-plan.ai Studio Canvas (2D Floor Plan + 3D Model + Split View)
 */
export default function EditableFloorplanCanvas({
  candidate,
  project,
  onUpdateCandidate,
  initialStudioTab = 'cad',
  copilotTimeOfDay = 'day',
  externalRenderStyle = 'photorealistic',
  externalViewAngle = 'angled',
  externalBgMode = 'white',
  externalExtraPrompt = '',
  externalTriggerCount = 0,
  onSwitchStudioTab,
}) {
  const initialGeom = ensureFloorsGeometry(candidate, project);

  const [floorsGeometry, setFloorsGeometry] = useState(initialGeom.floorsGeometry);
  const [activeFloorIdx, setActiveFloorIdx] = useState(0);
  const [viewAllFloors, setViewAllFloors] = useState(false);
  const [activeTab, setActiveTab] = useState(initialStudioTab); // 'cad' | '3d' | 'split'
  const [showRawUpload2D, setShowRawUpload2D] = useState(true);
  const [isEditMode, setIsEditMode] = useState(false);
  const [selectedRoomId, setSelectedRoomId] = useState(null);
  const [showLayers] = useState({
    walls: true,
    doors: true,
    windows: true,
    stairs: true,
    columns: false,
    furniture: true,
    dimensions: true,
  });

  useEffect(() => {
    if (initialStudioTab) setActiveTab(initialStudioTab);
  }, [initialStudioTab]);

  useEffect(() => {
    const g = ensureFloorsGeometry(candidate, project);
    setFloorsGeometry(g.floorsGeometry);
    setActiveFloorIdx(0);
    setSelectedRoomId(g.floorsGeometry?.[0]?.rooms?.[0]?.id || null);
  }, [candidate?.id, candidate?.floorsGeometry]);

  const siteBoundary = candidate?.siteBoundary || initialGeom.siteBoundary;
  const buildingBoundary = candidate?.buildingBoundary || initialGeom.buildingBoundary;
  const currentFloor = floorsGeometry[activeFloorIdx] || floorsGeometry[0];
  const selectedRoom = currentFloor?.rooms?.find((r) => r.id === selectedRoomId) || null;

  const liveCandidateFor3D = {
    ...candidate,
    siteBoundary,
    buildingBoundary,
    floorsGeometry,
    rooms: floorsGeometry.flatMap((f) => f.rooms || []),
  };

  const updateFloorRoomsAndRebuild = (floorIdx, updatedRooms) => {
    const nextFloors = floorsGeometry.map((fg, i) => {
      if (i !== floorIdx) return fg;
      const updatedFloor = {
        ...fg,
        rooms: updatedRooms.map((r) => ({
          ...r,
          width: Math.max(3.5, Number(r.width) || 6),
          height: Math.max(3.5, Number(r.height) || 6),
          area: Math.round((Number(r.width) || 6) * (Number(r.height) || 6)),
          dimensionsLabel: `${fmtFeetInches(r.width)} × ${fmtFeetInches(r.height)}`,
        })),
      };
      return rebuildFloorCADEntities(updatedFloor, buildingBoundary, siteBoundary);
    });

    setFloorsGeometry(nextFloors);
    const flatRooms = nextFloors.flatMap((f) =>
      f.rooms.map((rm) => ({
        name: rm.name,
        type: rm.type,
        floor: f.floor + 1,
        width: rm.width,
        height: rm.height,
        area: rm.area,
        score: rm.score || 92,
      }))
    );

    onUpdateCandidate?.({
      ...candidate,
      floorsGeometry: nextFloors,
      rooms: flatRooms,
    });
  };

  const handleRoomFieldChange = (field, value) => {
    if (!selectedRoom || !currentFloor) return;
    const updatedRooms = currentFloor.rooms.map((r) => {
      if (r.id !== selectedRoom.id) return r;
      return { ...r, [field]: ['x', 'y', 'width', 'height'].includes(field) ? Number(value) : value };
    });
    updateFloorRoomsAndRebuild(activeFloorIdx, updatedRooms);
  };

  const handleDragRoomOnCanvas = (roomId, patch) => {
    if (!currentFloor) return;
    const updatedRooms = currentFloor.rooms.map((r) => (r.id === roomId ? { ...r, ...patch } : r));
    updateFloorRoomsAndRebuild(activeFloorIdx, updatedRooms);
  };

  const handleAddRoom = () => {
    if (!currentFloor) return;
    const bx = Number(buildingBoundary?.x || 2);
    const by = Number(buildingBoundary?.y || 3);
    const newId = `rm_f${activeFloorIdx}_${Date.now().toString(36)}`;
    const newRoom = {
      id: newId,
      name: 'Bedroom',
      type: 'bedroom',
      floor: activeFloorIdx,
      zone: 'private',
      mandatory: false,
      x: bx + 2,
      y: by + 2,
      width: 10,
      height: 10,
      area: 100,
      dimensionsLabel: "10' × 10'",
      score: 92,
    };
    const updatedRooms = [...currentFloor.rooms, newRoom];
    setSelectedRoomId(newId);
    updateFloorRoomsAndRebuild(activeFloorIdx, updatedRooms);
  };

  const handleDeleteSelectedRoom = () => {
    if (!selectedRoom || !currentFloor || currentFloor.rooms.length <= 2) return;
    const updatedRooms = currentFloor.rooms.filter((r) => r.id !== selectedRoom.id);
    setSelectedRoomId(updatedRooms[0]?.id || null);
    updateFloorRoomsAndRebuild(activeFloorIdx, updatedRooms);
  };

  return (
    <div
      style={{
        background: '#FFFFFF',
        borderRadius: '14px',
        border: '1px solid #E2E8F0',
        boxShadow: '0 2px 10px rgba(15, 23, 42, 0.04)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Single Minimal Top Stage Header Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '10px',
          padding: '10px 16px',
          borderBottom: '1px solid #F1F5F9',
          background: '#FFFFFF',
        }}
      >
        {/* Left: Segmented View Pill + Floor Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div
            style={{
              display: 'inline-flex',
              background: '#F1F5F9',
              padding: '3px',
              borderRadius: '10px',
              gap: '2px',
            }}
          >
            {[
              { id: 'cad', label: '2D Plan' },
              { id: '3d', label: '3D Render' },
              { id: 'split', label: 'Split 2D → 3D' },
            ].map((tab) => {
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => {
                    setActiveTab(tab.id);
                    onSwitchStudioTab?.(tab.id);
                  }}
                  style={{
                    padding: '5px 13px',
                    borderRadius: '7px',
                    fontSize: '12px',
                    fontWeight: 600,
                    background: active ? '#2563EB' : 'transparent',
                    color: active ? '#FFFFFF' : '#475569',
                    border: 'none',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>

          {floorsGeometry.length > 1 && (
            <div
              style={{
                display: 'inline-flex',
                background: '#F1F5F9',
                padding: '3px',
                borderRadius: '9px',
                gap: '2px',
              }}
            >
              {floorsGeometry.map((fg, idx) => {
                const isCurr = !viewAllFloors && activeFloorIdx === idx;
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setViewAllFloors(false);
                      setActiveFloorIdx(idx);
                    }}
                    style={{
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '11.5px',
                      fontWeight: 600,
                      background: isCurr ? '#FFFFFF' : 'transparent',
                      color: isCurr ? '#0F172A' : '#64748B',
                      border: 'none',
                      cursor: 'pointer',
                      boxShadow: isCurr ? '0 1px 2px rgba(15,23,42,0.06)' : 'none',
                    }}
                  >
                    { `Floor ${idx + 1}` }
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right: Minimal Context Actions */}
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          {(activeTab === 'cad' || activeTab === 'split') && candidate?.isUploadedPlan && (
            <button
              type="button"
              onClick={() => setShowRawUpload2D(!showRawUpload2D)}
              style={{
                padding: '5px 10px',
                borderRadius: '8px',
                fontSize: '11.5px',
                fontWeight: 600,
                background: showRawUpload2D ? '#EFF6FF' : '#FFFFFF',
                color: showRawUpload2D ? '#2563EB' : '#475569',
                border: '1px solid #E2E8F0',
                cursor: 'pointer',
              }}
            >
              {showRawUpload2D ? 'Original 2D' : 'CAD View'}
            </button>
          )}

          {(activeTab === 'cad' || activeTab === 'split') && !candidate?.isUploadedPlan && (
            <button
              type="button"
              onClick={() => setIsEditMode(!isEditMode)}
              style={{
                padding: '5px 11px',
                borderRadius: '8px',
                fontSize: '11.5px',
                fontWeight: 600,
                background: isEditMode ? '#10B981' : '#FFFFFF',
                color: isEditMode ? '#FFFFFF' : '#334155',
                border: `1px solid ${isEditMode ? '#10B981' : '#E2E8F0'}`,
                cursor: 'pointer',
              }}
            >
              {isEditMode ? '✓ Done' : 'Edit 2D'}
            </button>
          )}

          {activeTab === 'cad' && (
            <button
              type="button"
              onClick={() => {
                setActiveTab('split');
                onSwitchStudioTab?.('split');
              }}
              style={{
                padding: '5px 12px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: 700,
                background: '#2563EB',
                color: '#FFFFFF',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              ✨ Convert to 3D →
            </button>
          )}
        </div>
      </div>

      {/* Inline Room Edit Bar (only visible when Edit 2D is active) */}
      {(activeTab === 'cad' || activeTab === 'split') && isEditMode && selectedRoom && (
        <div
          style={{
            background: '#F8FAFC',
            borderBottom: '1px solid #E2E8F0',
            padding: '7px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '8px',
            fontSize: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <input
              type="text"
              style={{ width: '120px', padding: '4px 8px', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '12px' }}
              value={selectedRoom.name}
              onChange={(e) => handleRoomFieldChange('name', e.target.value)}
            />
            <select
              style={{ padding: '4px 8px', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '12px' }}
              value={selectedRoom.type}
              onChange={(e) => handleRoomFieldChange('type', e.target.value)}
            >
              {['living', 'dining', 'kitchen', 'bedroom', 'bathroom', 'study', 'pooja', 'utility', 'parking', 'balcony', 'terrace'].map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            <label style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#475569' }}>
              W:
              <input
                type="number"
                step="0.5"
                min="3.5"
                style={{ width: '52px', padding: '4px 6px', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                value={selectedRoom.width}
                onChange={(e) => handleRoomFieldChange('width', e.target.value)}
              />
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#475569' }}>
              L:
              <input
                type="number"
                step="0.5"
                min="3.5"
                style={{ width: '52px', padding: '4px 6px', borderRadius: '6px', border: '1px solid #CBD5E1' }}
                value={selectedRoom.height}
                onChange={(e) => handleRoomFieldChange('height', e.target.value)}
              />
            </label>
          </div>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button
              type="button"
              onClick={handleAddRoom}
              style={{
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '11.5px',
                fontWeight: 600,
                background: '#EFF6FF',
                color: '#2563EB',
                border: '1px solid #BFDBFE',
                cursor: 'pointer',
              }}
            >
              + Room
            </button>
            <button
              type="button"
              onClick={handleDeleteSelectedRoom}
              style={{
                padding: '4px 10px',
                borderRadius: '6px',
                fontSize: '11.5px',
                fontWeight: 600,
                background: '#FEF2F2',
                color: '#DC2626',
                border: '1px solid #FECACA',
                cursor: 'pointer',
              }}
            >
              Delete
            </button>
          </div>
        </div>
      )}

      {/* 1. 2D FLOOR PLAN STAGE */}
      {activeTab === 'cad' && (
        <div style={{ height: '600px', width: '100%', background: '#FFFFFF' }}>
          {candidate?.isUploadedPlan && showRawUpload2D && candidate?.uploadedImageDataUrl ? (
            <div
              style={{
                height: '100%',
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '24px',
              }}
            >
              <img
                src={candidate.uploadedImageDataUrl}
                alt="Uploaded 2D Floor Plan"
                style={{ maxHeight: '100%', maxWidth: '100%', objectFit: 'contain' }}
              />
            </div>
          ) : (
            <SingleFloorCADSVG
              floorData={currentFloor}
              siteBoundary={siteBoundary}
              buildingBoundary={buildingBoundary}
              selectedRoomId={selectedRoomId}
              onSelectRoom={setSelectedRoomId}
              isEditMode={isEditMode}
              onDragRoom={handleDragRoomOnCanvas}
              showLayers={showLayers}
            />
          )}
        </div>
      )}

      {/* 2. GEMINI 3D RENDER STAGE */}
      {activeTab === '3d' && (
        <Interactive3DViewer
          candidate={liveCandidateFor3D}
          activeFloorIdx={activeFloorIdx}
          externalRenderStyle={externalRenderStyle}
          externalViewAngle={externalViewAngle}
          externalBgMode={externalBgMode}
          externalExtraPrompt={externalExtraPrompt}
          externalTriggerCount={externalTriggerCount}
          height={600}
        />
      )}

      {/* 3. CLEAN 50/50 SPLIT 2D → 3D STAGE (floor-plan.ai style) */}
      {activeTab === 'split' && (
        <div
          className="fp-split-stage"
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            alignItems: 'stretch',
            background: '#FFFFFF',
            minHeight: '580px',
          }}
        >
          {/* Left Half: 2D Floor Plan */}
          <div
            style={{
              position: 'relative',
              height: '580px',
              borderRight: '1px solid #F1F5F9',
              background: '#FFFFFF',
            }}
          >
            {candidate?.isUploadedPlan && showRawUpload2D && candidate?.uploadedImageDataUrl ? (
              <div
                style={{
                  height: '100%',
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '24px',
                }}
              >
                <img
                  src={candidate.uploadedImageDataUrl}
                  alt="Uploaded Floor Plan"
                  style={{ maxHeight: '100%', maxWidth: '100%', objectFit: 'contain' }}
                />
              </div>
            ) : (
              <SingleFloorCADSVG
                floorData={currentFloor}
                siteBoundary={siteBoundary}
                buildingBoundary={buildingBoundary}
                selectedRoomId={selectedRoomId}
                onSelectRoom={setSelectedRoomId}
                isEditMode={isEditMode}
                onDragRoom={handleDragRoomOnCanvas}
                showLayers={showLayers}
              />
            )}
          </div>

          {/* Right Half: Gemini 3D Cutaway Output */}
          <div style={{ position: 'relative', height: '580px', background: '#FFFFFF' }}>
            <Interactive3DViewer
              candidate={liveCandidateFor3D}
              activeFloorIdx={activeFloorIdx}
              externalRenderStyle={externalRenderStyle}
              externalViewAngle={externalViewAngle}
              externalBgMode={externalBgMode}
              externalExtraPrompt={externalExtraPrompt}
              externalTriggerCount={externalTriggerCount}
              height={580}
            />
          </div>
          <style>{`
            @media (max-width: 900px) {
              .fp-split-stage {
                grid-template-columns: 1fr !important;
              }
            }
          `}</style>
        </div>
      )}
    </div>
  );
}
