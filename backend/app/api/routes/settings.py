import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, SessionDep, RedisDep
from app.schemas.settings import AIProviderConfigCreate, AIProviderConfigPublic
from app.services.settings_service import get_provider_config, save_provider_config, delete_provider_config

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/ai-provider", response_model=AIProviderConfigPublic | None)
async def get_ai_provider(
    session: SessionDep,
    current_user: CurrentUser,
) -> AIProviderConfigPublic | None:
    return await get_provider_config(session=session, user_id=current_user.id)


@router.post("/ai-provider", response_model=AIProviderConfigPublic)
async def save_ai_provider(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    config_in: AIProviderConfigCreate,
) -> AIProviderConfigPublic:
    return await save_provider_config(
        session=session, user_id=current_user.id, config_in=config_in
    )


@router.delete("/ai-provider")
async def delete_ai_provider(
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    await delete_provider_config(session=session, user_id=current_user.id)
    return {"message": "AI provider config deleted"}