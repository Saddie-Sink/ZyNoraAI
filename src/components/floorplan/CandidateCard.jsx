import React from 'react';
import { True2DCandidatePreview } from './EditableFloorplanCanvas';

/**
 * Indian Residential Floor Plan SVG Renderer
 * ===========================================
 * Dynamically renders architectural floor plans tailored to the user's BHK:
 *   - 2 BHK: Drawing/Hall, Modular Kitchen, Pooja Room (🪔 NE corner),
 *            Formal Dining, Master Bedroom + Attached Bath,
 *            Bedroom 2 + Common Bath, Balcony / Verandah, Utility
 *   - 3 BHK / 4 BHK: Includes additional bedrooms & private suites
 *
 * All room areas are dynamically pulled from the ML backend (RPLAN priors).
 */

const ROOM_COLORS = {
  living:   { fill: 'rgba(200,169,110,0.12)', stroke: '#c8a96e', label: '#c8a96e' },
  dining:   { fill: 'rgba(180,160,120,0.10)', stroke: '#b4a078', label: '#b4a078' },
  kitchen:  { fill: 'rgba(120,180,140,0.12)', stroke: '#78b48c', label: '#78b48c' },
  pooja:    { fill: 'rgba(255,200,80,0.18)',  stroke: '#ffc850', label: '#ffc850' }, // sacred gold
  bedroom:  { fill: 'rgba(100,140,200,0.10)', stroke: '#6490c8', label: '#8ab0e0' },
  bathroom: { fill: 'rgba(80,160,180,0.08)',  stroke: '#50a0b4', label: '#70c0d0' },
  balcony:  { fill: 'rgba(80,200,120,0.08)',  stroke: '#50c878', label: '#70d890' },
  utility:  { fill: 'rgba(140,140,140,0.08)', stroke: '#8c8c8c', label: '#aaaaaa' },
  default:  { fill: 'rgba(160,160,160,0.06)', stroke: '#a0a0a0', label: '#c0c0c0' },
};

const ROOM_SHORT = {
  'Drawing / Hall':           'DRAWING / HALL',
  'Formal Dining':            'DINING',
  'Modular Kitchen':          'KITCHEN',
  'Pooja Room':               '🪔 POOJA',
  'Master Bedroom':           'MASTER BED',
  'Master Attached Bathroom': 'M. BATH',
  'Bedroom 2':                'BEDROOM 2',
  'Bedroom 3':                'BEDROOM 3',
  'Bedroom 4 / Guest Room':   'BED 4',
  'Common Bathroom':          'COMMON BATH',
  'Common Bathrooms (2)':     'BATHS (2)',
  'Balcony / Terrace':        'BALCONY',
  'Utility / Servant Quarter':'UTILITY',
};

function Room({ x, y, w, h, name, type, sqft, fontSize = 6.5 }) {
  const c = ROOM_COLORS[type] || ROOM_COLORS.default;
  const short = ROOM_SHORT[name] || (name ? name.toUpperCase().slice(0, 13) : 'ROOM');
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} fill={c.fill} stroke={c.stroke} strokeWidth="1" rx="1.5" />
      <text
        x={x + w / 2}
        y={y + h / 2 - (sqft ? 3 : 0)}
        fill={c.label}
        fontSize={fontSize}
        fontWeight="600"
        textAnchor="middle"
        dominantBaseline="middle"
        fontFamily="monospace"
      >
        {short}
      </text>
      {sqft && (
        <text
          x={x + w / 2}
          y={y + h / 2 + 7}
          fill="rgba(255,255,255,0.35)"
          fontSize="5"
          textAnchor="middle"
          dominantBaseline="middle"
        >
          {sqft} sqft
        </text>
      )}
    </g>
  );
}

function getArea(rooms, name) {
  if (!rooms || !rooms.length || !name) return null;
  // 1. Exact match
  let r = rooms.find(r => r.name === name);
  if (r?.area) return r.area;

  // 2. Partial / case-insensitive search
  const lower = name.toLowerCase();
  r = rooms.find(r => r.name && (r.name.toLowerCase().includes(lower) || lower.includes(r.name.toLowerCase())));
  if (r?.area) return r.area;

  // 3. Fallbacks by room type
  if (lower.includes('bath')) {
    const baths = rooms.filter(r => r.type === 'bathroom');
    if (baths.length > 0) return baths[0].area;
  }
  if (lower.includes('bed') || lower.includes('study') || lower.includes('guest')) {
    const beds = rooms.filter(r => r.type === 'bedroom');
    if (beds.length > 0) return beds[beds.length - 1].area;
  }
  return null;
}

// ── 2 BHK DEDICATED LAYOUTS ───────────────────────────────────────────────────

function Balanced2BHKSVG({ rooms, area }) {
  return (
    <svg viewBox="0 0 280 185" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <rect width="280" height="185" fill="#0a0a0a" />
      <rect x="14" y="12" width="252" height="161" fill="none" stroke="#4a4a4a" strokeWidth="2.5" />
      <text x="258" y="18" fill="rgba(200,169,110,0.6)" fontSize="7" fontWeight="bold">N↑</text>

      {/* Row 1: Drawing/Hall | Pooja (NE) | Master Bedroom */}
      <Room x={14}  y={12} w={120} h={64} name="Drawing / Hall"           type="living"   sqft={getArea(rooms, 'Drawing / Hall')} fontSize={6} />
      <Room x={134} y={12} w={56}  h={32} name="Pooja Room"               type="pooja"    sqft={getArea(rooms, 'Pooja Room')} fontSize={5.8} />
      <Room x={190} y={12} w={76}  h={64} name="Master Bedroom"           type="bedroom"  sqft={getArea(rooms, 'Master Bedroom')} fontSize={6} />

      {/* Row 2: Kitchen | Dining | Common Bath | Master Attached Bath */}
      <Room x={14}  y={76} w={66}  h={48} name="Modular Kitchen"          type="kitchen"  sqft={getArea(rooms, 'Modular Kitchen')} fontSize={5.5} />
      <Room x={80}  y={76} w={54}  h={48} name="Formal Dining"            type="dining"   sqft={getArea(rooms, 'Formal Dining')} fontSize={5.5} />
      <Room x={134} y={44} w={56}  h={36} name="Common Bathroom"          type="bathroom" sqft={getArea(rooms, 'Common Bathroom')} fontSize={5} />
      <Room x={190} y={76} w={76}  h={26} name="Master Attached Bathroom" type="bathroom" sqft={getArea(rooms, 'Master Attached Bathroom')} fontSize={4.8} />

      {/* Row 3: Balcony | Bedroom 2 | Utility */}
      <Room x={14}  y={124} w={120} h={49} name="Balcony / Terrace"       type="balcony"  sqft={getArea(rooms, 'Balcony / Terrace')} fontSize={5.8} />
      <Room x={134} y={102} w={76}  h={71} name="Bedroom 2"                type="bedroom"  sqft={getArea(rooms, 'Bedroom 2')} fontSize={6} />
      <Room x={210} y={102} w={56}  h={71} name="Utility / Servant Quarter" type="utility" sqft={getArea(rooms, 'Utility / Servant Quarter')} fontSize={5} />

      <text x="14" y="180" fill="rgba(200,169,110,0.5)" fontSize="6" fontFamily="monospace">
        BALANCED 2 BHK · {area?.toLocaleString()} SQ FT · 2 BATHS
      </text>
    </svg>
  );
}

function Atrium2BHKSVG({ rooms, area }) {
  return (
    <svg viewBox="0 0 280 185" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <rect width="280" height="185" fill="#0a0a0a" />
      <rect x="14" y="12" width="252" height="161" fill="none" stroke="#4a4a4a" strokeWidth="2.5" />
      <text x="258" y="18" fill="rgba(200,169,110,0.6)" fontSize="7" fontWeight="bold">N↑</text>

      {/* Central Atrium / Brahmasthana */}
      <rect x="96" y="58" width="88" height="64" fill="rgba(80,200,120,0.08)" stroke="#50c878" strokeWidth="1.5" strokeDasharray="3 2" rx="2" />
      <text x="140" y="86" fill="#50c878" fontSize="7.5" fontWeight="bold" textAnchor="middle" fontFamily="monospace">BRAHMASTHANA</text>
      <text x="140" y="96" fill="#50c878" fontSize="6" textAnchor="middle" fontFamily="monospace">OPEN ATRIUM</text>
      <text x="140" y="106" fill="rgba(80,200,120,0.4)" fontSize="5" textAnchor="middle">🌿 central courtyard</text>

      {/* Pooja in NE */}
      <Room x={184} y={12}  w={82} h={34} name="Pooja Room"               type="pooja"    sqft={getArea(rooms, 'Pooja Room')} fontSize={6} />
      {/* Living left */}
      <Room x={14}  y={12}  w={82} h={58} name="Drawing / Hall"           type="living"   sqft={getArea(rooms, 'Drawing / Hall')} fontSize={5.8} />
      <Room x={96}  y={12}  w={88} h={46} name="Formal Dining"            type="dining"   sqft={getArea(rooms, 'Formal Dining')} fontSize={5.5} />
      <Room x={14}  y={70}  w={82} h={46} name="Modular Kitchen"          type="kitchen"  sqft={getArea(rooms, 'Modular Kitchen')} fontSize={5.5} />
      <Room x={14}  y={116} w={82} h={57} name="Balcony / Terrace"       type="balcony"  sqft={getArea(rooms, 'Balcony / Terrace')} fontSize={5.5} />

      {/* Master right */}
      <Room x={184} y={46}  w={82} h={56} name="Master Bedroom"           type="bedroom"  sqft={getArea(rooms, 'Master Bedroom')} fontSize={6} />
      <Room x={184} y={102} w={82} h={48} name="Bedroom 2"                type="bedroom"  sqft={getArea(rooms, 'Bedroom 2')} fontSize={6} />

      {/* Bottom Baths & Utility */}
      <Room x={96}  y={122} w={44} h={51} name="Master Attached Bathroom" type="bathroom" sqft={null} fontSize={4.8} />
      <Room x={140} y={122} w={44} h={51} name="Common Bathroom"          type="bathroom" sqft={null} fontSize={4.8} />
      <Room x={184} y={150} w={82} h={23} name="Utility / Servant Quarter" type="utility" sqft={null} fontSize={4.5} />

      <text x="14" y="180" fill="rgba(80,200,120,0.5)" fontSize="6" fontFamily="monospace">
        CENTRAL ATRIUM 2 BHK · {area?.toLocaleString()} SQ FT · 2 BATHS
      </text>
    </svg>
  );
}

function Linear2BHKSVG({ rooms, area }) {
  return (
    <svg viewBox="0 0 280 185" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <rect width="280" height="185" fill="#0a0a0a" />
      <rect x="14" y="12" width="252" height="161" fill="none" stroke="#4a4a4a" strokeWidth="2.5" />
      <text x="258" y="18" fill="rgba(200,169,110,0.6)" fontSize="7" fontWeight="bold">N↑</text>

      {/* Top Grand Zone: Living + Dining + Pooja + Kitchen */}
      <Room x={14}  y={12} w={136} h={54} name="Drawing / Hall"           type="living"   sqft={getArea(rooms, 'Drawing / Hall')} fontSize={6} />
      <Room x={150} y={12} w={64}  h={54} name="Formal Dining"            type="dining"   sqft={getArea(rooms, 'Formal Dining')} fontSize={5.5} />
      <Room x={214} y={12} w={52}  h={28} name="Pooja Room"               type="pooja"    sqft={getArea(rooms, 'Pooja Room')} fontSize={5.5} />
      <Room x={214} y={40} w={52}  h={26} name="Modular Kitchen"          type="kitchen"  sqft={getArea(rooms, 'Modular Kitchen')} fontSize={5} />

      {/* Middle Zone: Master Bedroom & Bedroom 2 with Baths */}
      <Room x={14}  y={66} w={96}  h={54} name="Master Bedroom"           type="bedroom"  sqft={getArea(rooms, 'Master Bedroom')} fontSize={6} />
      <Room x={110} y={66} w={44}  h={54} name="Master Attached Bathroom" type="bathroom" sqft={null} fontSize={4.8} />
      <Room x={154} y={66} w={76}  h={54} name="Bedroom 2"                type="bedroom"  sqft={getArea(rooms, 'Bedroom 2')} fontSize={5.8} />
      <Room x={230} y={66} w={36}  h={54} name="Common Bathroom"          type="bathroom" sqft={null} fontSize={4.8} />

      {/* Bottom Zone: Expansive Balcony + Utility */}
      <Room x={14}  y={120} w={176} h={53} name="Balcony / Terrace"       type="balcony"  sqft={getArea(rooms, 'Balcony / Terrace')} fontSize={6} />
      <Room x={190} y={120} w={76}  h={53} name="Utility / Servant Quarter" type="utility" sqft={getArea(rooms, 'Utility / Servant Quarter')} fontSize={5} />

      <text x="14" y="180" fill="rgba(80,200,120,0.5)" fontSize="6" fontFamily="monospace">
        LINEAR N-S PAVILION 2 BHK · {area?.toLocaleString()} SQ FT · 2 BATHS
      </text>
    </svg>
  );
}

function Compact2BHKSVG({ rooms, area }) {
  return (
    <svg viewBox="0 0 280 185" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <rect width="280" height="185" fill="#0a0a0a" />
      <rect x="14" y="12" width="252" height="161" fill="none" stroke="#4a4a4a" strokeWidth="2.5" />
      <text x="258" y="18" fill="rgba(200,169,110,0.6)" fontSize="7" fontWeight="bold">N↑</text>

      {/* Compact High-Efficiency Grid */}
      <Room x={14}  y={12} w={124} h={54} name="Drawing / Hall"           type="living"   sqft={getArea(rooms, 'Drawing / Hall')} fontSize={6} />
      <Room x={138} y={12} w={60}  h={32} name="Pooja Room"               type="pooja"    sqft={getArea(rooms, 'Pooja Room')} fontSize={5.5} />
      <Room x={198} y={12} w={68}  h={54} name="Master Bedroom"           type="bedroom"  sqft={getArea(rooms, 'Master Bedroom')} fontSize={6} />

      <Room x={14}  y={66} w={68}  h={46} name="Modular Kitchen"          type="kitchen"  sqft={getArea(rooms, 'Modular Kitchen')} fontSize={5.5} />
      <Room x={82}  y={66} w={56}  h={46} name="Formal Dining"            type="dining"   sqft={getArea(rooms, 'Formal Dining')} fontSize={5.5} />
      <Room x={138} y={44} w={60}  h={36} name="Common Bathroom"          type="bathroom" sqft={null} fontSize={4.8} />
      <Room x={198} y={66} w={68}  h={24} name="Master Attached Bathroom" type="bathroom" sqft={null} fontSize={4.8} />
      <Room x={138} y={80} w={60}  h={46} name="Bedroom 2"                type="bedroom"  sqft={getArea(rooms, 'Bedroom 2')} fontSize={5.8} />

      <Room x={14}  y={112} w={184} h={61} name="Balcony / Terrace"       type="balcony"  sqft={getArea(rooms, 'Balcony / Terrace')} fontSize={6} />
      <Room x={198} y={90}  w={68}  h={83} name="Utility / Servant Quarter" type="utility" sqft={getArea(rooms, 'Utility / Servant Quarter')} fontSize={5} />

      <text x="14" y="180" fill="rgba(140,140,140,0.5)" fontSize="6" fontFamily="monospace">
        COMPACT GRID 2 BHK · {area?.toLocaleString()} SQ FT · 2 BATHS
      </text>
    </svg>
  );
}

function Segmented2BHKSVG({ rooms, area }) {
  return (
    <svg viewBox="0 0 280 185" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <rect width="280" height="185" fill="#0a0a0a" />
      <rect x="14" y="12" width="252" height="161" fill="none" stroke="#4a4a4a" strokeWidth="2.5" />
      <text x="258" y="18" fill="rgba(200,169,110,0.6)" fontSize="7" fontWeight="bold">N↑</text>

      {/* Divider */}
      <line x1="154" y1="12" x2="154" y2="173" stroke="#4a4a4a" strokeWidth="2.5" />

      {/* PUBLIC ZONE (left) */}
      <text x="84" y="20" fill="rgba(200,169,110,0.5)" fontSize="5.5" textAnchor="middle" fontFamily="monospace">PUBLIC ZONE</text>
      <Room x={14} y={22} w={140} h={58} name="Drawing / Hall"    type="living"   sqft={getArea(rooms, 'Drawing / Hall')} fontSize={6} />
      <Room x={14} y={80} w={70}  h={46} name="Modular Kitchen"   type="kitchen"  sqft={getArea(rooms, 'Modular Kitchen')} fontSize={5.5} />
      <Room x={84} y={80} w={70}  h={46} name="Formal Dining"     type="dining"   sqft={getArea(rooms, 'Formal Dining')} fontSize={5.5} />
      <Room x={14} y={126} w={56} h={47} name="Pooja Room"        type="pooja"    sqft={getArea(rooms, 'Pooja Room')} fontSize={5.5} />
      <Room x={70} y={126} w={84} h={47} name="Balcony / Terrace" type="balcony"  sqft={getArea(rooms, 'Balcony / Terrace')} fontSize={5.5} />

      {/* PRIVATE ZONE (right) - ONLY 2 BEDROOMS */}
      <text x="214" y="20" fill="rgba(100,144,200,0.5)" fontSize="5.5" textAnchor="middle" fontFamily="monospace">PRIVATE ZONE</text>
      <Room x={154} y={22}  w={112} h={60} name="Master Bedroom"           type="bedroom"  sqft={getArea(rooms, 'Master Bedroom')} fontSize={6} />
      <Room x={154} y={82}  w={55}  h={28} name="Master Attached Bathroom" type="bathroom" sqft={null} fontSize={4.8} />
      <Room x={209} y={82}  w={57}  h={28} name="Common Bathroom"          type="bathroom" sqft={null} fontSize={4.8} />
      <Room x={154} y={110} w={112} h={48} name="Bedroom 2"                type="bedroom"  sqft={getArea(rooms, 'Bedroom 2')} fontSize={6} />
      <Room x={154} y={158} w={112} h={15} name="Utility / Servant Quarter" type="utility" sqft={null} fontSize={4.2} />

      <text x="14" y="180" fill="rgba(100,144,200,0.5)" fontSize="6" fontFamily="monospace">
        SEGMENTED PRIVACY 2 BHK · {area?.toLocaleString()} SQ FT · 2 BATHS
      </text>
    </svg>
  );
}

// ── 3/4 BHK LAYOUTS (EXISTING) ────────────────────────────────────────────────

function BalancedSVG({ rooms, area, bedrooms = 4 }) {
  const bed4Name = bedrooms >= 4 ? "Bedroom 4 / Guest Room" : "Family Study / Lounge";
  const bed4Type = bedrooms >= 4 ? "bedroom" : "utility";
  return (
    <svg viewBox="0 0 280 185" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <rect width="280" height="185" fill="#0a0a0a" />
      <rect x="14" y="12" width="252" height="161" fill="none" stroke="#4a4a4a" strokeWidth="2.5" />
      <text x="258" y="18" fill="rgba(200,169,110,0.5)" fontSize="7" fontWeight="bold">N↑</text>
      <rect x={208} y={12} width={58} height={38} fill="rgba(255,200,80,0.08)" stroke="#ffc850" strokeWidth="0.8" strokeDasharray="2 2" />

      <Room x={14}  y={12} w={90} h={52} name="Drawing / Hall"           type="living"   sqft={getArea(rooms,'Drawing / Hall')} />
      <Room x={104} y={12} w={46} h={38} name="Formal Dining"            type="dining"   sqft={getArea(rooms,'Formal Dining')} fontSize={5.5}/>
      <Room x={150} y={12} w={58} h={22} name="Pooja Room"               type="pooja"    sqft={getArea(rooms,'Pooja Room')} fontSize={6}/>
      <Room x={208} y={12} w={58} h={38} name="Master Bedroom"           type="bedroom"  sqft={getArea(rooms,'Master Bedroom')} fontSize={5.5}/>

      <Room x={14}  y={64} w={62} h={42} name="Modular Kitchen"          type="kitchen"  sqft={getArea(rooms,'Modular Kitchen')} fontSize={5.5}/>
      <Room x={76}  y={64} w={28} h={42} name="Master Attached Bathroom" type="bathroom" sqft={null} fontSize={5}/>
      <Room x={104} y={50} w={46} h={56} name="Common Bathrooms (2)"     type="bathroom" sqft={getArea(rooms,'Common Bathrooms (2)')} fontSize={5}/>
      <Room x={150} y={34} w={58} h={72} name="Bedroom 2"                type="bedroom"  sqft={getArea(rooms,'Bedroom 2')} fontSize={5.5}/>
      <Room x={208} y={50} w={58} h={56} name="Bedroom 3"                type="bedroom"  sqft={getArea(rooms,'Bedroom 3')} fontSize={5.5}/>

      <Room x={14}  y={106} w={90} h={67} name={bed4Name}                type={bed4Type} sqft={getArea(rooms, bed4Name)} fontSize={5.5}/>
      <Room x={104} y={106} w={104} h={67} name="Balcony / Terrace"       type="balcony"  sqft={getArea(rooms,'Balcony / Terrace')} fontSize={5.5}/>
      <Room x={208} y={106} w={58} h={67} name="Utility / Servant Quarter" type="utility" sqft={getArea(rooms,'Utility / Servant Quarter')} fontSize={5}/>

      <text x="14" y="180" fill="rgba(200,169,110,0.5)" fontSize="6" fontFamily="monospace">
        BALANCED BIOPHILIC · {area?.toLocaleString()} SQ FT · {bedrooms} BHK
      </text>
    </svg>
  );
}

function AtriumSVG({ rooms, area, bedrooms = 4 }) {
  const bed4Name = bedrooms >= 4 ? "Bedroom 4 / Guest Room" : "Family Lounge";
  const bed4Type = bedrooms >= 4 ? "bedroom" : "living";
  return (
    <svg viewBox="0 0 280 185" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <rect width="280" height="185" fill="#0a0a0a" />
      <rect x="14" y="12" width="252" height="161" fill="none" stroke="#4a4a4a" strokeWidth="2.5" />
      <text x="258" y="18" fill="rgba(200,169,110,0.5)" fontSize="7" fontWeight="bold">N↑</text>

      <rect x="96" y="64" width="88" height="64" fill="rgba(80,200,120,0.08)" stroke="#50c878" strokeWidth="1.5" strokeDasharray="3 2" rx="2"/>
      <text x="140" y="90" fill="#50c878" fontSize="7.5" fontWeight="bold" textAnchor="middle" fontFamily="monospace">BRAHMASTHANA</text>
      <text x="140" y="100" fill="#50c878" fontSize="6" textAnchor="middle" fontFamily="monospace">OPEN ATRIUM</text>

      <Room x={184} y={12}  w={82} h={32} name="Pooja Room"               type="pooja"    sqft={getArea(rooms,'Pooja Room')} fontSize={6}/>
      <Room x={14}  y={12}  w={82} h={52} name="Drawing / Hall"           type="living"   sqft={getArea(rooms,'Drawing / Hall')} fontSize={5.5}/>
      <Room x={96}  y={12}  w={88} h={32} name="Formal Dining"            type="dining"   sqft={getArea(rooms,'Formal Dining')} fontSize={5.5}/>
      <Room x={14}  y={64}  w={82} h={38} name="Modular Kitchen"          type="kitchen"  sqft={getArea(rooms,'Modular Kitchen')} fontSize={5.5}/>
      <Room x={14}  y={102} w={82} h={71} name="Master Bedroom"           type="bedroom"  sqft={getArea(rooms,'Master Bedroom')} fontSize={5.5}/>

      <Room x={184} y={44}  w={82} h={42} name="Bedroom 2"                type="bedroom"  sqft={getArea(rooms,'Bedroom 2')} fontSize={5.5}/>
      <Room x={184} y={86}  w={82} h={42} name="Bedroom 3"                type="bedroom"  sqft={getArea(rooms,'Bedroom 3')} fontSize={5.5}/>
      <Room x={184} y={128} w={82} h={45} name={bed4Name}                type={bed4Type} sqft={getArea(rooms, bed4Name)} fontSize={5}/>

      <Room x={96}  y={128} w={44} h={45} name="Common Bathrooms (2)"     type="bathroom" sqft={null} fontSize={5}/>
      <Room x={140} y={128} w={44} h={45} name="Utility / Servant Quarter" type="utility" sqft={null} fontSize={5}/>

      <text x="14" y="180" fill="rgba(80,200,120,0.5)" fontSize="6" fontFamily="monospace">
        CENTRAL ATRIUM · {area?.toLocaleString()} SQ FT · {bedrooms} BHK
      </text>
    </svg>
  );
}

function LinearSVG({ rooms, area, bedrooms = 4 }) {
  const bed4Name = bedrooms >= 4 ? "Bedroom 4 / Guest Room" : "Study Room";
  const bed4Type = bedrooms >= 4 ? "bedroom" : "utility";
  return (
    <svg viewBox="0 0 280 185" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <rect width="280" height="185" fill="#0a0a0a" />
      <rect x="14" y="12" width="252" height="161" fill="none" stroke="#4a4a4a" strokeWidth="2.5" />
      <text x="258" y="18" fill="rgba(200,169,110,0.5)" fontSize="7" fontWeight="bold">N↑</text>

      <Room x={14}  y={12} w={130} h={52} name="Drawing / Hall"           type="living"   sqft={getArea(rooms,'Drawing / Hall')} />
      <Room x={144} y={12} w={64}  h={52} name="Formal Dining"            type="dining"   sqft={getArea(rooms,'Formal Dining')} fontSize={5.5}/>
      <Room x={208} y={12} w={28}  h={28} name="Pooja Room"               type="pooja"    sqft={null} fontSize={5}/>
      <Room x={208} y={40} w={28}  h={24} name="Modular Kitchen"          type="kitchen"  sqft={null} fontSize={4.5}/>

      <Room x={14}  y={64} w={68}  h={48} name="Master Bedroom"           type="bedroom"  sqft={getArea(rooms,'Master Bedroom')} fontSize={5.5}/>
      <Room x={82}  y={64} w={32}  h={48} name="Master Attached Bathroom" type="bathroom" sqft={null} fontSize={4.5}/>
      <Room x={114} y={64} w={66}  h={48} name="Bedroom 2"                type="bedroom"  sqft={getArea(rooms,'Bedroom 2')} fontSize={5.5}/>
      <Room x={180} y={64} w={56}  h={48} name="Bedroom 3"                type="bedroom"  sqft={getArea(rooms,'Bedroom 3')} fontSize={5.5}/>
      <Room x={236} y={64} w={30}  h={48} name="Common Bathrooms (2)"     type="bathroom" sqft={null} fontSize={4.5}/>

      <Room x={14}  y={112} w={100} h={61} name="Balcony / Terrace"       type="balcony"  sqft={getArea(rooms,'Balcony / Terrace')} />
      <Room x={114} y={112} w={88}  h={61} name={bed4Name}                type={bed4Type} sqft={getArea(rooms, bed4Name)} fontSize={5.5}/>
      <Room x={202} y={112} w={64}  h={61} name="Utility / Servant Quarter" type="utility" sqft={null} fontSize={5}/>

      <text x="14" y="180" fill="rgba(80,200,120,0.5)" fontSize="6" fontFamily="monospace">
        LINEAR N-S PAVILION · {area?.toLocaleString()} SQ FT · {bedrooms} BHK
      </text>
    </svg>
  );
}

function CompactSVG({ rooms, area, bedrooms = 4 }) {
  const bed4Name = bedrooms >= 4 ? "Bedroom 4 / Guest Room" : "Work Alcove";
  const bed4Type = bedrooms >= 4 ? "bedroom" : "utility";
  return (
    <svg viewBox="0 0 280 185" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <rect width="280" height="185" fill="#0a0a0a" />
      <rect x="14" y="12" width="252" height="161" fill="none" stroke="#4a4a4a" strokeWidth="2.5" />
      <text x="258" y="18" fill="rgba(200,169,110,0.5)" fontSize="7" fontWeight="bold">N↑</text>

      <Room x={14}  y={12} w={100} h={50} name="Drawing / Hall"           type="living"   sqft={getArea(rooms,'Drawing / Hall')} fontSize={5.5}/>
      <Room x={114} y={12} w={68}  h={50} name="Master Bedroom"           type="bedroom"  sqft={getArea(rooms,'Master Bedroom')} fontSize={5.5}/>
      <Room x={182} y={12} w={84}  h={28} name="Pooja Room"               type="pooja"    sqft={getArea(rooms,'Pooja Room')} fontSize={5.5}/>
      <Room x={182} y={40} w={42}  h={22} name="Modular Kitchen"          type="kitchen"  sqft={null} fontSize={4.5}/>
      <Room x={224} y={40} w={42}  h={22} name="Formal Dining"            type="dining"   sqft={null} fontSize={4.5}/>

      <Room x={14}  y={62} w={50}  h={48} name="Bedroom 2"                type="bedroom"  sqft={getArea(rooms,'Bedroom 2')} fontSize={5}/>
      <Room x={64}  y={62} w={50}  h={48} name="Bedroom 3"                type="bedroom"  sqft={getArea(rooms,'Bedroom 3')} fontSize={5}/>
      <Room x={114} y={62} w={68}  h={48} name={bed4Name}                type={bed4Type} sqft={getArea(rooms, bed4Name)} fontSize={5}/>
      <Room x={182} y={62} w={42}  h={48} name="Master Attached Bathroom" type="bathroom" sqft={null} fontSize={4.5}/>
      <Room x={224} y={62} w={42}  h={48} name="Common Bathrooms (2)"     type="bathroom" sqft={null} fontSize={4.5}/>

      <Room x={14}  y={110} w={252} h={26} name="Balcony / Terrace"       type="balcony"  sqft={getArea(rooms,'Balcony / Terrace')} />
      <Room x={14}  y={136} w={126} h={37} name="Utility / Servant Quarter" type="utility" sqft={null} fontSize={5}/>
      <Room x={140} y={136} w={126} h={37} name="Formal Dining"           type="dining"   sqft={getArea(rooms,'Formal Dining')} fontSize={5}/>

      <text x="14" y="180" fill="rgba(140,140,140,0.5)" fontSize="6" fontFamily="monospace">
        COMPACT GRID · {area?.toLocaleString()} SQ FT · {bedrooms} BHK
      </text>
    </svg>
  );
}

function SegmentedSVG({ rooms, area, bedrooms = 4 }) {
  const bed4Name = bedrooms >= 4 ? "Bedroom 4 / Guest Room" : "Quiet Study";
  const bed4Type = bedrooms >= 4 ? "bedroom" : "study";
  return (
    <svg viewBox="0 0 280 185" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <rect width="280" height="185" fill="#0a0a0a" />
      <rect x="14" y="12" width="252" height="161" fill="none" stroke="#4a4a4a" strokeWidth="2.5" />
      <text x="258" y="18" fill="rgba(200,169,110,0.5)" fontSize="7" fontWeight="bold">N↑</text>

      <line x1="154" y1="12" x2="154" y2="173" stroke="#4a4a4a" strokeWidth="2.5" />

      <text x="84" y="20" fill="rgba(200,169,110,0.4)" fontSize="5.5" textAnchor="middle" fontFamily="monospace" letterSpacing="1">PUBLIC ZONE</text>
      <Room x={14}  y={22}  w={140} h={55} name="Drawing / Hall"          type="living"   sqft={getArea(rooms,'Drawing / Hall')} />
      <Room x={14}  y={77}  w={70}  h={44} name="Modular Kitchen"         type="kitchen"  sqft={getArea(rooms,'Modular Kitchen')} fontSize={5.5}/>
      <Room x={84}  y={77}  w={70}  h={44} name="Formal Dining"           type="dining"   sqft={getArea(rooms,'Formal Dining')} fontSize={5.5}/>
      <Room x={14}  y={121} w={50}  h={52} name="Pooja Room"              type="pooja"    sqft={getArea(rooms,'Pooja Room')} fontSize={5.5}/>
      <Room x={64}  y={121} w={90}  h={52} name="Balcony / Terrace"       type="balcony"  sqft={getArea(rooms,'Balcony / Terrace')} fontSize={5.5}/>

      <text x="221" y="20" fill="rgba(100,144,200,0.4)" fontSize="5.5" textAnchor="middle" fontFamily="monospace" letterSpacing="1">PRIVATE ZONE</text>
      <Room x={154} y={22}  w={112} h={54} name="Master Bedroom"          type="bedroom"  sqft={getArea(rooms,'Master Bedroom')} fontSize={5.5}/>
      <Room x={154} y={76}  w={55}  h={42} name="Bedroom 2"               type="bedroom"  sqft={getArea(rooms,'Bedroom 2')} fontSize={5}/>
      <Room x={209} y={76}  w={57}  h={42} name="Bedroom 3"               type="bedroom"  sqft={getArea(rooms,'Bedroom 3')} fontSize={5}/>
      <Room x={154} y={118} w={55}  h={42} name={bed4Name}                type={bed4Type} sqft={getArea(rooms, bed4Name)} fontSize={5}/>
      <Room x={209} y={118} w={57}  h={25} name="Common Bathrooms (2)"    type="bathroom" sqft={null} fontSize={4.5}/>
      <Room x={209} y={143} w={57}  h={17} name="Utility / Servant Quarter" type="utility" sqft={null} fontSize={4}/>
      <Room x={154} y={160} w={55}  h={13} name="Master Attached Bathroom" type="bathroom" sqft={null} fontSize={4}/>

      <text x="14" y="180" fill="rgba(100,144,200,0.5)" fontSize="6" fontFamily="monospace">
        SEGMENTED PRIVACY · {area?.toLocaleString()} SQ FT · {bedrooms} BHK
      </text>
    </svg>
  );
}

/** Dispatcher selecting 2BHK vs 3/4BHK SVG */
export function IndianFloorplanSVG({ typology, rooms = [], area, bedrooms = 2 }) {
  const is2BHK = (bedrooms <= 2) || (rooms.filter(r => r.type === 'bedroom').length <= 2);

  if (is2BHK) {
    if (typology === 'atrium') return <Atrium2BHKSVG rooms={rooms} area={area} />;
    if (typology === 'linear') return <Linear2BHKSVG rooms={rooms} area={area} />;
    if (typology === 'compact') return <Compact2BHKSVG rooms={rooms} area={area} />;
    if (typology === 'segmented') return <Segmented2BHKSVG rooms={rooms} area={area} />;
    return <Balanced2BHKSVG rooms={rooms} area={area} />;
  }

  if (typology === 'atrium') return <AtriumSVG rooms={rooms} area={area} bedrooms={bedrooms} />;
  if (typology === 'linear') return <LinearSVG rooms={rooms} area={area} bedrooms={bedrooms} />;
  if (typology === 'compact') return <CompactSVG rooms={rooms} area={area} bedrooms={bedrooms} />;
  if (typology === 'segmented') return <SegmentedSVG rooms={rooms} area={area} bedrooms={bedrooms} />;
  return <BalancedSVG rooms={rooms} area={area} bedrooms={bedrooms} />;
}


// ── Main CandidateCard component ──────────────────────────────────────────────
export default function CandidateCard({ candidate, isSelected, onSelect }) {
  const {
    id, code, title, area, bedrooms, bathrooms, floors,
    requirementMatch, qualityScore, isTopRank, floorplanSvgType,
    vastuScore, paretoFront, rooms = [], efficiency, naturalLight,
    ventilation, layoutCluster, rank, rankLabel, selectionReasons = [],
  } = candidate;

  const badgeText = isTopRank
    ? '★ #1 Best Floorplan'
    : (rankLabel || (rank ? `#${rank} Ranked` : null));

  return (
    <div
      className={`fp-card ${isSelected ? 'selected' : ''}`}
      style={isTopRank ? {
        borderColor: isSelected ? 'var(--accent)' : 'rgba(200, 169, 110, 0.55)',
        boxShadow: isSelected
          ? '0 10px 30px rgba(200, 169, 110, 0.22)'
          : '0 4px 18px rgba(200, 169, 110, 0.12)'
      } : undefined}
      onClick={() => onSelect && onSelect(id)}
      role="button"
      tabIndex={0}
      aria-label={`Select ${code}: ${title}`}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onSelect && onSelect(id); }}
    >
      {/* SVG Floor Plan Preview */}
      <div className="fp-card__preview">
        {candidate.floorsGeometry && candidate.floorsGeometry.length > 0 ? (
          <True2DCandidatePreview candidate={candidate} />
        ) : (
          <IndianFloorplanSVG
            typology={floorplanSvgType}
            rooms={rooms}
            area={area}
            bedrooms={bedrooms}
          />
        )}

        {/* Badges */}
        {badgeText && (
          <span
            style={{
              position: 'absolute',
              top: '8px',
              left: '8px',
              zIndex: 2,
              background: isTopRank ? 'rgba(16, 185, 129, 0.92)' : 'rgba(15, 23, 42, 0.85)',
              color: '#fff',
              border: isTopRank ? '1px solid #34d399' : '1px solid rgba(255,255,255,0.2)',
              fontWeight: 700,
              fontSize: '10px',
              padding: '3px 8px',
              borderRadius: '6px',
            }}
          >
            {badgeText}
          </span>
        )}
        {paretoFront && (
          <span style={{
            position: 'absolute', top: '8px', right: '8px', zIndex: 2,
            fontSize: '9px', padding: '2px 6px', borderRadius: '10px',
            background: paretoFront === 1 ? 'rgba(100,144,200,0.25)' : 'rgba(80,80,80,0.3)',
            color: paretoFront === 1 ? '#8ab0e0' : '#888',
            border: `1px solid ${paretoFront === 1 ? 'rgba(100,144,200,0.4)' : 'rgba(80,80,80,0.3)'}`,
            fontFamily: 'monospace',
          }}>
            Front {paretoFront}
          </span>
        )}
      </div>

      <div className="fp-card__body">
        <div className="fp-card__header">
          <div>
            <div className="text-xs uppercase tracking-widest text-accent font-semibold">
              {code} {isTopRank ? '· AI Best Pick' : ''}
            </div>
            <div className="fp-card__title">{title}</div>
            {layoutCluster && (
              <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', marginTop: '2px', fontFamily: 'monospace' }}>
                {layoutCluster}
              </div>
            )}
          </div>
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--accent-dark)', lineHeight: 1 }}>
              {qualityScore || '—'}
            </div>
            <div style={{ fontSize: '9px', textTransform: 'uppercase', color: 'rgba(255,255,255,0.4)' }}>AI Score</div>
          </div>
        </div>

        {/* Stats row: EXACT BEDROOMS & BATHROOMS */}
        <div className="fp-card__meta">
          <div><div className="fp-meta-item__val">{bedrooms}</div><div className="fp-meta-item__lbl">BHK</div></div>
          <div><div className="fp-meta-item__val">{bathrooms}</div><div className="fp-meta-item__lbl">Baths</div></div>
          <div><div className="fp-meta-item__val">{area?.toLocaleString()}</div><div className="fp-meta-item__lbl">Sq Ft</div></div>
          <div><div className="fp-meta-item__val">{floors}</div><div className="fp-meta-item__lbl">Floors</div></div>
        </div>

        {/* Vastu score — India specific */}
        {vastuScore && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <span style={{ fontSize: '10px', color: 'rgba(255,200,80,0.7)' }}>🪔 Vastu Mandala</span>
            <span style={{ fontSize: '11px', fontWeight: 600, color: '#ffc850', fontFamily: 'monospace' }}>
              {vastuScore}/99
            </span>
          </div>
        )}

        {/* AI objective chips */}
        {(efficiency || naturalLight || ventilation) && (
          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '8px' }}>
            {candidate.proportionScore && <Chip label="Prop" value={candidate.proportionScore} />}
            {efficiency   && <Chip label="Eff" value={efficiency} />}
            {naturalLight && <Chip label="Light" value={naturalLight} />}
            {ventilation  && <Chip label="Vent" value={ventilation} />}
          </div>
        )}

        {/* AI Requirement Fit Reason */}
        {selectionReasons.length > 0 && (
          <div style={{
            fontSize: '11px',
            color: 'var(--text-secondary)',
            background: isTopRank ? 'rgba(16, 185, 129, 0.08)' : 'var(--surface-alt)',
            border: isTopRank ? '1px solid rgba(16, 185, 129, 0.25)' : '1px solid var(--border-soft)',
            borderRadius: '6px',
            padding: '6px 8px',
            marginBottom: '8px',
            lineHeight: 1.35,
          }}>
            <strong style={{ color: isTopRank ? '#059669' : 'var(--accent-dark)' }}>
              {isTopRank ? '★ Why #1: ' : 'AI Fit: '}
            </strong>
            {selectionReasons[0]}
          </div>
        )}

        {/* Requirement match bar */}
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-muted">Brief Fidelity</span>
            <span className="font-semibold text-accent">{requirementMatch}%</span>
          </div>
          <div style={{ height: '3px', background: 'rgba(255,255,255,0.08)', borderRadius: '2px', overflow: 'hidden' }}>
            <div style={{ width: `${requirementMatch}%`, height: '100%', background: 'var(--accent)', borderRadius: '2px' }} />
          </div>
        </div>

        <button
          type="button"
          className={`btn ${isSelected ? 'btn-primary' : 'btn-outline'} btn-sm w-full`}
          style={{ marginTop: 'auto' }}
        >
          {isSelected
            ? (isTopRank ? '✓ #1 Best Layout Selected' : '✓ Active Selected Layout')
            : (isTopRank ? 'Select #1 Best Layout' : 'Select Layout')}
        </button>
      </div>
    </div>
  );
}

function Chip({ label, value }) {
  return (
    <div style={{
      display: 'flex', gap: '3px', alignItems: 'center',
      background: 'rgba(255,255,255,0.05)', borderRadius: '4px',
      padding: '2px 6px', fontSize: '9px', fontFamily: 'monospace',
    }}>
      <span style={{ color: 'rgba(255,255,255,0.4)' }}>{label}</span>
      <span style={{ color: 'var(--accent)', fontWeight: 700 }}>{value}</span>
    </div>
  );
}
