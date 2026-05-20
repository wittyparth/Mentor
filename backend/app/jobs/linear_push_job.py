import json
import logging
import uuid

from app.core.database import AsyncSessionLocal
from app.core.redis import get_redis_pool
from app.models.project import JobStatus, ProjectStatus
from app.repositories import project_repo as p_repo
from app.repositories import job_repo as j_repo
from app.integrations.linear.client import LinearClient
from app.core.encryption import decrypt
from app.repositories.jira_token_repo import get_jira_token_by_user_and_cloud

logger = logging.getLogger(__name__)


async def linear_push_task(ctx: dict, project_id: str) -> None:
    project_id = uuid.UUID(project_id)

    async with AsyncSessionLocal() as session:
        project = await p_repo.get_project_by_id(session=session, project_id=project_id)
        if not project or not project.plan_json:
            logger.error(f"Project {project_id} not found or has no plan")
            return

        job = await j_repo.get_job_by_project_id(session=session, project_id=project_id)
        if not job:
            logger.error(f"Job for project {project_id} not found")
            return

        redis = ctx.get("redis") or await get_redis_pool()
        channel = f"devmentor:progress:{project_id}"

        async def publish_progress(stage: str, done: int, total: int, message: str):
            progress = {"stage": stage, "done": done, "total": total, "message": message}
            await redis.publish(channel, json.dumps({"event": "progress", **progress}))
            await j_repo.update_job_status(
                session=session, job=job, status=JobStatus.RUNNING.value, progress=progress
            )

        try:
            created_keys = project.jira_created_keys or {}

            if not project.jira_cloud_id or not project.jira_project_key:
                raise ValueError("Project missing Linear configuration")

            jira_token = await get_jira_token_by_user_and_cloud(
                session=session, user_id=project.user_id, cloud_id=project.jira_cloud_id
            )
            if not jira_token:
                raise ValueError("No Linear token found for this user/cloud")

            access_token = decrypt(jira_token.access_token_enc)
            client = LinearClient(access_token=access_token)

            teams = await client.get_teams()
            if not teams:
                raise ValueError("No Linear teams found for this user")
            team_id = teams[0]["id"]

            plan = project.plan_json
            created_keys = {}

            await publish_progress("creating_project", 1, 5, "Creating Linear project...")
            linear_project = await client.create_project(
                team_id=team_id,
                name=plan.get("epics", [{}])[0].get("name", "Project") if plan.get("epics") else "Project",
                description=plan.get("plan_summary", ""),
            )
            project_id_linear = linear_project.get("id")
            created_keys["project_id"] = project_id_linear

            await p_repo.update_project(session=session, project=project, update_data={"jira_created_keys": created_keys})

            await publish_progress("creating_stories", 2, 5, "Creating stories and subtasks...")
            epic_id_map = {}
            for epic in plan.get("epics", []):
                pass

            total_stories = len(plan.get("stories", []))
            for i, story in enumerate(plan.get("stories", [])):
                label_ids = []
                epic_data = next((e for e in plan.get("epics", []) if e.get("id") == story.get("epic_id")), None)
                label_name = epic_data.get("name", "") if epic_data else ""

                await client.create_issue(
                    team_id=team_id,
                    title=story.get("summary", "Untitled"),
                    description=story.get("description", ""),
                    priority=1 if story.get("priority") == "Highest" else 2 if story.get("priority") == "High" else 3,
                    project_id=project_id_linear,
                )

                for subtask in story.get("subtasks", []):
                    await client.create_issue(
                        team_id=team_id,
                        title=subtask.get("summary", "Untitled subtask"),
                        description=subtask.get("description", ""),
                        priority=3,
                        project_id=project_id_linear,
                    )

                progress_pct = int((i + 1) / total_stories * 100) if total_stories > 0 else 100
                await publish_progress("creating_stories", 2, 5, f"Creating stories... {progress_pct}%")

            await p_repo.update_project(session=session, project=project, update_data={
                "status": ProjectStatus.PUSHED.value,
                "jira_board_url": f"https://linear.app/team/{team_id}/project/{project_id_linear}",
            })

            await j_repo.update_job_status(
                session=session, job=job, status=JobStatus.COMPLETED.value,
                progress={"stage": "complete", "done": 5, "total": 5, "message": "Plan pushed to Linear!"}
            )
            await redis.publish(channel, json.dumps({
                "event": "jira_complete",
                "board_url": f"https://linear.app/team/{team_id}/project/{project_id_linear}",
            }))

        except Exception as e:
            logger.exception(f"Linear push failed for project {project_id}")
            await j_repo.update_job_status(
                session=session, job=job, status=JobStatus.FAILED.value, error=str(e)
            )
            await p_repo.update_project(session=session, project=project, update_data={"status": ProjectStatus.FAILED.value})
            await redis.publish(channel, json.dumps({"event": "failed", "error": str(e)}))
            raise