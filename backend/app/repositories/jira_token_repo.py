import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import JiraToken


async def create_jira_token(
    *,
    session: AsyncSession,
    user_id: uuid.UUID,
    cloud_id: str,
    site_name: str | None,
    access_token_enc: str,
    refresh_token_enc: str,
    expires_at=None,
) -> JiraToken:
    token = JiraToken(
        user_id=user_id,
        cloud_id=cloud_id,
        site_name=site_name,
        access_token_enc=access_token_enc,
        refresh_token_enc=refresh_token_enc,
        expires_at=expires_at,
    )
    session.add(token)
    await session.commit()
    await session.refresh(token)
    return token


async def get_jira_token_by_user_and_cloud(
    *, session: AsyncSession, user_id: uuid.UUID, cloud_id: str
) -> JiraToken | None:
    stmt = select(JiraToken).where(
        JiraToken.user_id == user_id, JiraToken.cloud_id == cloud_id
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_jira_tokens_by_user(
    *, session: AsyncSession, user_id: uuid.UUID
) -> list[JiraToken]:
    stmt = select(JiraToken).where(JiraToken.user_id == user_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_jira_token(
    *,
    session: AsyncSession,
    token: JiraToken,
    access_token_enc: str | None = None,
    refresh_token_enc: str | None = None,
    expires_at=None,
) -> JiraToken:
    if access_token_enc is not None:
        token.access_token_enc = access_token_enc
    if refresh_token_enc is not None:
        token.refresh_token_enc = refresh_token_enc
    if expires_at is not None:
        token.expires_at = expires_at
    session.add(token)
    await session.commit()
    await session.refresh(token)
    return token


async def delete_jira_token(*, session: AsyncSession, token: JiraToken) -> None:
    await session.delete(token)
    await session.commit()