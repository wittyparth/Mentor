import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.schemas.project import ProjectDetail, ProjectList
from app.services.project_service import get_project_detail, list_user_projects

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=ProjectList)
async def read_projects(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> ProjectList:
    return await list_user_projects(
        session=session, user_id=current_user.id, skip=skip, limit=limit
    )


@router.get("/{project_id}", response_model=ProjectDetail)
async def read_project(
    project_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> ProjectDetail:
    project = await get_project_detail(
        session=session, project_id=project_id, user_id=current_user.id
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project