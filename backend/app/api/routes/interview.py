import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.schemas.project import (
    ClarificationInput,
    ClarificationOutput,
    InterviewSubmitInput,
    ProjectDetail,
    ProjectList,
    ProjectPublic,
)
from app.services.interview_service import get_clarification_questions
from app.services.project_service import submit_interview, get_project_detail, list_user_projects

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/clarify", response_model=ClarificationOutput)
async def clarify(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    input_data: ClarificationInput,
) -> ClarificationOutput:
    try:
        return await get_clarification_questions(
            session=session, user_id=current_user.id, input_data=input_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI clarification failed: {str(e)}",
        )


@router.post("/submit")
async def submit(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    interview_data: InterviewSubmitInput,
) -> dict:
    project = await submit_interview(
        session=session, user_id=current_user.id, interview_data=interview_data
    )

    from app.repositories.job_repo import create_job
    job = await create_job(
        session=session,
        project_id=project.id,
        job_type="research_pipeline",
    )

    return {
        "project_id": str(project.id),
        "job_id": str(job.id),
        "status": project.status,
        "message": "Interview submitted. Research pipeline starting.",
    }