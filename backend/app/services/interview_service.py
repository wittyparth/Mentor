import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import get_default_ai_client, get_ai_client
from app.repositories import project_repo
from app.schemas.project import ClarificationInput, ClarificationOutput


async def get_clarification_questions(
    *,
    session: AsyncSession,
    user_id: uuid.UUID,
    input_data: ClarificationInput,
) -> ClarificationOutput:
    from app.ai.prompts.clarification import build_clarification_prompt
    from app.ai.output_models.clarification import ClarificationResponse

    ai_config_repo = await _get_user_ai_config(session=session, user_id=user_id)
    if ai_config_repo:
        client = get_ai_client(ai_config_repo)
    else:
        client = get_default_ai_client()

    messages = build_clarification_prompt(
        entry_type=input_data.entry_type.value,
        raw_idea=input_data.raw_idea,
        tech_stack=input_data.tech_stack,
        skill_level=input_data.skill_level.value if input_data.skill_level else None,
        constraints=input_data.constraints.model_dump() if input_data.constraints else None,
    )

    response = client.chat.completions.create(
        response_model=ClarificationResponse,
        messages=messages,
        max_retries=2,
    )

    return ClarificationOutput(
        questions=[
            {
                "question": q.question,
                "why_it_matters": q.why_it_matters,
                "is_critical": q.is_critical,
                "suggested_options": q.suggested_options,
            }
            for q in response.questions[:4]
        ],
        confidence_assessment=response.confidence_assessment,
    )


async def _get_user_ai_config(session: AsyncSession, user_id: uuid.UUID):
    from app.repositories.ai_provider_repo import get_active_config
    return await get_active_config(session=session, user_id=user_id)