"""
ZYNORA-ML — Pydantic Schemas
Defines all payload models for projects, spatial graphs, candidates, ML metrics, 3D meshes, and ArchViz views.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class LocationData(BaseModel):
    country: str = "India"
    state: str = "Tamil Nadu"
    city: str = "Chennai"
    orientation: str = "East"
    notes: Optional[str] = None

class PropertyData(BaseModel):
    siteWidth: float = 40.0
    siteLength: float = 60.0
    unit: str = "ft"
    floors: int = 2
    builtUpArea: float = 2400.0
    plotShape: str = "Rectangle"
    orientation: str = "East"

class RoomCounts(BaseModel):
    bedrooms: int = 3
    bathrooms: int = 3
    kitchen: int = 1
    livingRoom: int = 1
    dining: int = 1
    pooja: int = 1
    study: int = 0
    utility: int = 1
    parking: int = 1

class FamilyData(BaseModel):
    members: int = 4
    adults: int = 2
    children: int = 1
    elderly: int = 1
    rooms: RoomCounts = Field(default_factory=RoomCounts)
    requirements: List[str] = Field(default_factory=lambda: ["Vastu Shastra Compliance", "Cross Ventilation", "Natural Lighting"])

class BudgetData(BaseModel):
    currency: str = "INR"
    budgetRange: float = 16500000.0  # ₹1.65 Crores
    priority: str = "Premium"
    estimatedCostPerSqFt: Optional[float] = 5200.0

class StyleData(BaseModel):
    architecturalStyle: str = "Modern Contemporary Indian"
    materialPreferences: List[str] = Field(default_factory=lambda: ["Teak Wood", "Travertine Stone", "Glass"])
    customRequirements: Optional[str] = None

class ProjectCreate(BaseModel):
    name: str = "Ananya Luxury Villa · ECR, Chennai"
    projectType: str = "Villa"
    purpose: str = "New Construction"
    location: LocationData = Field(default_factory=LocationData)
    property: PropertyData = Field(default_factory=PropertyData)
    family: FamilyData = Field(default_factory=FamilyData)
    budget: BudgetData = Field(default_factory=BudgetData)
    style: StyleData = Field(default_factory=StyleData)
    floorplanMode: str = "generate"

class RoomAllocation(BaseModel):
    name: str
    area: float
    type: str
    score: float
    polygon: Optional[List[List[float]]] = None

class CandidateFloorplan(BaseModel):
    id: str
    code: str
    title: str
    description: str
    isTopRank: bool = False
    qualityScore: int
    requirementMatch: int
    area: float
    bedrooms: int
    bathrooms: float
    floors: int
    efficiency: int
    connectivity: int
    naturalLight: int
    ventilation: int
    floorplanSvgType: str
    rooms: List[RoomAllocation]
    highlights: List[str]
    svgBlueprint: Optional[str] = None

class MLAnalysisResponse(BaseModel):
    candidateId: str
    efficiencyScore: int
    connectivityScore: int
    lightingScore: int
    ventilationScore: int
    roomClassification: List[RoomAllocation]
    modelName: str = "Zynora-SpatialGNN-v1"
    confidence: str = "96.4% Pareto Confidence"
    anomaliesDetected: List[str] = Field(default_factory=list)

class MLRankResponse(BaseModel):
    ranking: List[Dict[str, Any]]
    rankingEngine: str = "Pareto-MultiObjective-NSGA-II"
    dominantCandidateId: str

class MeshGeometry(BaseModel):
    candidateId: str
    vertices: List[List[float]]
    faces: List[List[int]]
    levels: int
    footprintArea: float
    grossVolume: float
    materials: List[Dict[str, str]]

class ArchVizView(BaseModel):
    slot: str
    name: str
    subTitle: str
    angle: str
    elevation: str
    sunPosition: str
    lens: str
    aspect: str
    description: str
    imageUrl: str
    imageDataUri: Optional[str] = None

class RenderStatusResponse(BaseModel):
    renderJobId: str
    status: str
    progress: int
    views: List[ArchVizView]
