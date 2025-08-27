from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

# Models
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    workspace_id: str
    project_type: str  # 'data_quality', 'ml_pipeline', 'analytics', 'etl'
    priority: str = 'medium'  # 'low', 'medium', 'high', 'critical'

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    workspace_id: str
    project_type: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
    progress: int = 0

# In-memory storage (replace with database in production)
projects_db = [
    {
        "id": "1",
        "name": "Customer Data Quality Pipeline",
        "description": "Automated quality checks for customer data",
        "workspace_id": "1",
        "project_type": "data_quality",
        "priority": "high",
        "status": "in_progress",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "progress": 75
    },
    {
        "id": "2",
        "name": "Sales Analytics Dashboard",
        "description": "Real-time sales performance monitoring",
        "workspace_id": "3",
        "project_type": "analytics",
        "priority": "medium",
        "status": "completed",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "progress": 100
    },
    {
        "id": "3",
        "name": "ML Model Training Pipeline",
        "description": "Automated machine learning model training",
        "workspace_id": "1",
        "project_type": "ml_pipeline",
        "priority": "critical",
        "status": "planning",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "progress": 15
    }
]

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(workspace_id: Optional[str] = None):
    """Get all projects, optionally filtered by workspace"""
    if workspace_id:
        return [p for p in projects_db if p["workspace_id"] == workspace_id]
    return projects_db

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get a specific project by ID"""
    for project in projects_db:
        if project["id"] == project_id:
            return project
    raise HTTPException(status_code=404, detail="Project not found")

@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate):
    """Create a new project"""
    new_project = {
        "id": str(uuid.uuid4()),
        "name": project.name,
        "description": project.description,
        "workspace_id": project.workspace_id,
        "project_type": project.project_type,
        "priority": project.priority,
        "status": "planning",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "progress": 0
    }
    projects_db.append(new_project)
    return new_project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, project_update: ProjectUpdate):
    """Update an existing project"""
    for i, project in enumerate(projects_db):
        if project["id"] == project_id:
            # Update only provided fields
            if project_update.name is not None:
                project["name"] = project_update.name
            if project_update.description is not None:
                project["description"] = project_update.description
            if project_update.project_type is not None:
                project["project_type"] = project_update.project_type
            if project_update.priority is not None:
                project["priority"] = project_update.priority
            if project_update.status is not None:
                project["status"] = project_update.status
            
            project["updated_at"] = datetime.now()
            projects_db[i] = project
            return project
    
    raise HTTPException(status_code=404, detail="Project not found")

@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    for i, project in enumerate(projects_db):
        if project["id"] == project_id:
            deleted_project = projects_db.pop(i)
            return {"message": f"Project '{deleted_project['name']}' deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Project not found")

@router.put("/{project_id}/progress")
async def update_project_progress(project_id: str, progress: int):
    """Update project progress (0-100)"""
    if progress < 0 or progress > 100:
        raise HTTPException(status_code=400, detail="Progress must be between 0 and 100")
    
    for i, project in enumerate(projects_db):
        if project["id"] == project_id:
            project["progress"] = progress
            project["updated_at"] = datetime.now()
            
            # Auto-update status based on progress
            if progress == 100:
                project["status"] = "completed"
            elif progress >= 75:
                project["status"] = "near_completion"
            elif progress >= 50:
                project["status"] = "in_progress"
            elif progress >= 25:
                project["status"] = "started"
            else:
                project["status"] = "planning"
            
            projects_db[i] = project
            return {"message": f"Project progress updated to {progress}%"}
    
    raise HTTPException(status_code=404, detail="Project not found")

@router.get("/types", response_model=List[str])
async def get_project_types():
    """Get available project types"""
    return ["data_quality", "ml_pipeline", "analytics", "etl", "reporting", "integration"]

@router.get("/priorities", response_model=List[str])
async def get_project_priorities():
    """Get available project priorities"""
    return ["low", "medium", "high", "critical"]

@router.get("/statuses", response_model=List[str])
async def get_project_statuses():
    """Get available project statuses"""
    return ["planning", "started", "in_progress", "near_completion", "completed", "on_hold", "cancelled"]
