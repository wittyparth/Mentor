import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt, decrypt
from app.repositories import ai_provider_repo
from app.schemas.settings import AIProviderConfigCreate, AIProviderConfigPublic


async def get_provider_config(
    *, session: AsyncSession, user_id: uuid.UUID
) -> AIProviderConfigPublic | None:
    config = await ai_provider_repo.get_active_config(session=session, user_id=user_id)
    if not config:
        return None
    return AIProviderConfigPublic(
        id=str(config.id),
        provider=config.provider,
        model_name=config.model_name,
        base_url=config.base_url,
        has_key=True,
        is_active=config.is_active,
        created_at=str(config.created_at) if config.created_at else None,
    )


async def save_provider_config(
    *,
    session: AsyncSession,
    user_id: uuid.UUID,
    config_in: AIProviderConfigCreate,
) -> AIProviderConfigPublic:
    encrypted_key = encrypt(config_in.api_key)
    config = await ai_provider_repo.create_config(
        session=session,
        user_id=user_id,
        provider=config_in.provider,
        model_name=config_in.model_name,
        api_key_enc=encrypted_key,
        base_url=config_in.base_url,
    )
    return AIProviderConfigPublic(
        id=str(config.id),
        provider=config.provider,
        model_name=config.model_name,
        base_url=config.base_url,
        has_key=True,
        is_active=config.is_active,
        created_at=str(config.created_at) if config.created_at else None,
    )


async def delete_provider_config(
    *, session: AsyncSession, user_id: uuid.UUID
) -> None:
    await ai_provider_repo.delete_config(session=session, user_id=user_id)