"""
ZYNORA AI — AI Layer Pydantic Schemas
======================================
Defines all structured schemas for Gemini NLU/Vision extraction,
conversational design operations, image floorplan analysis,
and AI orchestrator payloads.
"""
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field


# ─── Room Types ──────────────────────────────────────────────────────────────
RoomTypeLiteral = Literal[
    "living",
    "family_living",
    "drawing",
    "dining",
    "kitchen",
    "bedroom",
    "master_bedroom",
    "bathroom",
    "common_bathroom",
    "attached_bathroom",
    "pooja",
    "study",
    "office",
    "utility",
    "laundry",
    "store",
    "foyer",
    "staircase",
    "balcony",
    "terrace",
    "courtyard",
    "garage",
    "parking",
    "corridor",
    "guest_room",
]


class RoomItem(BaseModel):
    name: str = Field(description="Name or label of the room, e.g. 'Master Bedroom', 'Modular Kitchen'")
    type: str = Field(
        default="bedroom",
        description="Standardized room type: living, kitchen, bedroom, master_bedroom, bathroom, pooja, etc.",
    )
    count: int = Field(default=1, description="Quantity of this room type")
    preferred_width: Optional[float] = Field(default=None, description="Preferred width in user units (e.g. feet)")
    preferred_depth: Optional[float] = Field(default=None, description="Preferred depth/length in user units")
    minimum_area: Optional[float] = Field(default=None, description="Minimum carpet area required in sq units")
    floor_level: int = Field(default=0, description="0 for ground floor, 1 for first floor, etc.")
    adjacent_to: List[str] = Field(
        default_factory=list,
        description="Rooms this space should ideally connect to or be close to",
    )
    separated_from: List[str] = Field(
        default_factory=list,
        description="Rooms this space should be acoustically or visually isolated from",
    )
    en_suite_bathroom: bool = Field(default=False, description="True if an attached bathroom is requested")
    vastu_zone_preference: Optional[str] = Field(
        default=None, description="Preferred Vastu zone: NE, SE, SW, NW, N, S, E, W, Center"
    )


class AdjacencyRequirement(BaseModel):
    from_room: str = Field(description="Source room name or type")
    to_room: str = Field(description="Target room name or type")
    priority: Literal["mandatory", "preferred", "optional"] = "preferred"
    reason: Optional[str] = None


class SeparationRequirement(BaseModel):
    room_a: str = Field(description="First room")
    room_b: str = Field(description="Second room to keep private/isolated from First room")
    priority: Literal["mandatory", "preferred"] = "preferred"


class ParkingRequirement(BaseModel):
    required: bool = True
    car_count: int = 1
    type: Literal["covered", "open", "garage", "carport", "none"] = "covered"
    ev_charging: bool = False


class StaircaseRequirement(BaseModel):
    required: bool = True
    type: Literal["internal", "external", "dog_legged", "spiral", "floating", "any"] = "internal"
    location_preference: Optional[str] = None


class CourtyardRequirement(BaseModel):
    required: bool = False
    type: Literal["central_atrium", "side_garden", "open_to_sky", "none"] = "none"
    biophilic: bool = True


class BalconyRequirement(BaseModel):
    required: bool = True
    count: int = 1
    attached_to: List[str] = Field(default_factory=lambda: ["master_bedroom"])


class TerraceRequirement(BaseModel):
    required: bool = False
    covered_pergola: bool = False


class VastuPreference(BaseModel):
    enabled: bool = True
    strictness: Literal["strict", "moderate", "lenient", "none"] = "moderate"
    key_priorities: List[str] = Field(
        default_factory=lambda: [
            "Pooja in North-East (Eeshanya)",
            "Kitchen in South-East (Agni)",
            "Master Bedroom in South-West (Nairutya)",
            "Open Center (Brahmasthana)",
        ]
    )


class Design3DPreferences(BaseModel):
    exterior_style: Optional[str] = Field(
        default="modern",
        description="modern, contemporary, minimal, luxury, tropical, traditional, industrial, scandinavian",
    )
    interior_style: Optional[str] = Field(
        default="contemporary",
        description="modern, contemporary, minimal, luxury, tropical, scandinavian",
    )
    roof_style: Optional[str] = Field(default="flat", description="flat, sloping, pitched, pergola, terrace")
    wall_material: Optional[str] = Field(
        default="plaster",
        description="plaster, stone_cladding, exposed_brick, concrete, travertine, glass",
    )
    floor_material: Optional[str] = Field(
        default="hardwood",
        description="hardwood, herringbone_oak, marble, teak, slate_tile, granite",
    )
    window_style: Optional[str] = Field(
        default="casement",
        description="casement, sliding, floor_to_ceiling, louvered, jali",
    )
    door_style: Optional[str] = Field(default="flush", description="teak_paneled, flush, glass_sliding, pivot")
    lighting: Optional[str] = Field(
        default="day",
        description="morning, day, golden_hour, sunset, night",
    )
    render_style: Optional[str] = Field(
        default="photorealistic",
        description="architectural, photorealistic, minimal, luxury, tropical, contemporary",
    )


# ─── HouseRequirements (Root Extraction Model) ───────────────────────────────
class HouseRequirements(BaseModel):
    """
    Standardized, machine-readable architectural requirements model.
    Converts natural language into structured design parameters.
    Does NOT contain final wall coordinates.
    """
    project_name: str = Field(default="ZyNora Residence", description="Project title or identifier")
    plot_width: Optional[float] = Field(default=30.0, description="Plot frontage width in user units")
    plot_depth: Optional[float] = Field(default=40.0, description="Plot depth/length in user units")
    units: Literal["ft", "m"] = Field(default="ft", description="Measurement units (feet or meters)")
    orientation: str = Field(
        default="East",
        description="Main plot/entrance orientation: East, North, North-East, West, South, etc.",
    )
    number_of_floors: int = Field(default=1, description="Number of habitable floor levels (1, 2, 3...)")
    building_type: Literal["residential", "commercial", "villa", "apartment", "duplex"] = "residential"

    rooms: List[RoomItem] = Field(default_factory=list, description="Explicit list of requested rooms")
    room_counts: Dict[str, int] = Field(
        default_factory=lambda: {
            "bedrooms": 3,
            "bathrooms": 2,
            "living": 1,
            "dining": 1,
            "kitchen": 1,
            "pooja": 1,
            "parking": 1,
        },
        description="Aggregated room counts mapping room type to integer count",
    )
    minimum_room_areas: Dict[str, float] = Field(
        default_factory=dict,
        description="Minimum area thresholds per room type",
    )
    preferred_room_areas: Dict[str, float] = Field(
        default_factory=dict,
        description="Preferred area targets per room type",
    )

    room_adjacency: List[AdjacencyRequirement] = Field(default_factory=list)
    room_separation: List[SeparationRequirement] = Field(default_factory=list)

    parking: ParkingRequirement = Field(default_factory=ParkingRequirement)
    staircase: StaircaseRequirement = Field(default_factory=StaircaseRequirement)
    courtyard: CourtyardRequirement = Field(default_factory=CourtyardRequirement)
    balcony: BalconyRequirement = Field(default_factory=BalconyRequirement)
    terrace: TerraceRequirement = Field(default_factory=TerraceRequirement)

    natural_light_priority: Literal["maximum", "high", "standard", "low"] = "high"
    cross_ventilation_priority: Literal["maximum", "high", "standard", "low"] = "high"
    architectural_style: str = "Modern Contemporary Indian"
    vastu_preferences: VastuPreference = Field(default_factory=VastuPreference)
    design_3d: Design3DPreferences = Field(default_factory=Design3DPreferences)

    special_requirements: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(
        default_factory=list,
        description="All assumptions made when interpreting underspecified requests",
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="Key information missing from user prompt (e.g. plot size, orientation)",
    )


# ─── Conversational Design Operations ────────────────────────────────────────
DesignOpType = Literal[
    "ADD_ROOM",
    "REMOVE_ROOM",
    "RESIZE_ROOM",
    "MOVE_ROOM",
    "CHANGE_ORIENTATION",
    "CHANGE_STYLE",
    "CHANGE_FACADE",
    "CHANGE_LIGHTING",
    "CHANGE_FLOORS",
    "ADD_PARKING",
    "ADD_COURTYARD",
    "ADD_BALCONY",
    "ADD_TERRACE",
    "OPTIMIZE_VASTU",
]


class DesignOperation(BaseModel):
    operation: DesignOpType = Field(description="Deterministic design action to execute")
    target: str = Field(description="Target room type, space or feature (e.g. 'kitchen', 'master_bedroom')")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the operation, e.g. {'width': 14, 'height': 16, 'unit': 'ft'}",
    )


class DesignOperationResult(BaseModel):
    operations: List[DesignOperation] = Field(default_factory=list)
    summary: str = Field(description="Summary of architectural modifications to apply")
    assumptions: List[str] = Field(default_factory=list)


# ─── Floorplan Image Understanding ───────────────────────────────────────────
class DetectedImageRoom(BaseModel):
    name: str = Field(description="Name or label written on the room, e.g. 'Bed Room', 'Kitchen'")
    type: str = Field(default="bedroom", description="Inferred standardized room type")
    dimensions_text: Optional[str] = Field(
        default=None, description="Verbatim dimension text found in image, e.g. 12'x14'"
    )
    estimated_width: Optional[float] = None
    estimated_depth: Optional[float] = None
    bounding_box_norm: Optional[List[float]] = Field(
        default=None, description="[ymin, xmin, ymax, xmax] normalized 0..1 coordinates"
    )
    vastu_zone: Optional[str] = None


class DetectedImageOpening(BaseModel):
    type: Literal["door", "window", "opening"] = "door"
    wall_side: Optional[str] = None
    position_norm: Optional[List[float]] = None


class DetectedImageWall(BaseModel):
    is_exterior: bool = False
    start_norm: Optional[List[float]] = None
    end_norm: Optional[List[float]] = None


class FloorplanImageAnalysis(BaseModel):
    """
    Structured interpretation of an uploaded 2D floorplan drawing.
    Dimensions are recorded only if visible; never fabricated.
    """
    rooms: List[DetectedImageRoom] = Field(default_factory=list)
    walls_detected: bool = True
    doors_detected: bool = True
    windows_detected: bool = True
    stairs_detected: bool = False
    columns_detected: bool = False
    dimensions_visible: bool = False
    dimensions_unit: Optional[str] = None
    orientation_visible: bool = False
    detected_orientation: Optional[str] = None
    parking_detected: bool = False
    balconies_detected: bool = False
    circulation_summary: str = ""
    estimated_plot_aspect_ratio: Optional[float] = None
    unreadable_elements: List[str] = Field(default_factory=list)
    notes_and_assumptions: List[str] = Field(default_factory=list)


# ─── API Request / Response Models ───────────────────────────────────────────
class RequirementsRequest(BaseModel):
    prompt: str = Field(description="Natural-language architectural prompt")
    project: Optional[Dict[str, Any]] = None


class RequirementsResponse(BaseModel):
    success: bool = True
    requirements: HouseRequirements
    wizardSync: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class GenerateFloorplanRequest(BaseModel):
    prompt: Optional[str] = Field(default="", description="Natural-language house prompt")
    topK: int = Field(default=3, ge=1, le=5, description="Number of floorplan candidates to return")
    project: Optional[Dict[str, Any]] = Field(default=None, description="Optional existing project state")


class ModifyFloorplanRequest(BaseModel):
    prompt: str = Field(description="Conversational modification request (e.g. 'Make kitchen larger')")
    candidate: Dict[str, Any] = Field(description="Current floorplan candidate to modify")
    project: Optional[Dict[str, Any]] = None


class AIStatusResponse(BaseModel):
    configured: bool
    provider: str
    model: str
    activeCapabilities: List[str]
    maxCandidates: int
    defaultUnit: str
    vastuEnabled: bool
    blenderEnabled: bool
