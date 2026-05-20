import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import AIProviderConfig


async def get_active_config(*, session: AsyncSession, user_id: uuid.UUID) -> AIProviderConfig | None:
    stmt = select(AIProviderConfig).where(
        AIProviderConfig.user_id == user_id, AIProviderConfig.is_active == True
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_config(
    *,
    session: AsyncSession,
    user_id: uuid.UUID,
    provider: str,
    model_name: str,
    api_key_enc: str,
    base_url: str | None = None,
) -> AIProviderConfig:
    existing = await get_active_config(session=session, user_id=user_id)
    if existing:
        existing.is_active = False
        session.add(existing)

    config = AIProviderConfig(
        user_id=user_id,
        provider=provider,
        model_name=model_name,
        api_key_enc=api_key_enc,
        base_url=base_url,
        is_active=True,
    )
    session.add(config)
    await session.commit()
    await session.refresh(config)
    return config


async def delete_config(*, session: AsyncSession, user_id: uuid.UUID) -> None:
    config = await get_active_config(session=session, user_id=user_id)
    if config:
        await session.delete(config)
        await session.commit()