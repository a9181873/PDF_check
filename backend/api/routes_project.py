from fastapi import APIRouter, HTTPException

from models.database import list_project_comparisons, list_projects, project_exists
from models.database import create_project as create_project_row
from models.schemas import ProjectCreateRequest, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["project"])


@router.post("", response_model=ProjectResponse)
async def create_project_api(payload: ProjectCreateRequest):
    row = create_project_row(payload.name)
    return ProjectResponse(**row)


@router.get("", response_model=list[ProjectResponse])
async def list_projects_api():
    rows = list_projects()
    return [ProjectResponse(**row) for row in rows]


@router.get("/{project_id}/comparisons")
async def list_project_comparisons_api(project_id: str):
    if not project_exists(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return list_project_comparisons(project_id)
