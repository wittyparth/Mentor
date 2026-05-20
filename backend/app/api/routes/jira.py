import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import RedirectResponse

from app.api.deps import CurrentUser, SessionDep, RedisDep
from app.core.config import settings
from app.integrations.linear.client import LinearOAuth
from app.schemas.jira import JiraPushInput, JiraPushResult, JiraSitePublic, JiraProjectPublic
from app.services.jira_service import list_jira_sites

router = APIRouter(prefix="/jira", tags=["jira"])


@router.get("/oauth/start")
async def jira_oauth_start(
    current_user: CurrentUser,
    redis: RedisDep,
) -> RedirectResponse:
    import secrets as sec

    state = sec.token_urlsafe(32)
    await redis.setex(f"jira_oauth_state:{current_user.id}", 600, state)

    url = LinearOAuth.build_authorization_url(state=state)
    return RedirectResponse(url=url)


@router.get("/oauth/callback")
async def jira_oauth_callback(
    code: str,
    state: str,
    current_user: CurrentUser,
    session: SessionDep,
    redis: RedisDep,
):
    stored_state = await redis.get(f"jira_oauth_state:{current_user.id}")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    await redis.delete(f"jira_oauth_state:{current_user.id}")

    token_data = await LinearOAuth.exchange_code_for_tokens(code=code)
    access_token = token_data.get("access_token", "")
    refresh_token = token_data.get("refresh_token", "")

    from app.services.jira_service import store_jira_tokens
    await store_jira_tokens(
        session=session,
        user_id=current_user.id,
        cloud_id="linear",
        site_name="Linear",
        access_token=access_token,
        refresh_token=refresh_token,
    )

    return RedirectResponse(url=f"{settings.FRONTEND_HOST}?jira_connected=true")


@router.get("/sites", response_model=list[JiraSitePublic])
async def list_sites(
    session: SessionDep,
    current_user: CurrentUser,
) -> list[JiraSitePublic]:
    return await list_jira_sites(session=session, user_id=current_user.id)


@router.post("/push/{project_id}", response_model=JiraPushResult)
async def push_to_jira(
    project_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    push_data: JiraPushInput,
) -> JiraPushResult:
    from app.repositories.project_repo import update_project, get_project_by_id
    from app.repositories.job_repo import create_job

    project = await get_project_by_id(session=session, project_id=project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    await update_project(
        session=session,
        project=project,
        update_data={
            "jira_cloud_id": push_data.cloud_id,
            "jira_project_key": push_data.project_key,
        },
    )

    job = await create_job(
        session=session,
        project_id=project_id,
        job_type="linear_push",
    )

    return JiraPushResult(
        job_id=str(job.id),
        message="Push job enqueued. Check SSE for progress.",
    )