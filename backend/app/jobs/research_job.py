import json
import logging
import uuid

from arq import cron

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.redis import get_redis_pool
from app.models.project import JobStatus, ProjectStatus
from app.repositories import project_repo as p_repo
from app.repositories import job_repo as j_repo
from app.ai.client import get_default_ai_client, get_ai_client
from app.ai.pipeline.research_pipeline import (
    run_stack_analysis,
    run_query_generation,
    run_parallel_search,
    run_synthesis,
    run_scope_calibration,
    run_plan_generation,
)

logger = logging.getLogger(__name__)


async def research_pipeline_task(ctx: dict, project_id: str) -> None:
    project_id = uuid.UUID(project_id)

    async with AsyncSessionLocal() as session:
        project = await p_repo.get_project_by_id(session=session, project_id=project_id)
        if not project:
            logger.error(f"Project {project_id} not found")
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
            job.progress = progress
            await j_repo.update_job_status(
                session=session, job=job, status=JobStatus.RUNNING.value, progress=progress
            )

        try:
            ai_config = None
            if project.user_id:
                from app.repositories.ai_provider_repo import get_active_config
                ai_config = await get_active_config(session=session, user_id=project.user_id)

            ai_client = get_ai_client(ai_config) if ai_config else get_default_ai_client()

            project_context = {
                "raw_idea": project.raw_idea,
                "entry_type": project.entry_type,
                "tech_stack": project.tech_stack,
                "skill_level": project.skill_level,
                "constraints": project.constraints,
                "clarifications": project.clarifications or [],
            }

            if not project.stack_analysis:
                await publish_progress("stack_analysis", 1, 6, "Analyzing your tech stack...")
                stack_analysis = await run_stack_analysis(ai_client, project_context, project_context.get("skill_level", "knows_basics"))
                project = await p_repo.update_project(session=session, project=project, update_data={"stack_analysis": stack_analysis.model_dump(), "status": ProjectStatus.RESEARCHING.value})
            else:
                from app.ai.output_models.stack_analysis import StackAnalysisOutput
                stack_analysis = StackAnalysisOutput(**project.stack_analysis)

            if not project.research_brief:
                await publish_progress("query_generation", 2, 6, "Generating research queries...")
                query_list = await run_query_generation(ai_client, project_context, stack_analysis)

                await publish_progress("parallel_search", 3, 6, "Researching topics in parallel...")
                search_results = await run_parallel_search(query_list)

                await publish_progress("synthesis", 4, 6, "Synthesizing research findings...")
                research_brief = await run_synthesis(ai_client, project_context, stack_analysis, search_results)
                project = await p_repo.update_project(session=session, project=project, update_data={"research_brief": research_brief.model_dump()})
            else:
                from app.ai.output_models.research import ResearchBriefOutput
                research_brief = ResearchBriefOutput(**project.research_brief)

            if not project.scoped_features:
                await publish_progress("scope_calibration", 5, 6, "Calibrating scope to your timeline...")
                scoped_features_raw = await run_scope_calibration(ai_client, project_context, research_brief)
                scoped_features = scoped_features_raw if isinstance(scoped_features_raw, dict) else scoped_features_raw.model_dump() if hasattr(scoped_features_raw, "model_dump") else {}
                project = await p_repo.update_project(session=session, project=project, update_data={"scoped_features": scoped_features})
            else:
                scoped_features = project.scoped_features

            if not project.plan_json:
                await publish_progress("plan_generation", 6, 6, "Generating your project plan...")
                plan = await run_plan_generation(ai_client, project_context, research_brief, scoped_features)
                project = await p_repo.update_project(session=session, project=project, update_data={
                    "plan_json": plan.model_dump(),
                    "status": ProjectStatus.READY.value,
                })
            else:
                from app.ai.output_models.plan import FullPlan
                plan = FullPlan(**project.plan_json)
                project = await p_repo.update_project(session=session, project=project, update_data={
                    "status": ProjectStatus.READY.value,
                })

            await j_repo.update_job_status(
                session=session, job=job, status=JobStatus.COMPLETED.value,
                progress={"stage": "complete", "done": 6, "total": 6, "message": "Plan ready!"}
            )
            await redis.publish(channel, json.dumps({"event": "complete", "project_id": str(project_id)}))

        except Exception as e:
            logger.exception(f"Research pipeline failed for project {project_id}")
            await j_repo.update_job_status(
                session=session, job=job, status=JobStatus.FAILED.value, error=str(e)
            )
            await p_repo.update_project(session=session, project=project, update_data={"status": ProjectStatus.FAILED.value})
            await redis.publish(channel, json.dumps({"event": "failed", "error": str(e)}))
            raise