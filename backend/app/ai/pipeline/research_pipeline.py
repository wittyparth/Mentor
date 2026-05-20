import json
import logging

from app.ai.client import get_default_model
from app.ai.prompts.stack_analysis import build_stack_analysis_prompt
from app.ai.prompts.query_generation import build_query_generation_prompt
from app.ai.prompts.synthesis import build_synthesis_prompt
from app.ai.prompts.scope_calibration import build_scope_calibration_prompt
from app.ai.prompts.plan_generation import build_plan_generation_prompt
from app.ai.output_models.stack_analysis import StackAnalysisOutput
from app.ai.output_models.research import SearchQueryList, ResearchBriefOutput
from app.ai.output_models.plan import FullPlan
from app.integrations.exa import search, format_search_results

logger = logging.getLogger(__name__)


async def run_stack_analysis(
    ai_client,
    project_context: dict,
    skill_level: str = "knows_basics",
) -> StackAnalysisOutput:
    messages = build_stack_analysis_prompt(
        project_idea=project_context.get("raw_idea", ""),
        mentioned_stack=project_context.get("tech_stack", {}).get("additional", []) if project_context.get("tech_stack") else None,
        clarification_qa=project_context.get("clarifications", []),
        skill_level=skill_level,
    )
    response = ai_client.chat.completions.create(
        model=get_default_model(cheap=True),
        response_model=StackAnalysisOutput,
        messages=messages,
        max_retries=2,
    )
    return response


async def run_query_generation(
    ai_client,
    project_context: dict,
    stack_analysis: StackAnalysisOutput,
) -> SearchQueryList:
    messages = build_query_generation_prompt(
        project_idea=project_context.get("raw_idea", ""),
        skill_level=project_context.get("skill_level", "knows_basics"),
        complete_stack=stack_analysis.complete_stack,
        gaps=[d.category for d in stack_analysis.decisions],
    )
    model = get_default_model(cheap=True)
    response = ai_client.chat.completions.create(
        model=model,
        response_model=SearchQueryList,
        messages=messages,
        max_retries=2,
    )
    return response


async def run_parallel_search(query_list: SearchQueryList) -> list[dict]:
    queries = []
    for q in query_list.queries:
        if q.priority <= 2 or len(queries) < 10:
            queries.append(q.query)
    return await search(queries=queries)


async def run_synthesis(
    ai_client,
    project_context: dict,
    stack_analysis: StackAnalysisOutput,
    search_results: list[dict],
) -> ResearchBriefOutput:
    formatted = format_search_results(search_results)
    messages = build_synthesis_prompt(
        stack_decisions=[d.model_dump() for d in stack_analysis.decisions],
        search_results=formatted,
        project_idea=project_context.get("raw_idea", ""),
        skill_level=project_context.get("skill_level", "knows_basics"),
        constraints=project_context.get("constraints"),
    )
    model = get_default_model(cheap=True)
    response = ai_client.chat.completions.create(
        model=model,
        response_model=ResearchBriefOutput,
        messages=messages,
        max_retries=2,
    )
    return response


async def run_scope_calibration(
    ai_client,
    project_context: dict,
    research_brief: ResearchBriefOutput,
) -> dict:
    messages = build_scope_calibration_prompt(
        research_brief=research_brief.model_dump_json(),
        constraints=project_context.get("constraints", {}),
        skill_level=project_context.get("skill_level", "knows_basics"),
    )
    model = get_default_model(cheap=True)
    response = ai_client.chat.completions.create(
        model=model,
        response_model=dict,
        messages=messages,
        max_retries=2,
    )
    return response


async def run_plan_generation(
    ai_client,
    project_context: dict,
    research_brief: ResearchBriefOutput,
    scoped_features: dict,
) -> FullPlan:
    messages = build_plan_generation_prompt(
        project_idea=project_context.get("raw_idea", ""),
        research_brief=research_brief.model_dump_json(),
        scoped_features=json.dumps(scoped_features, default=str),
        constraints=project_context.get("constraints"),
        skill_level=project_context.get("skill_level", "knows_basics"),
    )
    model = get_default_model(cheap=False)
    response = ai_client.chat.completions.create(
        model=model,
        response_model=FullPlan,
        messages=messages,
        max_retries=3,
        temperature=0.3,
    )

    if response.epics and response.stories:
        epic_ids = {e.id for e in response.epics}
        story_ids = {s.summary for s in response.stories}
        for story in response.stories:
            if story.epic_id not in epic_ids:
                story.epic_id = response.epics[0].id

    return response