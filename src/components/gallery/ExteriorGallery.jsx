import React, { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import ViewSlot from './ViewSlot';
import Badge from '../common/Badge';
import { DEMO_EXTERIOR_VIEWS } from '../../data/demoData';

export default function ExteriorGallery({ project, candidate }) {
  const [activeSlot, setActiveSlot] = useState(DEMO_EXTERIOR_VIEWS[0]);
  const [cadStyle, setCadStyle] = useState('blender'); // 'blender' | 'shaded' | 'blueprint'
  const [showDimensions, setShowDimensions] = useState(true);
  const [showGrids, setShowGrids] = useState(true);
  const [downloadSuccess, setDownloadSuccess] = useState(null);
  const svgRef = useRef(null);

  const isBlueprint = cadStyle === 'blueprint';
  const code = candidate?.code || 'Candidate B';
  const bedrooms = candidate?.bedrooms || 3;
  const area = candidate?.area || 2400;

  // Real client-side AutoCAD .DXF File Generator
  const handleExportDXF = () => {
    const projName = project?.name || 'Ananya Luxury Villa · Chennai';
    const dxfContent = `0
SECTION
2
HEADER
9
$ACADVER
1
AC1009
0
ENDSEC
0
SECTION
2
TABLES
0
TABLE
2
LAYER
70
4
0
LAYER
2
0
70
0
62
7
6
CONTINUOUS
0
LAYER
2
WALLS_OUTLINE
70
0
62
3
6
CONTINUOUS
0
LAYER
2
FENESTRATION_GLAZING
70
0
62
5
6
CONTINUOUS
0
LAYER
2
DIMENSIONS_DATUMS
70
0
62
1
6
CONTINUOUS
0
LAYER
2
GRID_AXES
70
0
62
4
6
DASHED
0
ENDTAB
0
ENDSEC
0
SECTION
2
ENTITIES
0
LINE
8
WALLS_OUTLINE
10
0.0
20
0.0
30
0.0
11
12.19
21
0.0
31
0.0
0
LINE
8
WALLS_OUTLINE
10
12.19
20
0.0
30
0.0
11
12.19
21
8.53
31
0.0
0
LINE
8
WALLS_OUTLINE
10
12.19
20
8.53
30
0.0
11
0.0
21
8.53
31
0.0
0
LINE
8
WALLS_OUTLINE
10
0.0
20
8.53
30
0.0
11
0.0
21
0.0
31
0.0
0
LINE
8
FENESTRATION_GLAZING
10
2.50
20
1.20
30
0.0
11
6.50
21
1.20
31
0.0
0
LINE
8
FENESTRATION_GLAZING
10
6.50
20
1.20
30
0.0
11
6.50
21
2.80
31
0.0
0
LINE
8
FENESTRATION_GLAZING
10
6.50
20
2.80
30
0.0
11
2.50
21
2.80
31
0.0
0
LINE
8
FENESTRATION_GLAZING
10
2.50
20
2.80
30
0.0
11
2.50
21
1.20
31
0.0
0
TEXT
8
DIMENSIONS_DATUMS
10
0.50
20
-1.20
30
0.0
40
0.50
1
${projName.toUpperCase()} - ${code.toUpperCase()} ELEVATION (${activeSlot.name.toUpperCase()})
0
TEXT
8
DIMENSIONS_DATUMS
10
0.50
20
-2.00
30
0.0
40
0.35
1
BUILT-UP AREA: ${area.toLocaleString()} SQ FT | LOCATION: CHENNAI, TAMIL NADU, INDIA
0
ENDSEC
0
EOF`;

    const blob = new Blob([dxfContent], { type: 'application/dxf' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ZYNORA_${code.replace(/\s+/g, '_')}_Elevation_${activeSlot.slot}.dxf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setDownloadSuccess('AutoCAD .DXF downloaded!');
    setTimeout(() => setDownloadSuccess(null), 3500);
  };

  // Real client-side Vector .SVG Blueprint Generator
  const handleExportSVG = () => {
    if (!svgRef.current) return;
    const serializer = new XMLSerializer();
    const source = serializer.serializeToString(svgRef.current);
    const blob = new Blob([source], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ZYNORA_${code.replace(/\s+/g, '_')}_CAD_Elevation_${activeSlot.slot}.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setDownloadSuccess('Vector CAD .SVG downloaded!');
    setTimeout(() => setDownloadSuccess(null), 3500);
  };

  return (
    <div className="gallery-layout">
      {/* CAD Toolbar & Display Mode Switcher */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: '1rem', background: 'rgba(255,255,255,0.03)',
        padding: '10px 16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.08)',
        flexWrap: 'wrap', gap: '12px'
      }}>
        {/* Left: Drafting Style Controls */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            View Mode:
          </span>
          <button
            type="button"
            className={`btn btn-sm ${cadStyle === 'blender' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setCadStyle('blender')}
            style={{
              fontSize: '11px',
              border: cadStyle === 'blender' ? '1px solid #f97316' : '1px solid rgba(255,255,255,0.12)',
              background: cadStyle === 'blender' ? 'rgba(249, 115, 22, 0.2)' : 'transparent',
              color: cadStyle === 'blender' ? '#fb923c' : 'rgba(255,255,255,0.7)',
            }}
          >
            🟠 Blender 4.5 Render (Photorealistic)
          </button>
          <button
            type="button"
            className={`btn btn-sm ${cadStyle === 'shaded' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setCadStyle('shaded')}
            style={{ fontSize: '11px' }}
          >
            📐 Shaded CAD Model
          </button>
          <button
            type="button"
            className={`btn btn-sm ${cadStyle === 'blueprint' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setCadStyle('blueprint')}
            style={{ fontSize: '11px' }}
          >
            📄 Blueprint Wireframe
          </button>

          {cadStyle !== 'blender' && (
            <>
              <span style={{ width: '1px', height: '16px', background: 'rgba(255,255,255,0.12)', margin: '0 4px' }} />

              {/* Toggle Datums */}
              <button
                type="button"
                className={`btn btn-sm ${showDimensions ? 'btn-outline' : 'btn-ghost'}`}
                onClick={() => setShowDimensions(!showDimensions)}
                style={{ fontSize: '11px', color: showDimensions ? 'var(--accent)' : 'rgba(255,255,255,0.4)' }}
              >
                {showDimensions ? '✓ Level Datums & Dims' : '+ Level Datums & Dims'}
              </button>

              {/* Toggle Grids */}
              <button
                type="button"
                className={`btn btn-sm ${showGrids ? 'btn-outline' : 'btn-ghost'}`}
                onClick={() => setShowGrids(!showGrids)}
                style={{ fontSize: '11px', color: showGrids ? 'var(--accent)' : 'rgba(255,255,255,0.4)' }}
              >
                {showGrids ? '✓ Structural Grid' : '+ Structural Grid'}
              </button>
            </>
          )}
        </div>

        {/* Right: Export Toolbar & Feedback */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {downloadSuccess && (
            <span style={{ fontSize: '11px', color: '#50c878', fontWeight: 600 }}>
              ✓ {downloadSuccess}
            </span>
          )}
          <a
            href="/renders/zynora_house.blend"
            download="zynora_house.blend"
            className="btn btn-outline btn-sm"
            style={{ fontSize: '11px', borderColor: '#f97316', color: '#fb923c', textDecoration: 'none' }}
            title="Download the full 3D Blender project file"
          >
            📥 Download .BLEND
          </a>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={handleExportDXF}
            style={{ fontSize: '11px', borderColor: 'var(--accent)', color: 'var(--accent)' }}
            title="Download AutoCAD DXF CAD drawing"
          >
            📥 Export AutoCAD .DXF
          </button>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={handleExportSVG}
            style={{ fontSize: '11px' }}
            title="Download Scalable Vector Graphic blueprint"
          >
            📐 Export Vector .SVG
          </button>
          <Link
            to={`/projects/${project?.id || 'demo'}/floorplans`}
            className="btn btn-primary btn-sm"
            style={{ fontSize: '11px' }}
          >
            ← 2D Floorplans
          </Link>
        </div>
      </div>

      {/* Main Architectural Viewport */}
      <div className="gallery-hero-viewport" style={{ position: 'relative', overflow: 'hidden', minHeight: '480px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#04060a' }}>
        {cadStyle === 'blender' ? (
          <div style={{ position: 'relative', width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px' }}>
            <img
              src={activeSlot.imageUrl || '/renders/01_FRONT.png'}
              alt={activeSlot.name}
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                objectFit: 'contain',
                borderRadius: '6px',
                boxShadow: '0 15px 40px rgba(0,0,0,0.85), 0 0 0 1px rgba(255,255,255,0.08)',
              }}
            />
            {/* Viewport HUD */}
            <div style={{
              position: 'absolute',
              top: '28px',
              left: '28px',
              background: 'rgba(10, 14, 23, 0.85)',
              backdropFilter: 'blur(8px)',
              padding: '6px 14px',
              borderRadius: '6px',
              border: '1px solid rgba(255,255,255,0.1)',
            }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#fed7aa' }}>
                🟠 Blender 4.5 Render · {activeSlot.slot} {activeSlot.name}
              </div>
              <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)', marginTop: '2px' }}>
                {activeSlot.angle} | Lens: {activeSlot.lens} | 1280 × 720 PNG
              </div>
            </div>

            <a
              href={activeSlot.imageUrl || '/renders/01_FRONT.png'}
              download={`Zynora_${activeSlot.slot}_${activeSlot.name.replace(/\s+/g, '_')}.png`}
              style={{
                position: 'absolute',
                bottom: '28px',
                right: '28px',
                background: 'rgba(10, 14, 23, 0.85)',
                backdropFilter: 'blur(8px)',
                border: '1px solid rgba(255,255,255,0.15)',
                padding: '6px 14px',
                borderRadius: '4px',
                color: '#fff',
                fontSize: '11px',
                fontWeight: 600,
                textDecoration: 'none',
              }}
            >
              📥 Save High-Res PNG
            </a>
          </div>
        ) : (
          <svg
            ref={svgRef}
            viewBox="0 0 920 500"
            width="100%"
            height="100%"
            style={{ background: isBlueprint ? '#0a192f' : '#0e1017', transition: 'background 0.3s ease' }}
            xmlns="http://www.w3.org/2000/svg"
          >
          <defs>
            {/* Blueprint Grid Pattern */}
            <pattern id="cadGrid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke={isBlueprint ? 'rgba(0, 229, 255, 0.07)' : 'rgba(255, 255, 255, 0.03)'} strokeWidth="0.5"/>
            </pattern>
            <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#151924" />
              <stop offset="70%" stopColor="#1e2433" />
              <stop offset="100%" stopColor="#302d28" />
            </linearGradient>
            <linearGradient id="wallLight" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#e8e4da" />
              <stop offset="100%" stopColor="#c8c2b5" />
            </linearGradient>
            <linearGradient id="woodLight" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#b37f48" />
              <stop offset="100%" stopColor="#7a4f27" />
            </linearGradient>
          </defs>

          {/* Background Grid */}
          <rect width="100%" height="100%" fill="url(#cadGrid)" />

          {/* Shaded Backdrop / Ground Plinth */}
          {!isBlueprint && (
            <>
              <rect width="100%" height="360" fill="url(#skyGrad)" opacity="0.4" />
              {/* Natural Ground Line */}
              <rect y="360" width="100%" height="140" fill="#141720" />
              <line x1="0" y1="360" x2="920" y2="360" stroke="#c8a96e" strokeWidth="1" opacity="0.6" />
            </>
          )}

          {/* Blueprint Ground Reference */}
          {isBlueprint && (
            <>
              <line x1="0" y1="360" x2="920" y2="360" stroke="#00e5ff" strokeWidth="1.5" />
              <text x="30" y="380" fill="#00e5ff" fontSize="9" fontFamily="monospace">±0.00m NATURAL GROUND LEVEL (NGL)</text>
            </>
          )}

          {/* Structural Column Grids (A, B, C, D) */}
          {showGrids && (
            <g opacity={isBlueprint ? 0.6 : 0.35}>
              <line x1="220" y1="50" x2="220" y2="360" stroke={isBlueprint ? '#00e5ff' : '#c8a96e'} strokeWidth="0.8" strokeDasharray="6 3 2 3" />
              <circle cx="220" cy="40" r="11" fill="none" stroke={isBlueprint ? '#00e5ff' : '#c8a96e'} strokeWidth="1" />
              <text x="220" y="44" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} fontSize="10" fontWeight="bold" textAnchor="middle" fontFamily="monospace">A</text>

              <line x1="380" y1="50" x2="380" y2="360" stroke={isBlueprint ? '#00e5ff' : '#c8a96e'} strokeWidth="0.8" strokeDasharray="6 3 2 3" />
              <circle cx="380" cy="40" r="11" fill="none" stroke={isBlueprint ? '#00e5ff' : '#c8a96e'} strokeWidth="1" />
              <text x="380" y="44" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} fontSize="10" fontWeight="bold" textAnchor="middle" fontFamily="monospace">B</text>

              <line x1="560" y1="50" x2="560" y2="360" stroke={isBlueprint ? '#00e5ff' : '#c8a96e'} strokeWidth="0.8" strokeDasharray="6 3 2 3" />
              <circle cx="560" cy="40" r="11" fill="none" stroke={isBlueprint ? '#00e5ff' : '#c8a96e'} strokeWidth="1" />
              <text x="560" y="44" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} fontSize="10" fontWeight="bold" textAnchor="middle" fontFamily="monospace">C</text>

              <line x1="720" y1="50" x2="720" y2="360" stroke={isBlueprint ? '#00e5ff' : '#c8a96e'} strokeWidth="0.8" strokeDasharray="6 3 2 3" />
              <circle cx="720" cy="40" r="11" fill="none" stroke={isBlueprint ? '#00e5ff' : '#c8a96e'} strokeWidth="1" />
              <text x="720" y="44" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} fontSize="10" fontWeight="bold" textAnchor="middle" fontFamily="monospace">D</text>
            </g>
          )}

          {/* Level Datum Annotations (Left Side) */}
          {showDimensions && (
            <g opacity={isBlueprint ? 0.9 : 0.75} fontFamily="monospace" fontSize="8.5">
              {/* +8.50m Roof Parapet */}
              <line x1="90" y1="130" x2="830" y2="130" stroke={isBlueprint ? '#00e5ff' : '#888'} strokeWidth="0.5" strokeDasharray="2 4" />
              <polygon points="100,130 115,124 115,136" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} />
              <text x="122" y="133" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} fontWeight="bold">▲ +8.50m ROOF PARAPET</text>

              {/* +6.00m First Floor Level */}
              <line x1="90" y1="210" x2="830" y2="210" stroke={isBlueprint ? '#00e5ff' : '#888'} strokeWidth="0.5" strokeDasharray="2 4" />
              <polygon points="100,210 115,204 115,216" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} />
              <text x="122" y="213" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} fontWeight="bold">▲ +6.00m FIRST FLOOR SLAB (FFL)</text>

              {/* +3.00m Ground Floor Ceiling */}
              <line x1="90" y1="285" x2="830" y2="285" stroke={isBlueprint ? '#00e5ff' : '#888'} strokeWidth="0.5" strokeDasharray="2 4" />
              <polygon points="100,285 115,279 115,291" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} />
              <text x="122" y="288" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} fontWeight="bold">▲ +3.00m GROUND CEILING</text>

              {/* +0.60m Plinth Level */}
              <line x1="90" y1="340" x2="830" y2="340" stroke={isBlueprint ? '#00e5ff' : '#888'} strokeWidth="0.5" strokeDasharray="2 4" />
              <polygon points="100,340 115,334 115,346" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} />
              <text x="122" y="343" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} fontWeight="bold">▲ +0.60m PLINTH LEVEL (Vastu Plinth)</text>
            </g>
          )}

          {/* ── CAD ELEVATION GEOMETRY PER SLOT ─────────────────────────────────── */}
          {activeSlot.slot === '01' ? (
            // 01 — Front Hero Perspective (Three-Quarter Isometric CAD Projection)
            <g transform="translate(180, 110)">
              {/* Ground Shadow */}
              {!isBlueprint && <ellipse cx="270" cy="250" rx="260" ry="18" fill="rgba(0,0,0,0.6)" />}

              {/* Plinth Base */}
              <polygon
                points="70,250 70,230 390,230 390,250"
                fill={isBlueprint ? 'none' : '#222633'}
                stroke={isBlueprint ? '#00e5ff' : '#3a4055'}
                strokeWidth={isBlueprint ? 1.5 : 2}
              />

              {/* Lower Concrete / Travertine Wall Massing */}
              <polygon
                points="80,230 80,120 280,110 380,140 380,230 280,235"
                fill={isBlueprint ? 'rgba(0, 229, 255, 0.05)' : 'url(#wallLight)'}
                stroke={isBlueprint ? '#00e5ff' : '#1a1c24'}
                strokeWidth="2"
              />

              {/* Double-Glazed Structural Ribbon Window */}
              <polygon
                points="110,225 110,140 250,132 250,228"
                fill={isBlueprint ? 'rgba(0, 229, 255, 0.15)' : '#263a56'}
                stroke={isBlueprint ? '#00e5ff' : '#0f141f'}
                strokeWidth="2"
              />
              {/* Window Mullions */}
              <line x1="156" y1="138" x2="156" y2="226" stroke={isBlueprint ? '#00e5ff' : '#141e2e'} strokeWidth="1.5" />
              <line x1="203" y1="135" x2="203" y2="227" stroke={isBlueprint ? '#00e5ff' : '#141e2e'} strokeWidth="1.5" />

              {/* Cantilevered Nilambur Teak Master Suite Volume */}
              <polygon
                points="200,140 200,45 440,30 490,65 490,160 380,140"
                fill={isBlueprint ? 'rgba(0, 229, 255, 0.08)' : 'url(#woodLight)'}
                stroke={isBlueprint ? '#00e5ff' : '#1a1c24'}
                strokeWidth="2"
              />

              {/* Teak Vertical Louvers (Solar Shading Fins) */}
              {[220, 240, 260, 280, 300, 320, 340, 360, 380, 400, 420].map((lx) => (
                <line
                  key={lx}
                  x1={lx}
                  y1={44 + (lx - 200) * -0.07}
                  x2={lx}
                  y2={138 + (lx - 200) * 0.01}
                  stroke={isBlueprint ? '#00e5ff' : 'rgba(60, 35, 15, 0.7)'}
                  strokeWidth="1.5"
                />
              ))}

              {/* Glass Balustrade */}
              <polygon
                points="340,150 470,165 470,130 340,120"
                fill={isBlueprint ? 'rgba(0, 229, 255, 0.2)' : 'rgba(74, 127, 200, 0.45)'}
                stroke={isBlueprint ? '#00e5ff' : '#c8a96e'}
                strokeWidth="1.5"
              />

              {/* Cantilevered Portico Roof & Parapet Edge */}
              <polygon
                points="190,45 450,28 500,65 240,75"
                fill={isBlueprint ? 'none' : '#202330'}
                stroke={isBlueprint ? '#00e5ff' : '#0f1117'}
                strokeWidth="2"
              />
            </g>
          ) : activeSlot.slot === '02' ? (
            // 02 — Front Left Elevation (Portico & Car Arrival)
            <g transform="translate(170, 115)">
              {!isBlueprint && <ellipse cx="280" cy="245" rx="270" ry="18" fill="rgba(0,0,0,0.6)" />}
              {/* Plinth */}
              <rect x="50" y="230" width="390" height="18" fill={isBlueprint ? 'none' : '#222633'} stroke={isBlueprint ? '#00e5ff' : '#3a4055'} strokeWidth="1.5" />

              {/* Ground Car Portico & Verandah Volume */}
              <polygon
                points="50,230 50,135 200,125 320,145 320,230"
                fill={isBlueprint ? 'rgba(0, 229, 255, 0.05)' : 'url(#wallLight)'}
                stroke={isBlueprint ? '#00e5ff' : '#1a1c24'}
                strokeWidth="2"
              />

              {/* Upper Floor Volume */}
              <polygon
                points="150,140 150,55 380,45 440,75 440,165 320,145"
                fill={isBlueprint ? 'rgba(0, 229, 255, 0.08)' : 'url(#woodLight)'}
                stroke={isBlueprint ? '#00e5ff' : '#1a1c24'}
                strokeWidth="2"
              />

              {/* Car Portico Bay Opening */}
              <rect
                x="60" y="160" width="110" height="70"
                fill={isBlueprint ? 'rgba(0, 229, 255, 0.1)' : '#1a1c24'}
                stroke={isBlueprint ? '#00e5ff' : '#c8a96e'}
                strokeWidth="1.5"
              />

              {/* Entrance Doorway */}
              <rect
                x="220" y="150" width="55" height="80"
                fill={isBlueprint ? 'none' : '#2b1a0d'}
                stroke={isBlueprint ? '#00e5ff' : '#c8a96e'}
                strokeWidth="1.5"
              />
            </g>
          ) : activeSlot.slot === '03' ? (
            // 03 — Front Straight (Orthographic Symmetrical CAD Elevation)
            <g transform="translate(190, 110)">
              {!isBlueprint && <ellipse cx="270" cy="250" rx="270" ry="18" fill="rgba(0,0,0,0.6)" />}

              {/* Ground Plinth */}
              <rect x="60" y="230" width="420" height="18" fill={isBlueprint ? 'none' : '#222633'} stroke={isBlueprint ? '#00e5ff' : '#3a4055'} strokeWidth="1.5" />

              {/* Ground Floor Main Wall */}
              <rect
                x="70" y="125" width="400" height="105"
                fill={isBlueprint ? 'rgba(0, 229, 255, 0.05)' : 'url(#wallLight)'}
                stroke={isBlueprint ? '#00e5ff' : '#1a1c24'}
                strokeWidth="2"
              />

              {/* Upper Floor Teak Volume */}
              <rect
                x="110" y="45" width="320" height="80"
                fill={isBlueprint ? 'rgba(0, 229, 255, 0.08)' : 'url(#woodLight)'}
                stroke={isBlueprint ? '#00e5ff' : '#1a1c24'}
                strokeWidth="2"
              />

              {/* Teak Vertical Louvers */}
              {[130, 150, 170, 190, 210, 230, 250, 270, 290, 310, 330, 350, 370, 390, 410].map((lx) => (
                <line key={lx} x1={lx} y1={46} x2={lx} y2={124} stroke={isBlueprint ? '#00e5ff' : 'rgba(60, 35, 15, 0.6)'} strokeWidth="1.5" />
              ))}

              {/* Symmetrical Window Bands */}
              <rect x="130" y="65" width="90" height="45" fill={isBlueprint ? 'rgba(0, 229, 255, 0.15)' : '#263a56'} stroke={isBlueprint ? '#00e5ff' : '#0f141f'} strokeWidth="1.5" />
              <rect x="320" y="65" width="90" height="45" fill={isBlueprint ? 'rgba(0, 229, 255, 0.15)' : '#263a56'} stroke={isBlueprint ? '#00e5ff' : '#0f141f'} strokeWidth="1.5" />

              {/* Central Main Entrance Doorway (East-facing auspicious threshold) */}
              <rect x="235" y="145" width="70" height="85" fill={isBlueprint ? 'none' : '#2b1a0d'} stroke={isBlueprint ? '#00e5ff' : '#c8a96e'} strokeWidth="2" />
              <text x="270" y="195" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} fontSize="7" textAnchor="middle" fontFamily="monospace">MAIN ENTRY</text>

              {/* Dimension Callout Arrow */}
              {showDimensions && (
                <g>
                  <line x1="70" y1="260" x2="470" y2="260" stroke={isBlueprint ? '#00e5ff' : '#c8a96e'} strokeWidth="1" />
                  <line x1="70" y1="255" x2="70" y2="265" stroke={isBlueprint ? '#00e5ff' : '#c8a96e'} strokeWidth="1" />
                  <line x1="470" y1="255" x2="470" y2="265" stroke={isBlueprint ? '#00e5ff' : '#c8a96e'} strokeWidth="1" />
                  <text x="270" y="272" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} fontSize="9" textAnchor="middle" fontFamily="monospace">
                    FRONT ELEVATION SPAN: 12.19m (40 ft 0 in)
                  </text>
                </g>
              )}
            </g>
          ) : activeSlot.slot === '04' ? (
            // 04 — Right Side Profile (East Flank & Balcony)
            <g transform="translate(190, 110)">
              {!isBlueprint && <ellipse cx="270" cy="250" rx="270" ry="18" fill="rgba(0,0,0,0.6)" />}
              <rect x="60" y="230" width="420" height="18" fill={isBlueprint ? 'none' : '#222633'} stroke={isBlueprint ? '#00e5ff' : '#3a4055'} strokeWidth="1.5" />

              {/* Long Side Elevation */}
              <rect
                x="60" y="125" width="410" height="105"
                fill={isBlueprint ? 'rgba(0, 229, 255, 0.05)' : 'url(#wallLight)'}
                stroke={isBlueprint ? '#00e5ff' : '#1a1c24'}
                strokeWidth="2"
              />

              {/* Cantilever Upper Profile */}
              <rect
                x="160" y="45" width="310" height="80"
                fill={isBlueprint ? 'rgba(0, 229, 255, 0.08)' : 'url(#woodLight)'}
                stroke={isBlueprint ? '#00e5ff' : '#1a1c24'}
                strokeWidth="2"
              />

              {/* Private Balcony Glass */}
              <rect
                x="360" y="65" width="90" height="40"
                fill={isBlueprint ? 'rgba(0, 229, 255, 0.2)' : 'rgba(74, 127, 200, 0.5)'}
                stroke={isBlueprint ? '#00e5ff' : '#c8a96e'}
                strokeWidth="1.5"
              />

              {/* Side Depth Dimension */}
              {showDimensions && (
                <g>
                  <line x1="60" y1="260" x2="470" y2="260" stroke={isBlueprint ? '#00e5ff' : '#c8a96e'} strokeWidth="1" />
                  <line x1="60" y1="255" x2="60" y2="265" stroke={isBlueprint ? '#00e5ff' : '#c8a96e'} strokeWidth="1" />
                  <line x1="470" y1="255" x2="470" y2="265" stroke={isBlueprint ? '#00e5ff' : '#c8a96e'} strokeWidth="1" />
                  <text x="265" y="272" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} fontSize="9" textAnchor="middle" fontFamily="monospace">
                    SIDE PLOT DEPTH: 18.28m (60 ft 0 in)
                  </text>
                </g>
              )}
            </g>
          ) : (
            // 05 — Left Side Elevation (West Service Flank)
            <g transform="translate(190, 110)">
              {!isBlueprint && <ellipse cx="270" cy="250" rx="270" ry="18" fill="rgba(0,0,0,0.6)" />}
              <rect x="60" y="230" width="420" height="18" fill={isBlueprint ? 'none' : '#222633'} stroke={isBlueprint ? '#00e5ff' : '#3a4055'} strokeWidth="1.5" />

              {/* Thermal Massing Wall (Western orientation reduces solar heat gain) */}
              <rect
                x="60" y="125" width="410" height="105"
                fill={isBlueprint ? 'rgba(0, 229, 255, 0.05)' : 'url(#wallLight)'}
                stroke={isBlueprint ? '#00e5ff' : '#1a1c24'}
                strokeWidth="2"
              />
              <rect
                x="60" y="45" width="280" height="80"
                fill={isBlueprint ? 'rgba(0, 229, 255, 0.08)' : 'url(#woodLight)'}
                stroke={isBlueprint ? '#00e5ff' : '#1a1c24'}
                strokeWidth="2"
              />

              {/* Clerestory Windows (High Ribbon for Daylight without heat) */}
              <rect
                x="90" y="60" width="220" height="22"
                fill={isBlueprint ? 'rgba(0, 229, 255, 0.2)' : '#263a56'}
                stroke={isBlueprint ? '#00e5ff' : '#0f141f'}
                strokeWidth="1.5"
              />

              {/* Service Entry Doorway */}
              <rect
                x="370" y="160" width="45" height="70"
                fill={isBlueprint ? 'none' : '#1a1c24'}
                stroke={isBlueprint ? '#00e5ff' : '#c8a96e'}
                strokeWidth="1.5"
              />
              <text x="392" y="198" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} fontSize="6" textAnchor="middle" fontFamily="monospace">UTILITY</text>
            </g>
          )}

          {/* Architectural Drawing Title Block (Bottom Right) */}
          <g transform="translate(620, 410)">
            <rect
              width="270"
              height="70"
              fill={isBlueprint ? 'rgba(10, 25, 47, 0.95)' : 'rgba(14, 16, 23, 0.95)'}
              stroke={isBlueprint ? '#00e5ff' : 'rgba(200, 169, 110, 0.4)'}
              strokeWidth="1"
            />
            <text x="14" y="20" fill={isBlueprint ? '#00e5ff' : 'var(--accent)'} fontSize="10" fontWeight="bold" fontFamily="monospace">
              ZYNORA-ML CAD DRAWING SHEET
            </text>
            <text x="14" y="36" fill="rgba(255,255,255,0.7)" fontSize="8.5" fontFamily="monospace">
              PROJ: {project?.name?.toUpperCase() || 'ANANYA VILLA · CHENNAI'}
            </text>
            <text x="14" y="50" fill="rgba(255,255,255,0.7)" fontSize="8.5" fontFamily="monospace">
              VIEW: {activeSlot.slot} · {activeSlot.name.toUpperCase()}
            </text>
            <text x="14" y="64" fill="rgba(255,255,255,0.4)" fontSize="7.5" fontFamily="monospace">
              SCALE: 1:100 (METRIC) · ORIENTATION: {project?.location?.orientation || 'EAST'}
            </text>
          </g>

          {/* Viewport Info Watermark (Top Left) */}
          <text x="30" y="42" fill={isBlueprint ? '#00e5ff' : 'rgba(255,255,255,0.9)'} fontSize="13" fontWeight="bold" letterSpacing="1" fontFamily="monospace">
            VIEW {activeSlot.slot}: {activeSlot.name.toUpperCase()}
          </text>
          <text x="30" y="58" fill={isBlueprint ? '#00e5ff' : '#c8a96e'} fontSize="9.5" fontFamily="monospace">
            {activeSlot.angle} · {activeSlot.elevation} · {activeSlot.lens}
          </text>
          <text x="30" y="74" fill="rgba(255,255,255,0.45)" fontSize="8.5" fontFamily="monospace">
            SOLAR TRAJECTORY: {activeSlot.sunPosition}
          </text>
        </svg>
        )}

        {/* Top Floating Badge */}
        <div style={{ position: 'absolute', top: '1rem', right: '1.5rem', display: 'flex', gap: '8px' }}>
          <Badge variant="success">Parametric CAD Viewport</Badge>
          <span className="badge badge-info">{activeSlot.lens}</span>
        </div>
      </div>

      {/* Five Exterior Views Thumbnail Selector */}
      <div style={{ marginTop: '1.5rem' }}>
        <div className="flex justify-between items-center mb-4 flex-wrap gap-3">
          <div>
            <span className="section-label">Coordinated Architectural Projections</span>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>5 Standard CAD Elevation Perspectives</h3>
            <p className="text-xs text-muted">
              Select any CAD viewport below to inspect elevation geometry, roof lines, fenestration spans, and datum heights.
            </p>
          </div>
          <Link to={`/projects/${project?.id || 'demo'}/floorplans`} className="btn btn-outline btn-sm">
            ← Back to Floorplans
          </Link>
        </div>

        <div className="gallery-slots-grid">
          {DEMO_EXTERIOR_VIEWS.map((view) => (
            <ViewSlot
              key={view.slot}
              view={view}
              isActive={activeSlot.slot === view.slot}
              onSelect={setActiveSlot}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
