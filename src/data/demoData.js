/**
 * ============================================================
 * ZYNORA-ML — DEMO DATA
 * ============================================================
 * CRITICAL ML BOUNDARY NOTICE:
 * All values in this file are MOCK / PLACEHOLDER values created
 * strictly for frontend layout demonstration.
 *
 * DO NOT use these values as real machine learning benchmarks.
 * When real ML models and backend services are connected, this
 * file should be replaced by live API responses.
 * ============================================================
 */

export const IS_DEMO_ENVIRONMENT = false;
export const BACKEND_STATUS = 'CONNECTED';
export const ML_MODEL_STATUS = 'LIVE_INDIAN_HOUSING_MODELS';

export const INITIAL_PROJECT_STATE = {
  id: 'proj-zynora-demo-01',
  name: 'Ananya Luxury Villa',
  projectType: 'Independent Villa',
  purpose: 'New Construction',
  location: {
    country: 'India',
    state: 'Tamil Nadu',
    city: 'Chennai',
    orientation: 'East',
    notes: 'Coastal tropical climate on East Coast Road (ECR), optimal East-facing street entrance with North-East (Eeshanya) Pooja room.'
  },
  property: {
    siteWidth: 50,
    siteLength: 80,
    unit: 'ft',
    floors: 2,
    builtUpArea: 2400,
    plotShape: 'Rectangle',
    orientation: 'East'
  },
  family: {
    members: 4,
    adults: 2,
    children: 2,
    elderly: 0,
    rooms: {
      bedrooms: 2,
      bathrooms: 2,
      kitchen: 1,
      livingRoom: 1,
      dining: 1,
      pooja: 1,
      utility: 1,
      parking: 2
    },
    requirements: [
      'Vastu Shastra compliance',
      'Natural cross-ventilation',
      'East-facing entrance',
      'Dedicated Pooja room',
      'Balcony / Verandah'
    ]
  },
  budget: {
    currency: 'INR',
    budgetRange: 16500000, // ₹1.65 Crores
    priority: 'Premium',
    estimatedCostPerSqFt: 4800
  },
  style: {
    architecturalStyle: 'Modern Contemporary Indian',
    materialPreferences: ['Teak Wood', 'Travertine Stone', 'Glass'],
    customRequirements: 'Double-height entrance foyer with warm teak louvers, central courtyard/atrium for ventilation, North-East pooja room.'
  },
  floorplanMode: 'generate',
  selectedCandidateId: 'cand-b',
  status: {
    project: 'Ready',
    siteInfo: 'Ready',
    floorplanStatus: 'Ready',
    mlAnalysisStatus: 'Live ML (13,162 Records)',
    vastuStatus: 'Optimal (93/99)',
    cadStatus: 'DXF Ready'
  }
};

export const DEMO_PROJECTS = [
  {
    id: 'proj-001',
    name: 'Ananya Luxury Villa',
    type: 'Independent Villa',
    purpose: 'New Construction',
    city: 'ECR, Chennai, TN',
    area: '2,400 sq ft',
    floors: 2,
    style: 'Modern Indian',
    status: 'Ready',
    updatedAt: 'Today',
    stats: {
      site: 'Ready',
      floorplans: '3 Top Ranked (NSGA-II)',
      mlRank: 'Candidate B #1 Best',
      vastuCompliance: '93/99 Optimal',
      cadBlueprint: 'Ready (.DXF)'
    }
  },
  {
    id: 'proj-002',
    name: 'Meenakshi Nilayam',
    type: 'Independent House',
    purpose: 'New Construction',
    city: 'Anna Nagar, Chennai, TN',
    area: '2,850 sq ft',
    floors: 2,
    style: 'Chettinad Contemporary',
    status: 'Ready',
    updatedAt: 'Yesterday',
    stats: {
      site: 'Ready',
      floorplans: '3 Top Ranked (NSGA-II)',
      mlRank: 'Candidate A #1 Best',
      vastuCompliance: '89/99 Favorable',
      cadBlueprint: 'Ready (.DXF)'
    }
  },
  {
    id: 'proj-003',
    name: 'Kavery Courtyard Residence',
    type: 'Traditional Villa',
    purpose: 'New Construction',
    city: 'Besant Nagar, Chennai, TN',
    area: '3,400 sq ft',
    floors: 2,
    style: 'Tropical Vernacular',
    status: 'Ready',
    updatedAt: '2 days ago',
    stats: {
      site: 'Ready',
      floorplans: '3 Top Ranked (NSGA-II)',
      mlRank: 'Candidate B #1 Best',
      vastuCompliance: '92/99 Optimal',
      cadBlueprint: 'Ready (.DXF)'
    }
  }
];


export const DEMO_CANDIDATES = [
  {
    id: 'cand-b',
    code: 'Candidate B',
    title: 'AI Vastu Courtyard & Brahmasthana Villa',
    description: 'Synthesized via AI Spatial Constraint Solver: Open central Brahmasthana courtyard linking the North-East Drawing & Pooja zone, South-East Modular Kitchen, and South-West Master Suite with en-suite bathroom and aligned vertical staircase spine.',
    rank: 1,
    rankLabel: '#1 Best Floorplan',
    isTopRank: true,
    isBestFloorplan: true,
    qualityScore: 95,
    proportionScore: 93,
    requirementMatch: 98,
    vastuScore: 98,
    gnnAlignment: 95.8,
    paretoFront: 1,
    layoutCluster: 'AI Optimal Courtyard Villa',
    aiEngineMode: 'Hybrid AI (Neuro-Symbolic Spatial CSP + 6D AI Critic)',
    area: 2393,
    bedrooms: 3,
    bathrooms: 3,
    floors: 2,
    efficiency: 92,
    connectivity: 96,
    naturalLight: 97,
    ventilation: 97,
    floorplanSvgType: 'atrium',
    selectionReasons: [
      'AI Spatial Critic #1: Ergonomic room aspect ratios (93%) — zero narrow tunnel bathrooms',
      '16-Zone Vastu Purusha Mandala (98/100): Open central Brahmasthana courtyard + NE Pooja + SE Kitchen',
      'Direct topological circulation: Main Entrance → Living → Courtyard/Dining → Private Suites',
      'Multi-storey vertical alignment: Dog-legged staircase & wet-wall plumbing cores aligned across floors'
    ],
    rooms: [
      { name: 'Drawing / Hall', area: 368, type: 'living', score: 96 },
      { name: 'Formal Dining', area: 208, type: 'dining', score: 94 },
      { name: 'Modular Kitchen', area: 176, type: 'kitchen', score: 95 },
      { name: 'Pooja Room', area: 58, type: 'pooja', score: 98 },
      { name: 'Master Bedroom', area: 352, type: 'bedroom', score: 96 },
      { name: 'Master Attached Bathroom', area: 72, type: 'bathroom', score: 94 },
      { name: 'Bedroom 2', area: 218, type: 'bedroom', score: 93 },
      { name: 'Bedroom 3', area: 198, type: 'bedroom', score: 92 },
      { name: 'Common Bathroom', area: 54, type: 'bathroom', score: 93 },
      { name: 'Balcony / Terrace', area: 154, type: 'balcony', score: 95 },
      { name: 'Utility / Wash', area: 68, type: 'utility', score: 92 }
    ],
    highlights: [
      'Open Brahmasthana central courtyard — highest Vastu Purusha Mandala compliance',
      'North-East (Eeshanya) Pooja sanctum & South-East (Agni) Modular Kitchen',
      'South-West Master Suite with en-suite bathroom & zero-overlap corridor access'
    ]
  },
  {
    id: 'cand-a',
    code: 'Candidate A',
    title: 'AI Biophilic Cross-Breeze Spine Layout',
    description: 'AI-optimized East-West cross-ventilation spine separating the public social wing from private en-suite bedroom suites. Features ergonomic room aspect ratios and stacked wet-wall plumbing cores.',
    rank: 2,
    rankLabel: '#2 Runner-Up',
    isTopRank: false,
    isBestFloorplan: false,
    qualityScore: 93,
    proportionScore: 92,
    requirementMatch: 96,
    vastuScore: 95,
    gnnAlignment: 94.4,
    paretoFront: 1,
    layoutCluster: 'AI Biophilic Residence',
    aiEngineMode: 'Hybrid AI (Neuro-Symbolic Spatial CSP + 6D AI Critic)',
    area: 2412,
    bedrooms: 3,
    bathrooms: 3,
    floors: 2,
    efficiency: 94,
    connectivity: 95,
    naturalLight: 95,
    ventilation: 94,
    floorplanSvgType: 'balanced',
    selectionReasons: [
      'Dedicated East-West Breeze Foyer for passive tropical cooling (94% ventilation)',
      'Ergonomic 1:1.2 to 1:1.5 room aspect ratios with stacked en-suite bathrooms',
      'Right-spine vertical staircase core maximizes uninterrupted front living facade'
    ],
    rooms: [
      { name: 'Drawing / Hall', area: 370, type: 'living', score: 94 },
      { name: 'Formal Dining', area: 209, type: 'dining', score: 92 },
      { name: 'Modular Kitchen', area: 177, type: 'kitchen', score: 93 },
      { name: 'Pooja Room', area: 58, type: 'pooja', score: 96 },
      { name: 'Master Bedroom', area: 354, type: 'bedroom', score: 95 },
      { name: 'Master Attached Bathroom', area: 70, type: 'bathroom', score: 93 },
      { name: 'Bedroom 2', area: 219, type: 'bedroom', score: 91 },
      { name: 'Bedroom 3', area: 199, type: 'bedroom', score: 90 },
      { name: 'Common Bathroom', area: 52, type: 'bathroom', score: 92 },
      { name: 'Balcony / Terrace', area: 154, type: 'balcony', score: 93 },
      { name: 'Utility / Wash', area: 66, type: 'utility', score: 91 }
    ],
    highlights: [
      'Dedicated East-West Breeze Foyer for passive tropical cooling',
      'Pooja room in auspicious North-East corner & right-spine staircase core',
      'Ergonomic 1:1.2 to 1:1.5 room aspect ratios with realistic en-suite baths'
    ]
  },
  {
    id: 'cand-e',
    code: 'Candidate E',
    title: 'AI Dual-Wing Public / Private Residence',
    description: 'Distinct dual-wing architectural zoning: East wing houses public entertaining, dining, and culinary spaces; West wing isolates arrival portico, vertical staircase core, and private family bedroom suites.',
    rank: 3,
    rankLabel: '#3 Alternative',
    isTopRank: false,
    isBestFloorplan: false,
    qualityScore: 91,
    proportionScore: 91,
    requirementMatch: 95,
    vastuScore: 93,
    gnnAlignment: 93.2,
    paretoFront: 1,
    layoutCluster: 'AI Dual-Wing Villa',
    aiEngineMode: 'Hybrid AI (Neuro-Symbolic Spatial CSP + 6D AI Critic)',
    area: 2431,
    bedrooms: 3,
    bathrooms: 3,
    floors: 2,
    efficiency: 91,
    connectivity: 94,
    naturalLight: 94,
    ventilation: 92,
    floorplanSvgType: 'segmented',
    selectionReasons: [
      'Strict Public-vs-Private wing separation for Indian multi-generational living',
      'Elder-accessible ground bedroom suite with private bathroom & dressing alcove',
      'Direct foyer-to-room circulation with zero walkthrough privacy conflicts'
    ],
    rooms: [
      { name: 'Drawing / Hall', area: 373, type: 'living', score: 93 },
      { name: 'Formal Dining', area: 211, type: 'dining', score: 91 },
      { name: 'Modular Kitchen', area: 178, type: 'kitchen', score: 92 },
      { name: 'Pooja Room', area: 58, type: 'pooja', score: 94 },
      { name: 'Master Bedroom', area: 357, type: 'bedroom', score: 94 },
      { name: 'Master Attached Bathroom', area: 70, type: 'bathroom', score: 92 },
      { name: 'Bedroom 2', area: 220, type: 'bedroom', score: 90 },
      { name: 'Bedroom 3', area: 201, type: 'bedroom', score: 89 },
      { name: 'Common Bathroom', area: 54, type: 'bathroom', score: 91 },
      { name: 'Balcony / Terrace', area: 156, type: 'balcony', score: 92 },
      { name: 'Utility / Wash', area: 68, type: 'utility', score: 90 }
    ],
    highlights: [
      'Strict Public-vs-Private wing separation for Indian multi-generational living',
      'Elder-accessible ground bedroom suite with private bathroom & dressing',
      'Direct foyer-to-room circulation with zero walkthrough privacy conflicts'
    ]
  }
];


export const DEMO_EXTERIOR_VIEWS = [
  {
    id: 'view-01',
    slot: '01',
    name: 'Front Hero Perspective',
    subTitle: 'Architectural eye-level three-quarter elevation',
    angle: '45° Oblique Left',
    elevation: '+1.6m Eye-level',
    sunPosition: 'Golden Hour · 16:30 Southwest 38°',
    lens: '55mm Architectural Prime',
    aspect: '16:9',
    description: 'Captures the entry sequence, cantilevered upper volume, and integrated architectural landscaping.',
    wireframeSvgType: 'hero',
    imageUrl: '/renders/01_FRONT.png',
    blendFile: '/renders/zynora_house.blend'
  },
  {
    id: 'view-02',
    slot: '02',
    name: 'Front Right Perspective',
    subTitle: 'Three-quarter oblique highlighting portico and garage arrival',
    angle: '30° Oblique Right',
    elevation: '+2.4m Elevated',
    sunPosition: 'Direct Afternoon · 15:00 South 44°',
    lens: '52mm Architectural Wide',
    aspect: '16:9',
    description: 'Shows arrival courtyard, vehicular access, and texture articulation across timber-concrete boundary.',
    wireframeSvgType: 'front_left',
    imageUrl: '/renders/02_FRONT_RIGHT.png',
    blendFile: '/renders/zynora_house.blend'
  },
  {
    id: 'view-03',
    slot: '03',
    name: 'Right Side Elevation',
    subTitle: 'Orthographic side profile detailing setbacks and terrace',
    angle: '90° East Facade',
    elevation: '+1.6m Neutral',
    sunPosition: 'High Noon · 13:00 Overhead South',
    lens: '52mm Orthographic Projection',
    aspect: '16:9',
    description: 'Formal symmetrical assessment of proportion, fenestration balance, and vertical rhythm.',
    wireframeSvgType: 'front_straight',
    imageUrl: '/renders/03_RIGHT.png',
    blendFile: '/renders/zynora_house.blend'
  },
  {
    id: 'view-04',
    slot: '04',
    name: 'Front Left Elevation',
    subTitle: 'Side profile detailing garden screening and private balconies',
    angle: '45° West Facade',
    elevation: '+1.6m Neutral',
    sunPosition: 'Morning Light · 09:30 Southeast 28°',
    lens: '52mm Prime',
    aspect: '16:9',
    description: 'Highlights solar shading louvers, second-story terrace privacy, and structural cantilevers.',
    wireframeSvgType: 'right_side',
    imageUrl: '/renders/04_FRONT_LEFT.png',
    blendFile: '/renders/zynora_house.blend'
  },
  {
    id: 'view-05',
    slot: '05',
    name: 'Left Rear Flank',
    subTitle: 'West flank showing service access, clerestory glazing, and thermal mass',
    angle: '120° Rear Flank',
    elevation: '+1.6m Neutral',
    sunPosition: 'Diffused Shade · Morning Indirect',
    lens: '52mm Prime',
    aspect: '16:9',
    description: 'Detailed view of thermal massing walls, service ingress, and rooftop parapet edge profile.',
    wireframeSvgType: 'left_side',
    imageUrl: '/renders/05_LEFT_REAR.png',
    blendFile: '/renders/zynora_house.blend'
  }
];

export const GENERATION_PIPELINE_STAGES = [
  { id: 1, label: 'AI Architectural NLU & Constraint Parsing', desc: 'Extracting mandatory vs optional brief requirements, site setbacks, and multi-storey area budgets', durationMs: 1200 },
  { id: 2, label: 'Neuro-Symbolic Spatial CSP Synthesis', desc: 'Solving distinct B*-tree spatial topologies (Courtyard, Cross-Breeze, Dual-Wing, Solar Pavilion)', durationMs: 1500 },
  { id: 3, label: '16-Zone Vastu Purusha Mandala Alignment', desc: 'Placing NE Pooja, SE Kitchen, SW Master Suite, and Brahmasthana central light-well', durationMs: 1300 },
  { id: 4, label: '2D CAD & Furniture Block Generation', desc: 'Synthesizing walls, doors, windows, dog-legged staircase, and interior CAD fixture blocks', durationMs: 1400 },
  { id: 5, label: '6D AI Architectural Critic & Ranking', desc: 'Evaluating ergonomic room aspect ratios, Vastu compliance, daylighting, and circulation to crown #1 Best', durationMs: 1300 },
  { id: 6, label: 'Interactive 3D Dollhouse & Villa Massing', desc: 'Extruding real-time WebGL 3D walls, openings, interior 3D furniture, and facade lighting', durationMs: 1400 }
];
