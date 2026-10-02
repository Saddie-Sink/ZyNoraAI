"""
Projects API Router
"""
from fastapi import APIRouter
from typing import List, Dict, Any
from backend.app.core.schemas import ProjectCreate

router = APIRouter(prefix="/projects", tags=["projects"])

# In-memory store
projects_db: Dict[str, Any] = {
    "proj-001": {
        "id": "proj-001",
        "name": "Ananya Luxury Villa",
        "projectType": "Independent Villa",
        "purpose": "New Construction",
        "city": "ECR, Chennai, TN",
        "area": "2,400 sq ft",
        "floors": 2,
        "style": "Modern Indian",
        "status": "Ready",
        "updatedAt": "Today",
        "location": {"city": "Chennai", "state": "Tamil Nadu", "country": "India", "orientation": "East"},
        "property": {"builtUpArea": 2400, "floors": 2, "siteWidth": 50, "siteLength": 80},
        "stats": {
            "site": "Configured",
            "floorplans": "5 Candidates Generated",
            "mlRank": "Candidate B Top",
            "model3d": "Massing Ready",
            "renderings": "5 Perspectives Synthesized"
        }
    }
}

@router.post("")
def create_project(payload: ProjectCreate):
    new_id = f"proj-{len(projects_db) + 1:03d}"
    proj_dict = payload.model_dump()
    proj_dict["id"] = new_id
    proj_dict["city"] = f"{payload.location.city}, {payload.location.state}"
    proj_dict["area"] = f"{payload.property.builtUpArea:,.0f} sq ft"
    proj_dict["floors"] = payload.property.floors
    proj_dict["status"] = "Ready"
    proj_dict["updatedAt"] = "Just now"
    proj_dict["stats"] = {
        "site": "Configured",
        "floorplans": "5 Candidates Generated",
        "mlRank": "Pareto Ranked",
        "model3d": "Massing Ready",
        "renderings": "5 Views Ready"
    }
    projects_db[new_id] = proj_dict
    return {"success": True, "data": proj_dict}

@router.get("")
def list_projects():
    return {"success": True, "data": list(projects_db.values())}

@router.get("/{project_id}")
def get_project(project_id: str):
    found = projects_db.get(project_id, list(projects_db.values())[0])
    return {"success": True, "data": found}
